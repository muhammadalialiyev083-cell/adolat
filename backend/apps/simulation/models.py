from decimal import Decimal

from django.db import models

from apps.core.models import BaseTenantModel
from apps.plans.models import ContinuityPlan


class Scenario(BaseTenantModel):
    """
    FR-10: Nosozlik / Falokat ssenariysi.
    Tahdid, ishdan chiqqan aktivlar ro'yxati va taxminiy uzilish davomiyligi.
    """

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    kind = models.CharField(
        max_length=30,
        choices=[
            ("SERVER", "Server nosozligi"),
            ("POWER", "Elektr uzilishi"),
            ("INTERNET", "Internet uzilishi"),
            ("MALWARE", "Zararli dastur"),
            ("SUPPLIER", "Yetkazib beruvchi uzilishi"),
            ("COMBINED", "Bir nechta uzilish"),
        ],
        default="SERVER",
    )
    is_synthetic = models.BooleanField(default=True)
    event_time = models.DateTimeField(null=True, blank=True)
    available_resources = models.JSONField(default=dict, blank=True)
    recovery_options = models.JSONField(default=list, blank=True)
    disrupted_asset_ids = models.JSONField(
        default=list, help_text="Ishdan chiqqan aktivlar ID lari [1, 2, ...]"
    )
    estimated_outage_hours = models.DecimalField(max_digits=6, decimal_places=2, default=8.0)

    outage_seconds = models.PositiveBigIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} (Outage: {self.estimated_outage_hours}h)"

    def save(self, *args, **kwargs):
        self.outage_seconds = int(Decimal(str(self.estimated_outage_hours)) * 3600)
        super().save(*args, **kwargs)


class Exercise(BaseTenantModel):
    """
    FR-13: Mashqlar va sinovlar (BCP test).
    Mashq sanasi, real tiklash vaqti va kamchiliklar xulosasi.
    """

    OUTCOME_CHOICES = [
        ("SUCCESS", "Muvaffaqiyatli"),
        ("PARTIAL", "Qisman muvaffaqiyatli"),
        ("FAILED", "Muvaffaqiyatsiz"),
    ]

    plan = models.ForeignKey(ContinuityPlan, on_delete=models.CASCADE, related_name="exercises")
    scenario = models.ForeignKey(
        Scenario, on_delete=models.SET_NULL, null=True, blank=True, related_name="exercises"
    )
    exercise_date = models.DateField()
    actual_recovery_hours = models.DecimalField(max_digits=6, decimal_places=2)
    outcome = models.CharField(max_length=20, choices=OUTCOME_CHOICES, default="SUCCESS")
    resource_shortages = models.TextField(blank=True)
    unfinished_tasks = models.TextField(blank=True)
    improvement_actions = models.TextField(blank=True)
    findings_closed = models.BooleanField(default=False)
    is_synthetic = models.BooleanField(default=True)
    planned_recovery_hours = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    findings = models.TextField(blank=True, help_text="Aniqlangan kamchiliklar va takliflar")

    actual_recovery_seconds = models.PositiveBigIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-exercise_date"]

    def __str__(self):
        return f"{self.plan.title} Mashq ({self.exercise_date}): {self.get_outcome_display()}"

    def save(self, *args, **kwargs):
        self.actual_recovery_seconds = int(Decimal(str(self.actual_recovery_hours)) * 3600)
        super().save(*args, **kwargs)


class SimulationRun(BaseTenantModel):
    scenario = models.ForeignKey(Scenario, on_delete=models.PROTECT, related_name="runs")
    algorithm_version = models.CharField(max_length=80, default="cascade-and-list-v1")
    input_snapshot = models.JSONField(default=dict)
    results = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]
