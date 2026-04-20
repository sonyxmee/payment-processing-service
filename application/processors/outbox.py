import asyncio

from typing import Callable, Sequence
from sqlalchemy.ext.asyncio import AsyncSession

from application.core.constants import OUTBOX_RETRY_LIMIT
from application.core.logger import outbox_logger as log
from application.models.outbox import OutboxEvent
from application.services.outbox import OutboxEventService

from .protocols import MessageBroker


class OutboxProcessor:
    """Отвечает за фоновую отправку исходящих событий в брокер."""

    def __init__(self, outbox_service: OutboxEventService, broker: MessageBroker):

        self.service: OutboxEventService = outbox_service
        self.broker: MessageBroker = broker
        self._stop_event = asyncio.Event()
        self.max_attempts = OUTBOX_RETRY_LIMIT

    def stop(self):
        """Инициирует процесс корректной остановки воркера."""
        log.info('Signal received, stopping Outbox Processor...')
        self._stop_event.set()

    async def run(self, db_session_factory: Callable):
        """Запускает основной цикл обработки событий. Выполняется до получения сигнала остановки."""

        log.info('Outbox Processor started.')

        while not self._stop_event.is_set():
            try:
                await self._run_iteration(db_session_factory)

            except Exception as e:
                log.critical(f'Infrastructure or database error: {e}', exc_info=True)
                await asyncio.sleep(5)

    async def _run_iteration(self, db_session_factory: Callable):
        """Выполняет одну итерацию обработки событий."""
        async with db_session_factory() as db_session:
            events: Sequence[OutboxEvent] = await self.service.get_pending_events(db_session=db_session, limit=10)

            if not events:
                await self._wait_for_next_tick()
                return

            for event in events:
                await self._process_event(event=event, db_session=db_session)

    async def _wait_for_next_tick(self):
        """Выполняет прерываемую паузу. Ожидает сигнала остановки или истечения таймаута."""
        try:
            await asyncio.wait_for(self._stop_event.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pass

    async def _process_event(self, event: OutboxEvent, db_session: AsyncSession):
        """Выполняет отправку события в брокер и обновление статуса."""
        try:
            await self.broker.send(event.event_type, event.payload)
            await self.service.mark_as_processed(event_id=event.id, db_session=db_session)
            log.info(f'Event {event.id} sent and marked.')
        except Exception as e:
            log.error(f'Failed to process event {event.id}: {e}')
            await self.handle_failure(event=event, exception=e, db_session=db_session)

    async def handle_failure(self, event: OutboxEvent, exception: Exception, db_session: AsyncSession):
        """Обрабатывает ошибку отправки события: принимает решение о повторе или завершении события."""
        new_attempts = event.attempts + 1
        if event.attempts + 1 >= self.max_attempts:
            await self.service.mark_as_exhausted(event_id=event.id, error_msg=str(exception), db_session=db_session)
            log.critical(f'Event {event.id} exhausted after {self.max_attempts} attempts.')
        else:
            await self.service.mark_as_failed(event_id=event.id, error_msg=str(exception), db_session=db_session)
            log.info(f'Event {event.id} failed, retry {new_attempts}/{self.max_attempts}')
