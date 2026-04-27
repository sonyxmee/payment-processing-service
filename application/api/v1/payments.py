from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.auth.authentication import authenticate_by_token
from application.core.dependencies import get_db_session
from application.models.payment import Payment
from application.schemas.auth import AuthContext
from application.schemas.payment import PaymentCreateSchema, PaymentResponseSchema
from application.services.dependencies import get_payment_service
from application.services.payment import PaymentService


router = APIRouter()


@router.post(
    path='',
    summary='Создание платежа',
    description=('Создает новый платеж в системе на основе переданных данных.'),
    status_code=status.HTTP_201_CREATED,
    response_model=PaymentResponseSchema,
    response_model_exclude_none=True,
)
async def create_payment(
    payload: PaymentCreateSchema,
    service: Annotated[PaymentService, Depends(get_payment_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session, scope='function')],
    auth: Annotated[AuthContext, Depends(authenticate_by_token)],
) -> PaymentResponseSchema:
    """Создает новый платеж."""
    payment: Payment = await service.create(payload=payload, db_session=db_session)

    return PaymentResponseSchema(result=payment, status_code=status.HTTP_201_CREATED)


@router.get(
    path='/{object_id}',
    summary='Получение платежа по идентификатору',
    description='Возвращает подробную информацию о платеже по его уникальному идентификатору.',
    status_code=status.HTTP_200_OK,
    response_model=PaymentResponseSchema,
    response_model_exclude_none=True,
)
async def get_record_by_id(
    object_id: Annotated[UUID, Path(description='Идентификатор платежа')],
    service: Annotated[PaymentService, Depends(get_payment_service)],
    db_session: Annotated[AsyncSession, Depends(get_db_session, scope='function')],
    auth: Annotated[AuthContext, Depends(authenticate_by_token)],
) -> PaymentResponseSchema:
    """Возвращает платеж по идентификатору."""
    payment: Payment = await service.get_one(
        id_=object_id,
        db_session=db_session,
    )

    return PaymentResponseSchema(result=payment)
