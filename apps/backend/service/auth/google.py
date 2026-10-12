"""Google sign-in (authorization-code flow, server-side exchange).

1. The web app sends the user to Google (its own ``state``/PKCE handling) and posts the
   returned ``code`` + ``redirectUri`` (+ optional PKCE ``codeVerifier``) to
   ``POST /auth/google/callback``.
2. :class:`GoogleOAuthClient` exchanges the code (sync ``httpx``; the route is a ``def``)
   and verifies the ``id_token`` signature against Google's JWKS, the audience
   (``BE_GOOGLE_CLIENT_ID``), issuer and expiry.
3. :class:`GoogleAuthService` maps the identity to a user: by ``external_id`` (Google
   ``sub``), else by verified email (links the account), else auto-registers when
   ``BE_GOOGLE_AUTO_REGISTER=true``. ``BE_GOOGLE_ALLOWED_DOMAINS`` restricts domains.
   A *pending* local account with that email is taken over (its unverified password is
   discarded) because Google proved ownership of the address.
4. The login then continues exactly like a password login (2FA gate, session issuance).
"""

from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import httpx
import jwt
from loguru import logger

from core.errors import (
    AuthenticationError,
    ConfigurationError,
    ConflictError,
    PermissionDeniedError,
    ServiceUnavailableError,
)
from db.base import Repository
from util.helper import censor_email, new_id

if TYPE_CHECKING:
    from core.config import Settings

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105  # endpoint URL, not a secret
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = frozenset({"accounts.google.com", "https://accounts.google.com"})
_USERNAME_SAFE = re.compile(r"[^a-z0-9._-]")


@dataclass(frozen=True)
class GoogleIdentity:
    sub: str
    email: str
    email_verified: bool
    name: str | None = None
    hosted_domain: str | None = None


class GoogleOAuthClient:
    """Code exchange + id_token verification. Holds a cached JWKS client (keep one per app)."""

    def __init__(
        self,
        settings: Settings,
        *,
        transport: httpx.BaseTransport | None = None,
        jwks_client: jwt.PyJWKClient | None = None,
    ) -> None:
        if not settings.google_configured:
            raise ConfigurationError("Google sign-in is not configured")
        self.settings = settings
        self.transport = transport
        self._jwks = jwks_client

    @property
    def jwks(self) -> jwt.PyJWKClient:
        if self._jwks is None:
            self._jwks = jwt.PyJWKClient(
                GOOGLE_JWKS_URL, cache_keys=True, lifespan=3600, timeout=int(self.settings.GOOGLE_HTTP_TIMEOUT)
            )
        return self._jwks

    def exchange_code(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> dict[str, Any]:
        s = self.settings
        form = {
            "code": code,
            "client_id": str(s.GOOGLE_CLIENT_ID),
            "client_secret": s.GOOGLE_CLIENT_SECRET.get_secret_value() if s.GOOGLE_CLIENT_SECRET else "",
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if code_verifier:
            form["code_verifier"] = code_verifier
        try:
            with httpx.Client(timeout=s.GOOGLE_HTTP_TIMEOUT, transport=self.transport) as client:
                response = client.post(GOOGLE_TOKEN_URL, data=form, headers={"Accept": "application/json"})
        except httpx.HTTPError as exc:
            logger.error("Google token exchange failed: {}", type(exc).__name__)
            raise ServiceUnavailableError("Google sign-in is temporarily unavailable") from None
        if response.status_code >= 500:
            logger.error("Google token endpoint returned {}", response.status_code)
            raise ServiceUnavailableError("Google sign-in is temporarily unavailable")
        if response.status_code != 200:
            logger.info("Google rejected the authorization code ({})", response.status_code)
            raise AuthenticationError("Invalid or expired Google authorization code")
        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("id_token"):
            raise AuthenticationError("Google did not return an identity token")
        return payload

    def verify_id_token(self, id_token: str) -> GoogleIdentity:
        try:
            key = self.jwks.get_signing_key_from_jwt(id_token).key
            claims = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=str(self.settings.GOOGLE_CLIENT_ID),
                leeway=self.settings.JWT_LEEWAY,
                options={"require": ["exp", "iat", "iss", "sub", "aud"]},
            )
        except jwt.PyJWKClientError as exc:
            logger.error("Google JWKS lookup failed: {}", type(exc).__name__)
            raise ServiceUnavailableError("Google sign-in is temporarily unavailable") from None
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid Google identity token") from None
        if claims.get("iss") not in GOOGLE_ISSUERS:
            raise AuthenticationError("Invalid Google identity token")
        return identity_from_claims(claims)

    def authenticate(self, code: str, redirect_uri: str, code_verifier: str | None = None) -> GoogleIdentity:
        tokens = self.exchange_code(code, redirect_uri, code_verifier)
        return self.verify_id_token(str(tokens["id_token"]))


def identity_from_claims(claims: dict[str, Any]) -> GoogleIdentity:
    email = str(claims.get("email") or "").strip().lower()
    verified = claims.get("email_verified")
    return GoogleIdentity(
        sub=str(claims["sub"]),
        email=email,
        email_verified=verified is True or verified == "true",
        name=claims.get("name"),
        hosted_domain=claims.get("hd"),
    )


class GoogleAuthService:
    def __init__(self, users: Repository, permissions: Repository, settings: Settings) -> None:
        self.users = users
        self.permissions = permissions
        self.settings = settings

    def _check_identity(self, identity: GoogleIdentity) -> None:
        if not identity.email or not identity.email_verified:
            raise AuthenticationError("Google account email is not verified")
        allowed = self.settings.GOOGLE_ALLOWED_DOMAINS
        domain = identity.email.rpartition("@")[2]
        if allowed and domain not in allowed:
            raise PermissionDeniedError("This Google account's domain is not allowed")

    def resolve_user(self, identity: GoogleIdentity) -> dict[str, Any]:
        """Find, link or (optionally) create the local user for a verified Google identity."""
        self._check_identity(identity)
        user = self.users.find_one({"external_id": identity.sub})
        if user is not None:
            return user
        user = self.users.find_one({"email": identity.email})
        if user is not None:
            return self._link(user, identity)
        if not self.settings.GOOGLE_AUTO_REGISTER:
            raise AuthenticationError("No account is associated with this Google account")
        return self._register(identity)

    def _link(self, user: dict[str, Any], identity: GoogleIdentity) -> dict[str, Any]:
        if user.get("external_id") and user["external_id"] != identity.sub:
            logger.warning("Google sub mismatch for {}", censor_email(identity.email))
            raise AuthenticationError("No account is associated with this Google account")
        changes: dict[str, Any] = {"external_id": identity.sub, "email_verified": True}
        if user.get("status") == "pending":
            # Unverified sign-up: Google proved the address; drop the unverified password.
            changes.update({"status": "active", "password_hash": None, "auth_provider": "google"})
        logger.info("Linked Google identity to {}", censor_email(identity.email))
        return self.users.update(user["id"], changes) or {**user, **changes}

    def _register(self, identity: GoogleIdentity) -> dict[str, Any]:
        local = _USERNAME_SAFE.sub("", identity.email.split("@", 1)[0].lower())[:24] or "user"
        permission = self.permissions.find_one({"alias": self.settings.DEFAULT_PERMISSION_ALIAS})
        user_id = new_id()
        for _ in range(5):
            data = {
                "id": user_id,
                "username": f"{local}-{secrets.token_hex(3)}",
                "fullname": identity.name or local,
                "email": identity.email,
                "status": "active",
                "email_verified": True,
                "auth_provider": "google",
                "external_id": identity.sub,
                "permission_id": permission["id"] if permission else None,
                "created_by": user_id,
            }
            try:
                created = self.users.insert(data)
            except ConflictError:
                existing = self.users.find_one({"external_id": identity.sub}) or self.users.find_one(
                    {"email": identity.email}
                )
                if existing is not None:  # concurrent first sign-in
                    return existing
                continue  # username collision: retry with another suffix
            logger.info("Registered {} via Google", censor_email(identity.email))
            return created
        raise ConflictError("Could not create an account, please try again")
