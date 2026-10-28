import uuid
from django.conf import settings
from django.db import models


class MonitoringIntegration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    provider = models.CharField(
        max_length=40,
        default="alertmanager_hmac",
        choices=[("alertmanager_hmac", "Signed Alertmanager relay")],
    )
    secret_env = models.CharField(max_length=100)
    enabled = models.BooleanField(default=False)
    last_success_at = models.DateTimeField(null=True, blank=True)

    def clean(self):
        import re
        from django.core.exceptions import ValidationError

        if not re.fullmatch(r"[A-Z_][A-Z0-9_]{0,99}", self.secret_env):
            raise ValidationError("Invalid secret environment variable name.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class MonitoringDelivery(models.Model):
    integration = models.ForeignKey(MonitoringIntegration, on_delete=models.CASCADE)
    event_id = models.CharField(max_length=128)
    body_sha256 = models.CharField(max_length=64)
    received_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="RECEIVED")
    invalid_rows = models.JSONField(default=list)
    attempts = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["-received_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["integration", "event_id"], name="unique_monitor_delivery"
            )
        ]


class MonitoringAlert(models.Model):
    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    integration = models.ForeignKey(MonitoringIntegration, on_delete=models.CASCADE)
    delivery = models.ForeignKey(MonitoringDelivery, on_delete=models.PROTECT)
    event_key = models.CharField(max_length=64)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    severity = models.CharField(max_length=10)
    source_timestamp = models.DateTimeField()
    source_status = models.CharField(max_length=20)
    process = models.ForeignKey(
        "processes.BusinessProcess", null=True, blank=True, on_delete=models.PROTECT
    )
    asset = models.ForeignKey("processes.Asset", null=True, blank=True, on_delete=models.PROTECT)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    incident = models.ForeignKey(
        "incidents.Incident", null=True, blank=True, on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["integration", "event_key"], name="unique_normalized_alert"
            )
        ]
