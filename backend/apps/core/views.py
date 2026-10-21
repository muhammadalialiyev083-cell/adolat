from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.authentication.permissions import IsTenantMember
from apps.core.models import AuditLog
from apps.core.serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    FR-12: Audit jurnali (Immutable Read-Only View).
    Faqat joriy tashkilotga tegishli audit yozuvlarini qaytaradi.
    Tahrirlash va o'chirish bloklangan.
    """

    serializer_class = AuditLogSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["actor__username", "action", "entity", "entity_id"]
    ordering_fields = ["timestamp", "id"]
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        user = self.request.user
        return AuditLog.objects.filter(organization=user.organization)
