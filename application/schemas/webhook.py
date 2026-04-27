import uuid

from enum import Enum

from application.core.schemas.base import BaseIdMixin, BaseSimpleSchema


class PaymentEventStatus(str, Enum):
    """Статусы платежа для трансляции во внешние системы."""

    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class PaymentWebhookPayload(BaseSimpleSchema):
    payment_id: uuid.UUID
    status: PaymentEventStatus


class PaymentWebhookSchema(BaseSimpleSchema, BaseIdMixin):
    status: str
    webhook_url: str
