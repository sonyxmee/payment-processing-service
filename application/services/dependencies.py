from application.repositories.payment import PaymentRepository
from application.repositories.outbox import OutboxEventRepository

from .outbox import OutboxEventService
from .payment import PaymentService


def get_outbox_service() -> OutboxEventService:
    """Фабрика для создания сервиса для работы с исходящими событиями."""
    return OutboxEventService(repository=OutboxEventRepository())


def get_payment_service() -> PaymentService:
    """Фабрика для создания сервиса платежей."""
    return PaymentService(repository=PaymentRepository(), outbox_service=get_outbox_service())
