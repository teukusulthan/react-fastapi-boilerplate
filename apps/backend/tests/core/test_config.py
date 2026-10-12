from __future__ import annotations

import pytest
from pydantic import ValidationError

from core.config import Settings, get_settings, load_settings
from util.crypto import generate_aes_key, generate_fernet_key


def test_defaults(settings: Settings) -> None:
    assert settings.PORT == 8020
    assert settings.DB_PROVIDER == "mongo"
    assert settings.AUTH_PROVIDER == "local"
    assert settings.SUPERUSER_ALIASES == ["admin", "owner"]
    assert settings.ENABLED_ROUTERS == []
    assert not settings.s3_configured
    assert not settings.smtp_configured
    assert not settings.kafka_configured


def test_short_jwt_secret_rejected(make_settings) -> None:
    with pytest.raises(ValidationError, match="at least 32"):
        make_settings(JWT_SECRET="short")


def test_csv_and_json_lists(make_settings) -> None:
    s = make_settings(ENABLED_ROUTERS="User, auth ,", CORS_ORIGINS='["http://a.test/", "http://b.test"]')
    assert s.ENABLED_ROUTERS == ["user", "auth"]
    assert s.CORS_ORIGINS == ["http://a.test", "http://b.test"]


def test_wildcard_cors_rejected(make_settings) -> None:
    with pytest.raises(ValidationError, match="not allowed"):
        make_settings(CORS_ORIGINS="*")


def test_enc_requires_valid_secret(make_settings) -> None:
    with pytest.raises(ValidationError, match="ENC_SECRET is required"):
        make_settings(ENC_ACTIVE=True)
    with pytest.raises(ValidationError, match="32 bytes"):
        make_settings(ENC_ACTIVE=True, ENC_SECRET="c2hvcnQ=")
    assert make_settings(ENC_ACTIVE=True, ENC_SECRET=generate_aes_key()).ENC_ACTIVE


def test_data_encryption_key_validated(make_settings) -> None:
    with pytest.raises(ValidationError, match="DATA_ENCRYPTION_KEY"):
        make_settings(DATA_ENCRYPTION_KEY="not-a-fernet-key")
    assert make_settings(DATA_ENCRYPTION_KEY=generate_fernet_key()).DATA_ENCRYPTION_KEY is not None


def test_provider_requirements(make_settings) -> None:
    with pytest.raises(ValidationError, match="SUPABASE_DB_URL is required"):
        make_settings(DB_PROVIDER="supabase")
    with pytest.raises(ValidationError, match="SUPABASE_JWKS_URL or"):
        make_settings(AUTH_PROVIDER="supabase")


def test_internal_token_min_length_and_blank(make_settings) -> None:
    with pytest.raises(ValidationError):
        make_settings(INTERNAL_TOKEN="too-short")
    assert make_settings(INTERNAL_TOKEN="").INTERNAL_TOKEN is None


def test_production_guards(make_settings) -> None:
    with pytest.raises(ValidationError, match="placeholder"):
        make_settings(ENVIRONMENT="production", JWT_SECRET="change-me-" + "x" * 40, COOKIE_SECURE=True)
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        make_settings(ENVIRONMENT="production", COOKIE_SECURE=False)


def test_redis_url(make_settings) -> None:
    s = make_settings(REDIS_HOST="r", REDIS_PORT=6380, REDIS_PASSWORD="pw", REDIS_DB=2, REDIS_SSL=True)
    assert s.redis_url == "rediss://:pw@r:6380/2"
    assert make_settings(REDIS_URL="redis://x:1/0").redis_url == "redis://x:1/0"


def test_env_file_selected_by_be_env_file(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env.custom"
    env_file.write_text("BE_APP_NAME=FromFile\nBE_PORT=9001\nUNPREFIXED=ignored\n")
    monkeypatch.setenv("BE_ENV_FILE", str(env_file))
    monkeypatch.setenv("BE_PORT", "9002")  # real env beats the file
    s = load_settings()
    assert s.APP_NAME == "FromFile"
    assert s.PORT == 9002


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
