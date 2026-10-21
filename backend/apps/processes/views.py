from apps.core.api import TenantViewSet
from apps.processes.serializers import (
    AssetSerializer,
    BusinessProcessSerializer,
    DependencySerializer,
)


class BusinessProcessViewSet(TenantViewSet):
    serializer_class = BusinessProcessSerializer
    search_fields = ["name", "description"]
    filter_fields = ["criticality", "status", "service", "owner", "department"]
    ordering_fields = ["id", "name"]


class AssetViewSet(TenantViewSet):
    serializer_class = AssetSerializer
    search_fields = ["name"]
    filter_fields = ["type"]
    ordering_fields = ["id", "name"]


class DependencyViewSet(TenantViewSet):
    serializer_class = DependencySerializer
    search_fields = ["notes"]
    filter_fields = ["from_type", "from_id", "to_type", "to_id"]
    ordering_fields = ["id"]
