from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, BaseMixin, TimestampMixin


class OutboxEvent(Base, BaseMixin, TimestampMixin):
    """Исходящее событие"""

    __tablename__ = 'outbox'

    event_type: Mapped[str] = mapped_column(String(100), nullable=False, comment='Тип события')
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, comment='Данные события')
    processed: Mapped[bool] = mapped_column(Boolean, server_default=False, index=True, comment='Статус обработки')
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='Время успешной обработки')
