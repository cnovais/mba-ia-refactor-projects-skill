"""Application settings. This is the only module that reads environment variables."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when a required setting is missing or malformed."""


def _env(name):
    value = os.environ.get(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def _env_int(name, default):
    value = _env(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        raise ConfigError(f"{name} must be an integer, got {value!r}")


def _env_bool(name, default):
    value = _env(name)
    if value is None:
        return default
    return value.lower() in ('1', 'true', 'yes', 'on')


def _env_list(name):
    value = _env(name)
    if value is None:
        return ()
    return tuple(item.strip() for item in value.split(',') if item.strip())


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    token_max_age_seconds: int
    cors_origins: tuple
    debug: bool
    host: str
    port: int
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None


def load_settings():
    load_dotenv()

    secret_key = _env('SECRET_KEY')
    if not secret_key:
        raise ConfigError(
            'SECRET_KEY environment variable is required. Generate one with: '
            'python -c "import secrets; print(secrets.token_hex(32))"'
        )

    return Settings(
        secret_key=secret_key,
        database_url=_env('DATABASE_URL') or 'sqlite:///tasks.db',
        token_max_age_seconds=_env_int('TOKEN_MAX_AGE_SECONDS', 8 * 60 * 60),
        cors_origins=_env_list('CORS_ORIGINS'),
        debug=_env_bool('FLASK_DEBUG', False),
        host=_env('HOST') or '127.0.0.1',
        port=_env_int('PORT', 5000),
        smtp_host=_env('SMTP_HOST'),
        smtp_port=_env_int('SMTP_PORT', 587),
        smtp_user=_env('SMTP_USER'),
        smtp_password=_env('SMTP_PASSWORD'),
    )
