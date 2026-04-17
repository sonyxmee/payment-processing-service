import re

from functools import wraps
from dataclasses import dataclass
from typing import Any, Callable, Optional
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound, DBAPIError

from application.core.logger import main_logger as log
from application.models.base import ModelT

from .exceptions import AlreadyExistsException, ObjectNotFoundException, DatabaseException


@dataclass
class ErrorDetail:
    """Контейнер для деталей ошибки."""

    column: str
    value: Any
    message: str


class SQLAlchemyErrorHandler:
    """Класс-стратегия для парсинга ошибок PostgreSQL."""

    @staticmethod
    def parse_unique_violation(error_msg: str) -> Optional[ErrorDetail]:
        """Парсинг ошибки уникальности."""
        pattern = r'Key \((.*?)\)=\((.*?)\) already exists'
        match: re.Match[str] | None = re.search(pattern, error_msg)
        error: ErrorDetail | None = None
        if match:
            error = ErrorDetail(
                column=match.group(1),
                value=match.group(2),
                message='Запись с таким значением уже существует.',
            )
        return error


def handle_db_exceptions(func: Callable) -> Callable:
    """Декоратор для перехвата и интерпретации ошибок БД."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> Any:
        model: ModelT = self.model
        model_name = (getattr(model, '__doc__', None) or model.__name__).split('\n')[0].strip()

        log_context = {
            'table': getattr(model, '__tablename__', 'unknown'),
            'method': func.__name__,
            'model': model.__name__,
        }

        try:
            return await func(self, *args, **kwargs)

        except NoResultFound as exc:
            log.error(
                'Object not found in database',
                extra={**log_context, 'error': str(exc)},
            )
            raise ObjectNotFoundException('Запрашиваемый объект не найден.') from exc

        except MultipleResultsFound as exc:
            log.critical(
                'Multiple results found where one was expected',
                extra={**log_context, 'error': str(exc)},
            )
            raise DatabaseException.from_message('Обнаружено дублирование данных на уровне БД') from exc

        except IntegrityError as exc:
            error_msg = str(exc.orig)

            unique_detail = SQLAlchemyErrorHandler.parse_unique_violation(error_msg)
            if unique_detail:
                log.warning(
                    'Unique constraint violation',
                    extra={
                        **log_context,
                        'column': unique_detail.column,
                        'value': unique_detail.value,
                    },
                )
                detail_str = f'"{model_name}" ({unique_detail.column}={unique_detail.value})'
                raise AlreadyExistsException.from_message(detail_str)

            log.error('Unhandled IntegrityError', extra={**log_context, 'orig_error': error_msg})
            raise DatabaseException.from_message('Ошибка целостности данных')

        except DBAPIError as exc:
            log.error(
                'Database API Error',
                extra={**log_context, 'pgcode': getattr(exc.orig, 'pgcode', None)},
            )
            raise DatabaseException.from_message('Техническая ошибка выполнения запроса') from exc

    return wrapper
