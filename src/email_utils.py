"""SMTP email utilities for password reset and contact form."""

import html as _html
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _smtp_config() -> dict:
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip() or "smtp.gmail.com"
    port_raw = (os.environ.get("SMTP_PORT", "587") or "587").strip()
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    user = (os.environ.get("SMTP_USER", "") or "").strip()
    password = (os.environ.get("SMTP_PASSWORD", "") or "").strip()
    from_email = (os.environ.get("SMTP_FROM", "") or "").strip() or user
    encryption = (os.environ.get("SMTP_ENCRYPTION", "tls") or "tls").strip().lower()
    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "from_email": from_email,
        "encryption": encryption,
    }


def is_email_configured() -> bool:
    cfg = _smtp_config()
    return bool(cfg["user"] and cfg["password"])


def send_password_reset_email(to_email: str, reset_token: str, app_url: str) -> bool:
    """Send a password-reset email. Returns True on success."""
    cfg = _smtp_config()
    if not (cfg["user"] and cfg["password"]):
        return False

    reset_url = f"{app_url}?reset_token={reset_token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reset your ExcelCV password"
    msg["From"] = f"ExcelCV <{cfg['from_email']}>"
    msg["To"] = to_email

    text_body = (
        "Reset your ExcelCV password\n\n"
        f"Click the link below to set a new password (expires in 1 hour):\n{reset_url}\n\n"
        "If you did not request this, you can safely ignore this email."
    )
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:500px;margin:0 auto;padding:24px;color:#1e293b">
  <h2 style="color:#3b82f6;margin-bottom:8px">Reset your ExcelCV password</h2>
  <p>Click the button below to set a new password.<br>
     This link expires in <strong>1 hour</strong>.</p>
  <p style="margin:24px 0">
    <a href="{reset_url}"
       style="display:inline-block;background:#3b82f6;color:#fff;
              padding:11px 28px;border-radius:6px;text-decoration:none;
              font-weight:600;font-size:15px">
      Reset password
    </a>
  </p>
  <p style="color:#64748b;font-size:0.85rem">
    If you did not request a password reset, you can safely ignore this email.
    Your password will not change.
  </p>
</body>
</html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        if cfg["encryption"] == "ssl":
            server_ctx = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15)
        else:
            server_ctx = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
        with server_ctx as server:
            server.ehlo()
            if cfg["encryption"] in ("tls", "starttls"):
                server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from_email"], [to_email], msg.as_string())
        return True
    except Exception:
        return False


def send_contact_email(name: str, reply_to: str, inquiry: str, subject: str, message: str) -> bool:
    """Send a contact form submission to the site owner. Returns True on success."""
    cfg = _smtp_config()
    if not (cfg["user"] and cfg["password"]):
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[ExcelCV Contact] {_html.escape(subject)}"
    msg["From"] = f"ExcelCV <{cfg['from_email']}>"
    msg["To"] = cfg["from_email"]
    msg["Reply-To"] = reply_to

    text_body = (
        "New contact form submission\n\n"
        f"Name: {name}\n"
        f"Email: {reply_to}\n"
        f"Type: {inquiry}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}"
    )
    e = _html.escape
    html_body = f"""<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:24px;color:#1e293b">
  <h2 style="color:#3b82f6;margin-bottom:8px">New Contact Form Submission</h2>
  <table style="border-collapse:collapse;width:100%">
    <tr><td style="padding:4px 8px;font-weight:600">Name:</td><td>{e(name)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:600">Email:</td>
        <td><a href="mailto:{e(reply_to)}">{e(reply_to)}</a></td></tr>
    <tr><td style="padding:4px 8px;font-weight:600">Type:</td><td>{e(inquiry)}</td></tr>
    <tr><td style="padding:4px 8px;font-weight:600">Subject:</td><td>{e(subject)}</td></tr>
  </table>
  <hr style="margin:16px 0">
  <p style="white-space:pre-wrap">{e(message)}</p>
</body>
</html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        if cfg["encryption"] == "ssl":
            server_ctx = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=15)
        else:
            server_ctx = smtplib.SMTP(cfg["host"], cfg["port"], timeout=15)
        with server_ctx as server:
            server.ehlo()
            if cfg["encryption"] in ("tls", "starttls"):
                server.starttls()
            server.login(cfg["user"], cfg["password"])
            server.sendmail(cfg["from_email"], [cfg["from_email"]], msg.as_string())
        return True
    except Exception:
        return False
