from enum import StrEnum
from typing import Any
from fastapi import status as fastapi_status

from .base import BaseSimpleSchema


class ResponseStatus(StrEnum):
    """Статусы результата выполнения операции в API."""

    OK = 'OK'
    FAIL = 'FAIL'


class BaseResponseSchema(BaseSimpleSchema):
    """Общая схема стандартного ответа API."""

    status: str = ResponseStatus.OK
    status_code: int = fastapi_status.HTTP_200_OK
    message: str | None = None
    result: Any | None = None


class ErrorResponseSchema(BaseSimpleSchema):
    """Схема ответа API с сообщением об ошибке."""

    status: str = ResponseStatus.FAIL
    status_code: int = fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str | None = None
