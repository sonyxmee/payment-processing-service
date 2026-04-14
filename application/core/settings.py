from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


class ApplicationSettings(BaseSettings):
    app_title: str = 'Payment Service'
    app_version: str = '1'

    database_url: PostgresDsn

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
        env_file_encoding='utf-8',
    )


settings: ApplicationSettings = ApplicationSettings()
