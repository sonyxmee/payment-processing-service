from sqlalchemy.ext.asyncio import AsyncSession

from application.models.payment import Payment
from application.repositories.payment import PaymentRepository
from application.schemas.enums import EventType
from application.schemas.payment import PaymentCreateSchema, PaymentCreatedEvent

from .base import BaseService
from .outbox import OutboxEventService


class PaymentService(BaseService):
    """Сервис для управления платежами."""

    repository: PaymentRepository

    def __init__(self, repository: PaymentRepository, outbox_service: OutboxEventService):
        """Инициализирует сервис платежей."""
        super().__init__(repository=repository)
        self.outbox_service = outbox_service

    async def create(self, payload: PaymentCreateSchema, db_session: AsyncSession) -> Payment:
        """Создает запись о новом платеже в БД и инициирует событие о создании в outbox."""

        payment: Payment = await super().create(payload=payload, db_session=db_session)
        await self.outbox_service.create(
            event_type=EventType.PAYMENT_CREATED,
            payload=PaymentCreatedEvent(payment_id=payment.id),
            db_session=db_session,
        )

        return payment
