from application.models.payment import Payment

from .base import BaseRepository


class PaymentRepository(BaseRepository):
    """Репозиторий для работы с платежами."""

    model: type[Payment] = Payment
