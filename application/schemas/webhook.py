from enum import Enum
from pydantic import BaseModel


class PaymentEventStatus(str, Enum):
    """Статусы платежа для трансляции во внешние системы."""

    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class PaymentWebhookPayload(BaseModel):
    payment_id: str
    status: PaymentEventStatus
