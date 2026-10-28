"""Explicit synthetic fixture for an isolated browser/CI SQLite database only."""

import os
import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bcms_backend.settings")
    import django

    django.setup()
    from django.conf import settings
    from apps.authentication.models import User
    from apps.organizations.models import Organization, Service
    from apps.processes.models import BusinessProcess

    path = str(settings.DATABASES["default"]["NAME"])
    if (
        not settings.DEBUG
        or settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3"
        or not any(value in path for value in ("browser", "e2e", "ci"))
    ):
        raise SystemExit(
            "Refusing fixture outside an explicit isolated DEBUG SQLite browser/CI database."
        )
    password = os.environ["BCMS_E2E_PASSWORD"]
    org, _ = Organization.objects.get_or_create(
        name="SYNTHETIC browser fixture", defaults={"sector": "Synthetic test", "is_demo": True}
    )
    user, created = User.objects.get_or_create(
        username="browser_admin", defaults={"organization": org, "role": "ADMIN"}
    )
    if created:
        user.set_password(password)
        user.save()
    service, _ = Service.objects.get_or_create(organization=org, name="SYNTHETIC browser service")
    BusinessProcess.objects.get_or_create(
        organization=org,
        name="SYNTHETIC browser process",
        defaults={"service": service, "owner": user},
    )
    print("Synthetic browser fixture ready. Existing passwords were preserved.")


if __name__ == "__main__":
    main()
