import enum

from sqlalchemy import DateTime, Enum, Numeric, String, Text, text, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import Uuid
from sqlalchemy.dialects.postgresql import JSONB, UUID

from decimal import Decimal
from datetime import datetime


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


class PaymentStatus(str, enum.Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class Currency(str, enum.Enum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class Payment(Base, BaseMixin):
    __tablename__ = 'payments'

    amount: Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), comment='Сумма платежа')
    currency: Mapped[Currency] = mapped_column(Enum(Currency), server_default=Currency.RUB, comment='Валюта')
    description: Mapped[str | None] = mapped_column(String(255), comment='Описание транзакции')
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, comment='Дополнительная информация')
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus), server_default=PaymentStatus.PENDING, index=True, comment='Текущий статус платежа'
    )  # TODO: передать .value
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, comment='Ключ идемпотентности для защиты от дублей')
    webhook_url: Mapped[str] = mapped_column(Text, comment='URL для уведомления о результате')

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment='Дата и время создания платежа'
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment='Дата и время завершения обработки платежа')
