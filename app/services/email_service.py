import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_smtp_sync(to_email: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())


async def send_otp_email(to_email: str, code: str) -> None:
    subject = "Your CDRR Engine verification code"
    html_body = f"""
    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto;">
      <h2 style="color: #111;">Verify your identity</h2>
      <p>Use the code below to complete your sign-in. This code expires in 5 minutes.</p>
      <p style="font-size: 32px; font-weight: 700; letter-spacing: 8px; text-align: center; padding: 16px; background: #f4f4f4; border-radius: 8px;">
        {code}
      </p>
      <p style="color: #888; font-size: 12px;">
        If you didn't request this code, you can safely ignore this email.
      </p>
    </div>
    """

    try:
        # smtplib is blocking, so run it in a thread to avoid blocking the event loop
        await asyncio.to_thread(_send_smtp_sync, to_email, subject, html_body)
    except Exception:
        logger.exception("Failed to send OTP email to %s", to_email)
        raise
