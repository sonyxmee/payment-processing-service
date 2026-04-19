from datetime import datetime
from typing import TypeVar

from sqlalchemy import DateTime, text, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid
from sqlalchemy.dialects.postgresql import UUID


class Base(AsyncAttrs, DeclarativeBase):
    """
    Базовый класс для декларативного сопоставления моделей с объектами БД.

    https://docs.sqlalchemy.org/en/20/orm/mapping_styles.html#orm-declarative-mapping
    """


class BaseMixin:
    """Базовый миксин моделей.

    Добавляет:
        `id` - поле с уникальным идентификатором записи (Primary Key)
        `__repr__` - метод, формирующий стандартное текстовое отображение класса
    """

    id: Mapped[Uuid] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
        comment='Уникальный идентификатор UUID',
    )

    def __repr__(self):
        return f'{type(self).__name__}[{self.id}]'


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment='Время создания',
    )


ModelT = TypeVar('ModelT', bound=Base)
