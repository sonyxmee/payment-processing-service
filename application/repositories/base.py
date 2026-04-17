from abc import ABC
from uuid import UUID
from pydantic import BaseModel
from typing import Any, Generic

from sqlalchemy import Select, select, Result
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.sqlalchemy import handle_db_exceptions
from application.models.base import ModelT


class BaseRepository(ABC, Generic[ModelT]):
    """Базовый репозиторий для взаимодействия с базой данных"""

    model: type[ModelT]

    @handle_db_exceptions
    async def create(self, schema: BaseModel, db_session: AsyncSession) -> ModelT:
        """Создаёт запись в базе данных и возвращает её."""
        data: dict[str, Any] = schema.model_dump()
        instance: ModelT = self.model(**data)

        db_session.add(instance)
        await db_session.flush()
        await db_session.refresh(instance)

        return instance

    @handle_db_exceptions
    async def get_one(
        self,
        id_: UUID,
        db_session: AsyncSession,
    ) -> ModelT:
        """Получить запись по идентификатору."""
        statement: Select = select(self.model).where(self.model.id == id_)
        result: Result = await db_session.execute(statement)
        object_: ModelT = result.scalar_one()
        return object_
