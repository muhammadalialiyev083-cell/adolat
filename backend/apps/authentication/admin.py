from django.contrib import admin
from apps.authentication.models import ExternalIdentity, IdentityProvider

# Operator Django admin only; tenant APIs cannot configure endpoints or secrets.
admin.site.register(IdentityProvider)
admin.site.register(ExternalIdentity)
