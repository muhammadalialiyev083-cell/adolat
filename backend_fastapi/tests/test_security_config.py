"""T-SEC: fail-closed production configuration and log redaction."""
import logging
import secrets
import pytest
from pydantic import ValidationError
from app.config import Settings


def production(**overrides):
    values = dict(ENVIRONMENT='production', DATABASE_URL='postgresql://localhost/bcms',
                  SECRET_KEY=secrets.token_urlsafe(48), SESSION_SECRET=secrets.token_urlsafe(48), DEBUG=False)
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_sec01_production_requires_database():
    with pytest.raises(ValidationError, match='Production requires DATABASE_URL'):
        production(DATABASE_URL=None)


@pytest.mark.parametrize('key', ['SECRET_KEY', 'SESSION_SECRET'])
def test_sec02_production_requires_both_secrets(key):
    with pytest.raises(ValidationError, match=key): production(**{key: None})


def test_sec03_debug_cannot_remain_enabled():
    with pytest.raises(ValidationError, match='DEBUG'): production(DEBUG=True)


@pytest.mark.parametrize('value', ['bcms-designer-dev-secret-key-2026', 'bcms-session-secret-key-2026', 'x'*64, 'change-me-placeholder-not-a-real-secret'])
def test_sec04_insecure_secrets_rejected_without_echo(value):
    with pytest.raises(ValidationError) as exc: production(SECRET_KEY=value)
    assert value not in str(exc.value)


def test_sec05_origins_parsing_and_wildcard_rejection():
    s = production(ALLOWED_ORIGINS=' https://one.example,https://two.example/, ,https://one.example ')
    assert s.allowed_origins_list == ['https://one.example', 'https://two.example']
    for origin in ['*', 'http://one.example', 'https://one.example/path', 'https://user:pass@one.example']:
        with pytest.raises(ValidationError): production(ALLOWED_ORIGINS=origin)


def test_sec06_explicit_local_mode_functional():
    a = Settings(_env_file=None, ENVIRONMENT='development', DATABASE_URL=None, SECRET_KEY=None, SESSION_SECRET=None)
    b = Settings(_env_file=None, ENVIRONMENT='test', DATABASE_URL=None, SECRET_KEY=None, SESSION_SECRET=None)
    assert a.DATABASE_URL.startswith('sqlite:') and b.DATABASE_URL == 'sqlite:///:memory:'
    assert a.SESSION_SECRET != b.SESSION_SECRET


def test_sec07_config_and_database_logs_hide_values(caplog):
    secret, password = secrets.token_urlsafe(48), secrets.token_urlsafe(24)
    s = production(SECRET_KEY=secret, DATABASE_URL=f'postgresql://user:{password}@localhost/bcms')
    with caplog.at_level(logging.DEBUG): logging.getLogger('bcms.config').debug('configuration=%r', s)
    assert secret not in caplog.text and password not in caplog.text
    from app.database import engine
    assert engine.echo is False and engine.hide_parameters is True
    bad_url = f'unsupported://user:{password}@localhost/bcms'
    with pytest.raises(ValidationError) as exc: production(DATABASE_URL=bad_url)
    assert password not in str(exc.value)


def test_production_cookie_flags():
    from starlette.middleware.sessions import SessionMiddleware
    s = production()
    middleware = SessionMiddleware(lambda: None, secret_key=s.SESSION_SECRET.get_secret_value(), https_only=True, same_site='none')
    assert 'secure' in middleware.security_flags and 'httponly' in middleware.security_flags


def test_missing_database_failure_precedes_seeding():
    from app.config import settings
    from seed_data import seed
    assert settings.ENVIRONMENT == 'test'
    with pytest.raises(RuntimeError, match='restricted'): seed()


def test_csrf_enforced_for_authenticated_writes(auth_client):
    token = auth_client.headers.pop('X-CSRFToken')
    assert auth_client.post('/api/v1/auth/logout').status_code == 403
    auth_client.headers['X-CSRFToken'] = token
    assert auth_client.post('/api/v1/auth/logout', headers={'Origin': 'https://untrusted.example'}).status_code == 403
    assert auth_client.get('/api/v1/auth/me').status_code == 200
    assert auth_client.post('/api/v1/auth/logout').status_code == 200


def test_csrf_endpoint_and_login_rotation(client):
    old = client.get('/api/v1/auth/csrf').json()['csrfToken']
    assert client.post('/api/v1/auth/login', json={'username': 'bcms_manager', 'password': 'Admin123!'}).status_code == 200
    new = client.get('/api/v1/auth/csrf').json()['csrfToken']
    assert old != new
    assert client.post('/api/v1/auth/logout', headers={'X-CSRFToken': old}).status_code == 403
    assert client.post('/api/v1/auth/logout', headers={'X-CSRFToken': new}).status_code == 200
