import uuid
from django.conf import settings
from django.db import models
from apps.core.models import BaseTenantModel


class Incident(BaseTenantModel):
    STATUSES = [
        "DETECTED",
        "TRIAGED",
        "INVESTIGATING",
        "CONTAINED",
        "RECOVERY_IN_PROGRESS",
        "MONITORING",
        "RESOLVED",
        "CLOSED",
    ]
    TYPES = [
        "CYBERATTACK",
        "MALWARE",
        "DATA_BREACH",
        "NETWORK_OUTAGE",
        "SERVER_FAILURE",
        "POWER_FAILURE",
        "NATURAL_DISASTER",
        "SUPPLIER_OUTAGE",
        "HUMAN_ERROR",
        "OTHER",
    ]
    identifier = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    incident_type = models.CharField(
        max_length=30, choices=[(v, v) for v in TYPES], default="OTHER"
    )
    severity = models.CharField(
        max_length=10,
        choices=[(v, v) for v in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]],
        default="MEDIUM",
    )
    detected_at = models.DateTimeField()
    occurred_at = models.DateTimeField(null=True, blank=True)
    reporting_source = models.CharField(max_length=200, blank=True)
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reported_incidents"
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_incidents"
    )
    affected_processes = models.ManyToManyField("processes.BusinessProcess", blank=True)
    affected_assets = models.ManyToManyField("processes.Asset", blank=True)
    related_risks = models.ManyToManyField("risks.Risk", blank=True)
    related_plans = models.ManyToManyField("plans.ContinuityPlan", blank=True)
    status = models.CharField(max_length=30, choices=[(v, v) for v in STATUSES], default="DETECTED")
    business_impact = models.TextField(blank=True)
    containment_actions = models.TextField(blank=True)
    recovery_verification = models.TextField(blank=True)
    resolution_summary = models.TextField(blank=True)
    lessons_learned = models.TextField(blank=True)
    evidence = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-detected_at", "-id"]
        indexes = [models.Index(fields=["organization", "status", "severity"])]
