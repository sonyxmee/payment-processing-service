from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import AfterValidator, Field


def validate_numeric_10_2(v: Decimal) -> Decimal:
    """Валидирует и нормализует денежную сумму для БД.

    1. Принудительно округляет значение до 2 знаков после запятой (scale=2),
       используя стратегию ROUND_HALF_UP.
    2. Проверяет, что общее количество значащих цифр не превышает 10.
    """

    rounded = v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    if len(rounded.as_tuple().digits) > 10:
        raise ValueError('Сумма превышает допустимый предел точности: макс. 10 знаков всего (включая 2 после запятой).')

    return rounded


PaymentAmount = Annotated[Decimal, AfterValidator(validate_numeric_10_2), Field(gt=0, examples=[99.99])]
