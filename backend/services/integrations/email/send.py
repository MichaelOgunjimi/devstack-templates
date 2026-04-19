import structlog

from .client import SMTPClient, _build_message
from .schemas import EmailAttachment, EmailMessage, EmailRecipient
from .templates import render_template

logger = structlog.get_logger(__name__)


def _normalize_recipients(to: str | list[str]) -> list[EmailRecipient]:
    recipients = [to] if isinstance(to, str) else to
    return [EmailRecipient(email=email) for email in recipients]


async def send_email(
    to: str | list[str],
    subject: str,
    html_body: str,
    *,
    text_body: str | None = None,
    reply_to: str | None = None,
    attachments: list[EmailAttachment] | None = None,
) -> None:
    recipients = _normalize_recipients(to)
    logger.info(
        "email.send.attempt",
        recipient_count=len(recipients),
        subject=subject,
    )

    try:
        async with SMTPClient() as client:
            message = _build_message(
                recipients,
                subject,
                html_body,
                reply_to=reply_to,
                attachments=attachments,
                text_body=text_body,
            )
            await client.send_message(message)
    except Exception:
        logger.exception("email.send.failed", recipient_count=len(recipients), subject=subject)
        raise

    logger.info("email.send.success", recipient_count=len(recipients), subject=subject)


async def send_templated_email(
    to: str | list[str],
    template_name: str,
    context: dict,
    *,
    subject: str | None = None,
) -> None:
    rendered_html = render_template(template_name, context)
    resolved_subject = subject or context.get("subject") or template_name.replace("_", " ").title()
    await send_email(to=to, subject=resolved_subject, html_body=rendered_html)


async def send_bulk(messages: list[EmailMessage]) -> dict[str, int]:
    sent = 0
    failed = 0
    logger.info("email.send_bulk.attempt", message_count=len(messages))

    async with SMTPClient() as client:
        for item in messages:
            try:
                mime_message = _build_message(
                    item.to,
                    item.subject,
                    item.html_body,
                    reply_to=item.reply_to,
                    attachments=item.attachments,
                    text_body=item.text_body,
                )
                await client.send_message(mime_message)
                sent += 1
            except Exception:
                failed += 1
                logger.exception("email.send_bulk.item_failed", subject=item.subject)

    logger.info("email.send_bulk.summary", sent=sent, failed=failed)
    return {"sent": sent, "failed": failed}

