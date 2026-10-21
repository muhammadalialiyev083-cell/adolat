from rest_framework import serializers

from apps.core.api import TenantSerializer
from apps.simulation.models import Exercise, Scenario, SimulationRun


class ScenarioSerializer(TenantSerializer):
    class Meta:
        model = Scenario
        fields = [
            "id",
            "organization",
            "title",
            "description",
            "disrupted_asset_ids",
            "estimated_outage_hours",
            "created_at",
            "updated_at",
        ]
        fields += ["kind", "is_synthetic", "event_time", "available_resources", "recovery_options"]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class ExerciseSerializer(TenantSerializer):
    process_owner_id = serializers.IntegerField(source="plan.process.owner_id", read_only=True)
    plan_title = serializers.CharField(source="plan.title", read_only=True)
    outcome_display = serializers.CharField(source="get_outcome_display", read_only=True)

    class Meta:
        model = Exercise
        fields = [
            "process_owner_id",
            "id",
            "organization",
            "plan",
            "plan_title",
            "scenario",
            "exercise_date",
            "actual_recovery_hours",
            "outcome",
            "outcome_display",
            "findings",
            "created_at",
            "updated_at",
        ]
        fields += [
            "resource_shortages",
            "unfinished_tasks",
            "improvement_actions",
            "findings_closed",
            "is_synthetic",
            "planned_recovery_hours",
        ]
        read_only_fields = [
            "planned_recovery_hours",
            "id",
            "organization",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if self.instance and "plan" in attrs and attrs["plan"].pk != self.instance.plan_id:
            raise serializers.ValidationError(
                {"plan": "Saqlangan mashq rejasini almashtirmang; yangi mashq yozuvi yarating."}
            )
        return attrs


class SimulationRunSerializer(TenantSerializer):
    scenario_title = serializers.CharField(source="scenario.title", read_only=True)

    class Meta:
        model = SimulationRun
        fields = [
            "id",
            "organization",
            "scenario",
            "scenario_title",
            "algorithm_version",
            "input_snapshot",
            "results",
            "created_at",
        ]
        read_only_fields = fields
