"""
Сериализаторы для различных типов данных.
"""

import datetime

from typing import Any, Annotated

from pydantic import AwareDatetime, WrapValidator
from pydantic_core.core_schema import ValidatorFunctionWrapHandler, ValidationInfo


def transform_to_utc_datetime(dt: datetime.datetime) -> datetime.datetime:
    """
    Устанавливает таймзону UTC.

    Внимание! Если у значения уже присутствует таймзона, то она будет перезаписана без приведения времени к UTC.
    """
    result: datetime.datetime = dt.replace(tzinfo=datetime.timezone.utc)

    return result


def datetime_with_timezone(value: Any, handler: ValidatorFunctionWrapHandler, info: ValidationInfo) -> int:
    """Валидатор, устанавливающий UTC-таймзону в формат datetime"""
    if isinstance(value, datetime.datetime):
        value = transform_to_utc_datetime(value)

    value = handler(value)

    if isinstance(value, datetime.datetime):
        value = transform_to_utc_datetime(value)

    return value


# Тип данных для схем Pydantic, автоматически устанавливающий UTC-таймзону в значение типа datetime
DateTimeUTC = Annotated[AwareDatetime, WrapValidator(datetime_with_timezone)]
