import asyncio
import random
import httpx

from datetime import datetime, timezone

from application.core.exceptions import PaymentNonRetryableException, PaymentWebhookException
from application.models.base import RowLockLevel
from application.orm.session import DatabaseSessionManager
from application.schemas.payment import PaymentCreatedDTO, PaymentUpdateSchema
from application.schemas.webhook import PaymentEventStatus, PaymentWebhookPayload, PaymentWebhookSchema
from application.services.payment import PaymentService
from application.models.payment import Payment, PaymentStatus
from application.core.logger import consumer_logger as log
from application.infrastructure.webhook import WebhookClient


class PaymentHandler:
    def __init__(self, service: PaymentService, webhook_client: WebhookClient, db_session_factory: DatabaseSessionManager):
        self.service = service
        self.webhook_client = webhook_client
        self.db_session_factory = db_session_factory

    async def handle(self, payload: dict):
        data: PaymentCreatedDTO = PaymentCreatedDTO(**payload)
        log.info(f'Processing payment {data.payment_id}...')

        async with self.db_session_factory.session() as db_session:
            payment: Payment = await self.service.get_one(id_=data.payment_id, db_session=db_session, lock_mode=RowLockLevel.UPDATE)

            if payment.status == PaymentStatus.SUCCEEDED:
                return

            try:
                await self._process_business_logic(payment)
                await self.service.update(
                    payment.id,
                    payload=PaymentUpdateSchema(status=PaymentStatus.SUCCEEDED, completed_at=datetime.now(timezone.utc)),
                    db_session=db_session,
                )
            except PaymentNonRetryableException:
                await self.service.update(
                    payment.id,
                    payload=PaymentUpdateSchema(status=PaymentStatus.FAILED, completed_at=datetime.now(timezone.utc)),
                    db_session=db_session,
                )
                raise
            webhook_data: PaymentWebhookSchema = PaymentWebhookSchema.model_validate(payment)

        await self._send_webhook(data=webhook_data)
        log.debug(f'Payment {payment.id} processed successfully.')

    async def _process_business_logic(self, payment: Payment):
        await asyncio.sleep(random.uniform(2, 5))
        if random.random() < 0.1:
            log.warning(f'Payment {payment.id} failed during processing.')
            raise PaymentNonRetryableException(f'Simulated failure for payment {payment.id}')

    async def _send_webhook(self, data: PaymentWebhookSchema):
        """Отправляет уведомление о завершении платежа."""
        payload: PaymentWebhookPayload = PaymentWebhookPayload(payment_id=data.id, status=PaymentEventStatus.SUCCEEDED)

        async with self.webhook_client as client:
            try:
                await client.send_notification(data.webhook_url, payload)
            except httpx.HTTPError as exc:
                log.error(f'Webhook delivery permanently failed for {data.id}: {exc}')
                raise PaymentWebhookException() from exc
