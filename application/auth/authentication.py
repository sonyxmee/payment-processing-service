from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Security
from fastapi.security import APIKeyHeader

from application.core.exceptions import InternalException, UnauthorizedException
from application.core.config import settings
from application.schemas.auth import AuthContext

from .security import verify_hash


api_key_header = APIKeyHeader(
    name='X-API-Key',
    scheme_name='API Key Authentication',
    auto_error=True,
)


def verify_api_token(hashed_token: str, plain_token: str) -> None:
    """Верифицирует API токен."""
    try:
        verify_hash(hashed_token=hashed_token, plain_token=plain_token)
    except VerifyMismatchError:
        raise UnauthorizedException('Некорректный API токен')
    except InvalidHashError as exception:
        user_message = 'Не удалось проверить доступ к ресурсу из-за неверных настроек приложения.'
        raise InternalException(user_message) from exception
    except Exception as exception:
        user_message = 'Произошла непредвиденная ошибка при проверке токена. Попробуйте повторить запрос чуть позже.'
        raise InternalException(user_message) from exception


async def authenticate_by_token(api_key: str = Security(api_key_header)) -> str:
    """Аутентификация через токен"""

    verify_api_token(
        hashed_token=settings.api_key_hash.get_secret_value(),
        plain_token=api_key,
    )

    return AuthContext()
