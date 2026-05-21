from .schemas import EmailAttachment, EmailMessage, EmailRecipient
from .send import send_bulk, send_email, send_templated_email

__all__ = [
    "EmailAttachment",
    "EmailMessage",
    "EmailRecipient",
    "send_bulk",
    "send_email",
    "send_templated_email",
]
