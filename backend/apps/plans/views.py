from copy import deepcopy

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.permissions import IsApproverRole, IsTenantMember
from apps.core.api import TenantViewSet
from apps.core.audit import record_audit
from apps.plans.documents import document_data, export_docx, export_pdf
from apps.plans.models import ContinuityPlan
from apps.plans.serializers import ContinuityPlanSerializer, StrategySerializer


class StrategyViewSet(TenantViewSet):
    serializer_class = StrategySerializer
    search_fields = ["name", "process__name"]
    filter_fields = ["process", "kind", "is_selected"]
    ordering_fields = ["id", "estimated_cost", "estimated_rto_hours"]


class ContinuityPlanViewSet(TenantViewSet):
    serializer_class = ContinuityPlanSerializer
    search_fields = ["title", "process__name", "scope"]
    filter_fields = ["process", "status"]
    ordering_fields = ["id", "created_at", "review_due_date"]

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsApproverRole])
    @transaction.atomic
    def publish(self, request, pk=None):
        plan = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if plan.status not in ("DRAFT", "IN_REVIEW", "APPROVED"):
            raise ValidationError({"status": "Bu holatdan e’lon qilish mumkin emas."})
        if plan.organization.separation_of_duties and (
            not plan.created_by_id or request.user.pk in {plan.created_by_id, plan.process.owner_id}
        ):
            raise ValidationError({"approval": "Mustaqil tasdiqlovchi va ma’lum muallif talab qilinadi."})
        bia = (
            plan.process.bia_assessments.filter(is_deleted=False)
            .order_by("-revision", "-id")
            .first()
        )
        if not bia or bia.status != "APPROVED":
            raise ValidationError(
                {
                    "process": "Rejani tasdiqlashdan oldin jarayonning eng so‘nggi BIA baholashi tasdiqlansin."
                }
            )
        required = [
            "scope",
            "activation_conditions",
            "contacts",
            "temporary_procedures",
            "return_to_normal",
            "verification_criteria",
        ]
        missing = [name for name in required if not getattr(plan, name).strip()]
        if not plan.steps.exists():
            missing.append("steps")
        if missing:
            raise ValidationError({name: "Tasdiqlashdan oldin to‘ldiring." for name in missing})
        if plan.schedule_run and not plan.schedule_run.results.get("constrained", {}).get(
            "feasible"
        ):
            raise ValidationError(
                {"schedule_run": "Bajarilmaydigan jadvalni tasdiqlash mumkin emas."}
            )
        plan.status, plan.approved_by, plan.approved_at = "PUBLISHED", request.user, timezone.now()
        data = dict(self.get_serializer(plan).data)
        data.pop("snapshot", None)
        data.update(
            organization_name=plan.organization.name,
            approved_by_username=request.user.username,
            schedule_snapshot=deepcopy(plan.schedule_run.results["constrained"])
            if plan.schedule_run
            else None,
            bia_snapshot=list(
                plan.process.bia_assessments.filter(is_deleted=False).order_by("-revision").values()
            ),
            resource_snapshot=deepcopy(plan.schedule_run.input_snapshot)
            if plan.schedule_run
            else None,
        )
        # Normalize Decimal/date fields before writing JSON.
        import json

        from django.core.serializers.json import DjangoJSONEncoder

        plan.snapshot = json.loads(json.dumps(data, cls=DjangoJSONEncoder))
        plan.save()
        record_audit(
            request,
            action="APPROVE",
            entity="ContinuityPlan",
            entity_id=plan.id,
            after_state={"status": "PUBLISHED", "version": plan.version},
        )
        return Response(
            {
                "message": "Reja tasdiqlandi va e’lon qilindi.",
                "plan": self.get_serializer(plan).data,
            }
        )

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def revise(self, request, pk=None):
        original = self.get_object()
        # Lock the process to serialize revision numbering on PostgreSQL.
        original.process.__class__.objects.select_for_update().get(pk=original.process_id)
        data = deepcopy(dict(self.get_serializer(original).data))
        for field in [
            "id",
            "organization",
            "snapshot",
            "previous_version",
            "approved_by",
            "approved_at",
        ]:
            data.pop(field, None)
        version_number = (
            ContinuityPlan.objects.filter(
                organization=request.user.organization, process=original.process
            ).count()
            + 1
        )
        data.update(status="DRAFT", version=f"{version_number}.0")
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        plan = serializer.save(organization=request.user.organization, previous_version=original, created_by=request.user)
        record_audit(
            request,
            action="CREATE",
            entity="ContinuityPlan",
            entity_id=plan.id,
            after_state={"previous_version": original.id, "version": plan.version},
        )
        return Response(self.get_serializer(plan).data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsApproverRole])
    @transaction.atomic
    def archive(self, request, pk=None):
        plan = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if plan.status not in {"APPROVED", "PUBLISHED"}:
            raise ValidationError({"status": "Faqat tasdiqlangan rejani arxivlang."})
        plan.status = "ARCHIVED"
        plan.save(update_fields=["status", "updated_at"])
        record_audit(
            request,
            action="UPDATE",
            entity="ContinuityPlan",
            entity_id=plan.pk,
            after_state={"status": "ARCHIVED"},
        )
        return Response(self.get_serializer(plan).data)

    def _export(self, request, extension):
        plan = self.get_object()
        data = document_data(plan)
        content = export_pdf(data) if extension == "pdf" else export_docx(data)
        record_audit(
            request,
            action="EXPORT",
            entity="ContinuityPlan",
            entity_id=plan.pk,
            after_state={"format": extension},
        )
        mime = (
            "application/pdf"
            if extension == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response = HttpResponse(content, content_type=mime)
        response["Content-Disposition"] = f'attachment; filename="BCP_{plan.pk}.{extension}"'
        return response

    @action(detail=True, methods=["get"])
    def export_pdf(self, request, pk=None):
        return self._export(request, "pdf")

    @action(detail=True, methods=["get"])
    def export_docx(self, request, pk=None):
        return self._export(request, "docx")
