from datetime import datetime
from enum import Enum, StrEnum

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin, TimestampMixin


class OutboxStatus(StrEnum):
    """Статусы обработки исходящих событий в системе Outbox."""

    PENDING = 'pending'  # Ожидает отправки
    PROCESSED = 'processed'  # Успешно отправлено
    FAILED = 'failed'  # Ошибка, но есть попытки
    EXHAUSTED = 'exhausted'  # Превышен лимит попыток


class OutboxEvent(Base, BaseMixin, TimestampMixin):
    """Исходящее событие"""

    __tablename__ = 'outbox'

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, comment='Тип события')
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='Данные события')

    status: Mapped[OutboxStatus] = mapped_column(Enum(OutboxStatus), default=OutboxStatus.PENDING, index=True, comment='Статус события')
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='Время успешной обработки')

    attempts: Mapped[int] = mapped_column(Integer, server_default='0', comment='Количество попыток отправки')
    error: Mapped[str | None] = mapped_column(Text, nullable=True, comment='Последняя ошибка при отправке')
