import asyncio
import random

from typing import Callable

import httpx

from application.core.exceptions import PaymentGatewayException, PaymentWebhookException
from application.models.base import RowLockLevel
from application.schemas.payment import PaymentCreatedDTO, PaymentUpdateSchema
from application.schemas.webhook import PaymentEventStatus, PaymentWebhookPayload
from application.services.payment import PaymentService
from application.models.payment import Payment, PaymentStatus
from application.core.logger import consumer_logger as log
from application.infrastructure.webhook import WebhookClient


class PaymentHandler:
    def __init__(self, service: PaymentService, webhook_client: WebhookClient):
        self.service = service
        self.webhook_client = webhook_client

    async def handle(self, payload: dict, db_session_factory: Callable):
        data: PaymentCreatedDTO = PaymentCreatedDTO(**payload)
        log.info(f'Processing payment {data.payment_id}...')

        async with db_session_factory() as db_session:
            payment: Payment = await self.service.get_one(id_=data.payment_id, db_session=db_session, lock_mode=RowLockLevel.UPDATE)

            if payment.status == PaymentStatus.SUCCEEDED:
                return

            try:
                await self._process_business_logic(payment)
                await self.service.update(payment, status=PaymentUpdateSchema(status=PaymentStatus.SUCCEEDED), db_session=db_session)
            except PaymentGatewayException:
                await self.service.update(payment, status=PaymentUpdateSchema(status=PaymentStatus.FAILED), db_session=db_session)
                raise

        await self._send_webhook(payment.webhook_url, payment.id)
        log.debug(f'Payment {payment.id} processed successfully.')

    async def _process_business_logic(self, payment: Payment):
        await asyncio.sleep(random.uniform(2, 5))
        if random.random() < 0.1:
            log.warning(f'Payment {payment.id} failed during processing.')
            raise PaymentGatewayException(f'Simulated failure for payment {payment.id}')

    async def _send_webhook(self, url: str, payment_id: str):
        """Отправляет уведомление о завершении платежа."""
        payload: PaymentWebhookPayload = PaymentWebhookPayload(payment_id=payment_id, status=PaymentEventStatus.SUCCEEDED)

        async with self.webhook_client as client:
            try:
                await client.send_notification(url, payload)
            except httpx.HTTPError as exc:
                log.error(f'Webhook delivery permanently failed for {payment_id}: {exc}')
                raise PaymentWebhookException() from exc
