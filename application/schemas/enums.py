from enum import StrEnum


class EventType(StrEnum):
    """Типы событий в системе."""

    PAYMENT_CREATED = 'payment.created'
