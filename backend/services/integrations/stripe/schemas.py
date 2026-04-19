from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PaymentIntentCreate(BaseModel):
    amount: int
    currency: str = "gbp"
    customer_id: str | None = None
    metadata: dict[str, str] | None = None


class PaymentIntentResponse(BaseModel):
    id: str
    amount: int
    currency: str
    status: str
    client_secret: str | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class RefundCreate(BaseModel):
    payment_intent_id: str
    amount: int | None = None
    reason: str | None = None


class RefundResponse(BaseModel):
    id: str
    amount: int
    status: str
    payment_intent_id: str


class WebhookEvent(BaseModel):
    id: str
    type: str
    data: dict[str, Any]
    created: datetime


class ConnectAccountCreate(BaseModel):
    email: str
    country: str = "GB"
    business_type: str = "individual"


class OnboardingLink(BaseModel):
    url: str
    expires_at: datetime
