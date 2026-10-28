import hashlib
from abc import ABC, abstractmethod
from django.utils import timezone
from rest_framework import serializers
from apps.processes.models import Asset, BusinessProcess


class MonitoringAdapter(ABC):
    @abstractmethod
    def normalize(self, alert, organization):
        """Return bounded normalized domain fields; never trust a tenant in data."""


class AlertmanagerAdapter(MonitoringAdapter):
    def normalize(self, alert, organization):
        if not isinstance(alert, dict) or not isinstance(alert.get("labels"), dict):
            raise serializers.ValidationError("invalid_schema")
        labels = alert["labels"]
        annotations = alert.get("annotations", {})
        if not isinstance(annotations, dict):
            raise serializers.ValidationError("invalid_schema")
        timestamp = serializers.DateTimeField().run_validation(alert.get("startsAt"))
        if timezone.is_naive(timestamp) or timestamp > timezone.now():
            raise serializers.ValidationError("invalid_timestamp")
        status = serializers.ChoiceField(choices=["firing", "resolved"]).run_validation(
            alert.get("status")
        )
        fingerprint = serializers.CharField(max_length=128).run_validation(alert.get("fingerprint"))
        title = serializers.CharField(max_length=255).run_validation(
            annotations.get("summary") or labels.get("alertname")
        )
        description = serializers.CharField(max_length=4000, allow_blank=True).run_validation(
            annotations.get("description", "")
        )
        severity = serializers.ChoiceField(
            choices=["info", "warning", "error", "critical"]
        ).run_validation(labels.get("severity", "warning"))
        data = {
            "title": title,
            "description": description,
            "severity": {
                "info": "LOW",
                "warning": "MEDIUM",
                "error": "HIGH",
                "critical": "CRITICAL",
            }[severity],
            "source_timestamp": timestamp,
            "source_status": status,
            "event_key": hashlib.sha256(
                f"{fingerprint}:{timestamp.isoformat()}:{status}".encode()
            ).hexdigest(),
        }
        for key, model in [("process", BusinessProcess), ("asset", Asset)]:
            raw = labels.get(key + "_id")
            data[key] = None
            if raw is not None:
                ident = serializers.IntegerField(min_value=1).run_validation(raw)
                obj = model.objects.filter(
                    pk=ident, organization=organization, is_deleted=False
                ).first()
                if not obj:
                    raise serializers.ValidationError("invalid_relationship")
                data[key] = obj
        return data


ADAPTERS = {"alertmanager_hmac": AlertmanagerAdapter()}
