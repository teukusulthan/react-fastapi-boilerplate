# Pure-function unit tests

Companion to [../SKILL.md](../SKILL.md). These need no app, DB or HTTP — just import and call. Real suites to
copy from: `apps/backend/tests/core/test_security.py`, `apps/backend/tests/db/test_query.py`,
`apps/backend/tests/core/test_config.py`, `apps/backend/tests/db/test_mongo_translator.py`,
`apps/backend/tests/db/test_supabase_translator.py`.

## Contents
- Passwords
- JWT issue/decode
- Payload & field crypto
- Query building (FindDTO → QuerySpec)
- DTO validation
- Settings validation

## Passwords (`core.security`)

```python
from core.errors import ValidationError
from core.security import hash_password, verify_password

def test_hash_and_verify():
    hashed = hash_password("correct horse")
    assert verify_password("correct horse", hashed) and not verify_password("wrong", hashed)
    assert not verify_password("anything", None)          # unknown user still costs a bcrypt round

def test_over_72_bytes_rejected():
    with pytest.raises(ValidationError):
        hash_password("x" * 73)
```

## JWT (`core.security`)

```python
from core.errors import AuthenticationError
from core.security import ACCESS, REFRESH, decode_token, issue_token_pair

def test_type_is_enforced(settings):
    pair = issue_token_pair("user-1", settings)
    assert decode_token(pair.access.token, settings, ACCESS).sub == "user-1"
    with pytest.raises(AuthenticationError):
        decode_token(pair.access.token, settings, REFRESH)
```

Token-store behaviour (revocation, refresh reuse) uses the `redis_client` fixture:
`TokenStore(redis_client, settings)` + `rotate_refresh_token(...)`.

## Crypto (`util.crypto`, `core.security`)

```python
from util.crypto import aesgcm_decrypt, aesgcm_encrypt, decode_aes_key, generate_aes_key

def test_aes_gcm_roundtrip():
    key = decode_aes_key(generate_aes_key())
    token = aesgcm_encrypt(key, b'{"a":1}')
    assert aesgcm_decrypt(key, token) == b'{"a":1}'
```
Secrets at rest: `encrypt_secret(value, make_settings(DATA_ENCRYPTION_KEY=generate_fernet_key()))` /
`decrypt_secret(...)` (no-op without a key).

## Query building (`db.query`)

```python
from core.errors import ValidationError
from db.query import build_query_spec
from db.schema import USERS
from dto.common import FindDTO

def test_sensitive_field_rejected():
    dto = FindDTO.model_validate({"filters": [{"field": "passwordHash", "operator": "is", "value": {"is": "x"}}]})
    with pytest.raises(ValidationError) as exc:
        build_query_spec(dto, USERS)
    assert exc.value.details[0]["field"] == "filters[0].field"
```

## DTO validation

Validate with `Model.model_validate({...camelCase...})` and assert `pydantic.ValidationError` for bad input
(e.g. unknown keys on `extra="forbid"` DTOs, `size` above `BE_MAX_PAGE_SIZE`). Remember `core.errors.ValidationError`
(422 app error) ≠ `pydantic.ValidationError` (raised by models).

## Settings validation

```python
def test_short_jwt_secret_rejected(make_settings):
    with pytest.raises(pydantic.ValidationError):
        make_settings(JWT_SECRET="short")
```
