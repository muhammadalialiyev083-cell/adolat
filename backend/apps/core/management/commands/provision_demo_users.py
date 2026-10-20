from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
from apps.organizations.models import Organization, Department
from apps.authentication.models import User


class Command(BaseCommand):
    help = "Provision/demo foydalanuvchilarni yaratadi yoki yangilaydi. Faqat ishga tushirishda avtomatik ishlamaydi."

    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get('ENVIRONMENT') == 'production' or os.environ.get('RENDER'):
            raise CommandError('Demo provisioning is restricted to explicit local development.')
        demo_password = os.environ.get('DEMO_USER_PASSWORD')
        if not demo_password or len(demo_password) < 12:
            raise CommandError('Set a local DEMO_USER_PASSWORD of at least 12 characters; never use production credentials.')
        org, _ = Organization.objects.get_or_create(
            name="Pilot Tashkilot",
            defaults={
                'sector': "Test",
                'timezone': "Asia/Tashkent",
                'max_acceptable_loss': 500000000.00,
            }
        )
        dept, _ = Department.objects.get_or_create(
            organization=org,
            name="Boshqarish",
            defaults={'head_name': "Admin"}
        )

        default_password = demo_password  # seed_demo_data bilan bir xil

        users = [
            {
                'username': 'admin',
                'role': User.ROLE_ADMIN,
                'email': 'admin@example.uz',
                'first_name': 'Admin',
                'last_name': 'User',
            },
            {
                'username': 'bcms_manager',
                'role': User.ROLE_BCMS_MANAGER,
                'email': 'manager@example.uz',
                'first_name': 'BCMS',
                'last_name': 'Manager',
            },
            {
                'username': 'director',
                'role': User.ROLE_APPROVER,
                'email': 'director@example.uz',
                'first_name': 'Director',
                'last_name': 'User',
            },
        ]

        for u in users:
            user, created = User.objects.get_or_create(
                username=u['username'],
                defaults={
                    'email': u['email'],
                    'role': u['role'],
                    'organization': org,
                    'department': dept,
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                }
            )
            user.set_password(default_password)
            user.is_active = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"{'Yaratildi' if created else 'Yangilandi'}: {user.username} ({user.role})"
                )
            )

        self.stdout.write(
            self.style.WARNING(
                "Local demo users prepared; password is never printed."
            )
        )
