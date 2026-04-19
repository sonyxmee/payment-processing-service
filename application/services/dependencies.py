from application.repositories.payment import PaymentRepository
from .payment import PaymentService


def payment_service() -> PaymentService:
    """Возвращает экземпляр сервиса для работы с платежами."""

    return PaymentService(PaymentRepository)
