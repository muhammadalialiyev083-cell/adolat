from django.db import transaction
from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from apps.authentication.permissions import IsTenantMember
from apps.core.api import MANAGERS, TenantViewSet
from apps.core.audit import record_audit
from apps.incidents.serializers import EvidenceReferenceSerializer, IncidentSerializer


class IncidentPermission(IsTenantMember):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and (
            request.method in permissions.SAFE_METHODS
            or request.user.role in MANAGERS
            or (
                request.user.role not in {"AUDITOR", "APPROVER"}
                and view.action in {"partial_update", "add_evidence"}
            )
        )


class IncidentViewSet(TenantViewSet):
    serializer_class = IncidentSerializer
    permission_classes = [IncidentPermission]
    http_method_names = ["get", "post", "patch", "head", "options"]
    search_fields = ["title", "description", "reporting_source"]
    ordering_fields = ["id", "detected_at", "severity", "status"]
    filter_fields = ["status", "severity", "owner", "incident_type"]

    def get_object(self):
        obj = viewsets.ModelViewSet.get_object(self)
        if (
            self.request.method not in permissions.SAFE_METHODS
            and self.request.user.role not in MANAGERS
            and obj.owner_id != self.request.user.pk
        ):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Faqat o‘zingizga biriktirilgan hodisa uchun yozing.")
        return obj

    def perform_create(self, serializer):
        obj = serializer.save(
            organization=self.request.user.organization, reporter=self.request.user
        )
        record_audit(
            self.request,
            action="CREATE",
            entity="Incident",
            entity_id=obj.pk,
            after_state=serializer.data,
        )

    @action(detail=True, methods=["post"], url_path="evidence")
    @transaction.atomic
    def add_evidence(self, request, pk=None):
        obj = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if len(obj.evidence) >= 100 or obj.status == "CLOSED":
            raise ValidationError(
                "Dalil limiti yoki yopilgan hodisa. Menejer hodisani qayta ochishi kerak."
            )
        serializer = EvidenceReferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = dict(
            serializer.validated_data,
            recorded_at=timezone.now().isoformat(),
            recorded_by=request.user.pk,
            verification="OPERATOR_REFERENCE_ONLY",
        )
        obj.evidence = [*obj.evidence, item]
        obj.save(update_fields=["evidence", "updated_at"])
        record_audit(
            request,
            action="UPDATE",
            entity="Incident",
            entity_id=obj.pk,
            after_state={"evidence_added": item},
        )
        return Response(self.get_serializer(obj).data)
