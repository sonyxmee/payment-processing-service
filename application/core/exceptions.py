from http import HTTPStatus


class CoreException(Exception):
    """Базовое исключение приложения"""

    status: str = 'FAIL'
    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
    message: str | None = None
    result: str | None = None

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        status: str | None = None,
        result: str | None = None,
    ):
        self.message = message if message is not None else self.message
        self.status_code = status_code if status_code is not None else self.status_code
        self.status = status if status is not None else self.status
        self.result = result if result is not None else self.result

    def __str__(self):
        """Строковое представление исключения с сообщением"""
        return self.message or self.__class__.__name__


class InternalException(CoreException):
    """Внутренняя ошибка сервера"""

    message = 'Произошла внутренняя ошибка сервера'


class UnauthorizedException(CoreException):
    """Исключение, возникающее при ошибке аутентификации"""

    status_code = HTTPStatus.UNAUTHORIZED
    message = 'Некорректные данные аутентификации'


class ObjectNotFoundException(CoreException):
    """Исключение, возникающее при отсутствии объекта"""

    status_code = HTTPStatus.NOT_FOUND
    message = 'Объект с указанным ID не найден'


class BadRequestException(CoreException):
    """Исключение, возникающее при передаче недопустимых данных"""

    status_code = HTTPStatus.BAD_REQUEST
    message = 'Переданы некорректные данные'


class DatabaseException(CoreException):
    """Исключение, возникающее при нарушении ограничений в SQLAlchemy"""

    status_code = HTTPStatus.BAD_REQUEST
    message = 'Ошибка взаимодействия с данными'

    @classmethod
    def from_message(cls, message: str):
        """Расширяет сообщение об ошибке"""
        return cls(message=f'{cls.message}: {message}')


class AlreadyExistsException(DatabaseException):
    """409 Conflict: Для нарушений уникальности."""

    status_code = HTTPStatus.CONFLICT
    message = 'Объект с такими данными уже существует'


class ConflictException(DatabaseException):
    """Исключение, возникающее при конфликте доступа к данным (например, блокировка строки)."""

    status_code = HTTPStatus.CONFLICT
    message = 'Ресурс в данный момент заблокирован или изменен'


class PaymentGatewayException(CoreException):
    """Ошибка при взаимодействии с платежным шлюзом."""

    status_code = HTTPStatus.FAILED_DEPENDENCY
    message = 'Ошибка взаимодействия с платежным шлюзом'


class PaymentWebhookException(CoreException):
    """Исключение при сбое вебхука."""

    status_code = HTTPStatus.FAILED_DEPENDENCY
    message = 'Ошибка при отправке вебхука'
