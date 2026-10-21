from getpass import getpass

from apps.authentication.models import User
from apps.organizations.models import Organization
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Yangi tashkilot va administrator; parol terminaldan yashirin so‘raladi."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--sector", required=True)
        parser.add_argument("--username", required=True)

    @transaction.atomic
    def handle(self, *args, **options):
        username = options["username"]
        if (
            User.objects.filter(username=username).exists()
            or Organization.objects.filter(name=options["name"]).exists()
        ):
            raise CommandError(
                "Hisob yoki tashkilot allaqachon mavjud; hech narsa o‘zgartirilmadi."
            )
        User._meta.get_field("username").run_validators(username)
        password = getpass("Yangi administrator paroli: ")
        if password != getpass("Parolni takrorlang: "):
            raise CommandError("Parollar mos emas.")
        try:
            validate_password(password, User(username=username))
        except ValidationError as exc:
            raise CommandError("; ".join(exc.messages))
        org = Organization.objects.create(name=options["name"], sector=options["sector"])
        User.objects.create_user(
            username=username, password=password, role="ADMIN", organization=org
        )
        self.stdout.write(self.style.SUCCESS("Tashkilot va administrator yaratildi."))
