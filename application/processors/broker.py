import json
import aio_pika

from typing import Any
from aio_pika.abc import AbstractChannel, AbstractExchange, AbstractRobustConnection


class RabbitMQBroker:
    def __init__(self, connection_url: str, exchange_name: str = 'events'):
        self.connection_url: str = connection_url
        self.exchange_name: str = exchange_name
        self.connection: AbstractRobustConnection | None = None
        self.channel: AbstractChannel | None = None
        self.exchange: AbstractExchange | None = None

    async def connect(self):
        """Инициализация соединения."""
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel()
        await self.channel.confirm_delivery()
        self.exchange = await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)

    async def send(self, routing_key: str, payload: dict[str, Any]) -> None:
        """Сериализация и отправка в RabbitMQ."""
        if not self.exchange:
            raise RuntimeError('Broker is not connected. Call connect() first.')

        body: bytes = json.dumps(payload, default=str).encode()
        message: aio_pika.Message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type='application/json',
        )
        await self.exchange.publish(message=message, routing_key=routing_key)

    async def close(self):
        """Закрытие соединения."""
        if self.connection:
            await self.connection.close()
