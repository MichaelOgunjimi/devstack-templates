from email.message import EmailMessage
from email.utils import formataddr
from typing import Self

import aiosmtplib
import structlog

from core.config import settings

from .schemas import EmailAttachment, EmailRecipient

logger = structlog.get_logger(__name__)


class EmailNotConfiguredError(Exception):
    """Raised when SMTP settings are missing or incomplete."""


def _ensure_configured() -> None:
    missing: list[str] = []
    if not settings.SMTP_HOST:
        missing.append("SMTP_HOST")
    if not settings.SMTP_PORT:
        missing.append("SMTP_PORT")
    if not settings.SMTP_FROM_EMAIL:
        missing.append("SMTP_FROM_EMAIL")

    if missing:
        raise EmailNotConfiguredError(f"Missing SMTP settings: {', '.join(missing)}")


def _build_message(
    to: list[EmailRecipient],
    subject: str,
    html_body: str,
    *,
    from_email: str | None = None,
    from_name: str | None = None,
    reply_to: str | None = None,
    attachments: list[EmailAttachment] | None = None,
    text_body: str | None = None,
) -> EmailMessage:
    sender_email = from_email or settings.SMTP_FROM_EMAIL
    sender_name = from_name or settings.SMTP_FROM_NAME

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = formataddr((sender_name, sender_email)) if sender_name else sender_email
    message["To"] = ", ".join(
        formataddr((recipient.name, recipient.email)) if recipient.name else recipient.email
        for recipient in to
    )
    if reply_to:
        message["Reply-To"] = reply_to

    if text_body:
        message.set_content(text_body)
        message.add_alternative(html_body, subtype="html")
    else:
        message.set_content(html_body, subtype="html")

    for attachment in attachments or []:
        maintype, subtype = "application", "octet-stream"
        if "/" in attachment.content_type:
            maintype, subtype = attachment.content_type.split("/", 1)
        message.add_attachment(
            attachment.content,
            maintype=maintype,
            subtype=subtype,
            filename=attachment.filename,
        )

    return message


class SMTPClient:
    """Async SMTP client wrapper for sending email messages."""

    def __init__(self) -> None:
        self._smtp = aiosmtplib.SMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            use_tls=settings.SMTP_USE_TLS,
            timeout=30,
        )

    async def __aenter__(self) -> Self:
        _ensure_configured()
        logger.info("email.smtp.connect.attempt", host=settings.SMTP_HOST, port=settings.SMTP_PORT)
        await self._smtp.connect()

        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            logger.info("email.smtp.login.attempt", username=settings.SMTP_USERNAME)
            await self._smtp.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            logger.info("email.smtp.login.success")

        logger.info("email.smtp.connect.success")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if self._smtp.is_connected:
                await self._smtp.quit()
                logger.info("email.smtp.disconnect.success")
        except Exception as disconnect_error:  # pragma: no cover - defensive logging
            logger.warning("email.smtp.disconnect.failed", error=str(disconnect_error))

    async def send_message(self, message: EmailMessage) -> None:
        logger.info(
            "email.smtp.send.attempt",
            recipients=message.get("To"),
            subject=message.get("Subject"),
        )
        await self._smtp.send_message(message)
        logger.info(
            "email.smtp.send.success",
            recipients=message.get("To"),
            subject=message.get("Subject"),
        )
