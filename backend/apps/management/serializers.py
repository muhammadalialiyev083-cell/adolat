from django.apps import apps
from rest_framework import serializers
from apps.core.api import MANAGERS, TenantSerializer, tenant_queryset
from apps.management.models import Task

ENTITY_MODELS = {
    "PROCESS": "processes.BusinessProcess",
    "BIA": "bia.BIAAssessment",
    "PLAN": "plans.ContinuityPlan",
    "RISK": "risks.Risk",
    "EXERCISE": "simulation.Exercise",
    "INCIDENT": "incidents.Incident",
}
TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "BLOCKED", "CANCELLED"},
    "IN_PROGRESS": {"BLOCKED", "DONE", "CANCELLED"},
    "BLOCKED": {"IN_PROGRESS", "CANCELLED"},
    "DONE": {"OPEN"},
    "CANCELLED": {"OPEN"},
}


class TaskSerializer(TenantSerializer):
    assigned_name = serializers.CharField(source="assigned_to.username", read_only=True)

    class Meta:
        model = Task
        exclude = ["is_deleted"]
        read_only_fields = ["organization", "created_by", "created_at", "updated_at"]

    def validate(self, attrs):
        user = self.context["request"].user

        def value(key):
            return attrs.get(key, getattr(self.instance, key, None))

        if self.instance and user.role not in MANAGERS:
            if self.instance.assigned_to_id != user.pk or set(attrs) - {
                "status",
                "completion_evidence",
                "resolution_notes",
            }:
                raise serializers.ValidationError(
                    "Faqat o‘zingizga biriktirilgan vazifa bajarilishini yangilang."
                )
        if not value("assigned_to").is_active:
            raise serializers.ValidationError({"assigned_to": "Faol mas’ulni tanlang."})
        if bool(value("entity_type")) != bool(value("entity_id")):
            raise serializers.ValidationError(
                {"entity_id": "Obyekt turi va IDsi birga kiritilsin."}
            )
        if value("entity_type"):
            model = apps.get_model(ENTITY_MODELS[value("entity_type")])
            if (
                not tenant_queryset(model.objects.all(), user.organization)
                .filter(pk=value("entity_id"))
                .exists()
            ):
                raise serializers.ValidationError(
                    {"entity_id": "Tashkilotda faol obyekt topilmadi."}
                )
        status = value("status") or "OPEN"
        if not self.instance and status != "OPEN":
            raise serializers.ValidationError({"status": "Yangi vazifa OPEN holatida bo‘lsin."})
        if self.instance and status != self.instance.status:
            if status not in TRANSITIONS[self.instance.status] or (
                status in {"OPEN", "CANCELLED"} and user.role not in MANAGERS
            ):
                raise serializers.ValidationError({"status": "Bu o‘tish uchun ruxsat yo‘q."})
            if status == "DONE" and not (
                value("completion_evidence") and value("resolution_notes")
            ):
                raise serializers.ValidationError(
                    {"completion_evidence": "Bajarish dalili va yechim izohini kiriting."}
                )
        return attrs
