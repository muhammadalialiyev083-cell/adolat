from django.conf import settings
from django.db import models

from apps.core.models import BaseTenantModel


class RecoveryResource(BaseTenantModel):
    name = models.CharField(max_length=200)
    kind = models.CharField(
        max_length=20,
        choices=[("STAFF", "Mutaxassis"), ("EQUIPMENT", "Uskuna"), ("LOCATION", "Ish joyi")],
        default="STAFF",
    )
    capacity = models.PositiveIntegerField(default=1)
    available_from_minutes = models.PositiveIntegerField(default=0)
    unavailable_until_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["organization", "name"], name="unique_resource_name")
        ]
        constraints += [
            models.CheckConstraint(
                condition=models.Q(capacity__gte=1), name="resource_positive_capacity"
            )
        ]


class ScheduleRun(BaseTenantModel):
    algorithm_version = models.CharField(max_length=80, default="deterministic-list-v1")
    input_snapshot = models.JSONField(default=dict)
    results = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at"]
