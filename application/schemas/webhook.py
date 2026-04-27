from enum import Enum

from application.core.schemas.base import BaseSimpleSchema


class PaymentEventStatus(str, Enum):
    """Статусы платежа для трансляции во внешние системы."""

    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class PaymentWebhookPayload(BaseSimpleSchema):
    payment_id: str
    status: PaymentEventStatus


class PaymentWebhookSchema(BaseSimpleSchema):
    id: int
    status: str
    webhook_url: str
