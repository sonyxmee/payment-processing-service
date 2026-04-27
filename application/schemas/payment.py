from uuid import UUID
from pydantic import Field, HttpUrl, field_serializer
from typing import Any, Optional, Dict

from application.core.schemas.api import BaseResponseSchema
from application.core.schemas.base import BaseIdMixin, BaseSimpleSchema, TimestampedMixin
from application.core.schemas.serializer import DateTimeUTC
from application.core.validator import PaymentAmount
from application.models.payment import Currency, PaymentStatus
from application.schemas.outbox import BaseUpdateSchema


class PaymentCreatedDTO(BaseSimpleSchema):
    """Схема данных события о создании платежа."""

    payment_id: UUID = Field(..., description='Уникальный идентификатор созданного платежа')

    class Config:
        """Конфигурация схемы."""

        frozen = True


class PaymentBaseSchema(BaseSimpleSchema):
    """Базовая схема платежа."""

    amount: PaymentAmount = Field(..., description='Сумма платежа')
    currency: Currency = Field(default=Currency.RUB, description='Валюта платежа')
    description: Optional[str] = Field(None, max_length=255, description='Описание транзакции')
    metadata_extra: Optional[Dict[str, Any]] = Field(None, description='Дополнительная информация в формате JSON', example={'key': 'value'})
    idempotency_key: str = Field(..., min_length=10, max_length=100, description='Ключ идемпотентности')
    webhook_url: HttpUrl = Field(..., description='URL для уведомления о результате')

    @field_serializer('webhook_url')
    def serialize_url(self, url: HttpUrl, _info):
        return str(url)


class PaymentCreateSchema(PaymentBaseSchema):
    """Схема для создания нового платежа."""


class PaymentUpdateSchema(BaseUpdateSchema):
    """Схема для обновления существующего платежа."""

    status: Optional[PaymentStatus] = Field(default=None, description='Текущий статус платежа')
    completed_at: Optional[DateTimeUTC] = Field(default=None, description='Дата и время завершения обработки платежа')


class PaymentViewSchema(PaymentBaseSchema, BaseIdMixin, TimestampedMixin):
    """Схема для отображения Платежа"""

    status: PaymentStatus = Field(..., description='Текущий статус платежа')
    completed_at: Optional[DateTimeUTC] = Field(default=None, description='Дата и время завершения обработки платежа')


class PaymentResponseSchema(BaseResponseSchema):
    """Схема успешного ответа при выполнении операции над Платежом."""

    result: PaymentViewSchema
