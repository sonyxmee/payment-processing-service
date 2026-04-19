from application.repositories.payment import PaymentRepository

from .base import BaseService


class PaymentService(BaseService):
    """Сервис для управления платежами."""

    repository: PaymentRepository
