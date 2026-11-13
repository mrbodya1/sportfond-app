"""Explicit, server-only SMTP diagnostic. Never prints credentials or sends by default."""
import argparse
import json
import os
import re
import smtplib
import ssl
from email.message import EmailMessage


def address(value):
    if not re.fullmatch(r"[^\s<>@,;]+@[^\s<>@,;]+\.[^\s<>@,;]+", value or ""):
        raise ValueError("invalid_email_address")
    return value


def check_mail(mode="connect", recipient=None):
    host = os.environ.get("SMTP_HOST", "smtp.beget.com")
    port = int(os.environ.get("SMTP_PORT", "465"))
    if port != 465:
        raise ValueError("only_implicit_tls_port_465_supported")
    username = os.environ.get("SMTP_USERNAME", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    if mode not in {"connect", "auth", "send"}:
        raise ValueError("invalid_mode")
    if mode != "connect":
        address(username)
        if not password:
            raise ValueError("missing_smtp_password")
    if mode == "send":
        address(recipient)
        sender = address(os.environ.get("SMTP_FROM", username))
    result = {"tls_connected": False, "authenticated": False, "accepted_by_smtp": False,
              "delivery_confirmed": False}
    with smtplib.SMTP_SSL(host, port, timeout=15, context=ssl.create_default_context()) as smtp:
        code, _ = smtp.ehlo()
        if code != 250:
            raise ValueError("smtp_ehlo_failed")
        result["tls_connected"] = True
        if mode != "connect":
            smtp.login(username, password)
            result["authenticated"] = True
        if mode == "send":
            message = EmailMessage()
            message["From"] = sender
            message["To"] = recipient
            message["Subject"] = "Sportfond — проверка доставки почты"
            message.set_content("Это одно тестовое письмо Sportfond для проверки SMTP Beget. "
                                "Оно не регистрирует аккаунт и не содержит кода входа. "
                                "Если письмо получено, сообщите об этом при проверке приложения.")
            refused = smtp.send_message(message)
            if refused:
                raise ValueError("recipient_refused")
            result["accepted_by_smtp"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["connect", "auth", "send"], default="connect")
    parser.add_argument("--to", help="Explicit test recipient; required only for send mode")
    args = parser.parse_args()
    if args.mode == "send" and not args.to:
        parser.error("--to is required for send")
    try:
        print(json.dumps(check_mail(args.mode, args.to)))
    except smtplib.SMTPAuthenticationError:
        print(json.dumps({"ok": False, "error": "authentication_failed"}))
        return 1
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        # Do not print exception messages: provider responses can contain user data.
        print(json.dumps({"ok": False, "error": type(exc).__name__}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
