from decimal import Decimal

from django.db import transaction
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.api import TenantViewSet
from apps.core.audit import record_audit
from apps.simulation.models import SimulationRun
from apps.simulation.serializers import (
    ExerciseSerializer,
    ScenarioSerializer,
    SimulationRunSerializer,
)
from apps.simulation.simulator import ScenarioSimulator


class ScenarioViewSet(TenantViewSet):
    serializer_class = ScenarioSerializer
    search_fields = ["title", "description"]
    filter_fields = ["kind", "is_synthetic"]
    ordering_fields = ["id", "title"]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def simulate(self, request, pk=None):
        scenario = self.get_object()
        result = ScenarioSimulator.simulate(scenario)
        snapshot = result.pop("input_snapshot")
        run = SimulationRun.objects.create(
            organization=request.user.organization,
            scenario=scenario,
            input_snapshot=snapshot,
            results=result,
        )
        result["simulation_run_id"] = run.pk
        record_audit(
            request,
            action="SIMULATE",
            entity="Scenario",
            entity_id=scenario.pk,
            after_state={"affected_count": result["affected_processes_count"]},
        )
        return Response(result)


class ExerciseViewSet(TenantViewSet):
    serializer_class = ExerciseSerializer
    search_fields = ["plan__title", "findings", "improvement_actions"]
    filter_fields = ["plan", "outcome", "findings_closed", "is_synthetic"]
    ordering_fields = ["id", "exercise_date", "actual_recovery_hours"]

    def perform_create(self, serializer):
        plan = serializer.validated_data["plan"]
        bia = (
            plan.process.bia_assessments.filter(is_deleted=False)
            .order_by("-revision", "-id")
            .first()
        )
        frozen_bias = plan.snapshot.get("bia_snapshot", [])
        target = (
            Decimal(frozen_bias[0]["rto_hours"]) if frozen_bias else bia.rto_hours if bia else None
        )
        obj = serializer.save(
            organization=self.request.user.organization,
            planned_recovery_hours=target,
        )
        record_audit(
            self.request,
            action="CREATE",
            entity="Exercise",
            entity_id=obj.pk,
            after_state=serializer.data,
        )


class SimulationRunViewSet(TenantViewSet):
    serializer_class = SimulationRunSerializer
    http_method_names = ["get", "head", "options"]
    search_fields = ["scenario__title"]
    filter_fields = ["scenario"]
    ordering_fields = ["id", "created_at"]
