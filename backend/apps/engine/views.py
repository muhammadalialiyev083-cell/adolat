from django.db import transaction
from rest_framework import serializers, status, views
from rest_framework.response import Response

from apps.authentication.permissions import IsTenantMember
from apps.core.api import TenantViewSet
from apps.core.audit import record_audit
from apps.engine.calculator import PriorityEngine, RiskCalculator, StrategyEvaluator
from apps.engine.models import ScheduleRun
from apps.engine.scheduler import compare_schedules, make_snapshot
from apps.engine.serializers import (
    RecoveryResourceSerializer,
    RiskInputSerializer,
    ScheduleInputSerializer,
    ScheduleRunSerializer,
    StrategyInputSerializer,
)
from apps.processes.models import BusinessProcess


class PriorityAnalysisView(views.APIView):
    """
    FR-07: Ustuvorlikni hisoblash (/api/v1/analyses/priority).
    Jarayon yoki butun tashkilot bo'yicha ustuvorlik ballarini hisoblaydi va saralaydi.
    """

    permission_classes = [IsTenantMember]

    def post(self, request):
        field = serializers.IntegerField(min_value=1, required=False)
        process_id = (
            field.run_validation(request.data["process_id"])
            if "process_id" in request.data
            else None
        )
        user = request.user

        if process_id:
            try:
                proc = BusinessProcess.objects.get(
                    id=process_id, organization=user.organization, is_deleted=False
                )
            except BusinessProcess.DoesNotExist:
                return Response({"error": "Jarayon topilmadi."}, status=status.HTTP_404_NOT_FOUND)

            result = PriorityEngine.calculate_priority(proc)
            return Response(result, status=status.HTTP_200_OK)

        # Butun tashkilot bo'yicha hisoblash
        procs = BusinessProcess.objects.filter(organization=user.organization, is_deleted=False)
        results = [PriorityEngine.calculate_priority(p) for p in procs]
        results.sort(
            key=lambda x: (x["priority_score"] is not None, x["priority_score"] or 0), reverse=True
        )

        return Response(
            {"total_processes": len(results), "ranked_processes": results},
            status=status.HTTP_200_OK,
        )


class EvaluateRiskAlgorithmView(views.APIView):
    """
    FR-07 va Hujjat 10.1 namunaviy API:
    So'rov: {"process_id": 12, "likelihood": 4, "impact": 5, "rto_hours": 4, "rpo_minutes": 60, "backup_interval_minutes": 360}
    Javob: {"risk_score": 20, "risk_class": "high", "rpo_gap": true, "observations": ["Zaxiralash intervali RPO talabidan katta"]}
    """

    permission_classes = [IsTenantMember]

    def post(self, request):
        inputs = RiskInputSerializer(data=request.data)
        inputs.is_valid(raise_exception=True)
        likelihood = inputs.validated_data["likelihood"]
        impact = inputs.validated_data["impact"]
        rpo_minutes = inputs.validated_data["rpo_minutes"]
        backup_interval = inputs.validated_data["backup_interval_minutes"]

        score = RiskCalculator.calculate_score(likelihood, impact)
        org = request.user.organization
        low_t = org.risk_low_threshold if org else 6
        med_t = org.risk_medium_threshold if org else 14
        risk_class = RiskCalculator.classify_risk(score, low_t, med_t)

        rpo_gap = backup_interval > rpo_minutes
        observations = []
        if rpo_gap:
            observations.append("Zaxiralash intervali RPO talabidan katta")

        return Response(
            {
                "risk_score": score,
                "risk_class": risk_class,
                "rpo_gap": rpo_gap,
                "observations": observations,
            },
            status=status.HTTP_200_OK,
        )


class EvaluateStrategyView(views.APIView):
    """
    FR-08: Tiklash strategiyasini baholash va optimalini tanlash.
    """

    permission_classes = [IsTenantMember]

    def post(self, request):
        inputs = StrategyInputSerializer(data=request.data)
        inputs.is_valid(raise_exception=True)
        target_rto = float(inputs.validated_data["target_rto_hours"])
        target_rpo = inputs.validated_data["target_rpo_minutes"]
        candidates = inputs.validated_data["strategies"]

        res = StrategyEvaluator.evaluate_strategies(target_rto, target_rpo, candidates)
        return Response(res, status=status.HTTP_200_OK)


class RecoveryResourceViewSet(TenantViewSet):
    serializer_class = RecoveryResourceSerializer
    search_fields = ["name"]
    ordering_fields = ["id", "name", "capacity"]


class ScheduleRunViewSet(TenantViewSet):
    serializer_class = ScheduleRunSerializer
    http_method_names = ["get", "post", "head", "options"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = ScheduleInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        org = request.user.organization
        snapshot = make_snapshot(
            org, values.get("budget", org.recovery_budget), values["staff_capacity"]
        )
        run = ScheduleRun.objects.create(
            organization=org,
            created_by=request.user,
            input_snapshot=snapshot,
            results=compare_schedules(snapshot),
        )
        record_audit(
            request,
            action="CREATE",
            entity="ScheduleRun",
            entity_id=run.id,
            after_state={"algorithm_version": run.algorithm_version},
        )
        return Response(self.get_serializer(run).data, status=201)
