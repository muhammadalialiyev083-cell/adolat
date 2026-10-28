from django.core.management.base import BaseCommand, CommandError
from apps.authentication.models import ExternalIdentity, IdentityProvider, User
from apps.core.audit import record_audit


class Command(BaseCommand):
    help = "Operator-reviewed stable subject mapping. Never provisions users or grants roles."

    def add_arguments(self, parser):
        parser.add_argument("--provider", required=True)
        parser.add_argument("--username", required=True)
        parser.add_argument("--subject", required=True)

    def handle(self, *args, **options):
        try:
            provider = IdentityProvider.objects.get(slug=options["provider"])
            user = User.objects.get(
                username=options["username"], organization=provider.organization, is_active=True
            )
            identity, created = ExternalIdentity.objects.get_or_create(
                provider=provider, subject=options["subject"], defaults={"user": user}
            )
            if identity.user_id != user.pk:
                raise CommandError("Subject already linked. Review mapping before changing it.")
            record_audit(
                action="CREATE" if created else "UPDATE",
                entity="ExternalIdentity",
                entity_id=identity.pk,
                organization=provider.organization,
                after_state={"mapping_reviewed": True, "user_id": user.pk},
            )
        except (IdentityProvider.DoesNotExist, User.DoesNotExist):
            raise CommandError("Provider or active tenant user unavailable.") from None
        self.stdout.write("Identity mapping reviewed; no privileges changed.")
