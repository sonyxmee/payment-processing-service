import aio_pika

from aio_pika.abc import AbstractChannel, AbstractMessage, FieldValue
from pydantic import ValidationError

from application.core.exceptions import ConflictException, PaymentGatewayException, PaymentWebhookException
from application.core.logger import consumer_logger as log
from application.infrastructure.config import PaymentConsumerConfig


class PaymentErrorHandler:
    """Обработчик ошибок для потребителя платежных сообщений.

    Определяет стратегию обработки исключений: маршрутизирует сообщения в
    очереди повторов или DLQ, управляет подтверждением (ACK/NACK) сообщений.
    """

    def __init__(self, channel: AbstractChannel, config: PaymentConsumerConfig):
        self.channel: AbstractChannel = channel
        self.config: PaymentConsumerConfig = config

    async def handle_validation_error(self, message: AbstractMessage, exc: ValidationError):
        """Критическая ошибка данных: отправляем в DLQ и подтверждаем."""
        log.warning(f'Validation error: {exc}. MsgID: {message.message_id}, CorrelationID: {message.headers.get("correlation_id")}')
        await self._republish_message(message, self.config.DLQ)
        await message.ack()

    async def handle_conflict(self, message: AbstractMessage, exc: ConflictException):
        """Конфликт данных в БД: делегируем логику ретраев."""
        log.warning(
            f'Conflict detected: {exc}, retrying... MsgID: {message.message_id}, CorrelationID: {message.headers.get("correlation_id")}'
        )
        await self._handle_failure(message)

    async def handle_gateway_error(self, message: AbstractMessage, exc: PaymentGatewayException):
        """Ошибка стороннего API: делегируем логику ретраев."""
        log.warning(f'Gateway error: {exc}. MsgID: {message.message_id}, CorrelationID: {message.headers.get("correlation_id")}')
        await self._handle_failure(message)

    async def handle_webhook_error(self, message: AbstractMessage, exc: PaymentWebhookException):
        """Ошибка при отправке webhook: перенаправляет сообщение в очередь для сбойных вебхуков."""
        log.error(
            f'Webhook delivery failed: {exc}. MsgID: {message.message_id}, CorrelationID: {message.headers.get("correlation_id")}, Error: {exc}'
        )
        await self.channel.default_exchange.publish(message, routing_key=self.config.WEBHOOKS_DLQ)
        await message.ack()

    async def handle_unknown(self, message: AbstractMessage, exc: Exception):
        """Fallback для неожиданной ошибки."""
        log.error(f'Unexpected error: {exc}. MsgID: {message.message_id}, CorrelationID: {message.headers.get("correlation_id")}')
        await self._republish_message(message, self.config.DLQ)
        await message.ack()

    async def _handle_failure(self, message: AbstractMessage):
        """Принимает решение при ошибке: ретрай или отправка в DLQ."""
        death_headers: FieldValue = message.headers.get('x-death', [])
        total_retries: int = sum(d.get('count', 0) for d in death_headers)
        next_attempt: int = total_retries + 1

        target_queue: str = self.config.RETRY_CONFIG[next_attempt].queue if next_attempt in self.config.RETRY_CONFIG else self.config.DLQ
        log.info(f'Processing failure for MsgID: {message.message_id}. Attempt: {next_attempt}, Target: {target_queue}')
        try:
            await self._republish_message(message, target_queue)
            await message.ack()

        except Exception as e:
            log.critical(f'CRITICAL: Failed to republish message {message.message_id} to {target_queue}: {e}')
            await message.nack(requeue=True)

    async def _republish_message(self, message: AbstractMessage, target_queue: str):
        """Метод публикации сообщения в очередь."""
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.body,
                headers=message.headers,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=target_queue,
        )
