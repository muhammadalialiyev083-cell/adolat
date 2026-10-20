from apps.core.serializers import TenantReferenceMixin
from rest_framework import serializers
from apps.processes.models import BusinessProcess, Asset, Dependency


class BusinessProcessSerializer(TenantReferenceMixin, serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    criticality_display = serializers.CharField(source='get_criticality_display', read_only=True)

    class Meta:
        model = BusinessProcess
        fields = [
            'id', 'organization', 'service', 'service_name', 'name', 'description',
            'owner', 'owner_name', 'criticality', 'criticality_display',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']


class AssetSerializer(TenantReferenceMixin, serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'organization', 'name', 'type', 'type_display', 'description',
            'owner', 'owner_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']


class DependencySerializer(TenantReferenceMixin, serializers.ModelSerializer):
    class Meta:
        model = Dependency
        fields = [
            'id', 'organization', 'from_type', 'from_id', 'to_type', 'to_id',
            'dependency_criticality', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organization', 'created_at', 'updated_at']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request:
            for side in ('from', 'to'):
                kind = attrs.get(side + '_type', getattr(self.instance, side + '_type', None))
                pk = attrs.get(side + '_id', getattr(self.instance, side + '_id', None))
                cls = {'PROCESS': BusinessProcess, 'ASSET': Asset}.get(kind)
                if cls is None or not cls.objects.filter(pk=pk, organization=request.user.organization, is_deleted=False).exists():
                    raise serializers.ValidationError({side + '_id': 'Active object in the current organization required.'})
        return attrs
