"""Email backends/templates and the OTP service (unit level)."""

from __future__ import annotations

import smtplib
from collections import Counter
from unittest import mock

import pytest
from pydantic import ValidationError as PydanticValidationError

from service.auth.otp import OtpService
from util.email import (
    ConsoleEmailSender,
    DisabledEmailSender,
    EmailMessage,
    Mailer,
    MemoryEmailSender,
    SmtpEmailSender,
    build_email_sender,
    deliver,
    resolve_email_backend,
)
from util.email_templates import DEFAULT_TEMPLATES_DIR, EmailTemplates

SMTP = {"SMTP_HOST": "smtp.example.com", "SMTP_FROM_EMAIL": "no-reply@example.com"}
TEMPLATES = [
    ("register_otp", {"fullname": "A", "username": "a", "code": "123456", "ttl_minutes": 10}),
    ("account_exists", {"fullname": "A", "login_url": "http://x/login"}),
    ("password_reset_otp", {"fullname": "A", "code": "123456", "ttl_minutes": 10}),
    ("password_changed", {"fullname": "A"}),
    ("two_factor_login_otp", {"fullname": "A", "code": "123456", "ttl_minutes": 10}),
    ("two_factor_setup_otp", {"fullname": "A", "code": "123456", "ttl_minutes": 10}),
    ("verify_email_link", {"fullname": "A", "link": "http://x/verify?token=t", "ttl_hours": 24}),
]


# ----------------------------------------------------------------- templates
@pytest.mark.parametrize(("name", "context"), TEMPLATES)
def test_every_template_renders(name, context):
    content = EmailTemplates(DEFAULT_TEMPLATES_DIR).render(name, {"app_name": "Acme", **context})
    assert "Acme" in content.subject and "\n" not in content.subject
    assert content.html and "<html" in content.html and "Acme" in content.html
    for banned in ("Fusion", "eBdesk", "Halo", "Terima"):
        assert banned not in content.text and banned not in content.html


def test_template_html_escaping_and_missing_values(tmp_path):
    content = EmailTemplates(DEFAULT_TEMPLATES_DIR).render(
        "password_changed", {"app_name": "Acme", "fullname": "<script>x</script>"}
    )
    assert "<script>" in content.text  # plain text is not escaped
    assert "<script>" not in content.html and "&lt;script&gt;" in content.html
    with pytest.raises(KeyError):
        EmailTemplates(DEFAULT_TEMPLATES_DIR).render("password_changed", {"app_name": "Acme"})
    with pytest.raises(ValueError, match="Invalid email template"):
        EmailTemplates(DEFAULT_TEMPLATES_DIR).render("../secrets", {})


def test_custom_templates_dir(tmp_path, make_settings):
    (tmp_path / "password_changed.txt").write_text("Subject: Kata sandi {app_name} diubah\n\nHai {fullname}\n")
    settings = make_settings(EMAIL_TEMPLATES_DIR=str(tmp_path))
    content = EmailTemplates.from_settings(settings).render("password_changed", {"app_name": "X", "fullname": "B"})
    assert content.subject == "Kata sandi X diubah" and content.text.startswith("Hai B") and content.html is None


# ------------------------------------------------------------------ backends
def test_backend_resolution(make_settings):
    assert resolve_email_backend(make_settings()) == "console"
    assert resolve_email_backend(make_settings(**SMTP)) == "smtp"
    assert isinstance(build_email_sender(make_settings()), ConsoleEmailSender)
    assert isinstance(build_email_sender(make_settings(EMAIL_BACKEND="disabled")), DisabledEmailSender)
    assert isinstance(build_email_sender(make_settings(**SMTP)), SmtpEmailSender)


def test_backend_settings_validation(make_settings):
    with pytest.raises(PydanticValidationError, match="BE_EMAIL_BACKEND=smtp"):
        make_settings(EMAIL_BACKEND="smtp")
    with pytest.raises(PydanticValidationError, match="console"):
        make_settings(
            EMAIL_BACKEND="console",
            ENVIRONMENT="production",
            COOKIE_SECURE=True,
            JWT_SECRET="prod-secret-0123456789abcdef0123456789abcdef",
        )
    prod = make_settings(
        ENVIRONMENT="production", COOKIE_SECURE=True, JWT_SECRET="prod-secret-0123456789abcdef0123456789abcdef"
    )
    assert resolve_email_backend(prod) == "disabled"  # boots fine without SMTP


def test_smtp_sender_starttls_login_and_message(make_settings):
    settings = make_settings(**SMTP, SMTP_USERNAME="user", SMTP_PASSWORD="pw", SMTP_FROM_NAME="Acme")
    with mock.patch("util.email.smtplib.SMTP") as smtp_cls:
        server = smtp_cls.return_value.__enter__.return_value = smtp_cls.return_value
        SmtpEmailSender(settings).send(EmailMessage(to="a@example.com", subject="Hi", text="body", html="<p>b</p>"))
    smtp_cls.assert_called_once_with("smtp.example.com", 587, timeout=10.0)
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "pw")
    sent = server.send_message.call_args.args[0]
    assert sent["To"] == "a@example.com" and sent["Subject"] == "Hi"
    assert "Acme" in sent["From"] and sent.is_multipart()


def test_smtp_sender_implicit_tls(make_settings):
    settings = make_settings(**SMTP, SMTP_SSL=True, SMTP_PORT=465)
    with mock.patch("util.email.smtplib.SMTP_SSL") as ssl_cls:
        server = ssl_cls.return_value
        server.__enter__.return_value = server
        SmtpEmailSender(settings).send(EmailMessage(to="a@example.com", subject="Hi", text="body"))
    assert ssl_cls.call_args.args[:2] == ("smtp.example.com", 465)
    server.starttls.assert_not_called()
    server.login.assert_not_called()


def test_deliver_swallows_errors(make_settings):
    with mock.patch("util.email.smtplib.SMTP", side_effect=smtplib.SMTPConnectError(421, "down")):
        ok = deliver(SmtpEmailSender(make_settings(**SMTP)), EmailMessage(to="a@example.com", subject="s", text="t"))
    assert ok is False


def test_mailer_without_background_and_disabled(make_settings):
    settings = make_settings()
    memory = MemoryEmailSender()
    mailer = Mailer(memory, EmailTemplates(DEFAULT_TEMPLATES_DIR), settings)
    mailer.send("password_changed", "a@example.com", fullname="A")
    assert memory.last("a@example.com").template == "password_changed"
    disabled = Mailer(DisabledEmailSender(), EmailTemplates(DEFAULT_TEMPLATES_DIR), settings)
    disabled.send("password_changed", "a@example.com", fullname="A")  # dropped, no raise
    from core.errors import ConfigurationError

    with pytest.raises(ConfigurationError):
        disabled.require_available()


# ----------------------------------------------------------------------- OTP
@pytest.fixture
def otp(redis_client, make_settings):
    return OtpService(redis_client, make_settings(OTP_RESEND_COOLDOWN=0, OTP_MAX_ATTEMPTS=3))


def test_otp_random_and_hashed(otp, redis_client):
    codes = [otp.issue("p", f"user{i}@example.com") for i in range(300)]
    assert all(len(c) == 6 and c.isdigit() for c in codes)
    assert len(set(codes)) > 250  # not a fixed/time-based secret (S2)
    digits = Counter("".join(codes))
    assert len(digits) == 10
    stored = [redis_client.hgetall(k) for k in redis_client.keys("*otp:code*")]
    assert len(stored) == 300
    assert all(set(item) == {"hash", "attempts"} and len(item["hash"]) == 64 for item in stored)  # never the code
    assert all("example.com" not in key for key in redis_client.keys("*"))  # subjects are hashed in keys


def test_otp_binding_single_use_and_attempts(otp):
    code = otp.issue("register", "a@example.com")
    assert not otp.verify("register", "b@example.com", code)
    assert not otp.verify("password-reset", "a@example.com", code)
    assert otp.verify("register", "A@Example.com", code, consume=False)
    assert otp.verify("register", "a@example.com", code)
    assert not otp.verify("register", "a@example.com", code)  # consumed

    code = otp.issue("register", "a@example.com")
    wrong = "000000" if code != "000000" else "111111"
    assert not otp.verify("register", "a@example.com", wrong)
    assert not otp.verify("register", "a@example.com", wrong)
    assert not otp.verify("register", "a@example.com", wrong)
    assert not otp.verify("register", "a@example.com", code)  # burnt after 3 attempts


def test_otp_cooldown_and_replacement(redis_client, make_settings):
    otp = OtpService(redis_client, make_settings(OTP_RESEND_COOLDOWN=60))
    first = otp.issue("register", "a@example.com")
    assert first is not None
    assert otp.issue("register", "a@example.com") is None
    assert 0 < otp.cooldown_remaining("register", "a@example.com") <= 60
    second = otp.issue("register", "a@example.com", respect_cooldown=False)
    if first != second:
        assert not otp.verify("register", "a@example.com", first, consume=False)
    assert otp.verify("register", "a@example.com", second)


def test_otp_expires(otp, redis_client):
    code = otp.issue("register", "a@example.com")
    for key in redis_client.keys("*otp:code*"):
        redis_client.delete(key)
    assert not otp.verify("register", "a@example.com", code)
    assert not redis_client.keys("*otp:code*")  # a failed verify never recreates the key without TTL
