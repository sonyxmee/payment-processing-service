from pydantic import Field

from application.core.schemas.base import BaseSimpleSchema, BaseUpdateSchema
from application.core.schemas.serializer import DateTimeUTC
from application.models.outbox import OutboxStatus
from application.schemas.enums import EventType


class OutboxEventBaseSchema(BaseSimpleSchema):
    """Базовая схема исходящего события."""

    event_type: EventType = Field(..., description='Тип события')
    payload: dict = Field(..., description='Данные события в формате JSON')
    status: OutboxStatus = Field(default=OutboxStatus.PENDING, description='Статус обработки')
    processed_at: DateTimeUTC | None = Field(default=None, description='Время успешной обработки')
    attempts: int = Field(default=0, description='Количество попыток отправки')
    error: str | None = Field(default=None, description='Текст ошибки при отправке')


class OutboxEventCreateSchema(OutboxEventBaseSchema):
    """Схема для создания записи события."""


class OutboxEventUpdateSchema(BaseUpdateSchema):
    """Схема для обновления записи события."""

    status: OutboxStatus | None = Field(None, description='Статус обработки')
    processed_at: DateTimeUTC | None = Field(None, description='Время успешной обработки')
    attempts: int | None = Field(None, description='Количество попыток отправки')
    error: str | None = Field(None, description='Текст ошибки при отправке')
