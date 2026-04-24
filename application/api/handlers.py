from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Any

from application.core.exceptions import CoreException
from application.core.logger import main_logger as log
from application.core.schemas.api import ErrorResponseSchema


async def request_exception_handler(request: Request, exception: Exception) -> JSONResponse:
    """Глобальный обработчик для непредвиденных исключений (500)."""
    log.exception(f'Handling {exception.__class__.__name__}: {exception!r}')
    return make_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message='Произошла внутренняя ошибка сервера.',
    )


async def core_exception_handler(_request: Request, exception: CoreException):
    """Обработчик исключений приложения."""
    log.error(f'CoreException: {exception.message}')
    return make_error_response(
        status_code=exception.status_code,
        status=exception.status,
        message=exception.message,
        result=exception.result,
    )


async def not_found_exception_handler(request: Request, exception: HTTPException) -> JSONResponse:
    """Обработчик ошибок 404 (Not Found)."""
    return make_error_response(
        status_code=status.HTTP_404_NOT_FOUND,
        status='Not found',
        message='Ресурс не найден',
    )


async def request_validation_error_handler(request: Request, exception: RequestValidationError) -> JSONResponse:
    """Обработчик ошибок валидации данных Pydantic (400)."""
    formatted_msg = format_validation_errors(exception.errors())

    return make_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        status='Validation Error',
        message=f'Ошибка валидации данных: {formatted_msg}',
    )


def make_error_response(status_code: int, message: str, status: str = 'error', result: Any = None) -> JSONResponse:
    """Создает стандартный JSON-ответ с описанием ошибки."""
    content = ErrorResponseSchema(
        status=status,
        status_code=status_code,
        message=message,
        result=result,
    ).model_dump()
    return JSONResponse(content=content, status_code=status_code)


def format_validation_errors(errors: list[dict[str, Any]]) -> str:
    """Преобразует список ошибок Pydantic в читаемую строку."""
    formatted = []
    for error in errors:
        location = ' -> '.join([str(l) for l in error['loc'] if l not in ('body', 'query', 'path')])
        message = error['msg']
        formatted.append(f'{location}: {message}')

    return '; '.join(formatted)
