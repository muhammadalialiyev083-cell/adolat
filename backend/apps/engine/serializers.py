from rest_framework import serializers

from apps.core.api import TenantSerializer
from apps.engine.models import RecoveryResource, ScheduleRun


class RecoveryResourceSerializer(TenantSerializer):
    class Meta:
        model = RecoveryResource
        fields = [
            "id",
            "organization",
            "name",
            "kind",
            "capacity",
            "available_from_minutes",
            "unavailable_until_minutes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class ScheduleRunSerializer(TenantSerializer):
    class Meta:
        model = ScheduleRun
        fields = [
            "id",
            "organization",
            "algorithm_version",
            "input_snapshot",
            "results",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class ScheduleInputSerializer(serializers.Serializer):
    budget = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    staff_capacity = serializers.IntegerField(min_value=1, max_value=100000, default=1)


class RiskInputSerializer(serializers.Serializer):
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    rto_hours = serializers.FloatField(min_value=0, default=24)
    rpo_minutes = serializers.IntegerField(min_value=0, default=60)
    backup_interval_minutes = serializers.IntegerField(min_value=0, default=60)


class CandidateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField()
    estimated_rto_hours = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    estimated_rpo_minutes = serializers.IntegerField(min_value=0)
    cost = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0)


class StrategyInputSerializer(serializers.Serializer):
    target_rto_hours = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=0)
    target_rpo_minutes = serializers.IntegerField(min_value=0)
    strategies = CandidateSerializer(many=True)
