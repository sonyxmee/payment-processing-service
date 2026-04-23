from abc import ABC
from uuid import UUID
from typing import Any, Generic, Optional, Tuple

from sqlalchemy import Select, select, Result, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.dml import ReturningUpdate

from application.core.schemas.base import SchemaT
from application.core.sqlalchemy import handle_db_exceptions
from application.models.base import ModelT, RowLockLevel


class BaseRepository(ABC, Generic[ModelT]):
    """Базовый репозиторий для взаимодействия с базой данных"""

    model: type[ModelT]

    @handle_db_exceptions
    async def create(self, payload: SchemaT, db_session: AsyncSession) -> ModelT:
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
        lock_mode: Optional[RowLockLevel] = None,
        **kwargs,
    ) -> ModelT:
        """Получить запись по идентификатору."""
        statement: Select = select(self.model).where(self.model.id == id_)
        statement = self._apply_lock(statement, lock_mode, **kwargs)

        result: Result = await db_session.execute(statement)
        object_: ModelT = result.scalar_one()
        return object_

    @handle_db_exceptions
    async def update(
        self,
        id_: UUID,
        payload: SchemaT,
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

    def _apply_lock(self, statement: Select, lock_mode: Optional[RowLockLevel], nowait: bool = True, **kwargs) -> Select:
        """Внутренний метод для применения блокировки строк в БД к statement.
        По умолчанию устанавливается режим nowait=True (если данные заблокированы, сразу выдастся ошибка OperationalError).
        """
        if lock_mode is None:
            return statement

        # Маппинг типа блокировки и параметров метода with_for_update
        mapping: dict[str, dict[str, bool]] = {
            RowLockLevel.SHARE: {'read': True},
            RowLockLevel.UPDATE: {},  # default FOR UPDATE
            RowLockLevel.NO_KEY_UPDATE: {'no_key_update': True},
            RowLockLevel.KEY_SHARE: {'read': True, 'key_share': True},
        }
        lock_params: dict[str, bool] = mapping.get(lock_mode, {})
        lock_params['nowait'] = nowait

        return statement.with_for_update(**lock_params)
