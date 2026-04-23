from typing import Protocol, Any


class MessageBroker(Protocol):
    """Интерфейс брокера сообщений."""

    async def publish(self, topic: str, payload: dict[str, Any]) -> None:
        """Публикует сообщение в брокер."""
