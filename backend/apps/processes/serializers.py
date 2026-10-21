from rest_framework import serializers

from apps.core.api import TenantSerializer
from apps.processes.models import Asset, BusinessProcess, Dependency


class BusinessProcessSerializer(TenantSerializer):
    service_name = serializers.CharField(source="service.name", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)
    criticality_display = serializers.CharField(source="get_criticality_display", read_only=True)

    class Meta:
        model = BusinessProcess
        fields = [
            "id",
            "organization",
            "service",
            "service_name",
            "name",
            "description",
            "owner",
            "owner_name",
            "criticality",
            "criticality_display",
            "status",
            "created_at",
            "updated_at",
        ]
        fields += [
            "department",
            "working_hours",
            "critical_periods",
            "required_staff",
            "resource_notes",
            "data_recovery_applicable",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class AssetSerializer(TenantSerializer):
    type_display = serializers.CharField(source="get_type_display", read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Asset
        fields = [
            "id",
            "organization",
            "name",
            "type",
            "type_display",
            "description",
            "owner",
            "owner_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class DependencySerializer(TenantSerializer):
    class Meta:
        model = Dependency
        fields = [
            "id",
            "organization",
            "from_type",
            "from_id",
            "to_type",
            "to_id",
            "dependency_criticality",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]
