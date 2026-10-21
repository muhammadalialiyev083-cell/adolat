from apps.core.api import TenantViewSet
from apps.risks.serializers import ControlSerializer, RiskSerializer


class RiskViewSet(TenantViewSet):
    serializer_class = RiskSerializer
    search_fields = ["threat", "vulnerability"]
    filter_fields = ["status", "process", "asset", "likelihood", "impact"]
    ordering_fields = ["id", "likelihood", "impact"]


class ControlViewSet(TenantViewSet):
    serializer_class = ControlSerializer
    search_fields = ["title", "description"]
    filter_fields = ["status", "risk"]
    ordering_fields = ["id", "name"]
