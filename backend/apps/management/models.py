from django.conf import settings
from django.db import models
from apps.core.models import BaseTenantModel


class Task(BaseTenantModel):
    STATUSES = ["OPEN", "IN_PROGRESS", "BLOCKED", "DONE", "CANCELLED"]
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entity_type = models.CharField(
        max_length=20,
        blank=True,
        choices=[(v, v) for v in ["PROCESS", "BIA", "PLAN", "RISK", "EXERCISE", "INCIDENT"]],
    )
    entity_id = models.PositiveBigIntegerField(null=True, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_tasks"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tasks"
    )
    priority = models.CharField(
        max_length=10,
        choices=[(v, v) for v in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]],
        default="MEDIUM",
    )
    status = models.CharField(max_length=20, choices=[(v, v) for v in STATUSES], default="OPEN")
    due_date = models.DateField(null=True, blank=True)
    completion_evidence = models.TextField(blank=True)
    resolution_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["due_date", "id"]
        indexes = [models.Index(fields=["organization", "status", "due_date"])]
