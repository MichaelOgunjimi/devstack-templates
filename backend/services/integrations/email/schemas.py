from pydantic import BaseModel, Field


class EmailRecipient(BaseModel):
    email: str
    name: str | None = None


class EmailAttachment(BaseModel):
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"


class EmailMessage(BaseModel):
    to: list[EmailRecipient]
    subject: str
    html_body: str
    text_body: str | None = None
    reply_to: str | None = None
    attachments: list[EmailAttachment] = Field(default_factory=list)
