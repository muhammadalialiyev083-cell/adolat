"""Freeze legacy approvals without inventing missing organization content."""

import json

from django.core.serializers.json import DjangoJSONEncoder
from django.db import migrations


def freeze(apps, schema_editor):
    Plan = apps.get_model("plans", "ContinuityPlan")
    Step = apps.get_model("plans", "PlanStep")
    for plan in Plan.objects.using(schema_editor.connection.alias).filter(
        status__in=["APPROVED", "PUBLISHED", "ARCHIVED"]
    ):
        if plan.snapshot:
            continue
        data = {
            field.name: getattr(plan, field.attname)
            for field in Plan._meta.fields
            if field.name != "snapshot"
        }
        data["organization_name"] = plan.organization.name
        data["process_name"] = plan.process.name
        data["approved_by_username"] = plan.approved_by.username if plan.approved_by_id else None
        data["steps"] = []
        for step in (
            Step.objects.using(schema_editor.connection.alias)
            .filter(plan_id=plan.pk)
            .order_by("sequence")
        ):
            data["steps"].append(
                {
                    "sequence": step.sequence,
                    "title": step.title,
                    "description": step.description,
                    "assigned_name": step.assigned_to.get_full_name()
                    if step.assigned_to_id and hasattr(step.assigned_to, "get_full_name")
                    else str(step.assigned_to_id or ""),
                    "expected_duration_minutes": step.expected_duration_minutes,
                }
            )
        data["legacy_snapshot"] = True
        Plan.objects.using(schema_editor.connection.alias).filter(pk=plan.pk).update(
            snapshot=json.loads(json.dumps(data, cls=DjangoJSONEncoder))
        )


class Migration(migrations.Migration):
    dependencies = [("plans", "0003_planstep_plan_step_positive_sequence_and_more")]
    operations = [migrations.RunPython(freeze, migrations.RunPython.noop)]
