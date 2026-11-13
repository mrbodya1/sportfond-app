import unittest
from unittest.mock import patch, MagicMock
from check_mail import check_mail


class MailSafetyTests(unittest.TestCase):
    def fake_smtp(self):
        smtp = MagicMock()
        smtp.ehlo.return_value = (250, b"ok")
        smtp.send_message.return_value = {}
        wrapper = MagicMock()
        wrapper.__enter__.return_value = smtp
        return smtp, wrapper

    @patch.dict("os.environ", {}, clear=True)
    @patch("check_mail.ssl.create_default_context")
    def test_default_neither_authenticates_nor_sends(self, tls_factory):
        smtp, wrapper = self.fake_smtp()
        with patch("check_mail.smtplib.SMTP_SSL", return_value=wrapper) as factory:
            result = check_mail()
        smtp.login.assert_not_called()
        smtp.send_message.assert_not_called()
        self.assertTrue(result["tls_connected"])
        tls_factory.assert_called_once_with()
        self.assertIs(factory.call_args.kwargs["context"], tls_factory.return_value)

    @patch.dict("os.environ", {"SMTP_USERNAME": "test@example.com", "SMTP_PASSWORD": "test-only"}, clear=True)
    @patch("check_mail.ssl.create_default_context")
    def test_auth_does_not_send(self, tls_factory):
        smtp, wrapper = self.fake_smtp()
        with patch("check_mail.smtplib.SMTP_SSL", return_value=wrapper):
            result = check_mail("auth")
        smtp.login.assert_called_once()
        smtp.send_message.assert_not_called()
        self.assertTrue(result["authenticated"])

    @patch.dict("os.environ", {"SMTP_USERNAME": "test@example.com", "SMTP_PASSWORD": "test-only"}, clear=True)
    @patch("check_mail.ssl.create_default_context")
    def test_send_requires_recipient_and_does_not_claim_delivery(self, tls_factory):
        with self.assertRaises(ValueError):
            check_mail("send", "bad\nBcc: other@example.com")
        smtp, wrapper = self.fake_smtp()
        with patch("check_mail.smtplib.SMTP_SSL", return_value=wrapper):
            result = check_mail("send", "recipient@example.com")
        smtp.send_message.assert_called_once()
        self.assertTrue(result["accepted_by_smtp"])
        self.assertFalse(result["delivery_confirmed"])


if __name__ == "__main__":
    unittest.main()
