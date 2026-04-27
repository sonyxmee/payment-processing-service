import asyncio
import logging

from application.core.constants import EVENTS_EXCHANGE
from application.core.dependencies import session_manager
from application.infrastructure.broker import RabbitPublisher
from application.processors.outbox import OutboxProcessor
from application.services.dependencies import get_outbox_service
from application.core.config import settings
from application.core.logger import outbox_logger

from .base import BaseWorker, run_worker


class OutboxWorker(BaseWorker):
    """Воркер для фоновой обработки событий Outbox.

    Реализует паттерн Transactional Outbox: считывает накопленные в БД записи
    о событиях и публикует их в брокер сообщений, обеспечивая согласованность
    между состоянием базы данных и внешними системами.
    """

    def __init__(self, broker, processor: OutboxProcessor, logger: logging.Logger, stop_event: asyncio.Event):
        """
        Инициализирует воркер.

        :param broker: Брокер сообщений для отправки событий.
        :param processor: Процессор, содержащий логику чтения из БД и публикации.
        :param logger: Логгер для фиксации событий жизненного цикла воркера.
        """

        super().__init__(broker, logger, stop_event)
        self.processor = processor

    async def run(self):
        """Запускает цикл обработки сообщений."""
        await self.processor.run(db_session_factory=session_manager)


async def main():
    """Точка входа для Outbox воркера."""

    async with RabbitPublisher(settings.rabbitmq_url, exchange_name=EVENTS_EXCHANGE) as broker:
        stop_event = asyncio.Event()
        processor = OutboxProcessor(
            outbox_service=get_outbox_service(),
            broker=broker,
            stop_event=stop_event,
        )

        worker = OutboxWorker(
            broker=broker,
            processor=processor,
            logger=outbox_logger,
            stop_event=stop_event,
        )

        await worker.start()


if __name__ == '__main__':
    run_worker(main)
