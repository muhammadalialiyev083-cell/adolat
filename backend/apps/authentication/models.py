from django.contrib.auth.models import AbstractUser
from django.db import models


class LoginRateBucket(models.Model):
    """Shared atomic fixed-window counters; no submitted identity or raw IP."""

    key = models.CharField(max_length=100, primary_key=True)
    attempts = models.PositiveIntegerField(default=0)
    expires_at = models.DateTimeField(db_index=True)


class User(AbstractUser):
    """
    FR-01: Foydalanuvchilar va rollar.
    Texnik topshiriqning 5-bo'limidagi 6 ta rolga muvofiq:
    ADMIN, BCMS_MANAGER, PROCESS_OWNER, RISK_ANALYST, APPROVER, AUDITOR.
    """

    ROLE_ADMIN = "ADMIN"
    ROLE_BCMS_MANAGER = "BCMS_MANAGER"
    ROLE_PROCESS_OWNER = "PROCESS_OWNER"
    ROLE_RISK_ANALYST = "RISK_ANALYST"
    ROLE_APPROVER = "APPROVER"
    ROLE_AUDITOR = "AUDITOR"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_BCMS_MANAGER, "BCMS menejeri"),
        (ROLE_PROCESS_OWNER, "Jarayon egasi"),
        (ROLE_RISK_ANALYST, "Risk tahlilchisi"),
        (ROLE_APPROVER, "Rahbariyat / Tasdiqlovchi"),
        (ROLE_AUDITOR, "Auditor / Kuzatuvchi"),
    ]

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
        help_text="Foydalanuvchi biriktirilgan tashkilot (Multi-tenant izolatsiyasi uchun)",
    )
    department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_PROCESS_OWNER,
        help_text="RBAC ruxsatlar modeli bo'yicha rol",
    )
    phone = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        org_name = self.organization.name if self.organization else "Superadmin"
        return f"{self.username} ({self.get_role_display()} - {org_name})"

    @property
    def is_org_admin(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_bcms_manager(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_BCMS_MANAGER] or self.is_superuser

    @property
    def is_approver(self):
        return self.role in [self.ROLE_ADMIN, self.ROLE_APPROVER] or self.is_superuser

    @property
    def is_auditor(self):
        return self.role == self.ROLE_AUDITOR


class IdentityProvider(models.Model):
    """Operator-reviewed provider configuration. Secret values live only in env."""

    organization = models.ForeignKey("organizations.Organization", on_delete=models.CASCADE)
    slug = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=150)
    issuer = models.URLField(max_length=500)
    client_id = models.CharField(max_length=200)
    client_secret_env = models.CharField(max_length=100)
    redirect_uri = models.URLField(max_length=500)
    enabled = models.BooleanField(default=False)
    required_groups = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        import re
        from urllib.parse import urlsplit
        from django.core.exceptions import ValidationError

        for value in [self.issuer, self.redirect_uri]:
            parsed = urlsplit(value)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.fragment
                or parsed.query
            ):
                raise ValidationError("OIDC endpoints require exact HTTPS URLs.")
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]{0,99}", self.client_secret_env):
            raise ValidationError("Invalid deployment secret variable name.")
        if not isinstance(self.required_groups, list) or any(
            not isinstance(g, str) or not g or len(g) > 200 for g in self.required_groups
        ):
            raise ValidationError("Required groups must be a list of nonempty strings.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class ExternalIdentity(models.Model):
    provider = models.ForeignKey(IdentityProvider, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["provider", "subject"], name="unique_oidc_subject"),
            models.UniqueConstraint(fields=["provider", "user"], name="unique_oidc_user"),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if (
            self.provider_id
            and self.user_id
            and self.provider.organization_id != self.user.organization_id
        ):
            raise ValidationError("Identity must belong to the provider organization.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
