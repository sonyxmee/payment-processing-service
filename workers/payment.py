import asyncio
import logging

from pydantic import ValidationError

from application.core.exceptions import ConflictException, PaymentGatewayException, PaymentWebhookException
from application.handlers.payment import PaymentHandler
from application.infrastructure.broker import BaseRabbitBroker
from application.core.config import settings
from application.infrastructure.consumer import PaymentConsumer
from application.infrastructure.dispatcher import ExceptionDispatcher
from application.infrastructure.error_handlers import PaymentErrorHandler
from application.infrastructure.webhook import WebhookClient
from application.services.dependencies import get_payment_service
from application.infrastructure.config import PaymentConsumerConfig as cfg
from application.core.logger import consumer_logger

from .base import BaseWorker, run_worker


class PaymentWorker(BaseWorker):
    """Воркер для фоновой обработки входящих платежных событий.

    Отвечает за жизненный цикл потребления сообщений из очереди,
    делегируя бизнес-логику PaymentConsumer.
    """

    def __init__(self, broker, consumer: PaymentConsumer, logger: logging.Logger, stop_event: asyncio.Event):
        """Инициализирует воркер.

        :param broker: Брокер сообщений.
        :param consumer: Консьюмер, содержащий логику обработки сообщений из очереди.
        :param logger: Логгер для фиксации событий жизненного цикла.
        :param stop_event: Событие для корректной остановки воркера.
        """
        super().__init__(broker, logger, stop_event)
        self.consumer = consumer

    async def run(self):
        """Запускает процесс обработки сообщений."""
        await self.consumer.run()


def setup_payment_dispatcher(error_policy: PaymentErrorHandler) -> ExceptionDispatcher:
    """Конфигурирует диспетчер исключений с необходимыми правилами обработки."""
    dispatcher = ExceptionDispatcher(default_handler=error_policy.handle_unknown)

    dispatcher.register(ValidationError, error_policy.handle_validation_error)
    dispatcher.register(ConflictException, error_policy.handle_conflict)
    dispatcher.register(PaymentGatewayException, error_policy.handle_gateway_error)
    dispatcher.register(PaymentWebhookException, error_policy.handle_webhook_error)

    return dispatcher


async def main():
    """Точка входа для Payment воркера."""

    async with BaseRabbitBroker(settings.rabbitmq_url) as broker:
        error_policy = PaymentErrorHandler(broker.channel, cfg)
        dispatcher = setup_payment_dispatcher(error_policy)

        payment_handler = PaymentHandler(service=get_payment_service(), webhook_client=WebhookClient())

        stop_event = asyncio.Event()
        consumer = PaymentConsumer(
            broker=broker,
            handler=payment_handler,
            dispatcher=dispatcher,
            stop_event=stop_event,
        )
        worker = PaymentWorker(
            broker=broker,
            consumer=consumer,
            logger=consumer_logger,
            stop_event=stop_event,
        )
        await worker.start()


if __name__ == '__main__':
    run_worker(main)
