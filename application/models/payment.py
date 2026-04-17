import enum

from sqlalchemy import CheckConstraint, DateTime, Enum, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from decimal import Decimal
from datetime import datetime

from .base import Base, BaseMixin


class PaymentStatus(str, enum.Enum):
    PENDING = 'pending'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'


class Currency(str, enum.Enum):
    RUB = 'RUB'
    USD = 'USD'
    EUR = 'EUR'


class Payment(Base, BaseMixin):
    """Платеж"""

    __tablename__ = 'payments'

    __table_args__ = (
        CheckConstraint('amount > 0', name='ck_payment_amount_positive'),
        CheckConstraint('completed_at >= created_at', name='ck_payment_date_order'),
        CheckConstraint('char_length(idempotency_key) >= 10', name='ck_payment_idempotency_key_len'),
        CheckConstraint("NOT (status IN ('SUCCEEDED', 'FAILED') AND completed_at IS NULL)", name='ck_payment_completion_date_required'),
    )

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
