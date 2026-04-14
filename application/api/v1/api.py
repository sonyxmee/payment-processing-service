from fastapi import APIRouter
from . import payments

api_router = APIRouter()
api_router.include_router(payments.router, prefix='/payments', tags=['Payments'])
