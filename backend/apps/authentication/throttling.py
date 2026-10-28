import time
from datetime import datetime, timezone

from django.db import DatabaseError
from django.db.models import F
from django.utils.crypto import salted_hmac
from rest_framework.exceptions import APIException
from rest_framework.throttling import BaseThrottle

from apps.authentication.models import LoginRateBucket


class AuthenticationUnavailable(APIException):
    status_code = 503
    default_detail = "Kirish xizmati vaqtincha mavjud emas. Keyinroq qayta urinib ko‘ring."
    default_code = "authentication_unavailable"


class LoginThrottle(BaseThrottle):
    """PostgreSQL/SQLite conditional UPDATE is atomic across all workers.

    Ten attempts per fixed minute per peer. The ingress must set REMOTE_ADDR
    from a trusted upstream; arbitrary browser X-Forwarded-For is ignored.
    """

    def allow_request(self, request, view):
        now = time.time()
        window = int(now // 60)
        self.remaining = (window + 1) * 60 - now
        peer = request.META.get("REMOTE_ADDR", "unknown")
        digest = salted_hmac("login-limit", peer).hexdigest()
        key = f"{window}:{digest}"
        try:
            LoginRateBucket.objects.get_or_create(
                key=key,
                defaults={"expires_at": datetime.fromtimestamp((window + 1) * 60, timezone.utc)},
            )
            return bool(
                LoginRateBucket.objects.filter(pk=key, attempts__lt=10).update(
                    attempts=F("attempts") + 1
                )
            )
        except DatabaseError:
            raise AuthenticationUnavailable() from None

    def wait(self):
        return self.remaining
