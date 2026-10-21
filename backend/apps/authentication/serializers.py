from django.contrib.auth import authenticate
from rest_framework import serializers

from apps.authentication.models import User
from apps.core.api import TenantSerializer
from apps.organizations.models import Department, Organization


class OrganizationSummarySerializer(TenantSerializer):
    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "sector",
            "timezone",
            "max_acceptable_loss",
            "risk_low_threshold",
            "risk_medium_threshold",
        ]


class DepartmentSummarySerializer(TenantSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "head_name"]


class UserSerializer(TenantSerializer):
    organization_detail = OrganizationSummarySerializer(source="organization", read_only=True)
    department_detail = DepartmentSummarySerializer(source="department", read_only=True)
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "organization",
            "organization_detail",
            "department",
            "department_detail",
            "phone",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]


class UserCreateUpdateSerializer(TenantSerializer):
    password = serializers.CharField(write_only=True, required=False, trim_whitespace=False)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "role",
            "department",
            "phone",
            "is_active",
        ]

    def validate(self, attrs):
        if (
            self.instance
            and self.instance.role == "ADMIN"
            and (
                attrs.get("role", self.instance.role) != "ADMIN"
                or not attrs.get("is_active", self.instance.is_active)
            )
        ):
            if (
                not User.objects.filter(
                    organization=self.instance.organization, role="ADMIN", is_active=True
                )
                .exclude(pk=self.instance.pk)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"role": "Tashkilotning oxirgi faol administratorini cheklash mumkin emas."}
                )
        from django.contrib.auth.password_validation import validate_password
        from django.core.exceptions import ValidationError

        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError(
                {"password": "Yangi foydalanuvchi uchun parol talab qilinadi."}
            )
        if "password" in attrs:
            candidate = self.instance or User(username=attrs.get("username", ""))
            try:
                validate_password(attrs["password"], candidate)
            except ValidationError as exc:
                raise serializers.ValidationError({"password": exc.messages})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Foydalanuvchi nomi yoki parol noto'g'ri.")
            if not user.is_active:
                raise serializers.ValidationError("Foydalanuvchi hisobi faol emas.")
            attrs["user"] = user
            return attrs
        raise serializers.ValidationError("Foydalanuvchi nomi va parol kiritilishi shart.")
