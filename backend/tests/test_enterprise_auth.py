from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.db import DatabaseError
from django.test import RequestFactory
from rest_framework.test import APIClient

from apps.authentication.models import LoginRateBucket
from apps.authentication.throttling import LoginThrottle
from apps.core.audit import get_client_ip

pytestmark = pytest.mark.django_db


def test_limit_is_shared_and_ignores_forged_forwarding():
    with patch("apps.authentication.throttling.time.time", return_value=6000):
        for i in range(10):
            response = APIClient().post(
                "/api/v1/auth/login",
                {"username": "unknown", "password": "invalid"},
                format="json",
                HTTP_X_FORWARDED_FOR=f"192.0.2.{i}",
            )
            assert response.status_code == 400
            cache.clear()
        response = APIClient().post("/api/v1/auth/login", {}, format="json")
        assert response.status_code == 429
        assert response["Retry-After"] == "60"
        bucket = LoginRateBucket.objects.get()
        assert bucket.attempts == 10
        assert "127.0.0.1" not in bucket.key
    with patch("apps.authentication.throttling.time.time", return_value=6061):
        assert LoginThrottle().allow_request(RequestFactory().get("/"), None)


def test_counter_failure_fails_closed():
    with patch(
        "apps.authentication.throttling.LoginRateBucket.objects.get_or_create",
        side_effect=DatabaseError("private database details"),
    ):
        response = APIClient().post("/api/v1/auth/login", {}, format="json")
    assert response.status_code == 503
    assert "private database" not in str(response.data)


def test_audit_peer_cannot_be_spoofed():
    request = RequestFactory().get(
        "/", REMOTE_ADDR="192.0.2.4", HTTP_X_FORWARDED_FOR="198.51.100.2"
    )
    assert get_client_ip(request) == "192.0.2.4"


def test_production_logging_and_audit_redact_secrets():
    import json
    import logging
    import os
    import secrets
    import subprocess
    import sys
    from pathlib import Path
    from apps.core.logging import SecurityJSONFormatter
    from apps.core.audit import record_audit

    record = logging.LogRecord(
        "django.request",
        logging.ERROR,
        __file__,
        1,
        "password=do-not-log code=private-code",
        (),
        None,
    )
    payload = json.loads(SecurityJSONFormatter().format(record))
    assert "do-not-log" not in str(payload) and "private-code" not in str(payload)
    audit = record_audit(
        after_state={
            "authorization": "Bearer private",
            "nested": {
                "password": "private",
                "client_secret": "private",
                "cookie": "private",
                "safe": "retained",
            },
        }
    )
    assert audit.after_state == {"nested": {"safe": "retained"}}
    environment = dict(
        os.environ,
        DEBUG="false",
        SECRET_KEY=secrets.token_urlsafe(48),
        DATABASE_URL="postgresql://unused@localhost/settings_check_only",
        CSRF_TRUSTED_ORIGINS="https://pilot.example",
        CORS_ALLOWED_ORIGINS="https://pilot.example",
        DJANGO_SETTINGS_MODULE="bcms_backend.settings",
    )
    for hosts, valid in [
        ("pilot.example", True),
        ("*.example", False),
        (".example", False),
        (",", False),
    ]:
        result = subprocess.run(
            [sys.executable, "-c", "import django; django.setup()"],
            env=dict(environment, ALLOWED_HOSTS=hosts),
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
        )
        assert (result.returncode == 0) is valid


@pytest.mark.django_db(transaction=True)
def test_postgres_concurrent_workers_share_one_limit():
    from concurrent.futures import ThreadPoolExecutor
    from django.db import close_old_connections, connection

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row concurrency test")

    def attempt(_):
        close_old_connections()
        try:
            return LoginThrottle().allow_request(
                RequestFactory().post("/", REMOTE_ADDR="192.0.2.88"), None
            )
        finally:
            close_old_connections()

    with (
        patch("apps.authentication.throttling.time.time", return_value=12000),
        ThreadPoolExecutor(max_workers=8) as executor,
    ):
        outcomes = list(executor.map(attempt, range(20)))
    assert sum(outcomes) == 10
    assert LoginRateBucket.objects.get().attempts == 10
