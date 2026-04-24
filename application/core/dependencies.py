from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession

from application.orm.session import session_manager


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Функция для получения сессии подключения к базе данных.

    Используется для внедрения зависимостей FastAPI.
    """
    async with session_manager.session() as session:
        yield session
