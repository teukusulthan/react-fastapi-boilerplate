"""Email template rendering (plain text + optional HTML), no template engine needed.

Layout of ``BE_EMAIL_TEMPLATES_DIR`` (default ``<backend>/templates/email``):

* ``<name>.txt`` (required): first line ``Subject: ...``, a blank line, then the plain-text body.
* ``<name>.html`` (optional): inner HTML content, wrapped in ``_layout.html``.
* Placeholders use ``{name}`` (``str.format``); write ``{{`` / ``}}`` for literal braces.
  Every message receives ``{app_name}`` (``BE_APP_NAME``). Values are HTML-escaped in the
  HTML part (never in the text part). A missing placeholder value is a bug -> ``KeyError``.

To localize: copy the folder, translate the files, point ``BE_EMAIL_TEMPLATES_DIR`` at the copy.

Templates used by the auth flows (placeholders besides ``app_name``):

=========================  ====================================
``register_otp``           fullname, username, code, ttl_minutes
``account_exists``         fullname, login_url
``password_reset_otp``     fullname, code, ttl_minutes
``password_changed``       fullname
``two_factor_login_otp``   fullname, code, ttl_minutes
``two_factor_setup_otp``   fullname, code, ttl_minutes
``verify_email_link``      fullname, link, ttl_hours
=========================  ====================================
"""

from __future__ import annotations

import html
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.config import Settings

DEFAULT_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates" / "email"
LAYOUT_NAME = "_layout.html"
_SUBJECT_PREFIX = "Subject:"


@dataclass(frozen=True)
class EmailContent:
    subject: str
    text: str
    html: str | None = None


@lru_cache(maxsize=64)
def _read(path: str) -> str | None:
    file = Path(path)
    return file.read_text(encoding="utf-8") if file.is_file() else None


def templates_dir(settings: Settings) -> Path:
    return Path(settings.EMAIL_TEMPLATES_DIR) if settings.EMAIL_TEMPLATES_DIR else DEFAULT_TEMPLATES_DIR


class EmailTemplates:
    """Loads and renders ``<name>.txt`` / ``<name>.html`` from one directory (files cached)."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    @classmethod
    def from_settings(cls, settings: Settings) -> EmailTemplates:
        return cls(templates_dir(settings))

    def _source(self, filename: str) -> str | None:
        return _read(str(self.directory / filename))

    def render(self, name: str, context: Mapping[str, Any]) -> EmailContent:
        if not name.replace("_", "").isalnum():
            raise ValueError(f"Invalid email template name {name!r}")
        source = self._source(f"{name}.txt")
        if source is None:
            raise FileNotFoundError(f"Email template {name}.txt not found in {self.directory}")
        first, _, body = source.partition("\n")
        if not first.startswith(_SUBJECT_PREFIX):
            raise ValueError(f"Email template {name}.txt must start with a 'Subject:' line")
        values = {key: "" if value is None else str(value) for key, value in context.items()}
        subject = " ".join(first[len(_SUBJECT_PREFIX) :].format_map(values).split())
        text = body.lstrip("\n").format_map(values)

        html_part = None
        html_source = self._source(f"{name}.html")
        if html_source is not None:
            escaped = {key: html.escape(value) for key, value in values.items()}
            content = html_source.format_map(escaped)
            layout = self._source(LAYOUT_NAME)
            if layout is not None:
                content = layout.format_map({**escaped, "subject": html.escape(subject), "content": content})
            html_part = content
        return EmailContent(subject=subject, text=text, html=html_part)
