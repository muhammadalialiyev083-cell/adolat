from django.db import transaction
from rest_framework import serializers

from apps.bia.models import BIAAssessment, BIAImpact
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
    process_owner_id = serializers.IntegerField(source="process.owner_id", read_only=True)
    process_name = serializers.CharField(source="process.name", read_only=True)
    approved_by_name = serializers.CharField(source="approved_by.get_full_name", read_only=True)
    has_rpo_gap = serializers.BooleanField(read_only=True)
    impacts = BIAImpactSerializer(many=True, required=False)

    class Meta:
        model = BIAAssessment
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
        read_only_fields = [
            "id",
            "organization",
            "approved_by",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        mtpd = attrs.get("mtpd_hours") or (self.instance.mtpd_hours if self.instance else None)
        rto = attrs.get("rto_hours") or (self.instance.rto_hours if self.instance else None)
        if rto is not None and mtpd is not None and rto > mtpd:
            raise serializers.ValidationError(
                {
                    "rto_hours": f"RTO ({rto}h) MTPD dan ({mtpd}h) katta bo'lishi mumkin emas. (RTO <= MTPD talabi)."
                }
            )
        impacts = attrs.get("impacts", [])
        horizons = [i["horizon_hours"] for i in impacts]
        if len(horizons) != len(set(horizons)):
            raise serializers.ValidationError({"impacts": "Vaqt oraliqlari takrorlanmasin."})
        return attrs

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
