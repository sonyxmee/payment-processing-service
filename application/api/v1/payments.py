from typing import Annotated
from fastapi import APIRouter, Depends, Path, status, Query


router = APIRouter()


@router.post('/', status_code=status.HTTP_201_CREATED, summary='Создание нового платежа')
async def create_payment():
    return {'id': 'uuid', 'status': 'pending'}