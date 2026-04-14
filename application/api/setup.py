from fastapi import APIRouter, FastAPI


def setup_api(application: FastAPI, router: APIRouter, prefix: str = ''):
    """Производит конфигурацию FastAPI-приложения."""

    application.include_router(router, prefix=prefix)
