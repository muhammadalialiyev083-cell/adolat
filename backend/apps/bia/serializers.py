from django.db import transaction
from rest_framework import serializers

from apps.bia.models import BIAAssessment, BIAImpact
from apps.bia.questionnaire import EvidenceSerializer, QuestionnaireSerializer, missing_evidence
from apps.core.api import TenantSerializer


class BIAImpactSerializer(TenantSerializer):
    class Meta:
        model = BIAImpact
        fields = [
            "id",
            "horizon_hours",
            "financial_loss",
            "operational_score",
            "legal_score",
            "reputational_score",
        ]


class BIAAssessmentSerializer(TenantSerializer):
    questionnaire = QuestionnaireSerializer(required=False)
    evidence = EvidenceSerializer(many=True, required=False, max_length=50)
    missing_evidence = serializers.SerializerMethodField()
    process_owner_id = serializers.IntegerField(source="process.owner_id", read_only=True)
    process_name = serializers.CharField(source="process.name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    has_rpo_gap = serializers.BooleanField(read_only=True)
    impacts = BIAImpactSerializer(many=True, required=False)

    class Meta:
        model = BIAAssessment
        # Revision is allocated in TenantSerializer after field validation.
        # DRF's generated validator otherwise tests model default revision=1
        # before allocation and rejects a legitimate next assessment.
        validators = []
        fields = [
            "process_owner_id",
            "id",
            "organization",
            "process",
            "process_name",
            "revision",
            "mtpd_hours",
            "rto_hours",
            "rpo_minutes",
            "backup_interval_minutes",
            "has_rpo_gap",
            "status",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "comments",
            "impacts",
            "created_at",
            "updated_at",
        ]
        fields += ["rationale", "data_source", "impact_weights", "recommended_values"]
        fields += [
            "questionnaire",
            "evidence",
            "evidence_required",
            "created_by",
            "approved_snapshot",
            "review_notes",
            "missing_evidence",
        ]
        read_only_fields = [
            "created_by",
            "approved_snapshot",
            "review_notes",
            "id",
            "organization",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if (
            self.instance
            and self.instance.evidence_required
            and attrs.get("evidence_required") is False
        ):
            raise serializers.ValidationError({"evidence_required": "Dalil talabi o‘chirilmaydi."})
        if attrs.get("evidence") or attrs.get("questionnaire"):
            attrs["evidence_required"] = True
        mtpd = attrs.get("mtpd_hours") or (self.instance.mtpd_hours if self.instance else None)
        rto = attrs.get("rto_hours") or (self.instance.rto_hours if self.instance else None)
        if rto is not None and mtpd is not None and rto >= mtpd:
            raise serializers.ValidationError(
                {"rto_hours": "RTO MTPDdan qat’iy qisqa bo‘lishi kerak (RTO < MTPD)."}
            )
        impacts = attrs.get("impacts", [])
        horizons = [i["horizon_hours"] for i in impacts]
        if len(horizons) != len(set(horizons)):
            raise serializers.ValidationError({"impacts": "Vaqt oraliqlari takrorlanmasin."})
        return attrs

    def get_missing_evidence(self, obj):
        return missing_evidence(obj)

    @transaction.atomic
    def create(self, validated_data):
        impacts_data = validated_data.pop("impacts", [])
        bia = BIAAssessment.objects.create(**validated_data)
        for impact_data in impacts_data:
            BIAImpact.objects.create(bia=bia, **impact_data)
        return bia

    @transaction.atomic
    def update(self, instance, validated_data):
        impacts = validated_data.pop("impacts", None)
        instance = super().update(instance, validated_data)
        if impacts is not None:
            instance.impacts.all().delete()
            for impact in impacts:
                BIAImpact.objects.create(bia=instance, **impact)
        return instance
