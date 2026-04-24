import abc
import asyncio
import signal
import logging

from typing import Callable, Coroutine, Any

from application.infrastructure.broker import BaseRabbitBroker


class BaseWorker(abc.ABC):
    def __init__(self, broker: BaseRabbitBroker, logger: logging.Logger, stop_event: asyncio.Event):
        self.broker = broker
        self.log = logger
        self._stop_event = stop_event
        self._setup_signals()

    def _setup_signals(self):
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_signal)

    def _handle_signal(self):
        self.log.info(f'Signal received, stopping {self.__class__.__name__}...')
        self._stop_event.set()

    @abc.abstractmethod
    async def run(self):
        """Основной метод запуска воркера."""
        pass

    async def start(self):
        """Точка входа для запуска воркера."""
        self.log.info(f'{self.__class__.__name__} started.')
        try:
            await self.run()
        except Exception as e:
            self.log.critical(f'{self.__class__.__name__} crashed: {e}', exc_info=True)
            raise
        finally:
            self.log.info('Worker stopped.')


def run_worker(main_coroutine: Callable[[], Coroutine[Any, Any, None]]):
    """Универсальный раннер воркеров."""
    try:
        asyncio.run(main_coroutine())
    except KeyboardInterrupt:
        pass
    except Exception:
        raise
