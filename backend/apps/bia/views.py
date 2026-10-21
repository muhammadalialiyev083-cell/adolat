from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.permissions import IsApproverRole, IsTenantMember
from apps.bia.serializers import BIAAssessmentSerializer
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
        bia.status, bia.approved_by, bia.approved_at = "APPROVED", request.user, timezone.now()
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
