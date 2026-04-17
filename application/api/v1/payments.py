from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.authentication import authenticate_by_token
from application.core.dependencies import get_db_session
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
    db_session: Annotated[AsyncSession, Depends(get_db_session, scope='function')],
) -> ...:
    """Создает Платеж"""
    return {'id': 'uuid', 'status': 'pending'}
