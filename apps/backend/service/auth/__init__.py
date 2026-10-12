"""Authentication services (local provider flows + Google sign-in).

Modules:

* ``tokens``       — :class:`SessionService`: session issuance, refresh rotation, logout.
* ``login``        — :class:`LoginService`: password login, lockout, 2FA gate.
* ``two_factor``   — :class:`TwoFactorService`: email/TOTP challenges, setup/enable/disable.
* ``otp``          — :class:`OtpService`: hashed, attempt-bounded one-time codes.
* ``registration`` — :class:`RegistrationService`, :class:`EmailVerificationService`.
* ``password``     — :class:`PasswordService`: forgot/reset/change password.
* ``google``       — :class:`GoogleOAuthClient`, :class:`GoogleAuthService`.
* ``deps``         — FastAPI providers (``LoginServiceDep`` …); import routes' deps from there.

Services receive repositories / Redis / settings through their constructor; nothing is
instantiated at import time.
"""
