from typing import ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AmqpDsn, PostgresDsn, SecretStr


def get_basic_settings_config(env_prefix: str | None = None) -> SettingsConfigDict:
    """Создаёт базовый набор настроек для схемы BaseSettings из pydantic_settings"""
    params: dict = {
        'extra': 'ignore',
        'env_file': '.env',
        'env_file_encoding': 'utf-8',
        'env_nested_delimiter': '__',
    }

    if env_prefix is not None:
        params['env_prefix'] = env_prefix

    return SettingsConfigDict(**params)


class DatabaseSettings(BaseSettings):
    """Настройки подключения к базе данных"""

    dsn: PostgresDsn
    alembic_dsn: PostgresDsn

    pool_size: int = 5  # кол-во соединений, которые должны оставаться открытыми внутри пула подключений
    max_overflow: int = 10  # соединения, которые могут быть открыты сверх pool_size настроек
    pool_recycle: int = 3600  # время жизни соединения в пуле (сек)
    pool_timeout: int = 30  # таймаут получения соединения из пула (сек)

    model_config: ClassVar[SettingsConfigDict] = get_basic_settings_config(env_prefix='DATABASE')


class ApplicationSettings(BaseSettings):
    """Настройки приложения"""

    app_title: str = 'Payment Service'
    app_version: str = '1'

    database: DatabaseSettings
    api_key_hash: SecretStr
    rabbitmq_url: AmqpDsn

    # CORS settings
    cors_origins: set[str] = set()  # список URL, которым разрешен доступ к API
    cors_allow_credentials: bool = False  # разрешить передачу кук и заголовков авторизации (Authorization headers)
    cors_allow_methods: set[str] = {'GET'}  # HTTP-методы, разрешенные для запросов (GET, POST, PUT, DELETE и т.д.)
    cors_allow_headers: set[str] = set()  # список заголовков, которые разрешено передавать в запросе
    cors_max_age: int = 600  # время кэширования preflight-запроса (OPTIONS) браузером в секундах (600 = 10 минут)

    model_config: ClassVar[SettingsConfigDict] = get_basic_settings_config()


settings: ApplicationSettings = ApplicationSettings()
