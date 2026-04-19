from fastapi import Depends

from application.repositories.payment import PaymentRepository
from application.repositories.outbox import OutboxEventRepository

from .outbox import OutboxEventService
from .payment import PaymentService


def get_payment_service(
    repository: PaymentRepository = Depends(),
    outbox: OutboxEventService = Depends(),
) -> PaymentService:
    """Фабрика для создания сервиса платежей."""
    return PaymentService(repo=repository, outbox_service=outbox)


def get_outbox_service(repository: OutboxEventRepository = Depends()) -> OutboxEventService:
    """Фабрика для создания сервиса для работы с исходящими событиями."""
    return OutboxEventService(repository=repository)
