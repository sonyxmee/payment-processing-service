from typing import Annotated
from fastapi import APIRouter, Depends, status

from application.auth.authentication import authenticate_by_token
from application.schemas.auth import AuthContext


router = APIRouter()


@router.post(
    path='',
    summary='Создание нового платежа',
    description='Создание нового платежа',
    status_code=status.HTTP_201_CREATED,
    response_model=...,
    response_model_exclude_none=True,
)
async def create_payment(
    auth: Annotated[AuthContext, Depends(authenticate_by_token)],
) -> ...:
    """Создает Платеж"""
    return {'id': 'uuid', 'status': 'pending'}
