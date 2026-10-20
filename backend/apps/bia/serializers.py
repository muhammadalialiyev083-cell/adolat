from apps.core.serializers import TenantReferenceMixin
from rest_framework import serializers
from apps.bia.models import BIAAssessment, BIAImpact


class BIAImpactSerializer(serializers.ModelSerializer):
    operational_score = serializers.IntegerField(min_value=1, max_value=5, required=False)
    legal_score = serializers.IntegerField(min_value=1, max_value=5, required=False)
    reputational_score = serializers.IntegerField(min_value=1, max_value=5, required=False)
    financial_loss = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=0, required=False)
    horizon_hours = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)

    class Meta:
        model = BIAImpact
        fields = [
            'id', 'horizon_hours', 'financial_loss',
            'operational_score', 'legal_score', 'reputational_score'
        ]


class BIAAssessmentSerializer(TenantReferenceMixin, serializers.ModelSerializer):
    process_name = serializers.CharField(source='process.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    has_rpo_gap = serializers.BooleanField(read_only=True)
    impacts = BIAImpactSerializer(many=True, required=False)

    class Meta:
        model = BIAAssessment
        fields = [
            'id', 'organization', 'process', 'process_name', 'revision',
            'mtpd_hours', 'rto_hours', 'rpo_minutes', 'backup_interval_minutes',
            'has_rpo_gap', 'status', 'approved_by', 'approved_by_name',
            'approved_at', 'comments', 'impacts', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'approved_by', 'approved_at', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        mtpd = attrs.get('mtpd_hours', self.instance.mtpd_hours if self.instance else None)
        rto = attrs.get('rto_hours', self.instance.rto_hours if self.instance else None)
        for field in ('rto_hours', 'mtpd_hours'):
            if attrs.get(field) is not None and attrs[field] < 0:
                raise serializers.ValidationError({field: 'Nonnegative time required.'})
        if rto is not None and mtpd is not None and rto > mtpd:
            raise serializers.ValidationError({
                'rto_hours': f"RTO ({rto}h) MTPD dan ({mtpd}h) katta bo'lishi mumkin emas. (RTO <= MTPD talabi)."
            })
        return attrs

    def create(self, validated_data):
        impacts_data = validated_data.pop('impacts', [])
        bia = BIAAssessment.objects.create(**validated_data)
        for impact_data in impacts_data:
            BIAImpact.objects.create(bia=bia, **impact_data)
        return bia
