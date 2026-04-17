import re

from functools import wraps
from dataclasses import dataclass
from typing import Any, Callable, Optional
from sqlalchemy.exc import IntegrityError, MultipleResultsFound, NoResultFound, DBAPIError

from application.core.logger import main_logger as log

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

    @staticmethod
    def parse_value_too_long(error_msg: str) -> Optional[ErrorDetail]:
        """Парсинг ошибки превышения длины поля (DataError)."""
        pattern = r'value too long for type (.*?)\((\d+)\)'
        match = re.search(pattern, error_msg)
        error: ErrorDetail | None = None
        if match:
            error = ErrorDetail(
                column='данные',
                value=f'max {match.group(2)}',
                message='Передано слишком длинное значение.',
            )
        return error

    @staticmethod
    def parse_check_violation(error_msg: str) -> Optional[ErrorDetail]:
        """Парсинг нарушения ограничений CHECK."""
        pattern = r'violates check constraint "(.*?)"'
        match = re.search(pattern, error_msg)
        error: ErrorDetail | None = None
        if match:
            error = ErrorDetail(
                column=match.group(1),
                value='constraint',
                message='Нарушено бизнес-ограничение данных.',
            )
        return error


class DBExceptionHandler:
    """Класс для централизованной обработки исключений БД."""

    def __init__(self, model: Any, func_name: str, model_name: str):
        """Инициализирует контекст обработчика."""

        self.model = model
        self.log_context = {
            'table': getattr(model, '__tablename__', 'unknown'),
            'method': func_name,
            'model': model.__name__,
        }
        self.model_name = model_name

    async def handle(self, exc: Exception) -> None:
        """Маршрутизирует исключение соответствующему специализированному обработчику."""

        handlers: dict[type[Exception], Callable] = {
            NoResultFound: self._handle_not_found,
            MultipleResultsFound: self._handle_multiple_results,
            IntegrityError: self._handle_integrity_error,
            DBAPIError: self._handle_dbapi_error,
        }

        handler = handlers.get(type(exc))
        if handler:
            await handler(exc)

        if isinstance(exc, IntegrityError):
            await self._handle_integrity_error(exc)
        elif isinstance(exc, DBAPIError):
            await self._handle_dbapi_error(exc)

        raise exc

    async def _handle_not_found(self, exc: NoResultFound):
        """Обрабатывает ошибки отсутствия записи."""

        log.error('Object not found in database', extra={**self.log_context, 'error': str(exc)})
        raise ObjectNotFoundException('Запрашиваемый объект не найден.') from exc

    async def _handle_multiple_results(self, exc: MultipleResultsFound):
        """Обрабатывает ошибки целостности, когда найдено более одной записи."""

        log.critical('Multiple results found', extra={**self.log_context, 'error': str(exc)})
        raise DatabaseException.from_message('Обнаружено дублирование данных на уровне БД') from exc

    async def _handle_integrity_error(self, exc: IntegrityError):
        """Обрабатывает нарушения целостности данных: Unique и Check constraints."""

        error_msg: str = str(exc.orig)

        unique: ErrorDetail | None = SQLAlchemyErrorHandler.parse_unique_violation(error_msg)
        if unique:
            log.warning('Unique violation', extra={**self.log_context, 'column': unique.column})
            raise AlreadyExistsException.from_message(f'"{self.model_name}" ({unique.column}={unique.value})')

        check: ErrorDetail | None = SQLAlchemyErrorHandler.parse_check_violation(error_msg)
        if check:
            raise DatabaseException.from_message(f'"{self.model_name}" ({check.column}={check.value})')

        log.error('Unhandled IntegrityError', extra={**self.log_context, 'orig_error': error_msg})
        raise DatabaseException.from_message('Ошибка целостности данных')

    async def _handle_dbapi_error(self, exc: DBAPIError):
        """Обрабатывает низкоуровневые ошибки драйвера БД."""

        error_msg: str = str(exc.orig)
        error: ErrorDetail | None = SQLAlchemyErrorHandler.parse_value_too_long(error_msg)
        if error:
            raise DatabaseException.from_message(f'"{self.model_name}": {error.message}')

        log.error('Database API Error', extra={**self.log_context, 'orig_error': error_msg, 'pgcode': getattr(exc.orig, 'pgcode', None)})
        raise DatabaseException.from_message('Техническая ошибка выполнения запроса') from exc


def handle_db_exceptions(func: Callable) -> Callable:
    """Декоратор для перехвата и интерпретации ошибок БД."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs) -> Any:
        try:
            return await func(self, *args, **kwargs)
        except (NoResultFound, MultipleResultsFound, IntegrityError, DBAPIError) as exc:
            model_name: str = (getattr(self.model, '__doc__', None) or self.model.__name__).split('\n')[0].strip()
            handler: DBExceptionHandler = DBExceptionHandler(self.model, func.__name__, model_name)
            await handler.handle(exc)
        except Exception:
            raise

    return wrapper
