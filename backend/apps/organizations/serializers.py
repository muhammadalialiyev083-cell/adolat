from rest_framework import serializers

from apps.core.api import TenantSerializer
from apps.organizations.models import Department, Organization, Service


class OrganizationSerializer(TenantSerializer):
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
            "created_at",
            "updated_at",
        ]
        fields += ["is_demo", "contact_details", "recovery_budget", "separation_of_duties"]
        read_only_fields = ["id", "is_demo", "created_at", "updated_at"]


class DepartmentSerializer(TenantSerializer):
    class Meta:
        model = Department
        fields = ["id", "organization", "name", "head_name", "created_at", "updated_at"]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class ServiceSerializer(TenantSerializer):
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "organization",
            "name",
            "description",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]
