from typing import Any, AsyncIterator
from contextlib import asynccontextmanager
from pydantic import PostgresDsn
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from application.core.config import settings


class DatabaseSessionManager:
    """Менеджер сессий подключения к базе данных."""

    def __init__(self, url: PostgresDsn, **sessionmaker_options) -> None:
        engine_kwargs: dict[str, Any] = self._get_engine_kwargs(url)
        self._engine: AsyncEngine = create_async_engine(**engine_kwargs)

        self._sessionmaker: async_sessionmaker = async_sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            **sessionmaker_options,
        )

    def _get_engine_kwargs(self, url: PostgresDsn) -> dict[str, Any]:
        """Формирует словарь аргументов для создания асинхронного движка SQLAlchemy."""
        engine_kwargs: dict[str, Any] = {
            'url': url.unicode_string(),
            'pool_size': settings.database.pool_size,
            'max_overflow': settings.database.max_overflow,
            'pool_recycle': settings.database.pool_recycle,
            'pool_timeout': settings.database.pool_timeout,
        }
        return engine_kwargs

    async def close(self) -> None:
        """Закрывает все соединения пула."""
        await self._engine.dispose()

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Контекстный менеджер для сессии.
        Автоматически открывает транзакцию и делает commit/rollback.
        """
        async with self._sessionmaker() as session:
            async with session.begin():
                yield session


session_manager: DatabaseSessionManager = DatabaseSessionManager(url=settings.database.dsn)
