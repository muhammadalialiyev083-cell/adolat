import uuid

from django.conf import settings
from django.db import models


class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    entity = models.CharField(max_length=30)
    headers = models.JSONField(default=list)
    rows = models.JSONField(default=list)
    preview = models.JSONField(default=list)
    mapping = models.JSONField(default=dict)
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    committed_at = models.DateTimeField(null=True)


class ImportIdentity(models.Model):
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    entity = models.CharField(max_length=30)
    external_key = models.CharField(max_length=120)
    object_id = models.PositiveBigIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['organization', 'entity', 'external_key'], name='unique_import_identity')]
