from application.models.outbox import OutboxEvent

from .base import BaseRepository


class OutboxEventRepository(BaseRepository):
    """Репозиторий для работы с очередью исходящих событий.."""

    model: type[OutboxEvent] = OutboxEvent
