from django.db.models import F, Q
from django.utils import timezone
from rest_framework import permissions, views, viewsets
from rest_framework.response import Response
from apps.authentication.permissions import IsTenantMember
from apps.bia.models import BIAAssessment
from apps.core.api import MANAGERS, TenantViewSet
from apps.core.models import AuditLog
from apps.management.models import Task
from apps.management.serializers import TaskSerializer
from apps.plans.models import ContinuityPlan
from apps.risks.models import Risk
from apps.simulation.models import Exercise


class TaskPermission(IsTenantMember):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.role in MANAGERS
            or (request.user.role != "AUDITOR" and view.action in {"update", "partial_update"})
        )


class TaskViewSet(TenantViewSet):
    serializer_class = TaskSerializer
    permission_classes = [TaskPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]
    search_fields = ["title", "description"]
    ordering_fields = ["id", "due_date", "priority", "status", "created_at"]
    filter_fields = ["assigned_to", "status", "priority"]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role not in MANAGERS | {"AUDITOR", "APPROVER"}:
            queryset = queryset.filter(assigned_to=self.request.user)
        if self.request.query_params.get("overdue") == "true":
            queryset = queryset.filter(due_date__lt=timezone.localdate()).exclude(
                status__in=["DONE", "CANCELLED"]
            )
        return queryset

    def get_object(self):
        return viewsets.ModelViewSet.get_object(self)


class ManagementDashboardView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        org = request.user.organization
        bia = BIAAssessment.objects.filter(organization=org, is_deleted=False)
        plans = ContinuityPlan.objects.filter(organization=org, is_deleted=False)
        tasks = Task.objects.filter(organization=org, is_deleted=False)
        risks = Risk.objects.filter(organization=org, is_deleted=False)
        exercises = Exercise.objects.filter(organization=org, is_deleted=False)
        if request.user.role not in MANAGERS | {"APPROVER", "AUDITOR"}:
            bia = bia.filter(process__owner=request.user)
            plans = plans.filter(process__owner=request.user)
            tasks = tasks.filter(assigned_to=request.user)
            risks = risks.filter(process__owner=request.user)
            exercises = exercises.filter(plan__process__owner=request.user)
        today = timezone.localdate()
        pending_bia = bia.filter(status="SUBMITTED")
        pending_plans = plans.filter(status="IN_REVIEW")
        recent = AuditLog.objects.filter(
            organization=org, entity__in=["BIAAssessment", "ContinuityPlan"]
        ).filter(Q(action="APPROVE") | Q(after_state__decision__in=["reject", "request_changes"]))
        if request.user.role not in MANAGERS | {"APPROVER", "AUDITOR"}:
            recent = recent.filter(
                Q(
                    entity="BIAAssessment",
                    entity_id__in=[str(i) for i in bia.values_list("pk", flat=True)],
                )
                | Q(
                    entity="ContinuityPlan",
                    entity_id__in=[str(i) for i in plans.values_list("pk", flat=True)],
                )
            )
        return Response(
            {
                "pending_bia": list(pending_bia.values("id", "process__name", "revision")[:20]),
                "pending_plans": list(pending_plans.values("id", "title")[:20]),
                "counts": {
                    "pending_bia": pending_bia.count(),
                    "pending_plans": pending_plans.count(),
                    "overdue_tasks": tasks.filter(due_date__lt=today)
                    .exclude(status__in=["DONE", "CANCELLED"])
                    .count(),
                    "incomplete_evidence": bia.filter(evidence_required=True)
                    .exclude(status="APPROVED")
                    .filter(Q(evidence=[]) | Q(rationale=""))
                    .count(),
                    "open_findings": exercises.filter(findings_closed=False)
                    .exclude(findings="")
                    .count(),
                    "unreviewed_high_risks": risks.annotate(score=F("likelihood") * F("impact"))
                    .filter(score__gt=org.risk_medium_threshold, status="IDENTIFIED")
                    .count(),
                    "upcoming_reviews": plans.filter(
                        status__in=["APPROVED", "PUBLISHED"],
                        review_due_date__gte=today,
                        review_due_date__lte=today + timezone.timedelta(days=30),
                    ).count(),
                },
                "recent_decisions": list(
                    recent.values("entity", "entity_id", "action", "timestamp")[:10]
                ),
            }
        )
