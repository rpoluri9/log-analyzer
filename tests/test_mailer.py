from unittest.mock import patch

from logalyzer.mailer import send_report

CONFIG = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 587,
    "use_tls": True,
    "username": "user",
    "password": "secret",
    "from_addr": "from@example.com",
    "to_addrs": ["a@example.com", "b@example.com"],
}


def test_send_report_uses_smtp_correctly():
    with patch("logalyzer.mailer.smtplib.SMTP") as mock_smtp:
        sent_to = send_report(CONFIG, "Subject!", "plain body",
                              "<p>html body</p>")
    assert sent_to == ["a@example.com", "b@example.com"]
    mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
    server = mock_smtp.return_value.__enter__.return_value
    server.starttls.assert_called_once()
    server.login.assert_called_once_with("user", "secret")
    server.send_message.assert_called_once()
    msg = server.send_message.call_args[0][0]
    assert msg["Subject"] == "Subject!"
    assert msg["From"] == "from@example.com"
    assert "a@example.com" in msg["To"]


def test_send_report_single_string_recipient():
    cfg = dict(CONFIG, to_addrs="solo@example.com", use_tls=False,
               username="")
    with patch("logalyzer.mailer.smtplib.SMTP") as mock_smtp:
        sent_to = send_report(cfg, "Hi", "body")
    assert sent_to == ["solo@example.com"]
    server = mock_smtp.return_value.__enter__.return_value
    server.starttls.assert_not_called()
    server.login.assert_not_called()
    server.send_message.assert_called_once()
