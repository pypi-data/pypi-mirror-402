from enum import Enum

from pydantic import AnyUrl
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'


class CommonSettings(BaseSettings):
    debug: bool = False
    environment: Environment = Environment.DEVELOPMENT
    sentry_dsn: AnyUrl | None = None

    class Config:
        use_enum_values = True
