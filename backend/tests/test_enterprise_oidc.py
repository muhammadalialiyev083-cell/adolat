import base64
import hashlib
import json
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
import requests
from joserfc import jwt
from joserfc.jwk import RSAKey
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient

from apps.authentication.models import ExternalIdentity, IdentityProvider, User
from apps.authentication.oidc import safe_destination
from apps.core.models import AuditLog
from apps.organizations.models import Organization

pytestmark = pytest.mark.django_db


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setenv("TEST_OIDC_CLIENT_SECRET", "synthetic-oidc-fixture-secret")
    org = Organization.objects.create(name="OIDC fixture", sector="Synthetic")
    user = User.objects.create_user(username="mapped", role="PROCESS_OWNER", organization=org)
    provider = IdentityProvider.objects.create(
        organization=org,
        slug="fixture",
        name="Fixture",
        issuer="https://identity.example",
        client_id="test-client",
        client_secret_env="TEST_OIDC_CLIENT_SECRET",
        redirect_uri="https://app.example/api/v1/auth/sso/fixture/callback",
        enabled=True,
        required_groups=["bcms"],
    )
    identity = ExternalIdentity.objects.create(
        provider=provider, user=user, subject="stable-subject"
    )
    return provider, user, identity


class ProviderTransport:
    """Mock HTTP transport with real RS256/JWK verification by Authlib."""

    def __init__(self):
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.private = private.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public = private.public_key().public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.signing_key = RSAKey.import_key(self.private)
        self.jwk = RSAKey.import_key(public, {"kid": "test-key"}).as_dict()
        self.nonce = None
        self.changes = {}
        self.token_body = None
        self.fail = False

    def send(self, prepared, **kwargs):
        assert kwargs.get("timeout") == 10
        assert kwargs.get("verify") is not False
        if self.fail:
            raise requests.ConnectionError("provider private error")
        path = urlsplit(prepared.url).path
        if path == "/.well-known/openid-configuration":
            data = {
                "issuer": "https://identity.example",
                "authorization_endpoint": "https://identity.example/authorize",
                "token_endpoint": "https://identity.example/token",
                "jwks_uri": "https://identity.example/jwks",
                "id_token_signing_alg_values_supported": ["RS256"],
                "token_endpoint_auth_methods_supported": ["client_secret_basic"],
            }
        elif path == "/token":
            self.token_body = parse_qs(prepared.body)
            claims = {
                "iss": "https://identity.example",
                "aud": "test-client",
                "sub": "stable-subject",
                "nonce": self.nonce,
                "exp": int(time.time()) + 300,
                "iat": int(time.time()),
                "groups": ["bcms"],
                "roles": ["ADMIN"],
                "email": "forged@example.invalid",
            }
            claims.update(self.changes)
            data = {
                "access_token": "synthetic-access-token",
                "token_type": "Bearer",
                "id_token": jwt.encode(
                    {"alg": "RS256", "kid": "test-key"}, claims, self.signing_key
                ),
            }
        elif path == "/jwks":
            data = {"keys": [self.jwk]}
        else:
            raise AssertionError(f"Unexpected OIDC request: {path}")
        response = requests.Response()
        response.status_code = 200
        response._content = json.dumps(data).encode()
        response.headers["Content-Type"] = "application/json"
        response.request = prepared
        return response


def begin(client, transport):
    result = client.post(
        "/api/v1/auth/sso/fixture/begin", {"return_to": "/#/bia-questionnaire"}, format="json"
    )
    assert result.status_code == 200, result.data
    params = parse_qs(urlsplit(result.data["authorization_url"]).query)
    transport.nonce = params["nonce"][0]
    assert params["code_challenge_method"] == ["S256"]
    return params


def finish(client, params):
    return client.get(
        "/api/v1/auth/sso/fixture/callback", {"code": "synthetic-code", "state": params["state"][0]}
    )


def test_real_signed_oidc_flow_pkce_mapping_logout_and_replay(provider):
    _, user, _ = provider
    client = APIClient()
    transport = ProviderTransport()
    with patch("requests.sessions.Session.send", side_effect=transport.send):
        params = begin(client, transport)
        result = finish(client, params)
    assert result.status_code == 302 and result.url == "/#/bia-questionnaire"
    verifier = transport.token_body["code_verifier"][0]
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    assert challenge == params["code_challenge"][0]
    assert client.get("/api/v1/auth/me").data["id"] == user.pk
    assert client.get("/api/v1/auth/me").data["role"] == "PROCESS_OWNER"
    assert "synthetic-access-token" not in str(dict(client.session))
    assert "synthetic-access-token" not in str(list(AuditLog.objects.values()))
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 403
    assert finish(client, params).url == "/?auth_error=sso_failed"


@pytest.mark.parametrize(
    "changes",
    [
        {"nonce": "invalid"},
        {"aud": "wrong"},
        {"iss": "https://attacker.example"},
        {"exp": 1},
        {"sub": "unknown"},
        {"groups": None},
    ],
)
def test_bad_claims_and_unknown_identity_fail(provider, changes):
    client, transport = APIClient(), ProviderTransport()
    with patch("requests.sessions.Session.send", side_effect=transport.send):
        params = begin(client, transport)
        transport.changes = changes
        assert finish(client, params).url == "/?auth_error=sso_failed"
    assert client.get("/api/v1/auth/me").status_code == 403


@pytest.mark.parametrize(
    "mode",
    [
        "disabled_user",
        "disabled_identity",
        "cross_tenant",
        "invalid_state",
        "expired_flow",
        "provider_outage",
    ],
)
def test_disabled_identity_invalid_state_and_outage(provider, mode):
    _, user, identity = provider
    client, transport = APIClient(), ProviderTransport()
    with patch("requests.sessions.Session.send", side_effect=transport.send):
        params = begin(client, transport)
        if mode == "disabled_user":
            User.objects.filter(pk=user.pk).update(is_active=False)
        elif mode == "disabled_identity":
            ExternalIdentity.objects.filter(pk=identity.pk).update(enabled=False)
        elif mode == "cross_tenant":
            other = Organization.objects.create(name="Foreign", sector="Synthetic")
            User.objects.filter(pk=user.pk).update(organization=other)
        elif mode == "invalid_state":
            params["state"] = ["forged"]
        elif mode == "expired_flow":
            session = client.session
            flow = session["oidc_flow"]
            flow["started"] = 1
            session["oidc_flow"] = flow
            session.save()
        else:
            transport.fail = True
        assert finish(client, params).url == "/?auth_error=sso_failed"
    assert client.get("/api/v1/auth/me").status_code == 403


def test_discovery_csrf_configuration_and_session_revocation(provider):
    provider_obj, _, identity = provider
    client = APIClient(enforce_csrf_checks=True)
    assert (
        client.post(
            "/api/v1/auth/sso/discover", {"organization_code": "fixture"}, format="json"
        ).status_code
        == 403
    )
    token = client.get("/api/v1/auth/csrf").data["csrfToken"]
    assert client.post(
        "/api/v1/auth/sso/discover",
        {"organization_code": "fixture"},
        format="json",
        HTTP_X_CSRFTOKEN=token,
    ).data == {"enabled": True, "provider": "fixture"}
    assert (
        client.post(
            "/api/v1/auth/sso/discover",
            {"organization_code": "unknown"},
            format="json",
            HTTP_X_CSRFTOKEN=token,
        ).data["enabled"]
        is False
    )
    transport = ProviderTransport()
    with patch("requests.sessions.Session.send", side_effect=transport.send):
        normal = APIClient()
        params = begin(normal, transport)
        assert finish(normal, params).url == "/#/bia-questionnaire"
    identity.enabled = False
    identity.save()
    assert normal.get("/api/v1/auth/me").status_code == 403
    provider_obj.enabled = False
    provider_obj.save()
    assert APIClient().post("/api/v1/auth/sso/fixture/begin", {}, format="json").status_code == 503


def test_provider_and_mapping_fail_closed(provider):
    provider_obj, user, _ = provider
    provider_obj.issuer = "http://identity.example"
    with pytest.raises(ValidationError):
        provider_obj.save()
    provider_obj.refresh_from_db()
    user.organization = Organization.objects.create(name="Foreign", sector="Synthetic")
    user.save()
    with pytest.raises(ValidationError):
        ExternalIdentity(provider=provider_obj, user=user, subject="another").save()


@pytest.mark.parametrize(
    "value",
    [
        "https://evil.example",
        "//evil.example",
        "/#//evil",
        "/#/plans?next=https://evil.example",
        None,
        "javascript:alert(1)",
    ],
)
def test_safe_return(value):
    assert safe_destination(value) == "/#/dashboard"
