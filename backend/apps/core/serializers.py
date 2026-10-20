from rest_framework import serializers
from apps.core.models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    actor_role = serializers.CharField(source='actor.get_role_display', read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            'id', 'organization', 'actor', 'actor_username', 'actor_role',
            'action', 'entity', 'entity_id', 'before_state', 'after_state',
            'timestamp', 'ip_address'
        ]
        read_only_fields = fields


class TenantReferenceMixin:
    """Reject cross-tenant or deleted object references before model save."""
    def validate(self, attrs):
        attrs = super().validate(attrs)
        request = self.context.get('request')
        if request:
            org_id = request.user.organization_id
            for field in ('service', 'owner', 'process', 'asset', 'plan', 'scenario'):
                obj = attrs.get(field)
                if obj is not None and (getattr(obj, 'organization_id', org_id) != org_id or getattr(obj, 'is_deleted', False)):
                    raise serializers.ValidationError({field: 'Active object in the current organization required.'})
        return attrs
