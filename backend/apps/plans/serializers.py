from django.db import transaction
from rest_framework import serializers

from apps.core.api import TenantSerializer
from apps.plans.models import ContinuityPlan, PlanStep, Strategy


class StrategySerializer(TenantSerializer):
    process_owner_id = serializers.IntegerField(source="process.owner_id", read_only=True)
    process_name = serializers.CharField(source="process.name", read_only=True)

    class Meta:
        model = Strategy
        fields = [
            "process_owner_id",
            "id",
            "organization",
            "process",
            "process_name",
            "name",
            "description",
            "estimated_rto_hours",
            "estimated_rpo_minutes",
            "estimated_cost",
            "is_selected",
            "created_at",
            "updated_at",
        ]
        fields += [
            "kind",
            "preparation_minutes",
            "staff_required",
            "resource_requirements",
            "conditions",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class PlanStepSerializer(TenantSerializer):
    assigned_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)

    class Meta:
        model = PlanStep
        fields = [
            "id",
            "plan",
            "sequence",
            "title",
            "description",
            "assigned_to",
            "assigned_name",
            "expected_duration_minutes",
        ]
        read_only_fields = ["id", "plan"]


class ContinuityPlanSerializer(TenantSerializer):
    process_owner_id = serializers.IntegerField(source="process.owner_id", read_only=True)
    process_name = serializers.CharField(source="process.name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    steps = PlanStepSerializer(many=True, required=False)

    class Meta:
        model = ContinuityPlan
        fields = [
            "process_owner_id",
            "id",
            "organization",
            "process",
            "process_name",
            "title",
            "version",
            "scope",
            "status",
            "status_display",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "steps",
            "created_at",
            "updated_at",
        ]
        fields += [
            "activation_conditions",
            "contacts",
            "temporary_procedures",
            "return_to_normal",
            "verification_criteria",
            "review_due_date",
            "snapshot",
            "previous_version",
            "schedule_run",
        ]
        read_only_fields = [
            "id",
            "organization",
            "approved_by",
            "approved_at",
            "snapshot",
            "previous_version",
            "created_at",
            "updated_at",
        ]

    @transaction.atomic
    def create(self, validated_data):
        steps_data = validated_data.pop("steps", [])
        plan = ContinuityPlan.objects.create(**validated_data)
        for s in steps_data:
            PlanStep.objects.create(plan=plan, **s)
        return plan

    @transaction.atomic
    def update(self, instance, validated_data):
        steps = validated_data.pop("steps", None)
        instance = super().update(instance, validated_data)
        if steps is not None:
            instance.steps.all().delete()
            for step in steps:
                PlanStep.objects.create(plan=instance, **step)
        return instance
