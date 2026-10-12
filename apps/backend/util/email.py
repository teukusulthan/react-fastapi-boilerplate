"""Outgoing email: sender backends and a request-scoped :class:`Mailer`.

Backends (``BE_EMAIL_BACKEND``):

* ``smtp`` — :class:`SmtpEmailSender` (smtplib; implicit TLS with ``BE_SMTP_SSL=true``,
  otherwise STARTTLS when ``BE_SMTP_STARTTLS=true``; ``BE_SMTP_TIMEOUT`` for connect/IO).
* ``console`` — :class:`ConsoleEmailSender` writes the message to the log (development only,
  refused in production because it prints one-time codes).
* ``disabled`` — :class:`DisabledEmailSender`; flows that need email raise ``CONFIGURATION_ERROR``.
* ``auto`` (default) — ``smtp`` when configured, else ``console`` (dev/test) or ``disabled`` (production).

Boot never fails because of email settings; problems surface when an email is needed.

Delivery happens off the request path: :meth:`Mailer.send` renders the template
immediately (template bugs fail loudly) and queues the SMTP call on FastAPI
``BackgroundTasks``; delivery errors are logged, never returned to the client
(so SMTP latency/failures cannot block a request or reveal whether an account exists).
"""

from __future__ import annotations

import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.headerregistry import Address
from email.message import EmailMessage as MimeMessage
from email.utils import formataddr, make_msgid
from threading import Lock
from typing import TYPE_CHECKING, Any

from loguru import logger

from core.errors import ConfigurationError
from util.email_templates import EmailContent, EmailTemplates
from util.helper import censor_email

if TYPE_CHECKING:
    from fastapi import BackgroundTasks

    from core.config import Settings


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    text: str
    html: str | None = None
    template: str | None = None  # for logs/tests only

    @classmethod
    def from_content(cls, to: str, content: EmailContent, template: str | None = None) -> EmailMessage:
        return cls(to=to, subject=content.subject, text=content.text, html=content.html, template=template)


class EmailSender(ABC):
    """Delivers one message synchronously (called from a background task / thread)."""

    name: str = "base"
    available: bool = True

    @abstractmethod
    def send(self, message: EmailMessage) -> None: ...


class SmtpEmailSender(EmailSender):
    name = "smtp"

    def __init__(self, settings: Settings) -> None:
        if not settings.smtp_configured:
            raise ConfigurationError("SMTP is not configured (BE_SMTP_HOST / BE_SMTP_FROM_EMAIL)")
        self.settings = settings

    def build(self, message: EmailMessage) -> MimeMessage:
        s = self.settings
        mime = MimeMessage()
        mime["Subject"] = message.subject
        mime["From"] = formataddr((s.smtp_from_name, str(s.SMTP_FROM_EMAIL)))
        mime["To"] = str(Address(addr_spec=message.to))
        domain = str(s.SMTP_FROM_EMAIL).rpartition("@")[2] or None
        mime["Message-ID"] = make_msgid(domain=domain)
        mime.set_content(message.text)
        if message.html:
            mime.add_alternative(message.html, subtype="html")
        return mime

    def _connect(self) -> smtplib.SMTP:
        s = self.settings
        host, port, timeout = str(s.SMTP_HOST), s.SMTP_PORT, s.SMTP_TIMEOUT
        context = ssl.create_default_context()
        if s.SMTP_SSL:
            return smtplib.SMTP_SSL(host, port, timeout=timeout, context=context)
        smtp = smtplib.SMTP(host, port, timeout=timeout)
        try:
            if s.SMTP_STARTTLS:
                smtp.starttls(context=context)
        except BaseException:
            smtp.close()
            raise
        return smtp

    def send(self, message: EmailMessage) -> None:
        s = self.settings
        mime = self.build(message)
        with self._connect() as smtp:
            if s.SMTP_USERNAME:
                password = s.SMTP_PASSWORD.get_secret_value() if s.SMTP_PASSWORD else ""
                smtp.login(s.SMTP_USERNAME, password)
            smtp.send_message(mime)


class ConsoleEmailSender(EmailSender):
    """Development sink: logs the full message (including one-time codes)."""

    name = "console"

    def send(self, message: EmailMessage) -> None:
        logger.info(
            "[email:console] to={} subject={!r} (BE_EMAIL_BACKEND=console; not delivered)\n{}",
            message.to,
            message.subject,
            message.text,
        )


class DisabledEmailSender(EmailSender):
    name = "disabled"
    available = False

    def send(self, message: EmailMessage) -> None:
        raise ConfigurationError("Email delivery is not configured")


class MemoryEmailSender(EmailSender):
    """Keeps messages in ``outbox`` (tests, local tooling). Thread-safe."""

    name = "memory"

    def __init__(self) -> None:
        self.outbox: list[EmailMessage] = []
        self._lock = Lock()

    def send(self, message: EmailMessage) -> None:
        with self._lock:
            self.outbox.append(message)

    def to(self, address: str) -> list[EmailMessage]:
        return [m for m in self.outbox if m.to == address]

    def last(self, address: str | None = None, template: str | None = None) -> EmailMessage:
        for message in reversed(self.outbox):
            if (address is None or message.to == address) and (template is None or message.template == template):
                return message
        raise LookupError(f"No email sent to {address!r} (template={template!r})")

    def clear(self) -> None:
        with self._lock:
            self.outbox.clear()


def resolve_email_backend(settings: Settings) -> str:
    if settings.EMAIL_BACKEND != "auto":
        return settings.EMAIL_BACKEND
    if settings.smtp_configured:
        return "smtp"
    return "disabled" if settings.is_production else "console"


def build_email_sender(settings: Settings) -> EmailSender:
    backend = resolve_email_backend(settings)
    if backend == "smtp":
        return SmtpEmailSender(settings)
    if backend == "console":
        logger.warning("Email backend is 'console': messages are logged, not delivered (development only)")
        return ConsoleEmailSender()
    logger.warning("Email delivery is disabled: register / password reset / email 2FA will return 503")
    return DisabledEmailSender()


def deliver(sender: EmailSender, message: EmailMessage) -> bool:
    """Send and swallow errors (logged). Returns ``True`` on success."""
    try:
        sender.send(message)
    except Exception as exc:  # noqa: BLE001  # background delivery must never crash; logged instead
        logger.error(
            "Sending email {!r} to {} failed: {}",
            message.template or message.subject,
            censor_email(message.to),
            type(exc).__name__,
        )
        return False
    logger.debug("Email {!r} sent to {}", message.template or message.subject, censor_email(message.to))
    return True


class Mailer:
    """Request-scoped facade: render a template, deliver in the background."""

    def __init__(
        self,
        sender: EmailSender,
        templates: EmailTemplates,
        settings: Settings,
        background: BackgroundTasks | None = None,
    ) -> None:
        self.sender = sender
        self.templates = templates
        self.settings = settings
        self.background = background

    @property
    def available(self) -> bool:
        return self.sender.available

    def require_available(self) -> None:
        """Call BEFORE any account lookup so the 503 never depends on account existence."""
        if not self.sender.available:
            raise ConfigurationError("Email delivery is not configured")

    def render(self, template: str, to: str, **context: Any) -> EmailMessage:
        content = self.templates.render(template, {"app_name": self.settings.APP_NAME, **context})
        return EmailMessage.from_content(to, content, template=template)

    def send(self, template: str, to: str, **context: Any) -> None:
        if not self.sender.available:
            logger.warning("Email {!r} to {} dropped: delivery disabled", template, censor_email(to))
            return
        message = self.render(template, to, **context)
        if self.background is not None:
            self.background.add_task(deliver, self.sender, message)
        else:
            deliver(self.sender, message)
