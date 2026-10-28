import hashlib
import hmac
import json
import time
from pathlib import Path

import pytest
from rest_framework.test import APIClient

from apps.authentication.models import User
from apps.incidents.models import Incident
from apps.monitoring.models import MonitoringAlert, MonitoringDelivery, MonitoringIntegration
from apps.organizations.models import Organization, Service
from apps.processes.models import BusinessProcess

pytestmark = pytest.mark.django_db


@pytest.fixture
def operation():
    org = Organization.objects.create(name="Operations test", sector="Synthetic")
    admin = User.objects.create_user(username="opsadmin", organization=org, role="ADMIN")
    owner = User.objects.create_user(username="opsowner", organization=org, role="PROCESS_OWNER")
    auditor = User.objects.create_user(username="opsauditor", organization=org, role="AUDITOR")
    other = Organization.objects.create(name="Private other", sector="Synthetic")
    foreign = User.objects.create_user(username="foreign", organization=other, role="ADMIN")
    process = BusinessProcess.objects.create(
        organization=org,
        name="Process",
        owner=owner,
        service=Service.objects.create(organization=org, name="Service"),
    )
    client = APIClient()
    client.force_authenticate(admin)
    return client, admin, owner, auditor, foreign, process


def test_task_transitions_assignment_isolation_and_no_approval(operation):
    client, admin, owner, auditor, foreign, process = operation
    data = {
        "title": "Recover",
        "assigned_to": owner.pk,
        "entity_type": "PROCESS",
        "entity_id": process.pk,
        "due_date": "2026-01-01",
    }
    response = client.post("/api/v1/tasks/", data, format="json")
    assert response.status_code == 201, response.data
    ident = response.data["id"]
    assert response.data["created_by"] == admin.pk
    assert (
        client.patch(f"/api/v1/tasks/{ident}/", {"status": "DONE"}, format="json").status_code
        == 400
    )
    client.force_authenticate(owner)
    assert (
        client.patch(
            f"/api/v1/tasks/{ident}/", {"assigned_to": admin.pk}, format="json"
        ).status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/v1/tasks/{ident}/", {"status": "IN_PROGRESS"}, format="json"
        ).status_code
        == 200
    )
    assert (
        client.patch(f"/api/v1/tasks/{ident}/", {"status": "DONE"}, format="json").status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/v1/tasks/{ident}/",
            {
                "status": "DONE",
                "completion_evidence": "Observed restore record",
                "resolution_notes": "Verified by owner",
            },
            format="json",
        ).status_code
        == 200
    )
    assert (
        client.patch(f"/api/v1/tasks/{ident}/", {"status": "OPEN"}, format="json").status_code
        == 400
    )
    assert not process.bia_assessments.exists() and not process.continuity_plans.exists()
    client.force_authenticate(admin)
    assert (
        client.patch(f"/api/v1/tasks/{ident}/", {"status": "OPEN"}, format="json").status_code
        == 200
    )
    assert client.get("/api/v1/management").data["counts"]["overdue_tasks"] == 1
    data["assigned_to"] = foreign.pk
    assert client.post("/api/v1/tasks/", data, format="json").status_code == 400
    client.force_authenticate(foreign)
    assert client.get(f"/api/v1/tasks/{ident}/").status_code == 404
    client.force_authenticate(auditor)
    assert (
        client.patch(
            f"/api/v1/tasks/{ident}/", {"status": "IN_PROGRESS"}, format="json"
        ).status_code
        == 403
    )
    assert client.get("/api/v1/tasks/").data["count"] == 1


def test_incident_lifecycle_provenance_evidence_and_reopening(operation):
    client, admin, owner, _, _, process = operation
    response = client.post(
        "/api/v1/incidents/",
        {"title": "Synthetic outage", "owner": owner.pk, "affected_processes": [process.pk]},
        format="json",
    )
    assert response.status_code == 201, response.data
    ident = response.data["id"]
    detected = response.data["detected_at"]
    assert response.data["reporter"] == admin.pk
    assert (
        client.patch(f"/api/v1/incidents/{ident}/", {"status": "CLOSED"}, format="json").status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/v1/incidents/{ident}/", {"detected_at": "2020-01-01T00:00:00Z"}, format="json"
        ).status_code
        == 400
    )
    client.force_authenticate(owner)
    evidence = {
        "title": "Case log",
        "source_reference": "SYNTHETIC:case-1",
        "custody_note": "Received by test owner",
        "sha256": "a" * 64,
    }
    result = client.post(f"/api/v1/incidents/{ident}/evidence/", evidence, format="json")
    assert result.status_code == 200, result.data
    assert result.data["evidence"][0]["recorded_by"] == owner.pk
    assert result.data["evidence"][0]["verification"] == "OPERATOR_REFERENCE_ONLY"
    for status, extra in [
        ("TRIAGED", {"business_impact": "Observed interruption"}),
        ("INVESTIGATING", {}),
        ("CONTAINED", {}),
        ("RECOVERY_IN_PROGRESS", {"containment_actions": "Approved response performed"}),
        ("MONITORING", {}),
        (
            "RESOLVED",
            {"recovery_verification": "Observed health record", "resolution_summary": "Restored"},
        ),
        ("CLOSED", {"lessons_learned": "Update response checklist"}),
    ]:
        response = client.patch(
            f"/api/v1/incidents/{ident}/", {"status": status, **extra}, format="json"
        )
        assert response.status_code == 200, (status, response.data)
    assert response.data["detected_at"] == detected
    assert (
        client.post(f"/api/v1/incidents/{ident}/evidence/", evidence, format="json").status_code
        == 400
    )
    assert (
        client.patch(
            f"/api/v1/incidents/{ident}/",
            {"status": "TRIAGED", "reopen_reason": "Recurrence"},
            format="json",
        ).status_code
        == 400
    )
    client.force_authenticate(admin)
    assert (
        client.patch(
            f"/api/v1/incidents/{ident}/",
            {"status": "TRIAGED", "reopen_reason": "Observed recurrence"},
            format="json",
        ).status_code
        == 200
    )


def test_incident_many_relations_are_tenant_scoped(operation):
    client, _, _, _, foreign, process = operation
    foreign_process = BusinessProcess.objects.create(
        organization=foreign.organization,
        name="Secret process",
        service=Service.objects.create(organization=foreign.organization, name="Secret service"),
    )
    response = client.post(
        "/api/v1/incidents/",
        {
            "title": "Attempt",
            "owner": foreign.pk,
            "affected_processes": [process.pk, foreign_process.pk],
        },
        format="json",
    )
    assert response.status_code == 400 and "Secret process" not in str(response.data)
    assert Incident.objects.count() == 0


@pytest.fixture
def monitoring(operation, monkeypatch):
    client, admin, owner, auditor, foreign, process = operation
    monkeypatch.setenv("TEST_MONITOR_SECRET", "synthetic-monitoring-signature-key-12345")
    integration = MonitoringIntegration.objects.create(
        organization=admin.organization,
        name="Synthetic relay",
        secret_env="TEST_MONITOR_SECRET",
        enabled=True,
    )
    payload = {
        "alerts": [
            {
                "fingerprint": "synthetic-01",
                "startsAt": "2026-01-01T00:00:00Z",
                "status": "firing",
                "labels": {
                    "alertname": "Synthetic outage",
                    "severity": "critical",
                    "process_id": str(process.pk),
                },
                "annotations": {
                    "summary": "Synthetic fixture only",
                    "description": "Not a live operational incident",
                },
            }
        ]
    }
    return operation, integration, payload


def signed_send(integration, payload, event="event-1", timestamp=None, signature=None, raw=None):
    body = raw if raw is not None else json.dumps(payload).encode()
    stamp = str(timestamp or int(time.time()))
    sign = hmac.new(
        b"synthetic-monitoring-signature-key-12345",
        stamp.encode() + b"." + event.encode() + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    return APIClient().generic(
        "POST",
        f"/api/v1/monitoring/webhook/{integration.pk}",
        body,
        content_type="application/json",
        HTTP_X_RISKGUARD_EVENT_ID=event,
        HTTP_X_RISKGUARD_TIMESTAMP=stamp,
        HTTP_X_RISKGUARD_SIGNATURE=signature or sign,
    )


def test_signed_webhook_dedup_ack_and_incident_conversion(monitoring):
    (client, admin, _, _, _, _), integration, payload = monitoring
    assert signed_send(integration, payload).status_code == 202
    assert signed_send(integration, payload).data["duplicate"] is True
    assert signed_send(integration, payload, event="event-2").status_code == 202
    assert MonitoringAlert.objects.count() == 1
    integration.refresh_from_db()
    assert integration.last_success_at is not None
    alert = MonitoringAlert.objects.get()
    assert alert.organization_id == admin.organization_id
    assert client.post(f"/api/v1/monitoring-alerts/{alert.pk}/acknowledge/").status_code == 200
    response = client.post(f"/api/v1/monitoring-alerts/{alert.pk}/convert/")
    assert response.status_code == 200, response.data
    ident = response.data["incident"]
    assert client.post(f"/api/v1/monitoring-alerts/{alert.pk}/convert/").data["incident"] == ident
    assert Incident.objects.count() == 1
    assert Incident.objects.get().affected_processes.count() == 1
    assert "TEST_MONITOR_SECRET" not in str(client.get("/api/v1/monitoring/integrations").data)
    assert "synthetic-monitoring-signature-key" not in str(
        client.get("/api/v1/monitoring-deliveries/").data
    )


@pytest.mark.parametrize(
    "case",
    ["bad_signature", "stale", "conflict", "invalid_json", "too_large", "cross_tenant", "mixed"],
)
def test_monitoring_rejection_replay_and_partial_batches(monitoring, case):
    (_, _, _, _, foreign, _), integration, payload = monitoring
    if case == "bad_signature":
        assert signed_send(integration, payload, signature="bad").status_code == 403
    elif case == "stale":
        assert signed_send(integration, payload, timestamp=1).status_code == 403
    elif case == "conflict":
        assert signed_send(integration, payload).status_code == 202
        payload["extra"] = "changed"
        assert signed_send(integration, payload).status_code == 409
    elif case == "invalid_json":
        assert signed_send(integration, payload, raw=b"{bad").status_code == 400
        assert MonitoringDelivery.objects.get().status == "DEAD_LETTER"
    elif case == "too_large":
        assert signed_send(integration, payload, raw=b"a" * (256 * 1024 + 1)).status_code == 413
    else:
        foreign_process = BusinessProcess.objects.create(
            organization=foreign.organization,
            name="Private",
            service=Service.objects.create(organization=foreign.organization, name="Private"),
        )
        bad = json.loads(json.dumps(payload["alerts"][0]))
        bad["labels"]["process_id"] = str(foreign_process.pk)
        payload["alerts"] = [bad] if case == "cross_tenant" else [bad, payload["alerts"][0]]
        result = signed_send(integration, payload)
        assert result.data["invalid"] == 1
        assert result.data["status"] == ("DEAD_LETTER" if case == "cross_tenant" else "PARTIAL")
        assert MonitoringAlert.objects.count() == (0 if case == "cross_tenant" else 1)


def test_monitoring_tenant_roles_and_shared_rate_limit(monitoring):
    (client, _, _, auditor, foreign, _), integration, payload = monitoring
    assert signed_send(integration, payload).status_code == 202
    alert = MonitoringAlert.objects.get()
    client.force_authenticate(foreign)
    assert client.get(f"/api/v1/monitoring-alerts/{alert.pk}/").status_code == 404
    client.force_authenticate(auditor)
    assert client.post(f"/api/v1/monitoring-alerts/{alert.pk}/convert/").status_code == 403
    for index in range(59):
        assert signed_send(integration, payload, event=f"e-{index}").status_code == 202
    assert signed_send(integration, payload, event="limited").status_code == 429


def test_reference_fixture_is_passive_json():
    fixture = Path(__file__).parent / "fixtures/alertmanager.json"
    assert json.loads(fixture.read_text())["alerts"][0]["annotations"]["summary"].startswith(
        "SYNTHETIC"
    )
