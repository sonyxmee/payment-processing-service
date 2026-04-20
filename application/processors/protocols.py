from typing import Protocol, Any


class MessageBroker(Protocol):
    """Интерфейс брокера сообщений."""

    async def send(self, topic: str, payload: dict[str, Any]) -> None:
        """Отправляет сообщение в брокер."""
