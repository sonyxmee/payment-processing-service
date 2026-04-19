from pydantic import Field

from application.core.schemas.base import BaseSimpleSchema
from application.schemas.enums import EventType


class OutboxEventBaseSchema(BaseSimpleSchema):
    """Базовая схема исходящего события."""

    event_type: EventType = Field(..., description='Тип события')
    payload: dict = Field(..., description='Данные события в формате JSON')


class OutboxEventCreateSchema(OutboxEventBaseSchema):
    """Схема для создания записи события."""
