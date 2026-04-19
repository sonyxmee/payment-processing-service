from uuid import UUID
from pydantic import Field
from decimal import Decimal
from typing import Any, Optional, Dict

from application.core.schemas.base import BaseSimpleSchema
from application.models.payment import Currency


class PaymentCreatedEvent(BaseSimpleSchema):
    """Схема данных события о создании платежа."""

    payment_id: UUID = Field(..., description='Уникальный идентификатор созданного платежа')

    class Config:
        """Конфигурация схемы."""

        frozen = True


class PaymentBaseSchema(BaseSimpleSchema):
    """Базовая схема платежа."""

    amount: Decimal = Field(..., gt=0, description='Сумма платежа')
    currency: Currency = Field(default=Currency.RUB, description='Валюта платежа')
    description: Optional[str] = Field(None, max_length=255, description='Описание транзакции')
    metadata_extra: Optional[Dict[str, Any]] = Field(None, description='Дополнительная информация в формате JSON')
    idempotency_key: str = Field(..., min_length=10, max_length=100, description='Ключ идемпотентности')
    webhook_url: str = Field(..., description='URL для уведомления о результате')


class PaymentCreateSchema(PaymentBaseSchema):
    """Схема для создания нового платежа."""
