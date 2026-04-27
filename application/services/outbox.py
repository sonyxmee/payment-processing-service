from uuid import UUID
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from application.core.constants import PENDING_EVENTS_LIMIT
from application.core.schemas.base import SchemaT
from application.models.outbox import OutboxStatus
from application.repositories.outbox import OutboxEventRepository
from application.schemas.enums import EventType
from application.schemas.outbox import OutboxEventCreateSchema, OutboxEventUpdateSchema

from .base import BaseService


class OutboxEventService(BaseService):
    """Сервис для управления очередью исходящих событий.."""

    repository: OutboxEventRepository

    async def create(
        self,
        event_type: EventType,
        payload: SchemaT,
        db_session: AsyncSession,
    ):
        """Сериализует данные события и сохраняет запись о событии в БД."""

        serialized_payload: dict[str, Any] = payload.model_dump(mode='json')
        data = OutboxEventCreateSchema(event_type=event_type, payload=serialized_payload)

        return await super().create(payload=data, db_session=db_session)

    async def get_pending_events(self, db_session: AsyncSession, limit: int = PENDING_EVENTS_LIMIT):
        """Возвращает список необработанных событий."""
        return await self.repository.get_pending_events(db_session=db_session, limit=limit)

    async def mark_as_processed(self, event_id: UUID, db_session: AsyncSession):
        """Успешное завершение: ставим флаг и время."""
        update_data = OutboxEventUpdateSchema(
            status=OutboxStatus.PROCESSED,
            processed_at=datetime.now(timezone.utc),
            error=None,
        )
        await self.repository.update(id_=event_id, payload=update_data, db_session=db_session)

    async def mark_as_failed(self, event_id: UUID, error_msg: str, db_session: AsyncSession):
        """Ошибка: увеличивает счетчик попыток и сохраняет текст ошибки."""
        await self.repository.increment_attempts(
            event_id=event_id,
            status=OutboxStatus.FAILED,
            error_msg=error_msg,
            db_session=db_session,
        )

    async def mark_as_exhausted(self, event_id: UUID, error_msg: str, db_session: AsyncSession):
        """Помечает событие как окончательно неуспешное (исчерпан лимит попыток) и исключает его из дальнейшей обработки."""
        update_data = OutboxEventUpdateSchema(status=OutboxStatus.EXHAUSTED, error=error_msg)
        await self.repository.update(id_=event_id, payload=update_data, db_session=db_session)
