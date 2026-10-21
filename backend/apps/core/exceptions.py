from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    if isinstance(exc, DjangoValidationError):
        return Response(getattr(exc, "message_dict", {"detail": exc.messages}), status=400)
    if isinstance(exc, IntegrityError):
        return Response(
            {"detail": "Yozuv takrorlangan yoki bog‘liqlik cheklovi buzilgan."}, status=409
        )
    response = exception_handler(exc, context)
    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)) and response is not None:
        response.data["code"] = "authentication_required"
    if isinstance(exc, PermissionDenied):
        request = context.get("request")
        if request and request.user.is_authenticated:
            from apps.core.audit import record_audit

            record_audit(
                request,
                action="DENIED",
                entity="Authorization",
                after_state={"path": request.path, "method": request.method},
            )
    return response
