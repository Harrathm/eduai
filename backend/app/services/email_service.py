"""Email service for transactional emails (password reset, notifications)."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_password_reset_email(
    to_email: str,
    reset_token: str,
    user_name: Optional[str] = None,
) -> bool:
    """Send a password reset email with the reset link.

    Returns True if the email was sent successfully, False otherwise.
    Never raises exceptions — failures are logged server-side.
    """
    settings = get_settings()

    if not settings.smtp_host:
        logger.warning("SMTP not configured — password reset email not sent")
        return False

    reset_link = f"{settings.frontend_reset_url}?token={reset_token}"
    display_name = user_name or "utilisateur"

    subject = "EDUAI Learning — Réinitialisation de votre mot de passe"

    text_body = (
        f"Bonjour {display_name},\n\n"
        f"Vous avez demandé la réinitialisation de votre mot de passe.\n\n"
        f"Cliquez sur le lien ci-dessous pour définir un nouveau mot de passe :\n\n"
        f"{reset_link}\n\n"
        f"Ce lien expire dans 1 heure.\n\n"
        f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
        f"Cordialement,\nL'équipe EDUAI Learning"
    )

    html_body = (
        f"<html><body>"
        f"<p>Bonjour {display_name},</p>"
        f"<p>Vous avez demandé la réinitialisation de votre mot de passe.</p>"
        f"<p><a href='{reset_link}'>Cliquez ici pour réinitialiser votre mot de passe</a></p>"
        f"<p>Ce lien expire dans 1 heure.</p>"
        f"<p>Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.</p>"
        f"<p>Cordialement,<br>L'équipe EDUAI Learning</p>"
        f"</body></html>"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from_address}>"
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)

        if settings.smtp_username and settings.smtp_password:
            server.login(settings.smtp_username, settings.smtp_password)

        server.sendmail(settings.email_from_address, to_email, msg.as_string())
        server.quit()
        logger.info("Password reset email sent to %s", to_email)
        return True
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        return False
