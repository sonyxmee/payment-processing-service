import asyncio
import json
from typing import Any
import aio_pika

from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractQueue, AbstractRobustConnection, AbstractMessage

from application.handlers.payment import PaymentHandler
from application.infrastructure.dispatcher import ExceptionDispatcher

from .config import PaymentConsumerConfig as cfg


class PaymentConsumer:
    """Потребитель платежных сообщений из брокера.

    Класс управляет жизненным циклом соединения, инициализацией инфраструктуры
    очередей и процессом потребления сообщений. Делегирует бизнес-логику
    обработчику, а управление ошибками - диспетчеру исключений.
    """

    def __init__(self, connection_url, handler: PaymentHandler, dispatcher: ExceptionDispatcher, stop_event: asyncio.Event):
        self.connection_url = connection_url
        self.handler = handler
        self.dispatcher = dispatcher
        self._stop_event = stop_event

    async def run(self):
        """Точка входа для раннера."""
        self._connection: AbstractRobustConnection = await aio_pika.connect_robust(self.connection_url)
        self.channel: AbstractChannel = await self._connection.channel()

        await self._setup_infrastructure()
        await self.consume()

    async def _setup_infrastructure(self):
        """Точка сборки инфраструктуры."""
        await self._setup_exchanges()
        await self._setup_error_infrastructure()
        await self._setup_main_queue()

    async def _setup_exchanges(self):
        """Объявление всех необходимых обменников."""
        self.events_exchange: AbstractExchange = await self.channel.declare_exchange(
            cfg.EVENTS_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        self.dlx: AbstractExchange = await self.channel.declare_exchange(
            cfg.DLX_EXCHANGE,
            aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

    async def _setup_error_infrastructure(self):
        """Настройка инфраструктуры обработки ошибок (DLQ и очереди ретраев)."""
        # Настройка DLQ
        dlq: AbstractQueue = await self.channel.declare_queue(cfg.DLQ, durable=True)
        await dlq.bind(self.dlx, routing_key=cfg.FAILED_ROUTING_KEY)

        # Настройка очередей с задержкой для ретраев
        for data in cfg.RETRY_CONFIG.values():
            await self.channel.declare_queue(
                name=data.queue,
                durable=True,
                arguments={
                    'x-message-ttl': data.delay * 1000,
                    'x-dead-letter-exchange': '',
                    'x-dead-letter-routing-key': cfg.MAIN_QUEUE,
                },
            )

    async def _setup_main_queue(self):
        """Настройка основной очереди и привязка к входящим событиям."""
        main_queue: AbstractQueue = await self.channel.declare_queue(
            cfg.MAIN_QUEUE, durable=True, arguments={'x-dead-letter-exchange': cfg.DLX_EXCHANGE}
        )
        await main_queue.bind(self.events_exchange, routing_key=cfg.CREATED_ROUTING_KEY)

    async def consume(self):
        """Точка входа: цикл чтения сообщений из очереди."""
        queue: AbstractQueue = await self.channel.get_queue(cfg.MAIN_QUEUE)
        await self.channel.set_qos(prefetch_count=1)

        async for message in queue:
            if self._stop_event.is_set():
                break
            try:
                await self._process_message(message)
            except Exception as e:
                await self.dispatcher.dispatch(message, e)

    async def _process_message(self, message: AbstractMessage):
        """Обработка сообщения."""
        payload: Any = json.loads(message.body.decode())
        await self.handler.handle(payload)
        await message.ack()
