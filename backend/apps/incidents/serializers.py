from django.utils import timezone
from rest_framework import serializers
from apps.core.api import MANAGERS, TenantSerializer
from apps.incidents.models import Incident
from apps.plans.models import ContinuityPlan

TRANSITIONS = {
    "DETECTED": {"TRIAGED"},
    "TRIAGED": {"INVESTIGATING"},
    "INVESTIGATING": {"CONTAINED"},
    "CONTAINED": {"RECOVERY_IN_PROGRESS"},
    "RECOVERY_IN_PROGRESS": {"MONITORING"},
    "MONITORING": {"RESOLVED"},
    "RESOLVED": {"CLOSED", "INVESTIGATING"},
    "CLOSED": {"TRIAGED"},
}


class EvidenceReferenceSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    source_reference = serializers.CharField(max_length=1000)
    sha256 = serializers.RegexField(r"^[a-fA-F0-9]{64}$", required=False)
    custody_note = serializers.CharField(max_length=2000)
    # Integrity is an operator-provided reference, not a verification claim.


class IncidentSerializer(TenantSerializer):
    reopen_reason = serializers.CharField(
        write_only=True, required=False, max_length=2000, allow_blank=True
    )
    related_plans = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=ContinuityPlan.objects.filter(
            is_deleted=False, status__in=["APPROVED", "PUBLISHED"]
        ),
    )
    recovery_objectives = serializers.SerializerMethodField()
    recovery_tasks = serializers.SerializerMethodField()
    detected_at = serializers.DateTimeField(required=False, default=timezone.now)

    class Meta:
        model = Incident
        exclude = ["is_deleted"]
        read_only_fields = [
            "identifier",
            "organization",
            "reporter",
            "evidence",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        user = self.context["request"].user
        reason = attrs.pop("reopen_reason", "")

        def value(key):
            return attrs.get(key, getattr(self.instance, key, None))

        if self.instance:
            if any(
                key in attrs and attrs[key] != getattr(self.instance, key)
                for key in ["detected_at", "occurred_at", "reporting_source"]
            ):
                raise serializers.ValidationError(
                    "Saqlangan vaqt va manba o‘zgarmaydi; izohda tuzatishni qayd qiling."
                )
            if user.role not in MANAGERS and (
                self.instance.owner_id != user.pk
                or set(attrs)
                - {
                    "business_impact",
                    "containment_actions",
                    "recovery_verification",
                    "resolution_summary",
                    "lessons_learned",
                    "status",
                }
            ):
                raise serializers.ValidationError(
                    "Faqat o‘zingiz mas’ul bo‘lgan hodisa javobini yangilang."
                )
        if not value("owner").is_active:
            raise serializers.ValidationError({"owner": "Faol mas’ulni tanlang."})
        if value("occurred_at") and value("occurred_at") > value("detected_at"):
            raise serializers.ValidationError(
                {"occurred_at": "Sodir bo‘lish vaqti aniqlanishdan keyin bo‘lmasin."}
            )
        if value("detected_at") > timezone.now():
            raise serializers.ValidationError({"detected_at": "Kelajak vaqtini kiritmang."})
        status = value("status") or "DETECTED"
        if not self.instance and status != "DETECTED":
            raise serializers.ValidationError(
                {"status": "Yangi hodisa DETECTED holatidan boshlanadi."}
            )
        if self.instance and status != self.instance.status:
            if status not in TRANSITIONS[self.instance.status]:
                raise serializers.ValidationError(
                    {"status": "Hodisa hayot siklidagi navbatdagi ruxsat etilgan holatni tanlang."}
                )
            if self.instance.status in {"RESOLVED", "CLOSED"} and status != "CLOSED":
                if user.role not in MANAGERS or not reason.strip():
                    raise serializers.ValidationError(
                        {"reopen_reason": "Qayta ochish uchun menejer huquqi va sabab kerak."}
                    )
            required = {
                "TRIAGED": "business_impact",
                "RECOVERY_IN_PROGRESS": "containment_actions",
                "RESOLVED": "recovery_verification",
                "CLOSED": "lessons_learned",
            }
            key = required.get(status)
            if key and not value(key):
                raise serializers.ValidationError(
                    {key: "Keyingi holatga o‘tishdan oldin dalilni kiriting."}
                )
            if status in {"RESOLVED", "CLOSED"} and not value("resolution_summary"):
                raise serializers.ValidationError(
                    {"resolution_summary": "Yechim xulosasini kiriting."}
                )
            if reason:
                attrs["resolution_summary"] = (
                    (value("resolution_summary") or "") + "\nQayta ochish: " + reason
                )
        return attrs

    def get_recovery_objectives(self, obj):
        result = []
        for process in obj.affected_processes.all():
            bia = (
                process.bia_assessments.filter(is_deleted=False, status="APPROVED")
                .order_by("-revision")
                .first()
            )
            if bia:
                result.append(
                    {
                        "process_id": process.pk,
                        "bia_id": bia.pk,
                        "revision": bia.revision,
                        "rto_seconds": bia.rto_seconds,
                        "rpo_seconds": bia.rpo_seconds,
                        "mtpd_seconds": bia.mtpd_seconds,
                        "source": "APPROVED_OBJECTIVE",
                    }
                )
        return result

    def get_recovery_tasks(self, obj):
        from apps.management.models import Task

        return list(
            Task.objects.filter(
                organization=obj.organization,
                is_deleted=False,
                entity_type="INCIDENT",
                entity_id=obj.pk,
            ).values("id", "title", "assigned_to", "status")
        )
