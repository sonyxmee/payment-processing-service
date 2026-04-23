from typing import Awaitable, Callable, Type
from aio_pika.abc import AbstractMessage


class ExceptionDispatcher:
    """Маршрутизирует исключения к соответствующим обработчикам в зависимости от типа ошибки."""

    def __init__(self, default_handler: Callable[[AbstractMessage, Exception], Awaitable[None]]) -> None:
        """Инициализирует диспетчер и задает обработчик по умолчанию."""
        self._handlers: dict[Type[Exception], Callable[[AbstractMessage, Exception], Awaitable[None]]] = {}
        self._default_handler = default_handler

    def register(
        self,
        exception_type: Type[Exception],
        handler: Callable[[AbstractMessage, Exception], Awaitable[None]],
    ) -> None:
        """Регистрирует обработчик для указанного типа исключения."""
        self._handlers[exception_type] = handler

    async def dispatch(self, message: AbstractMessage, exc: Exception) -> None:
        """Находит и вызывает подходящий обработчик исключения, либо обработчик по умолчанию."""
        handler: Callable[[AbstractMessage, Exception], Awaitable[None]] | None = self._handlers.get(type(exc))

        if not handler:
            for exc_type, h in self._handlers.items():
                if isinstance(exc, exc_type):
                    handler = h
                    break

        target_handler: Callable[[AbstractMessage, Exception], Awaitable[None]] = handler or self._default_handler
        await target_handler(message, exc)
