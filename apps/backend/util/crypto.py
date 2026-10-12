"""Cryptographic primitives (pure functions, no settings access).

* AES-256-GCM for the optional request/response payload encryption
  (wire format: ``base64(nonce[12] | ciphertext | tag[16])``).
* Fernet (AES-128-CBC + HMAC-SHA256) for encrypting individual secrets at rest
  (e.g. TOTP secrets). Encrypted values carry the ``enc:v1:`` prefix so plaintext
  legacy values can still be read.
"""

from __future__ import annotations

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

GCM_NONCE_BYTES = 12
FIELD_PREFIX = "enc:v1:"


class CryptoError(ValueError):
    """Raised when a key is malformed or a ciphertext cannot be decrypted."""


def decode_aes_key(value: str) -> bytes:
    """Decode a base64 (standard or urlsafe) AES-256 key and check it is 32 bytes."""
    raw = value.strip()
    raw += "=" * (-len(raw) % 4)
    altchars = b"-_" if ("-" in raw or "_" in raw) else None
    try:
        key = base64.b64decode(raw, altchars=altchars, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise CryptoError("AES key must be base64 encoded") from exc
    if len(key) != 32:
        raise CryptoError(f"AES-256 key must decode to 32 bytes, got {len(key)}")
    return key


def aesgcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes | None = None) -> str:
    """Encrypt ``plaintext`` and return ``base64(nonce | ciphertext | tag)``."""
    nonce = os.urandom(GCM_NONCE_BYTES)
    sealed = AESGCM(key).encrypt(nonce, plaintext, associated_data)
    return base64.b64encode(nonce + sealed).decode("ascii")


def aesgcm_decrypt(key: bytes, token: str, associated_data: bytes | None = None) -> bytes:
    """Inverse of :func:`aesgcm_encrypt`. Raises :class:`CryptoError` on any failure."""
    try:
        blob = base64.b64decode(token, validate=True)
    except (binascii.Error, ValueError, TypeError) as exc:
        raise CryptoError("Ciphertext is not valid base64") from exc
    if len(blob) < GCM_NONCE_BYTES + 16:
        raise CryptoError("Ciphertext too short")
    nonce, sealed = blob[:GCM_NONCE_BYTES], blob[GCM_NONCE_BYTES:]
    try:
        return AESGCM(key).decrypt(nonce, sealed, associated_data)
    except InvalidTag as exc:
        raise CryptoError("Ciphertext authentication failed") from exc


def generate_aes_key() -> str:
    """Return a fresh base64 AES-256 key (for ``BE_ENC_SECRET``)."""
    return base64.b64encode(os.urandom(32)).decode("ascii")


def generate_fernet_key() -> str:
    """Return a fresh Fernet key (for ``BE_DATA_ENCRYPTION_KEY``)."""
    return Fernet.generate_key().decode("ascii")


def build_fernet(key: str) -> Fernet:
    try:
        return Fernet(key.strip().encode("ascii"))
    except (ValueError, binascii.Error) as exc:
        raise CryptoError("Fernet key must be 32 url-safe base64-encoded bytes") from exc


def encrypt_field(fernet: Fernet | None, plaintext: str | None) -> str | None:
    """Encrypt a secret for storage. Without a key the value is stored as-is."""
    if plaintext is None or fernet is None:
        return plaintext
    return FIELD_PREFIX + fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")


def decrypt_field(fernet: Fernet | None, stored: str | None) -> str | None:
    """Decrypt a value written by :func:`encrypt_field` (plaintext values pass through)."""
    if stored is None or not stored.startswith(FIELD_PREFIX):
        return stored
    if fernet is None:
        raise CryptoError("Encrypted field found but BE_DATA_ENCRYPTION_KEY is not configured")
    try:
        return fernet.decrypt(stored[len(FIELD_PREFIX) :].encode("ascii")).decode("utf-8")
    except InvalidToken as exc:
        raise CryptoError("Encrypted field could not be decrypted (wrong key?)") from exc
