from dataclasses import dataclass

from application.core.constants import EVENTS_EXCHANGE
from application.schemas.enums import EventType


@dataclass(frozen=True)
class RetryLevel:
    """Конфигурация параметров для повторной попытки отправки сообщения."""

    delay: int
    queue: str


class PaymentConsumerConfig:
    """Конфигурация инфраструктуры RabbitMQ для обработки платежей."""

    EVENTS_EXCHANGE = EVENTS_EXCHANGE
    DLX_EXCHANGE = 'dlx_exchange'

    MAIN_QUEUE = 'payments.new'
    DLQ = 'payments.dlq'
    WEBHOOKS_DLQ = 'payments.webhooks.dlq'

    CREATED_ROUTING_KEY = EventType.PAYMENT_CREATED.value
    FAILED_ROUTING_KEY = 'payments.failed'

    RETRY_CONFIG = {
        1: RetryLevel(delay=10, queue='payments.retry_10s'),
        2: RetryLevel(delay=60, queue='payments.retry_60s'),
        3: RetryLevel(delay=300, queue='payments.retry_300s'),
    }
