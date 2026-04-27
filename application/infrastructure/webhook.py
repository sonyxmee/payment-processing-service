import httpx

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from application.core.logger import consumer_logger as log
from application.schemas.webhook import PaymentWebhookPayload


class WebhookClient(httpx.AsyncClient):
    """Асинхронный клиент для отправки вебхуков с автоматическими ретраями."""

    def __init__(self, **kwargs):
        if 'timeout' not in kwargs:
            kwargs['timeout'] = httpx.Timeout(5.0)
        super().__init__(**kwargs)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def send_notification(self, url: str, payload: PaymentWebhookPayload) -> None:
        """Отправляет POST-запрос с автоматическим повтором при 5xx и сетевых ошибках."""
        response: httpx.Response = await self.post(url, json=payload)

        if response.is_error:
            if response.is_server_error:
                log.warning(f'Server error {response.status_code} for {url}. Triggering retry...')
            else:
                log.error(f'Client error {response.status_code} for {url}. No retry.')

            response.raise_for_status()

        log.info(f'Webhook delivered to {url} (Status: {response.status_code})')
        return response
