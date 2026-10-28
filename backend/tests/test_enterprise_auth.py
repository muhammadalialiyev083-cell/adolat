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
    with patch('apps.authentication.throttling.time.time', return_value=6000):
        for i in range(10):
            response = APIClient().post('/api/v1/auth/login', {'username': 'unknown', 'password': 'invalid'}, format='json', HTTP_X_FORWARDED_FOR=f'192.0.2.{i}')
            assert response.status_code == 400
            cache.clear()
        response = APIClient().post('/api/v1/auth/login', {}, format='json')
        assert response.status_code == 429
        assert response['Retry-After'] == '60'
        bucket = LoginRateBucket.objects.get()
        assert bucket.attempts == 10
        assert '127.0.0.1' not in bucket.key
    with patch('apps.authentication.throttling.time.time', return_value=6061):
        assert LoginThrottle().allow_request(RequestFactory().get('/'), None)


def test_counter_failure_fails_closed():
    with patch('apps.authentication.throttling.LoginRateBucket.objects.get_or_create', side_effect=DatabaseError('private database details')):
        response = APIClient().post('/api/v1/auth/login', {}, format='json')
    assert response.status_code == 503
    assert 'private database' not in str(response.data)


def test_audit_peer_cannot_be_spoofed():
    request = RequestFactory().get('/', REMOTE_ADDR='192.0.2.4', HTTP_X_FORWARDED_FOR='198.51.100.2')
    assert get_client_ip(request) == '192.0.2.4'
