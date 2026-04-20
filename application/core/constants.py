from typing import Final

OUTBOX_RETRY_LIMIT = 3
PENDING_EVENTS_LIMIT: Final[int] = 10

# Константы для RabbitMQ
PAYMENTS_QUEUE_NAME = 'payments.new'
PAYMENTS_ROUTING_KEY = 'payments.new'
PAYMENTS_EXCHANGE = 'payments_exchange'
