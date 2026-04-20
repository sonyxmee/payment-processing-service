import asyncio
import signal

from application.core.dependencies import get_db_session
from application.processors.broker import RabbitMQBroker
from application.processors.outbox import OutboxProcessor
from application.services.dependencies import get_outbox_service
from application.core.config import settings
from application.core.logger import outbox_logger as log

# from .base import run_worker


async def main():
    broker: RabbitMQBroker = RabbitMQBroker(connection_url=settings.rabbitmq_url)
    await broker.connect()

    processor = OutboxProcessor(outbox_service=get_outbox_service(), broker=broker)

    loop = asyncio.get_running_loop()

    def handle_signal():
        log.info('Shutdown signal received, initiating graceful stop...')
        processor.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    try:
        log.info('Outbox worker starting...')
        await processor.run(db_session_factory=get_db_session)
    except Exception as e:
        log.critical(f'Outbox Worker crashed unexpectedly: {e}', exc_info=True)
    finally:
        log.info('Cleaning up resources...')
        await broker.close()
        log.info('Worker stopped cleanly.')


# async def main():
#     broker = RabbitMQBroker(connection_url=settings.rabbitmq_url)
#     await broker.connect()

#     async def run_logic():
#         await processor.run(db_session_factory=get_db_session)

#     processor = OutboxProcessor(outbox_service=get_outbox_service(), broker=broker)
#     await run_worker(stop_callback=processor.stop, run_logic=run_logic, shutdown_logic=broker.close, log=log)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Игнорируем, так как сигнал уже обработан внутри
        pass
