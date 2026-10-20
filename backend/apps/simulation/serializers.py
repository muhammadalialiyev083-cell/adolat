from apps.core.serializers import TenantReferenceMixin
from rest_framework import serializers
from apps.simulation.models import Scenario, Exercise


class ScenarioSerializer(TenantReferenceMixin, serializers.ModelSerializer):
    estimated_outage_hours = serializers.DecimalField(max_digits=6, decimal_places=2, min_value=0)
    disrupted_asset_ids = serializers.ListField(child=serializers.IntegerField(min_value=1), required=False)

    def validate_disrupted_asset_ids(self, value):
        from apps.processes.models import Asset
        request = self.context.get('request')
        if request and Asset.objects.filter(organization=request.user.organization, is_deleted=False, id__in=value).count() != len(set(value)):
            raise serializers.ValidationError('Active assets in the current organization required.')
        return value

    class Meta:
        model = Scenario
        fields = ['id', 'organization', 'title', 'description', 'disrupted_asset_ids', 'estimated_outage_hours', 'created_at', 'updated_at']
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']


class ExerciseSerializer(TenantReferenceMixin, serializers.ModelSerializer):
    plan_title = serializers.CharField(source='plan.title', read_only=True)
    outcome_display = serializers.CharField(source='get_outcome_display', read_only=True)

    class Meta:
        model = Exercise
        fields = [
            'id', 'organization', 'plan', 'plan_title', 'scenario',
            'exercise_date', 'actual_recovery_hours', 'outcome', 'outcome_display',
            'findings', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']
