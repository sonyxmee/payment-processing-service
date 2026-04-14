from typing import Any
from fastapi import FastAPI

from application.api.setup import setup_api
from application.api.router import root_router
from application.core.settings import settings


params: dict[str, Any] = {'title': settings.app_title, 'version': settings.app_version}
payment_app: FastAPI = FastAPI(**params)
prefix: str = f'/api/v{payment_app.version}'

setup_api(application=payment_app, router=root_router, prefix=prefix)
