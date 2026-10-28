from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.permissions import IsApproverRole, IsTenantMember
from apps.bia.serializers import BIAAssessmentSerializer
from apps.bia.questionnaire import missing_evidence
from apps.core.api import TenantViewSet
from apps.core.audit import record_audit


class BIAAssessmentViewSet(TenantViewSet):
    serializer_class = BIAAssessmentSerializer
    search_fields = ["process__name", "comments", "data_source"]
    filter_fields = ["process", "status"]
    ordering_fields = ["id", "revision", "rto_hours", "created_at"]

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsApproverRole])
    @transaction.atomic
    def approve(self, request, pk=None):
        bia = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if bia.status not in ("DRAFT", "SUBMITTED"):
            raise ValidationError(
                {"status": "Faqat qoralama yoki yuborilgan baholash tasdiqlanadi."}
            )
        if bia.organization.separation_of_duties and (
            not bia.created_by_id or request.user.pk in {bia.created_by_id, bia.process.owner_id}
        ):
            raise ValidationError({"approval": "Mustaqil tasdiqlovchi va ma’lum muallif talab qilinadi."})
        if bia.evidence_required and missing_evidence(bia):
            raise ValidationError({"evidence": missing_evidence(bia)})
        if bia.evidence_required:
            bia.evidence = [dict(item, review_status="REVIEWED") for item in bia.evidence]
        bia.status, bia.approved_by, bia.approved_at = "APPROVED", request.user, timezone.now()
        snapshot = dict(self.get_serializer(bia).data)
        snapshot.pop("approved_snapshot", None)
        snapshot["process_context"] = {
            "name": bia.process.name, "department_id": bia.process.department_id,
            "owner_id": bia.process.owner_id, "service_id": bia.process.service_id,
            "working_hours": bia.process.working_hours,
        }
        bia.approved_snapshot = snapshot
        bia.save()
        record_audit(
            request,
            action="APPROVE",
            entity="BIAAssessment",
            entity_id=bia.id,
            after_state=self.get_serializer(bia).data,
        )
        return Response({"message": "BIA tasdiqlandi.", "bia": self.get_serializer(bia).data})

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def revise(self, request, pk=None):
        original = self.get_object()
        from django.db.models import Max

        process = original.process.__class__.objects.select_for_update().get(pk=original.process_id)
        revision = (process.bia_assessments.aggregate(value=Max("revision"))["value"] or 0) + 1
        data = dict(self.get_serializer(original).data)
        for key in ["id", "organization", "approved_by", "approved_at"]:
            data.pop(key, None)
        data.update(status="DRAFT", revision=revision)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsApproverRole])
    @transaction.atomic
    def review(self, request, pk=None):
        bia = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        decision = request.data.get("decision")
        notes = request.data.get("notes", "")
        if bia.status not in {"DRAFT", "SUBMITTED"} or decision not in {"reject", "request_changes"}:
            raise ValidationError({"decision": "Faol qoralama uchun reject yoki request_changes tanlang."})
        if not isinstance(notes, str) or not notes.strip() or len(notes) > 4000:
            raise ValidationError({"notes": "Ko‘rib chiqish sababini kiriting (4000 belgigacha)."})
        bia.status = "REJECTED" if decision == "reject" else "DRAFT"
        bia.review_notes = notes.strip()
        bia.save()
        record_audit(request, action="UPDATE", entity="BIAAssessment", entity_id=bia.pk, after_state={"decision": decision, "notes": bia.review_notes, "status": bia.status})
        return Response(self.get_serializer(bia).data)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        bia = self.get_object()
        data = bia.approved_snapshot if bia.status == "APPROVED" and bia.approved_snapshot else self.get_serializer(bia).data
        record_audit(request, action="EXPORT", entity="BIAAssessment", entity_id=bia.pk)
        response = JsonResponse(data, json_dumps_params={"ensure_ascii": False, "indent": 2})
        response["Content-Disposition"] = f'attachment; filename="bia-{bia.pk}-v{bia.revision}.json"'
        return response
