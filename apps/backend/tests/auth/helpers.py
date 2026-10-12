"""Plain helpers shared by the auth tests (fixtures live in conftest.py)."""

from __future__ import annotations

import re
from typing import Any

PASSWORD = "Sup3r-Secret-pass"  # same as tests/conftest.py TEST_PASSWORD (user_factory default)
SECRET_MARKERS = ("passwordHash", "password_hash", "twoFactorSecret", "two_factor_secret", "otpHash", "otp_hash")
_CODE = re.compile(r"^\s+(\d{4,10})\s*$", re.MULTILINE)


def code_from(message: Any) -> str:
    """Extract the one-time code from an email's text body (indented line with digits)."""
    match = _CODE.search(message.text)
    assert match, message.text
    return match.group(1)


def assert_no_secrets(text: str) -> None:
    for marker in SECRET_MARKERS:
        assert marker not in text, f"{marker} leaked in response"
