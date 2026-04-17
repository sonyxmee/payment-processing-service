class CoreException(Exception):
    """Базовое исключение приложения"""

    status: str = 'FAIL'
    status_code: int = 500
    message: str | None = None
    debug_info: str | None = None

    def __init__(
        self,
        message: str | None = None,
        status_code: int | None = None,
        status: str | None = None,
        debug_info: str | None = None,
    ):
        self.message = message if message is not None else self.message
        self.status_code = status_code if status_code is not None else self.status_code
        self.status = status if status is not None else self.status
        self.debug_info = debug_info if debug_info is not None else self.debug_info

    def __str__(self):
        """Строковое представление исключения с сообщением"""
        return self.message or self.__class__.__name__


class InternalException(CoreException):
    """Внутренняя ошибка сервера"""

    message = 'Произошла внутренняя ошибка сервера'


class UnauthorizedException(CoreException):
    """Исключение, возникающее при ошибке аутентификации"""

    status_code = 401
    message = 'Некорректные данные аутентификации'


class ObjectNotFoundException(CoreException):
    """Исключение, возникающее при отсутствии объекта"""

    status_code = 404
    message = 'Объект с указанным ID не найден'


class DatabaseException(CoreException):
    """Исключение, возникающее при нарушении ограничений в SQLAlchemy"""

    status_code = 400
    message = 'Ошибка взаимодействия с данными'

    @classmethod
    def from_message(cls, message: str):
        """Расширяет сообщение об ошибке"""
        return cls(message=f'{cls.message}: {message}')


class AlreadyExistsException(DatabaseException):
    """409 Conflict: Для нарушений уникальности."""

    status_code = 409
    message = 'Объект с такими данными уже существует'
