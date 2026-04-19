from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.schemas.base import SchemaT
from application.repositories.outbox import OutboxEventRepository
from application.schemas.enums import EventType
from application.schemas.outbox import OutboxEventCreateSchema

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
