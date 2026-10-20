"""Explicit environment modes. Production fails closed; secrets never appear in repr/errors."""
from typing import Literal
import secrets
from urllib.parse import urlsplit
from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: Literal['development', 'test', 'production'] = 'production'
    DATABASE_URL: str | None = Field(default=None, repr=False)
    SECRET_KEY: SecretStr | None = None
    SESSION_SECRET: SecretStr | None = None
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = ''
    PAGE_SIZE: int = Field(default=50, ge=1, le=1000)
    TIMEZONE: str = 'Asia/Tashkent'
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', hide_input_in_errors=True, extra='ignore')

    @model_validator(mode='after')
    def secure_mode(self):
        origins = self.allowed_origins_list
        for origin in origins:
            parsed = urlsplit(origin)
            if origin == '*' or parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
                raise ValueError('ALLOWED_ORIGINS must contain explicit HTTP(S) origins without credentials or paths')
            if self.ENVIRONMENT == 'production' and parsed.scheme != 'https':
                raise ValueError('Production CORS origins must use HTTPS')
        if self.ENVIRONMENT == 'production':
            if not self.DATABASE_URL:
                raise ValueError('Production requires DATABASE_URL')
            if self.DEBUG:
                raise ValueError('DEBUG must be disabled in production')
            for name in ('SECRET_KEY', 'SESSION_SECRET'):
                secret = getattr(self, name)
                value = secret.get_secret_value() if secret else ''
                if len(value) < 32 or len(set(value)) < 12 or any(word in value.lower() for word in ('secret', 'changeme', 'change-me', 'example', 'placeholder', 'development', 'bcms-')):
                    raise ValueError(f'Production requires a strong independently generated {name}')
            if self.SECRET_KEY == self.SESSION_SECRET:
                raise ValueError('Production requires distinct secrets')
        else:
            self.DATABASE_URL = self.DATABASE_URL or ('sqlite:///:memory:' if self.ENVIRONMENT == 'test' else 'sqlite:///./bcms_dev.db')
            self.SECRET_KEY = self.SECRET_KEY if self.SECRET_KEY and self.SECRET_KEY.get_secret_value() else SecretStr(secrets.token_urlsafe(48))
            self.SESSION_SECRET = self.SESSION_SECRET if self.SESSION_SECRET and self.SESSION_SECRET.get_secret_value() else SecretStr(secrets.token_urlsafe(48))
        from sqlalchemy.engine import make_url
        try:
            url = make_url(self.DATABASE_URL)
            if url.get_backend_name() not in ('postgresql', 'sqlite'):
                raise ValueError
            if self.ENVIRONMENT == 'production' and url.password and any(x in url.password.lower() for x in ('bcms_secret', 'changeme', 'placeholder')):
                raise ValueError
        except Exception:
            raise ValueError('DATABASE_URL must be a valid supported URL without known development credentials') from None
        return self

    @property
    def allowed_origins_list(self) -> list[str]:
        return list(dict.fromkeys(o.strip().rstrip('/') for o in self.ALLOWED_ORIGINS.split(',') if o.strip()))


settings = Settings()
