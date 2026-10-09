"""Send reports by email over SMTP."""
import smtplib
from email.message import EmailMessage


def send_report(config: dict, subject: str, body_text: str,
                body_html: str | None = None) -> list[str]:
    """Send a report email.

    config keys: smtp_host, smtp_port, use_tls, username, password,
    from_addr, to_addrs (a list, or a single address string).
    Returns the list of recipients.
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = config["from_addr"]
    to_addrs = config["to_addrs"]
    if isinstance(to_addrs, str):
        to_addrs = [to_addrs]
    msg["To"] = ", ".join(to_addrs)
    msg.set_content(body_text)
    if body_html:
        msg.add_alternative(body_html, subtype="html")

    host = config.get("smtp_host", "localhost")
    port = int(config.get("smtp_port", 25))
    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if config.get("use_tls"):
            smtp.starttls()
        if config.get("username"):
            smtp.login(config["username"], config.get("password", ""))
        smtp.send_message(msg)
    return to_addrs
