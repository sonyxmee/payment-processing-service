import json
import aio_pika

from typing import Optional

from pydantic import AmqpDsn


class BaseRabbitBroker:
    """Базовый брокер сообщений RabbitMQ."""

    def __init__(self, connection_url: AmqpDsn):
        self.connection_url: str = connection_url.unicode_string()
        self.connection: Optional[aio_pika.abc.AbstractRobustConnection] = None
        self.channel: Optional[aio_pika.abc.AbstractChannel] = None

    async def connect(self):
        """Открытие соединения и канала."""
        self.connection = await aio_pika.connect_robust(self.connection_url)
        self.channel = await self.connection.channel(publisher_confirms=True)

    async def close(self):
        """Закрытие соединения."""
        if self.connection:
            await self.connection.close()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


class RabbitPublisher(BaseRabbitBroker):
    def __init__(self, connection_url: str, exchange_name: str):
        super().__init__(connection_url)
        self.exchange_name: str = exchange_name
        self.exchange: Optional[aio_pika.abc.AbstractExchange] = None

    async def connect(self):
        """Открывает соединение с брокером и создает базовый exchange."""
        await super().connect()
        self.exchange = await self.channel.declare_exchange(self.exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)

    async def publish(self, routing_key: str, payload: dict):
        """Метод публикации сообщения."""
        if not self.exchange:
            raise RuntimeError('Exchange not declared. Connect first.')

        body: bytes = json.dumps(payload, default=str).encode()
        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type='application/json',
        )
        await self.exchange.publish(message, routing_key=routing_key)
