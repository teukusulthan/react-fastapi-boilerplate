from __future__ import annotations

import time

import jwt
import pytest

from core.errors import AuthenticationError, ValidationError
from core.security import (
    ACCESS,
    REFRESH,
    SupabaseTokenVerifier,
    TokenStore,
    create_token,
    decode_token,
    decrypt_secret,
    encrypt_secret,
    generate_otp,
    hash_otp,
    hash_password,
    issue_token_pair,
    rotate_refresh_token,
    validate_password_policy,
    verify_internal_token,
    verify_otp,
    verify_password,
)
from util.crypto import FIELD_PREFIX, generate_fernet_key


# ------------------------------------------------------------- passwords
def test_hash_and_verify() -> None:
    hashed = hash_password("correct horse")
    assert hashed.startswith("$2")
    assert verify_password("correct horse", hashed)
    assert not verify_password("wrong", hashed)
    assert not verify_password("anything", None)
    assert not verify_password("anything", "not-a-bcrypt-hash")


def test_password_over_72_bytes_rejected() -> None:
    with pytest.raises(ValidationError):
        hash_password("x" * 73)
    assert not verify_password("x" * 73, hash_password("x" * 72))


def test_password_policy(settings) -> None:
    with pytest.raises(ValidationError) as exc:
        validate_password_policy("short", settings, "newPassword")
    assert exc.value.details[0]["field"] == "newPassword"
    validate_password_policy("long-enough", settings)


# ------------------------------------------------------------------- JWT
def test_token_pair_claims(settings) -> None:
    pair = issue_token_pair("user-1", settings)
    access = decode_token(pair.access.token, settings, ACCESS)
    refresh = decode_token(pair.refresh.token, settings, REFRESH)
    assert access.sub == refresh.sub == "user-1"
    assert access.session_id == refresh.session_id == pair.session_id
    assert access.jti != refresh.jti
    assert access.raw["iss"] == settings.JWT_ISSUER
    assert 0 < access.remaining_seconds <= settings.JWT_ACCESS_TTL


def test_token_type_is_always_checked(settings) -> None:
    pair = issue_token_pair("u", settings)
    with pytest.raises(AuthenticationError, match="type"):
        decode_token(pair.access.token, settings, REFRESH)
    with pytest.raises(AuthenticationError, match="type"):
        decode_token(pair.refresh.token, settings, ACCESS)


def test_expired_token(settings) -> None:
    token = create_token("u", ACCESS, settings, ttl=-60).token
    with pytest.raises(AuthenticationError, match="expired"):
        decode_token(token, settings, ACCESS)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c, s: jwt.encode(c, "another-secret-another-secret-xxxxxxxx", algorithm="HS256"),
        lambda c, s: jwt.encode({**c, "iss": "evil"}, s, algorithm="HS256"),
        lambda c, s: jwt.encode({k: v for k, v in c.items() if k != "jti"}, s, algorithm="HS256"),
        lambda c, s: jwt.encode(c, None, algorithm="none"),
        lambda c, s: "garbage",
    ],
)
def test_invalid_tokens_rejected(settings, mutate) -> None:
    secret = settings.JWT_SECRET.get_secret_value()
    claims = {
        "sub": "u",
        "iat": time.time(),
        "exp": int(time.time()) + 60,
        "jti": "j",
        "type": ACCESS,
        "iss": settings.JWT_ISSUER,
    }
    with pytest.raises(AuthenticationError):
        decode_token(mutate(claims, secret), settings, ACCESS)


# ------------------------------------------------------------ revocation
def test_revoke_jti_session_and_user(settings, redis_client) -> None:
    store = TokenStore(redis_client, settings)
    pair = issue_token_pair("u1", settings)
    claims = decode_token(pair.access.token, settings, ACCESS)
    assert not store.is_revoked(claims)
    store.revoke(claims)
    assert store.is_revoked(claims)
    assert (
        0
        < redis_client.ttl(f"{settings.REDIS_KEY_PREFIX}:auth:revoked:jti:{claims.jti}")
        <= settings.JWT_ACCESS_TTL + 60
    )

    other = decode_token(issue_token_pair("u1", settings).access.token, settings, ACCESS)
    store.revoke_session(other.session_id)
    assert store.is_revoked(other)

    third = decode_token(issue_token_pair("u1", settings).access.token, settings, ACCESS)
    assert not store.is_revoked(third)
    store.revoke_all_for_user("u1")
    assert store.is_revoked(third)
    fresh = decode_token(issue_token_pair("u1", settings).access.token, settings, ACCESS)
    assert not store.is_revoked(fresh)


def test_refresh_rotation_and_reuse_detection(settings, redis_client) -> None:
    store = TokenStore(redis_client, settings)
    pair = issue_token_pair("u2", settings)
    old_refresh = decode_token(pair.refresh.token, settings, REFRESH)
    new_pair = rotate_refresh_token(old_refresh, store, settings)
    assert new_pair.session_id == pair.session_id

    with pytest.raises(AuthenticationError, match="already been used"):
        rotate_refresh_token(old_refresh, store, settings)
    # reuse revoked the whole family, including the freshly rotated tokens
    new_access = decode_token(new_pair.access.token, settings, ACCESS)
    assert store.is_revoked(new_access)
    with pytest.raises(AuthenticationError):
        rotate_refresh_token(decode_token(new_pair.refresh.token, settings, REFRESH), store, settings)


def test_single_session_tracking(settings, redis_client) -> None:
    store = TokenStore(redis_client, settings)
    store.set_active_session("u3", "sid-a")
    assert store.is_session_current("u3", "sid-a")
    assert not store.is_session_current("u3", "sid-b")
    store.clear_active_session("u3", "sid-b")  # not current -> no-op
    assert store.get_active_session("u3") == "sid-a"
    store.clear_active_session("u3", "sid-a")
    assert store.get_active_session("u3") is None


# ------------------------------------------------------------- internal
def test_internal_token(settings, make_settings) -> None:
    good = settings.INTERNAL_TOKEN.get_secret_value()
    assert verify_internal_token(good, settings)
    assert not verify_internal_token(good + "x", settings)
    assert not verify_internal_token(None, settings)
    assert not verify_internal_token(good, make_settings(INTERNAL_TOKEN=None))


# ------------------------------------------------------------------ OTP
def test_otp_hash_is_bound_to_purpose_and_subject(settings) -> None:
    code = generate_otp(6)
    assert len(code) == 6 and code.isdigit()
    stored = hash_otp(code, settings, purpose="register", subject="A@x.io")
    assert code not in stored
    assert verify_otp(code, stored, settings, purpose="register", subject="a@x.io")
    assert not verify_otp(code, stored, settings, purpose="reset", subject="a@x.io")
    assert not verify_otp(code, stored, settings, purpose="register", subject="b@x.io")
    assert not verify_otp("", stored, settings, purpose="register", subject="a@x.io")


# ------------------------------------------------------- secrets at rest
def test_field_encryption(make_settings) -> None:
    plain = make_settings()
    assert encrypt_secret("JBSWY3DP", plain) == "JBSWY3DP"
    keyed = make_settings(DATA_ENCRYPTION_KEY=generate_fernet_key())
    stored = encrypt_secret("JBSWY3DP", keyed)
    assert stored.startswith(FIELD_PREFIX) and "JBSWY3DP" not in stored
    assert decrypt_secret(stored, keyed) == "JBSWY3DP"
    assert decrypt_secret("legacy-plain", keyed) == "legacy-plain"


# -------------------------------------------------------------- supabase
def test_supabase_hs256_verification(make_settings) -> None:
    secret = "supabase-jwt-secret-0123456789abcdef0123"
    s = make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET=secret)
    verifier = SupabaseTokenVerifier(s)
    now = int(time.time())
    good = jwt.encode(
        {"sub": "abc", "aud": "authenticated", "exp": now + 60, "email": "a@b.c"}, secret, algorithm="HS256"
    )
    assert verifier.verify(good)["sub"] == "abc"
    wrong_aud = jwt.encode({"sub": "abc", "aud": "anon", "exp": now + 60}, secret, algorithm="HS256")
    with pytest.raises(AuthenticationError):
        verifier.verify(wrong_aud)
    expired = jwt.encode({"sub": "abc", "aud": "authenticated", "exp": now - 600}, secret, algorithm="HS256")
    with pytest.raises(AuthenticationError, match="expired"):
        verifier.verify(expired)
