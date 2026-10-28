import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone as dt_timezone

from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, serializers, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.authentication.models import LoginRateBucket, User
from apps.authentication.permissions import IsBCMSManagerRole, IsTenantMember
from apps.core.audit import record_audit
from apps.core.pagination import TenantPagination
from apps.incidents.models import Incident
from apps.monitoring.adapters import ADAPTERS
from apps.monitoring.models import MonitoringAlert, MonitoringDelivery, MonitoringIntegration


class WebhookView(views.APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []  # Authenticated by HMAC, never browser cookies.

    def post(self, request, pk):
        integration = MonitoringIntegration.objects.filter(pk=pk, enabled=True).first()
        secret = os.environ.get(integration.secret_env, "") if integration else ""
        if not integration or len(secret) < 32:
            return Response({"detail": "Manba tasdiqlanmadi."}, status=403)
        if int(request.META.get("CONTENT_LENGTH") or 0) > 256 * 1024:
            return Response({"detail": "Hajm chegarasi oshdi."}, status=413)
        raw = request.body
        event_id = request.headers.get("X-RiskGuard-Event-Id", "")
        timestamp = request.headers.get("X-RiskGuard-Timestamp", "")
        signature = request.headers.get("X-RiskGuard-Signature", "")
        if (
            len(raw) > 256 * 1024
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", event_id)
            or not re.fullmatch(r"\d{10}", timestamp)
            or abs(time.time() - int(timestamp)) > 300
        ):
            return Response({"detail": "Manba tasdiqlanmadi."}, status=403)
        expected = hmac.new(
            secret.encode(),
            timestamp.encode() + b"." + event_id.encode() + b"." + raw,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return Response({"detail": "Manba tasdiqlanmadi."}, status=403)
        window = int(time.time() // 60)
        key = f"monitor:{integration.pk}:{window}"
        LoginRateBucket.objects.get_or_create(
            key=key,
            defaults={"expires_at": datetime.fromtimestamp((window + 1) * 60, dt_timezone.utc)},
        )
        if not LoginRateBucket.objects.filter(pk=key, attempts__lt=60).update(
            attempts=F("attempts") + 1
        ):
            return Response(
                {"detail": "Hodisa yuborish chegarasiga yetildi."},
                status=429,
                headers={"Retry-After": "60"},
            )
        try:
            payload = json.loads(raw)
        except (ValueError, RecursionError):
            payload = None
        return self.ingest(integration, event_id, raw, payload)

    @transaction.atomic
    def ingest(self, integration, event_id, raw, payload):
        # Serialize event insertion/deduplication on this integration only.
        integration = MonitoringIntegration.objects.select_for_update().get(pk=integration.pk)
        digest = hashlib.sha256(raw).hexdigest()
        existing = MonitoringDelivery.objects.filter(
            integration=integration, event_id=event_id
        ).first()
        if existing:
            if existing.body_sha256 != digest:
                return Response({"detail": "Hodisa identifikatori ziddiyati."}, status=409)
            existing.attempts = min(existing.attempts + 1, 100)
            existing.save(update_fields=["attempts"])
            record_audit(
                action="UPDATE",
                entity="MonitoringDelivery",
                entity_id=existing.pk,
                organization=integration.organization,
                after_state={"duplicate": True, "attempts": existing.attempts},
            )
            return Response({"duplicate": True, "status": existing.status})
        delivery = MonitoringDelivery.objects.create(
            integration=integration, event_id=event_id, body_sha256=digest
        )
        alerts = payload.get("alerts") if isinstance(payload, dict) else None
        if not isinstance(alerts, list) or not 1 <= len(alerts) <= 50:
            delivery.status = "DEAD_LETTER"
            delivery.invalid_rows = [{"row": None, "code": "invalid_envelope"}]
            delivery.save()
            record_audit(
                action="UPDATE",
                entity="MonitoringDelivery",
                entity_id=delivery.pk,
                organization=integration.organization,
                after_state={"status": delivery.status, "error": "invalid_envelope"},
            )
            return Response({"status": delivery.status}, status=400)
        invalid = []
        for index, alert in enumerate(alerts):
            try:
                data = ADAPTERS[integration.provider].normalize(alert, integration.organization)
                MonitoringAlert.objects.get_or_create(
                    integration=integration,
                    event_key=data["event_key"],
                    defaults={
                        **data,
                        "organization": integration.organization,
                        "delivery": delivery,
                    },
                )
            except (ValidationError, ValueError, TypeError, KeyError):
                invalid.append({"row": index + 1, "code": "invalid_alert_or_relationship"})
        delivery.status = (
            "PROCESSED"
            if not invalid
            else ("DEAD_LETTER" if len(invalid) == len(alerts) else "PARTIAL")
        )
        delivery.invalid_rows = invalid
        delivery.save()
        if len(invalid) < len(alerts):
            integration.last_success_at = timezone.now()
            integration.save(update_fields=["last_success_at"])
        record_audit(
            action="CREATE",
            entity="MonitoringDelivery",
            entity_id=delivery.pk,
            organization=integration.organization,
            after_state={
                "status": delivery.status,
                "valid_alerts": len(alerts) - len(invalid),
                "invalid_alerts": len(invalid),
            },
        )
        return Response(
            {
                "status": delivery.status,
                "accepted": len(alerts) - len(invalid),
                "invalid": len(invalid),
            },
            status=202,
        )


class IntegrationStatusView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        return Response(
            [
                {
                    "id": str(i.pk),
                    "name": i.name,
                    "provider": i.provider,
                    "enabled": i.enabled,
                    "secret_configured": len(os.environ.get(i.secret_env, "")) >= 32,
                    "last_success_at": i.last_success_at,
                }
                for i in MonitoringIntegration.objects.filter(
                    organization=request.user.organization
                )
            ]
        )


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringAlert
        exclude = ["event_key"]
        read_only_fields = [f.name for f in MonitoringAlert._meta.fields]


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [IsTenantMember]
    pagination_class = TenantPagination

    def get_queryset(self):
        queryset = MonitoringAlert.objects.filter(organization=self.request.user.organization)
        if self.request.query_params.get("severity"):
            queryset = queryset.filter(severity=self.request.query_params["severity"])
        return queryset

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsBCMSManagerRole])
    @transaction.atomic
    def acknowledge(self, request, pk=None):
        alert = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if not alert.acknowledged_at:
            alert.acknowledged_by, alert.acknowledged_at = request.user, timezone.now()
            alert.save()
            record_audit(
                request,
                action="UPDATE",
                entity="MonitoringAlert",
                entity_id=alert.pk,
                after_state={"acknowledged": True},
            )
        return Response(self.get_serializer(alert).data)

    @action(detail=True, methods=["post"], permission_classes=[IsTenantMember, IsBCMSManagerRole])
    @transaction.atomic
    def convert(self, request, pk=None):
        alert = self.get_queryset().select_for_update().get(pk=self.get_object().pk)
        if not alert.incident_id:
            owner_id = serializers.IntegerField(min_value=1).run_validation(
                request.data.get("owner", request.user.pk)
            )
            owner = get_object_or_404(
                User,
                pk=owner_id,
                organization=request.user.organization,
                is_active=True,
            )
            incident = Incident.objects.create(
                organization=request.user.organization,
                title=alert.title,
                description=alert.description,
                detected_at=alert.source_timestamp,
                reporting_source=alert.integration.name,
                reporter=request.user,
                owner=owner,
                severity=alert.severity,
            )
            if alert.process_id:
                incident.affected_processes.add(alert.process)
            if alert.asset_id:
                incident.affected_assets.add(alert.asset)
            alert.incident = incident
            alert.save()
            record_audit(
                request,
                action="CREATE",
                entity="Incident",
                entity_id=incident.pk,
                after_state={"source_alert_id": alert.pk},
            )
        return Response(self.get_serializer(alert).data)


class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = MonitoringDelivery
        fields = [
            "id",
            "integration",
            "event_id",
            "received_at",
            "status",
            "invalid_rows",
            "attempts",
        ]


class DeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DeliverySerializer
    permission_classes = [IsTenantMember]
    pagination_class = TenantPagination

    def get_queryset(self):
        return MonitoringDelivery.objects.filter(
            integration__organization=self.request.user.organization
        )
