from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from rest_framework import permissions, serializers, status, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response

from apps.authentication.models import User
from apps.authentication.throttling import LoginThrottle
from apps.authentication.serializers import (
    LoginSerializer,
    UserCreateUpdateSerializer,
    UserSerializer,
)
from apps.core.api import DomainPermission, TenantViewSet
from apps.core.audit import record_audit


@method_decorator(never_cache, name="dispatch")
class LoginView(views.APIView):
    """
    FR-01: Kirish (Login).
    Parolni tekshiradi, sessiya ochadi va audit jurnaliga yozadi.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "login"
    throttle_classes = [LoginThrottle]

    def post(self, request):
        # DRF's session authentication only checks CSRF for authenticated users.
        # Login must also validate it before creating an anonymous user's session.
        SessionAuthentication().enforce_csrf(request)
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            record_audit(
                request=request,
                action="LOGIN_FAILED",
                entity="Session",
                after_state={"reason": "invalid_credentials"},
            )
            raise serializers.ValidationError(serializer.errors)
        user = serializer.validated_data["user"]
        login(request, user)

        # Audit yozish
        record_audit(
            request=request,
            action="LOGIN",
            entity="User",
            entity_id=user.id,
            actor=user,
            organization=user.organization,
            after_state={"username": user.username, "role": user.role},
        )

        user_data = UserSerializer(user).data
        return Response(
            {
                "message": "Muvaffaqiyatli kirildi.",
                "user": user_data,
                "csrfToken": get_token(request),
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(never_cache, name="dispatch")
class LogoutView(views.APIView):
    """
    FR-01: Tizimdan chiqish (Logout).
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        record_audit(
            request=request,
            action="LOGOUT",
            entity="User",
            entity_id=user.id,
            actor=user,
            organization=user.organization,
        )
        logout(request)
        return Response(
            {
                "message": "Tizimdan muvaffaqiyatli chiqildi.",
                "csrfToken": get_token(request),
            },
            status=status.HTTP_200_OK,
        )


@method_decorator(never_cache, name="dispatch")
class MeView(views.APIView):
    """
    Joriy foydalanuvchi profilini va rollarini qaytaradi.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class UserViewSet(TenantViewSet):
    """
    FR-01 va FR-02: Tashkilot doirasida foydalanuvchilarni boshqarish.
    Faqat Administrator foydalanuvchi qo'sha/o'zgartira oladi.
    Auditor faqat ko'ra oladi.
    """

    permission_classes = [DomainPermission]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return UserCreateUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(organization=user.organization)

    def perform_create(self, serializer):
        user = serializer.save(organization=self.request.user.organization)
        record_audit(
            request=self.request,
            action="CREATE",
            entity="User",
            entity_id=user.id,
            after_state=UserSerializer(user).data,
        )

    def perform_update(self, serializer):
        before_state = UserSerializer(serializer.instance).data
        user = serializer.save()
        record_audit(
            request=self.request,
            action="UPDATE",
            entity="User",
            entity_id=user.id,
            before_state=before_state,
            after_state=UserSerializer(user).data,
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserCreateUpdateSerializer(
            user, data={"is_active": False}, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(status=204)


@method_decorator(never_cache, name="dispatch")
class CSRFTokenView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(never_cache, name="dispatch")
class PasswordChangeView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        old = request.data.get("old_password")
        new = request.data.get("new_password")
        if not isinstance(old, str) or not request.user.check_password(old):
            raise serializers.ValidationError({"old_password": "Joriy parol noto‘g‘ri."})
        if not isinstance(new, str):
            raise serializers.ValidationError({"new_password": "Yangi parolni kiriting."})
        try:
            validate_password(new, request.user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": exc.messages})
        request.user.set_password(new)
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        record_audit(
            request,
            action="UPDATE",
            entity="User",
            entity_id=request.user.pk,
            after_state={"password_changed": True},
        )
        return Response({"message": "Parol yangilandi.", "csrfToken": get_token(request)})
