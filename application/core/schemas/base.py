import uuid

from typing import Self, TypeVar
from pydantic import BaseModel, ConfigDict, Field, model_validator

from application.core.exceptions import BadRequestException
from application.core.schemas.serializer import DateTimeUTC

SchemaT = TypeVar('SchemaT', bound=BaseModel)


class BaseSimpleSchema(BaseModel):
    """
    Упрощённая схема для наследования в Pydantic-схеме.

    Производит конфигурацию:
    - Включает ORM-режим
    - Разрешает заполнение поля по псевдониму
    - Допускает наличие непредусмотренных атрибутов (игнорирует их)
    - При сериализации использует значения enum вместо объектов
    """

    model_config: ConfigDict = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',
        use_enum_values=True,
    )


class BaseUpdateSchema(BaseSimpleSchema):
    """
    Базовая схема для наследования в Pydantic-схеме, предназначенная для валидации данных обновления модели.
    Проверяет, что переданные данные содержат хотя бы одно заполненное поле перед выполнением обновления.
    """

    @model_validator(mode='after')
    def check_instance(self) -> Self:
        """Проверяет, что экземпляр имеет заполненные поля"""
        if not self.model_fields_set:
            message: str = 'Невозможно обновить запись: данные для обновления не предоставлены. Необходимо заполнить как минимум одно поле.'
            raise BadRequestException(message)
        return self


class BaseIdMixin:
    """Миксин для идентификатора записи"""

    id: uuid.UUID = Field(..., title='Идентификатор', description='Идентификатор записи')


class TimestampedMixin:
    """Миксин с полями created_at"""

    created_at: DateTimeUTC = Field(..., title='Дата создания', description='Дата и время создания объекта')
