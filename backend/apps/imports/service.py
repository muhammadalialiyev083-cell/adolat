import hashlib
import json

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework.exceptions import ValidationError

from apps.core.api import tenant_queryset
from apps.engine.serializers import RecoveryResourceSerializer
from apps.imports.models import ImportIdentity
from apps.organizations.serializers import DepartmentSerializer, ServiceSerializer
from apps.processes.serializers import AssetSerializer, BusinessProcessSerializer, DependencySerializer

SERIALIZERS = {
    'departments': DepartmentSerializer, 'services': ServiceSerializer,
    'processes': BusinessProcessSerializer, 'assets': AssetSerializer,
    'dependencies': DependencySerializer, 'resources': RecoveryResourceSerializer,
}
# The stable external key is separate from mutable domain names. FK references are
# existing tenant-scoped IDs, validated by the same domain serializers as CRUD.
FIELDS = {
    'departments': ['key', 'name', 'head_name'],
    'services': ['key', 'name', 'description', 'owner'],
    'processes': ['key', 'name', 'service', 'owner', 'department', 'description', 'working_hours', 'required_staff', 'criticality', 'status'],
    'assets': ['key', 'name', 'type', 'description', 'owner'],
    'dependencies': ['key', 'from_type', 'from_id', 'to_type', 'to_id', 'dependency_criticality', 'notes'],
    'resources': ['key', 'name', 'kind', 'capacity', 'available_from_minutes', 'unavailable_until_minutes'],
}
REQUIRED = {
    'departments': ['key', 'name'], 'services': ['key', 'name'],
    'processes': ['key', 'name', 'service'], 'assets': ['key', 'name', 'type'],
    'dependencies': ['key', 'from_type', 'from_id', 'to_type', 'to_id'],
    'resources': ['key', 'name'],
}


def fingerprint(instance, serializer_class, request):
    payload = serializer_class(instance, context={'request': request}).data
    return hashlib.sha256(json.dumps(payload, sort_keys=True, cls=DjangoJSONEncoder).encode()).hexdigest()


def find_existing(entity, key, data, organization, lock=False):
    cls = SERIALIZERS[entity]
    queryset = tenant_queryset(cls.Meta.model.objects.all(), organization)
    if lock:
        queryset = queryset.select_for_update()
    identity = ImportIdentity.objects.filter(organization=organization, entity=entity, external_key=key).first()
    if identity:
        instance = queryset.filter(pk=identity.object_id).first()
        if not instance:
            raise ValidationError('Kalit faol yozuvga mos kelmaydi. Administrator tekshirsin.')
        return instance
    if entity == 'dependencies':
        lookup = {field: data.get(field) for field in ['from_type', 'from_id', 'to_type', 'to_id']}
    else:
        lookup = {'name': data.get('name')}
    try:
        return queryset.filter(**lookup).first()
    except (ValueError, TypeError):
        return None


def preview(batch, mapping, request):
    if not isinstance(mapping, dict) or any(k not in FIELDS[batch.entity] or v not in batch.headers for k, v in mapping.items()):
        raise ValidationError({'mapping': 'Faqat tanilgan maydon va fayl ustunlarini moslang.'})
    if any(k not in mapping for k in REQUIRED[batch.entity]) or len(set(mapping.values())) != len(mapping):
        raise ValidationError({'mapping': 'Majburiy maydonlarni takrorlanmagan ustunlarga moslang.'})
    result, seen_keys, seen_targets = [], set(), set()
    cls = SERIALIZERS[batch.entity]
    for number, row in enumerate(batch.rows, 2):
        raw = {field: row[batch.headers.index(header)] for field, header in mapping.items()}
        key = raw.pop('key', '')
        data = {k: v for k, v in raw.items() if v != ''}
        record = {'row': number, 'key': key, 'data': data, 'existing_id': None, 'fingerprint': None, 'errors': {}}
        try:
            if not key or len(key) > 120 or key in seen_keys:
                raise ValidationError({'key': 'Kalit bo‘sh, uzun yoki faylda takrorlangan.'})
            seen_keys.add(key)
            instance = find_existing(batch.entity, key, data, batch.organization)
            if instance:
                if instance.pk in seen_targets:
                    raise ValidationError({'key': 'Fayldagi ikki qator bir yozuvga mos keldi.'})
                seen_targets.add(instance.pk)
                record['existing_id'] = instance.pk
                record['fingerprint'] = fingerprint(instance, cls, request)
            serializer = cls(instance, data=data, partial=bool(instance), context={'request': request})
            serializer.is_valid(raise_exception=True)
        except ValidationError as exc:
            record['errors'] = exc.detail
        result.append(record)
    return result
