from typing import Sequence
from uuid import UUID
from sqlalchemy import Result, select, Select, update

from application.models.outbox import OutboxEvent, OutboxStatus
from application.orm.session import AsyncSession

from .base import BaseRepository


class OutboxEventRepository(BaseRepository):
    """Репозиторий для работы с очередью исходящих событий.."""

    model: type[OutboxEvent] = OutboxEvent

    async def get_pending_events(self, db_session: AsyncSession, limit: int) -> Sequence[OutboxEvent]:
        """Получает необработанные события с блокировкой FOR UPDATE SKIP LOCKED."""

        statement: Select = (
            select(OutboxEvent)
            .where(OutboxEvent.status.in_([OutboxStatus.PENDING, OutboxStatus.FAILED]))
            .order_by(OutboxEvent.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

        result: Result = await db_session.execute(statement)
        return result.scalars().all()

    async def increment_attempts(self, event_id: UUID, error_msg: str, status: OutboxStatus, db_session: AsyncSession):
        """Атомарное увеличение счетчика попыток и запись ошибки."""
        statement: Select = (
            update(OutboxEvent)
            .where(OutboxEvent.id == event_id)
            .values(
                attempts=OutboxEvent.attempts + 1,
                error=error_msg,
                status=status,
            )
        )
        await db_session.execute(statement)
        await db_session.flush()
