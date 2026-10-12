"""Session issuance, refresh rotation and logout (local provider), via ``core.security``.

* One login = one session id (``sid``) shared by the access/refresh pair and kept across
  refresh rotations.
* Refresh rotates: the presented refresh ``jti`` is consumed atomically; presenting it
  again (reuse) revokes the whole session family.
* Single-session accounts (``multi_login=false``): a new login revokes the previous
  session and registers the new ``sid`` as the only active one.
* Logout revokes the access ``jti`` and the whole session (so every refresh token of that
  login dies too). Idempotent.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fastapi import Request
from loguru import logger

from core.deps import ensure_user_can_authenticate
from core.errors import AppError, AuthenticationError
from core.security import (
    ACCESS,
    ACCESS_COOKIE,
    REFRESH,
    REFRESH_COOKIE,
    TokenPair,
    TokenStore,
    bearer_token,
    decode_token,
    issue_token_pair,
    rotate_refresh_token,
)
from db.base import Repository
from dto.auth import AuthTokens, LoginResponse
from dto.user_profile import UserProfile
from service.user_profile import load_user_profile
from util.helper import utc_now

if TYPE_CHECKING:
    from core.config import Settings
    from core.security import TokenClaims


@dataclass(frozen=True)
class AuthResult:
    """A completed authentication: token pair + the user's profile."""

    pair: TokenPair
    profile: UserProfile

    def to_response(self) -> LoginResponse:
        return LoginResponse(
            user=self.profile,
            auth=AuthTokens(
                access_token=self.pair.access.token,
                refresh_token=self.pair.refresh.token,
                expires_at=self.pair.access.expires_at,
            ),
        )


class SessionService:
    def __init__(
        self,
        users: Repository,
        permissions: Repository,
        groups: Repository,
        store: TokenStore,
        settings: Settings,
    ) -> None:
        self.users = users
        self.permissions = permissions
        self.groups = groups
        self.store = store
        self.settings = settings

    # ------------------------------------------------------------ login
    def start(self, user: dict[str, Any]) -> AuthResult:
        """Issue a fresh session for an already-authenticated, active user."""
        ensure_user_can_authenticate(user)
        user_id = user["id"]
        pair = issue_token_pair(user_id, self.settings)
        if not user.get("multi_login", True):
            previous = self.store.get_active_session(user_id)
            if previous and previous != pair.session_id:
                self.store.revoke_session(previous)
            self.store.set_active_session(user_id, pair.session_id)
        updated = self.users.update(user_id, {"last_login_at": utc_now()}) or user
        return AuthResult(pair, self.profile(updated))

    def profile(self, user: dict[str, Any]) -> UserProfile:
        return load_user_profile(user, self.permissions, self.groups)

    # ---------------------------------------------------------- refresh
    def _refresh_claims(self, request: Request) -> TokenClaims:
        """Decode the refresh token from ``Authorization: Bearer`` or the ``refresh_token`` cookie."""
        candidates = [token for token in (bearer_token(request), request.cookies.get(REFRESH_COOKIE)) if token]
        if not candidates:
            raise AuthenticationError("Refresh token required")
        error: AppError | None = None
        for token in dict.fromkeys(candidates):
            try:
                return decode_token(token, self.settings, REFRESH)
            except AuthenticationError as exc:
                error = error or exc
        raise error or AuthenticationError("Invalid token")

    def refresh(self, request: Request) -> AuthResult:
        claims = self._refresh_claims(request)
        try:
            user = ensure_user_can_authenticate(self.users.get_by_id(claims.sub))
        except AuthenticationError:
            if claims.session_id:
                self.store.revoke_session(claims.session_id)
            raise
        single = not user.get("multi_login", True)
        if single and not self.store.is_session_current(user["id"], claims.session_id):
            raise AuthenticationError("Session is no longer active")
        pair = rotate_refresh_token(claims, self.store, self.settings)
        if single:
            self.store.set_active_session(user["id"], pair.session_id)
        return AuthResult(pair, self.profile(user))

    # ----------------------------------------------------------- logout
    def _try_decode(self, token: str | None, token_type: str) -> TokenClaims | None:
        if not token:
            return None
        try:
            return decode_token(token, self.settings, token_type)
        except AuthenticationError:
            return None

    def logout(self, request: Request) -> None:
        """Revoke whatever valid local tokens the request carries (never fails)."""
        bearer = bearer_token(request)
        access = self._try_decode(bearer, ACCESS) or self._try_decode(request.cookies.get(ACCESS_COOKIE), ACCESS)
        refresh = self._try_decode(bearer, REFRESH) or self._try_decode(request.cookies.get(REFRESH_COOKIE), REFRESH)
        revoked_sessions: set[str] = set()
        for claims in (access, refresh):
            if claims is None:
                continue
            self.store.revoke(claims)
            if claims.session_id and claims.session_id not in revoked_sessions:
                self.store.revoke_session(claims.session_id)
                self.store.clear_active_session(claims.sub, claims.session_id)
                revoked_sessions.add(claims.session_id)
        if revoked_sessions:
            logger.debug("Logged out {} session(s)", len(revoked_sessions))

    def revoke_all(self, user_id: str) -> None:
        """Invalidate every token issued to the user before now."""
        self.store.revoke_all_for_user(user_id)
