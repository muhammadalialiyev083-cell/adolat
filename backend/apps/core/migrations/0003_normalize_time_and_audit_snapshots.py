from django.db import migrations, models


def normalize(apps, schema_editor):
    mappings = [
        (
            "bia",
            "BIAAssessment",
            {
                "rto_seconds": ("rto_hours", 3600),
                "mtpd_seconds": ("mtpd_hours", 3600),
                "rpo_seconds": ("rpo_minutes", 60),
                "backup_interval_seconds": ("backup_interval_minutes", 60),
            },
        ),
        (
            "plans",
            "Strategy",
            {
                "recovery_seconds": ("estimated_rto_hours", 3600),
                "rpo_seconds": ("estimated_rpo_minutes", 60),
            },
        ),
        ("simulation", "Scenario", {"outage_seconds": ("estimated_outage_hours", 3600)}),
        ("simulation", "Exercise", {"actual_recovery_seconds": ("actual_recovery_hours", 3600)}),
    ]
    for app, model, mapping in mappings:
        cls = apps.get_model(app, model)
        cls.objects.using(schema_editor.connection.alias).update(
            **{
                destination: models.F(source) * factor
                for destination, (source, factor) in mapping.items()
            }
        )
    # Old audit roles are deliberately left unknown; current roles are not historical proof.


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_auditlog_actor_role_snapshot_alter_auditlog_action"),
        ("bia", "0005_biaassessment_backup_interval_seconds_and_more"),
        ("plans", "0005_strategy_recovery_seconds_strategy_rpo_seconds"),
        ("simulation", "0004_exercise_actual_recovery_seconds_and_more"),
    ]
    operations = [migrations.RunPython(normalize, migrations.RunPython.noop)]
