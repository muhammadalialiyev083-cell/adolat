"""Explicit, idempotent synthetic university dataset. Never resets an account."""

import os

from apps.authentication.models import User
from apps.bia.models import BIAAssessment, BIAImpact
from apps.engine.models import RecoveryResource
from apps.organizations.models import Department, Organization, Service
from apps.plans.models import Strategy
from apps.processes.models import Asset, BusinessProcess, Dependency
from apps.risks.models import Control, Risk
from apps.simulation.models import Scenario
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = (
        "Alohida o‘quv universiteti DEMO ma’lumotlarini yuklaydi; BCMS_DEMO_PASSWORD talab etiladi."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError(
                "Demo ma’lumotlar faqat DEBUG=true bo‘lgan alohida muhitda yuklanadi."
            )
        password = os.environ.get("BCMS_DEMO_PASSWORD", "")
        try:
            validate_password(password)
        except ValidationError as exc:
            raise CommandError(
                "BCMS_DEMO_PASSWORD kuchli parol bo‘lsin: " + "; ".join(exc.messages)
            )
        name = "O‘quv universiteti · DEMO"
        if Organization.objects.filter(name=name, is_demo=False).exists():
            raise CommandError("Bu nomdagi haqiqiy tashkilotni o‘zgartirish mumkin emas.")
        org, _ = Organization.objects.get_or_create(
            name=name,
            defaults={
                "sector": "Oliy ta’lim · sun’iy to‘plam",
                "is_demo": True,
                "contact_details": "O‘quv aloqa markazi: demo@example.invalid",
                "recovery_budget": 50000000,
            },
        )
        department, _ = Department.objects.get_or_create(
            organization=org,
            name="Raqamli xizmatlar markazi",
            defaults={"head_name": "O‘quv mas’uli"},
        )
        users = {}
        for username, role in [
            ("demo_admin", "ADMIN"),
            ("demo_manager", "BCMS_MANAGER"),
            ("demo_owner", "PROCESS_OWNER"),
            ("demo_auditor", "AUDITOR"),
            ("demo_approver", "APPROVER"),
        ]:
            user = User.objects.filter(username=username).first()
            if user and user.organization_id != org.id:
                raise CommandError(f"{username} boshqa tashkilotga tegishli; hisob saqlandi.")
            if not user:
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    role=role,
                    organization=org,
                    department=department,
                    first_name="O‘quv",
                    last_name=role,
                )
            users[role] = user
        service, _ = Service.objects.get_or_create(
            organization=org,
            name="Raqamli ta’lim",
            defaults={"owner": users["BCMS_MANAGER"], "description": "DEMO universitet xizmati"},
        )
        resource, _ = RecoveryResource.objects.get_or_create(
            organization=org,
            name="Zaxira server quvvati",
            defaults={"capacity": 2, "kind": "EQUIPMENT"},
        )
        assets = []
        for asset_name, typ in [
            ("Ma’lumotlar bazasi", "DATABASE"),
            ("Elektr ta’minoti", "POWER"),
            ("Internet kanali", "NETWORK"),
        ]:
            asset, _ = Asset.objects.get_or_create(
                organization=org, name=asset_name, defaults={"type": typ, "owner": users["ADMIN"]}
            )
            assets.append(asset)
        for i, (title, rto, mtpd) in enumerate(
            [
                ("Elektron ta’lim", 4, 12),
                ("Talabalar hisoboti", 8, 24),
                ("Shartnoma to‘lovlari", 3, 10),
                ("Elektron kutubxona", 24, 72),
            ]
        ):
            process, _ = BusinessProcess.objects.get_or_create(
                organization=org,
                name=title,
                defaults={
                    "service": service,
                    "department": department,
                    "owner": users["PROCESS_OWNER"],
                    "criticality": "CRITICAL" if i in (0, 2) else "HIGH",
                    "description": "O‘quv universiteti uchun sun’iy jarayon",
                    "working_hours": "08:00–18:00",
                    "critical_periods": "Imtihon va qabul davri",
                },
            )
            Dependency.objects.get_or_create(
                organization=org,
                from_type="PROCESS",
                from_id=process.id,
                to_type="ASSET",
                to_id=assets[0].id,
            )
            bia, _ = BIAAssessment.objects.get_or_create(
                organization=org,
                process=process,
                revision=1,
                defaults={
                    "rto_hours": rto,
                    "mtpd_hours": mtpd,
                    "rationale": "O‘quv ekspert bahosi",
                    "data_source": "Sun’iy universitet to‘plami",
                    "rpo_minutes": 60,
                    "backup_interval_minutes": 120,
                },
            )
            for horizon in [1, 4, 12]:
                BIAImpact.objects.get_or_create(
                    bia=bia,
                    horizon_hours=horizon,
                    defaults={
                        "financial_loss": horizon * 1000000,
                        "operational_score": min(5, 1 + horizon // 3),
                        "legal_score": 3,
                        "reputational_score": 4,
                    },
                )
            risk, _ = Risk.objects.get_or_create(
                organization=org,
                process=process,
                threat="Server uskunasi nosozligi",
                defaults={
                    "asset": assets[0],
                    "likelihood": 4,
                    "impact": 5,
                    "owner": users["BCMS_MANAGER"],
                    "evidence": "Sun’iy ordinal baho",
                    "treatment": "Zaxira serverga o‘tish",
                },
            )
            Control.objects.get_or_create(
                risk=risk,
                title="Replika va backupni tekshirish",
                defaults={"status": "PLANNED", "owner": users["ADMIN"]},
            )
            Strategy.objects.get_or_create(
                organization=org,
                process=process,
                name="Zaxira infratuzilmadan tiklash",
                defaults={
                    "estimated_rto_hours": 1,
                    "estimated_rpo_minutes": 30,
                    "estimated_cost": 2000000,
                    "staff_required": 1,
                    "resource_requirements": {str(resource.id): 1},
                    "conditions": "Zaxira server va tiklash jamoasi mavjud.",
                },
            )
        for kind, title, failed in [
            ("SERVER", "Server nosozligi", [assets[0].id]),
            ("POWER", "Elektr uzilishi", [assets[1].id]),
            ("INTERNET", "Internet uzilishi", [assets[2].id]),
            ("MALWARE", "Zararli dastur sababli uzilish", [assets[0].id]),
            ("SUPPLIER", "Asosiy yetkazib beruvchi uzilishi", [assets[2].id]),
            ("COMBINED", "Birgalikdagi uzilish", [a.id for a in assets]),
        ]:
            Scenario.objects.get_or_create(
                organization=org,
                title=title,
                defaults={
                    "kind": kind,
                    "is_synthetic": True,
                    "disrupted_asset_ids": failed,
                    "estimated_outage_hours": 8,
                },
            )
        self.stdout.write(
            self.style.SUCCESS(
                "DEMO universitet tayyor. Hisoblar: demo_admin, demo_manager, demo_owner, demo_auditor, demo_approver. Mavjud parollar o‘zgartirilmadi."
            )
        )
