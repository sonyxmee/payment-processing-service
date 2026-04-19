from abc import ABC
from uuid import UUID
from pydantic import BaseModel
from typing import Any, Generic, Tuple

from sqlalchemy import Select, select, Result, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate

from application.core.sqlalchemy import handle_db_exceptions
from application.models.base import ModelT


class BaseRepository(ABC, Generic[ModelT]):
    """Базовый репозиторий для взаимодействия с базой данных"""

    model: type[ModelT]

    @handle_db_exceptions
    async def create(self, payload: BaseModel, db_session: AsyncSession) -> ModelT:
        """Создаёт запись в базе данных и возвращает её."""
        data: dict[str, Any] = payload.model_dump()
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

    @handle_db_exceptions
    async def update(
        self,
        id_: UUID,
        payload: BaseModel,
        db_session: AsyncSession,
    ) -> ModelT:
        """Обновляет объект в базе данных и возвращает обновлённую запись."""
        data: dict[str, Any] = payload.model_dump(exclude_unset=True)

        update_statement: ReturningUpdate[Tuple] = (
            update(self.model)
            .where(
                self.model.id == id_,
            )
            .values(**data)
            .returning(self.model.id)
        )
        result: Result[Tuple] = await db_session.execute(update_statement)

        updated_id: UUID = result.scalar_one()
        await db_session.flush()

        select_statement: Select[Tuple[ModelT]] = (
            select(self.model)
            .where(
                self.model.id == updated_id,
            )
            .execution_options(populate_existing=True)
        )

        final_result: Result[Tuple[ModelT]] = await db_session.execute(select_statement)
        return final_result.scalar_one()
