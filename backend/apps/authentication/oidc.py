"""Authorization Code + state + nonce + S256 PKCE, using Authlib's Django client."""

import os
import time
from urllib.parse import urlsplit

from authlib.integrations.django_client import OAuth
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.utils.crypto import get_random_string
from rest_framework import permissions, views
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.models import ExternalIdentity, IdentityProvider
from apps.authentication.throttling import LoginThrottle
from apps.core.audit import record_audit

# Only resource names, never arbitrary URLs or paths, are accepted after SSO.
RETURN_ROUTES = {
    "dashboard",
    "initial-setup",
    "menu",
    "catalog",
    "wizard",
    "organizations",
    "departments",
    "users",
    "services",
    "processes",
    "assets",
    "dependencies",
    "bia",
    "bia-questionnaire",
    "risks",
    "controls",
    "strategies",
    "resources",
    "schedule",
    "plans",
    "scenarios",
    "simulation-runs",
    "exercises",
    "audit-logs",
    "password",
    "imports",
    "management",
    "incidents",
    "integrations",
}


def safe_destination(value):
    if isinstance(value, str) and value.startswith("/#/") and value[3:] in RETURN_ROUTES:
        return value
    return "/#/dashboard"


def configured(provider):
    return bool(provider and provider.enabled and os.environ.get(provider.client_secret_env))


def client_for(provider):
    provider.full_clean()
    if not configured(provider):
        raise ValueError("Provider unavailable")
    oauth = OAuth()
    client = oauth.register(
        name=f"enterprise_{provider.pk}",
        client_id=provider.client_id,
        client_secret=os.environ[provider.client_secret_env],
        server_metadata_url=provider.issuer.rstrip("/") + "/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid profile",
            "code_challenge_method": "S256",
            "default_timeout": 10,
        },
    )
    metadata = client.load_server_metadata()
    if metadata.get("issuer") != provider.issuer:
        raise ValueError("Issuer mismatch")
    for key in ["authorization_endpoint", "token_endpoint", "jwks_uri"]:
        parsed = urlsplit(metadata.get(key, ""))
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise ValueError("Unsafe metadata")
    return client


class DiscoverSSOView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request):
        SessionAuthentication().enforce_csrf(request)
        code = request.data.get("organization_code")
        if not isinstance(code, str) or len(code) > 80:
            raise ValidationError({"organization_code": "Tashkilot kodini kiriting."})
        provider = IdentityProvider.objects.filter(slug=code, enabled=True).first()
        # No organization details, client IDs, issuer, mapping, or secrets disclosed.
        return Response(
            {
                "enabled": configured(provider),
                "provider": provider.slug if configured(provider) else None,
            }
        )


class BeginSSOView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [LoginThrottle]

    def post(self, request, slug):
        SessionAuthentication().enforce_csrf(request)
        provider = IdentityProvider.objects.filter(slug=slug, enabled=True).first()
        try:
            client = client_for(provider)
            # A fresh anonymous session prevents state carried over from another
            # identity. Authlib keeps state/nonce/verifier on the server session.
            request.session.flush()
            request.session["oidc_flow"] = {
                "provider": provider.pk,
                "started": time.time(),
                "return_to": safe_destination(request.data.get("return_to")),
            }
            response = client.authorize_redirect(
                request, provider.redirect_uri, nonce=get_random_string(32), prompt="select_account"
            )
            return Response({"authorization_url": response.url})
        except Exception:
            request.session.pop("oidc_flow", None)
            return Response(
                {"detail": "Korporativ kirish sozlamasi yoki xizmatini tekshirib bo‘lmadi."},
                status=503,
            )


class CallbackSSOView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, slug):
        flow = request.session.pop("oidc_flow", None)
        try:
            provider = IdentityProvider.objects.get(slug=slug, enabled=True)
            if (
                not isinstance(flow, dict)
                or flow.get("provider") != provider.pk
                or not 0 <= time.time() - flow.get("started", 0) <= 300
            ):
                raise ValueError("Expired or mismatched flow")
            token = client_for(provider).authorize_access_token(
                request,
                claims_options={
                    "iss": {"essential": True, "value": provider.issuer},
                    "aud": {"essential": True, "value": provider.client_id},
                },
                leeway=30,
            )
            claims = token.get("userinfo")
            if not claims or not isinstance(claims.get("sub"), str) or len(claims["sub"]) > 255:
                raise ValueError("No verified subject")
            groups = claims.get("groups")
            if provider.required_groups and (
                not isinstance(groups, list)
                or not all(isinstance(g, str) for g in groups)
                or not set(provider.required_groups).issubset(groups)
            ):
                raise ValueError("Required groups missing")
            identity = ExternalIdentity.objects.select_related("user").get(
                provider=provider, subject=claims["sub"], enabled=True
            )
            user = identity.user
            if not user.is_active or user.organization_id != provider.organization_id:
                raise ValueError("Identity unavailable")
            # Do not map privileges from email/domain or provider-controlled roles.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            request.session["enterprise_identity_id"] = identity.pk
            request.session["enterprise_provider_version"] = provider.updated_at.isoformat()
            record_audit(
                request,
                action="LOGIN",
                entity="ExternalIdentity",
                entity_id=identity.pk,
                actor=user,
                organization=user.organization,
                after_state={"method": "OIDC"},
            )
            return HttpResponseRedirect(safe_destination(flow.get("return_to")))
        except Exception:
            logout(request)
            record_audit(
                request,
                action="LOGIN_FAILED",
                entity="ExternalIdentity",
                after_state={"reason": "oidc_failed"},
            )
            # Provider response, code, tokens, subject and exception never reach UI/log.
            return HttpResponseRedirect("/?auth_error=sso_failed")


class EnterpriseSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        identity_id = request.session.get("enterprise_identity_id")
        if identity_id:
            valid = (
                request.user.is_authenticated
                and ExternalIdentity.objects.filter(
                    pk=identity_id,
                    enabled=True,
                    user_id=request.user.pk,
                    user__is_active=True,
                    provider__enabled=True,
                    provider__organization_id=request.user.organization_id,
                    provider__updated_at=request.session.get("enterprise_provider_version"),
                ).exists()
            )
            if not valid:
                logout(request)
        return self.get_response(request)
