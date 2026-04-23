from abc import ABC
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.schemas.base import SchemaT
from application.models.base import ModelT, RowLockLevel
from application.repositories.base import BaseRepository


class BaseService(ABC):
    """
    Базовый класс сервисного слоя.
    Обеспечивает интерфейс взаимодействия между API и уровнем данных (репозиторием).
    """

    def __init__(self, repository: BaseRepository):
        self.repository: BaseRepository = repository

    async def get_one(self, id_: int, db_session: AsyncSession, lock_mode: Optional[RowLockLevel] = None, **kwargs) -> ModelT:
        """Метод получения одной записи"""
        return await self.repository.get_one(id_=id_, db_session=db_session, lock_mode=lock_mode, **kwargs)

    async def create(self, payload: SchemaT, db_session: AsyncSession) -> ModelT:
        """Метод создания записи"""
        return await self.repository.create(schema=payload, db_session=db_session)

    async def update(self, id_: int, payload: SchemaT, db_session: AsyncSession) -> ModelT:
        """Метод обновления записи"""
        return await self.repository.update(id_=id_, payload=payload, db_session=db_session)
