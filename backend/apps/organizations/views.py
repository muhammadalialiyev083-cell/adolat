from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from apps.core.api import TenantViewSet
from apps.core.audit import record_audit
from apps.organizations.models import Organization
from apps.organizations.serializers import (
    DepartmentSerializer,
    OrganizationSerializer,
    ServiceSerializer,
)


class OrganizationViewSet(TenantViewSet):
    serializer_class = OrganizationSerializer

    def get_queryset(self):
        return Organization.objects.filter(pk=self.request.user.organization_id)

    @transaction.atomic
    def perform_create(self, serializer):
        if self.request.user.organization_id:
            raise PermissionDenied("Yangi tashkilotni alohida administrator hisobidan sozlang.")
        organization = serializer.save()
        self.request.user.organization = organization
        self.request.user.save(update_fields=["organization"])
        record_audit(
            self.request,
            action="CREATE",
            entity="Organization",
            entity_id=organization.pk,
            after_state=serializer.data,
        )


class DepartmentViewSet(TenantViewSet):
    serializer_class = DepartmentSerializer
    search_fields = ["name"]
    filter_fields = []
    ordering_fields = ["id", "name"]


class ServiceViewSet(TenantViewSet):
    serializer_class = ServiceSerializer
    search_fields = ["name", "description"]
    filter_fields = ["owner"]
    ordering_fields = ["id", "name"]
