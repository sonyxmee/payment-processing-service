from typing import Callable

from fastapi import APIRouter, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from application.api.handlers import (
    core_exception_handler,
    not_found_exception_handler,
    request_exception_handler,
    request_validation_error_handler,
)
from application.core.exceptions import CoreException
from application.core.logger import main_logger as log
from application.core.config import ApplicationSettings, settings


def setup_api(application: FastAPI, router: APIRouter, prefix: str = ''):
    """Производит конфигурацию FastAPI-приложения."""

    application.include_router(router, prefix=prefix)

    exception_handlers: list[tuple[int | type[Exception], Callable]] = [
        (RequestValidationError, request_validation_error_handler),
        (status.HTTP_404_NOT_FOUND, not_found_exception_handler),
        (Exception, request_exception_handler),
        (CoreException, core_exception_handler),
    ]
    _add_exception_handlers(application=application, handlers=exception_handlers)
    _add_cors_middleware(application=application, settings_instance=settings)


def _add_exception_handlers(application: FastAPI, handlers: list[tuple[int | type[Exception], Callable]]):
    """Регистрирует список обработчиков исключений в приложении FastAPI."""

    log.info('\tДобавляются обработчики исключений:')
    for exc_class_or_status_code, func in handlers:
        log.info(f'\t\t{exc_class_or_status_code=} -> {func=}')
        application.add_exception_handler(exc_class_or_status_code, func)


def _add_cors_middleware(application: FastAPI, settings_instance: ApplicationSettings):
    """Настройка CORS для безопасного взаимодействия с фронтендом."""

    log.info('\tДобавляется CORSMiddleware...')
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings_instance.cors_origins,
        allow_credentials=settings_instance.cors_allow_credentials,
        allow_methods=settings_instance.cors_allow_methods,
        allow_headers=settings_instance.cors_allow_headers,
        max_age=settings_instance.cors_max_age,
    )
