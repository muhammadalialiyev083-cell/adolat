"""Shared tenant boundary, validation, transactional writes and object policy."""

from decimal import Decimal

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction
from django.db.models.deletion import ProtectedError
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from apps.core.audit import record_audit

MANAGERS = {"ADMIN", "BCMS_MANAGER"}


def tenant_queryset(queryset, organization):
    names = {f.name for f in queryset.model._meta.fields}
    if "organization" in names:
        queryset = queryset.filter(organization=organization)
    elif "risk" in names:
        queryset = queryset.filter(risk__organization=organization, risk__is_deleted=False)
    elif "plan" in names:
        queryset = queryset.filter(plan__organization=organization, plan__is_deleted=False)
    if "is_deleted" in names:
        queryset = queryset.filter(is_deleted=False)
    return queryset


class TenantSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request:
            for field in fields.values():
                if (
                    isinstance(field, serializers.PrimaryKeyRelatedField)
                    and field.queryset is not None
                ):
                    field.queryset = tenant_queryset(field.queryset, request.user.organization)
        return fields

    def run_validation(self, data=serializers.empty):
        attrs = super().run_validation(data)
        if not isinstance(attrs, dict):
            return attrs
        model = self.Meta.model

        def value(key, default=None):
            return attrs.get(key, getattr(self.instance, key, default))

        errors = {}
        for field in model._meta.fields:
            if field.name not in attrs or attrs[field.name] is None:
                continue
            val = attrs[field.name]
            if (
                isinstance(field, (models.DecimalField, models.IntegerField))
                and not field.primary_key
            ):
                if not Decimal(str(val)).is_finite() or val < 0:
                    errors[field.name] = "Qiymat chekli va manfiy bo‘lmasligi kerak."
                if (
                    field.name
                    in {
                        "capacity",
                        "staff_required",
                        "required_staff",
                        "sequence",
                        "revision",
                        "rto_hours",
                        "mtpd_hours",
                        "estimated_rto_hours",
                        "actual_recovery_hours",
                        "max_acceptable_loss",
                    }
                    and val <= 0
                ):
                    errors[field.name] = "Qiymat noldan katta bo‘lishi kerak."
            if (
                field.name
                in {
                    "likelihood",
                    "impact",
                    "likelihood_residual",
                    "impact_residual",
                    "operational_score",
                    "legal_score",
                    "reputational_score",
                }
                and not 1 <= val <= 5
            ):
                errors[field.name] = "Ball 1 dan 5 gacha bo‘lishi kerak."
        request = self.context.get("request")
        if request and request.user.role == "PROCESS_OWNER":
            if model.__name__ == "BusinessProcess":
                if self.instance and self.instance.owner_id != request.user.id:
                    raise PermissionDenied("Faqat o‘zingiz mas’ul bo‘lgan jarayonni tahrirlang.")
                if "owner" in attrs and attrs["owner"] != request.user:
                    errors["owner"] = "Jarayon egasini almashtirishga ruxsat yo‘q."
            proc = value("process")
            if not proc and model.__name__ == "Exercise" and value("plan"):
                proc = value("plan").process
            if proc and proc.owner_id != request.user.id:
                raise PermissionDenied(
                    "Faqat o‘zingizga biriktirilgan jarayon uchun yozish mumkin."
                )
        if model.__name__ in {"ContinuityPlan", "BIAAssessment"}:
            locked = {"APPROVED", "PUBLISHED", "ARCHIVED"}
            if self.instance and self.instance.status in locked:
                raise ValidationError(
                    {"status": "Tasdiqlangan nusxa o‘zgarmaydi. Yangi versiya yarating."}
                )
            allowed = (
                {"DRAFT", "IN_REVIEW"}
                if model.__name__ == "ContinuityPlan"
                else {"DRAFT", "SUBMITTED", "REJECTED"}
            )
            if value("status", "DRAFT") not in allowed:
                errors["status"] = "Tasdiqlash faqat maxsus tasdiqlash amali orqali bajariladi."
        if model.__name__ == "BIAAssessment":
            from apps.bia.models import BIAAssessment

            process = value("process")
            if process and not self.instance and "revision" not in attrs:
                from django.db.models import Max

                attrs["revision"] = (
                    BIAAssessment.objects.filter(process=process).aggregate(v=Max("revision"))["v"]
                    or 0
                ) + 1
            if process:
                duplicates = BIAAssessment.objects.filter(
                    process=process, revision=value("revision", 1)
                )
                if self.instance:
                    duplicates = duplicates.exclude(pk=self.instance.pk)
                if duplicates.exists():
                    errors["revision"] = "Bu jarayon uchun versiya allaqachon mavjud."

            if (
                value("rto_hours") is not None
                and value("mtpd_hours") is not None
                and value("rto_hours") >= value("mtpd_hours")
            ):
                errors["rto_hours"] = "RTO MTPDdan qat’iy qisqa bo‘lishi kerak."
            weights = value("impact_weights", {})
            if weights:
                keys = {"financial", "operational", "legal", "reputational"}
                try:
                    valid = (
                        set(weights) == keys
                        and all(
                            not isinstance(v, bool)
                            and Decimal(str(v)).is_finite()
                            and 0 <= Decimal(str(v)) <= 1
                            for v in weights.values()
                        )
                        and abs(sum(Decimal(str(v)) for v in weights.values()) - 1)
                        < Decimal("0.000001")
                    )
                except (ValueError, TypeError, ArithmeticError):
                    valid = False
                if not valid:
                    errors["impact_weights"] = (
                        "To‘rtta mezon vazni 0..1 oralig‘ida, yig‘indisi 1 bo‘lsin."
                    )
            if attrs.get("recommended_values"):
                errors["recommended_values"] = (
                    "Tavsiyalar serverda hisoblanadi; qo‘lda kiritilmaydi."
                )
        if model.__name__ == "Risk":
            if (value("likelihood_residual") is None) != (value("impact_residual") is None):
                errors["likelihood_residual"] = "Qoldiq ehtimollik va ta’sir birgalikda kiritilsin."
        if model.__name__ == "Organization":
            if not 1 <= value("risk_low_threshold", 6) < value("risk_medium_threshold", 14) < 25:
                errors["risk_low_threshold"] = "Chegaralar: 1 ≤ past < o‘rta < 25."
            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            try:
                ZoneInfo(value("timezone", "Asia/Tashkent"))
            except (ZoneInfoNotFoundError, ValueError):
                errors["timezone"] = "IANA vaqt mintaqasini kiriting."
        if model.__name__ == "Dependency":
            from apps.processes.models import Asset, BusinessProcess

            org = (
                request.user.organization
                if request
                else getattr(self.instance, "organization", None)
            )
            for side in ("from", "to"):
                cls = BusinessProcess if value(side + "_type") == "PROCESS" else Asset
                if not cls.objects.filter(
                    pk=value(side + "_id"), organization=org, is_deleted=False
                ).exists():
                    errors[side + "_id"] = "Ushbu tashkilotda faol obyekt topilmadi."
            if value("from_type") == value("to_type") and value("from_id") == value("to_id"):
                errors["to_id"] = "Obyekt o‘ziga bog‘lana olmaydi."
        if model.__name__ == "Scenario":
            from apps.processes.models import Asset

            ids = value("disrupted_asset_ids", [])
            org = request.user.organization if request else None
            if (
                not isinstance(ids, list)
                or any(type(i) is not int or i <= 0 for i in ids)
                or len(ids) != len(set(ids))
                or Asset.objects.filter(organization=org, is_deleted=False, id__in=ids).count()
                != len(ids)
            ):
                errors["disrupted_asset_ids"] = (
                    "Faqat tashkilotning takrorlanmagan faol aktiv IDlari ruxsat etiladi."
                )
            options = value("recovery_options", [])
            from apps.plans.models import Strategy

            if (
                not isinstance(options, list)
                or any(type(i) is not int for i in options)
                or Strategy.objects.filter(
                    organization=org, is_deleted=False, id__in=options
                ).count()
                != len(set(options))
            ):
                errors["recovery_options"] = "Tiklash variantlari shu tashkilotga tegishli bo‘lsin."
        if model.__name__ in {"Strategy", "Scenario"}:
            from apps.engine.models import RecoveryResource

            requirements = value(
                "resource_requirements" if model.__name__ == "Strategy" else "available_resources",
                {},
            )
            valid = isinstance(requirements, dict)
            if valid:
                for key, count in requirements.items():
                    if (
                        not str(key).isdigit()
                        or type(count) is not int
                        or count < 0
                        or not RecoveryResource.objects.filter(
                            pk=key, organization=request.user.organization, is_deleted=False
                        ).exists()
                    ):
                        valid = False
            if not valid:
                errors[
                    "resource_requirements"
                    if model.__name__ == "Strategy"
                    else "available_resources"
                ] = "Resurs IDsi va manfiy bo‘lmagan butun miqdor kiriting."
        if model.__name__ == "Exercise":
            plan = value("plan")
            if plan and plan.status not in {"APPROVED", "PUBLISHED"}:
                errors["plan"] = "Mashq tasdiqlangan rejaga bog‘lansin."
        if errors:
            raise ValidationError(errors)
        return attrs


class DomainPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not u.is_authenticated:
            return False
        if not u.organization_id and not (
            u.is_superuser and view.basename == "organization" and view.action == "create"
        ):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        role = u.role
        if view.basename in {"user", "organization"}:
            return role == "ADMIN" or u.is_superuser
        if role in MANAGERS:
            return True
        if view.basename in {"risk", "control"} and role == "RISK_ANALYST":
            return True
        return role == "PROCESS_OWNER" and view.basename in {
            "process",
            "bia",
            "risk",
            "strategy",
            "plan",
            "exercise",
        }


class TenantViewSet(viewsets.ModelViewSet):
    permission_classes = [DomainPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = []
    ordering_fields = ["id"]
    filter_fields = ()

    def get_queryset(self):
        return tenant_queryset(
            self.serializer_class.Meta.model.objects.all(), self.request.user.organization
        )

    def filter_queryset(self, queryset):
        for field in self.filter_fields:
            raw = self.request.query_params.get(field)
            if raw is not None:
                try:
                    queryset = queryset.filter(**{field: raw})
                except (ValueError, DjangoValidationError):
                    raise ValidationError({field: "Filtr qiymati noto‘g‘ri."})
        params = self.request.query_params
        names = {field.name for field in queryset.model._meta.fields}
        if "created_at" in names:
            date_field = "exercise_date" if "exercise_date" in names else "created_at__date"
            for param, comparison in [("since", "gte"), ("until", "lte")]:
                if params.get(param):
                    date = serializers.DateField().run_validation(params[param])
                    queryset = queryset.filter(**{date_field + "__" + comparison: date})
        model = queryset.model.__name__
        if model == "Risk" and params.get("risk_class"):
            from django.db.models import F

            queryset = queryset.annotate(computed_score=F("likelihood") * F("impact"))
            cls = params["risk_class"]
            low = self.request.user.organization.risk_low_threshold
            medium = self.request.user.organization.risk_medium_threshold
            if cls == "high":
                queryset = queryset.filter(computed_score__gt=medium)
            elif cls == "medium":
                queryset = queryset.filter(computed_score__gt=low, computed_score__lte=medium)
            elif cls == "low":
                queryset = queryset.filter(computed_score__lte=low)
            else:
                raise ValidationError({"risk_class": "low, medium yoki high kiriting."})
        if model == "BIAAssessment" and params.get("rpo_gap") == "true":
            from django.db.models import F

            queryset = queryset.filter(
                backup_interval_minutes__gt=F("rpo_minutes"), process__data_recovery_applicable=True
            )
        if model == "ContinuityPlan":
            if params.get("approved") == "true":
                queryset = queryset.filter(status__in=["APPROVED", "PUBLISHED"])
            if params.get("overdue") == "true":
                from django.utils import timezone

                queryset = queryset.filter(
                    status__in=["APPROVED", "PUBLISHED"], review_due_date__lt=timezone.localdate()
                )
        if model == "Exercise" and params.get("open_findings") == "true":
            queryset = queryset.filter(findings_closed=False).exclude(findings="")
        return super().filter_queryset(queryset)

    def get_object(self):
        obj = super().get_object()
        if (
            self.request.method not in permissions.SAFE_METHODS
            and self.request.user.role == "PROCESS_OWNER"
        ):
            proc = (
                obj
                if obj.__class__.__name__ == "BusinessProcess"
                else getattr(obj, "process", getattr(getattr(obj, "plan", None), "process", None))
            )
            if proc is None or proc.owner_id != self.request.user.id:
                raise PermissionDenied("Bu jarayon uchun yozish huquqingiz yo‘q.")
        return obj

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def perform_create(self, serializer):
        names = {f.name for f in serializer.Meta.model._meta.fields}
        extra = {"organization": self.request.user.organization} if "organization" in names else {}
        if (
            serializer.Meta.model.__name__ == "BusinessProcess"
            and self.request.user.role == "PROCESS_OWNER"
        ):
            extra["owner"] = self.request.user
        obj = serializer.save(**extra)
        record_audit(
            self.request,
            action="CREATE",
            entity=obj.__class__.__name__,
            entity_id=obj.pk,
            after_state=serializer.data,
        )

    def perform_update(self, serializer):
        before = self.get_serializer(serializer.instance).data
        serializer.save()
        record_audit(
            self.request,
            action="UPDATE",
            entity=serializer.instance.__class__.__name__,
            entity_id=serializer.instance.pk,
            before_state=before,
            after_state=serializer.data,
        )

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.role == "PROCESS_OWNER":
            proc = (
                obj
                if obj.__class__.__name__ == "BusinessProcess"
                else getattr(obj, "process", getattr(getattr(obj, "plan", None), "process", None))
            )
            if proc is None or proc.owner_id != request.user.id:
                raise PermissionDenied("Faqat o‘zingiz mas’ul bo‘lgan yozuvni o‘chirish mumkin.")
        if getattr(obj, "status", None) in {"APPROVED", "PUBLISHED", "ARCHIVED"}:
            raise ValidationError("Tasdiqlangan nusxani o‘chirish mumkin emas.")
        if obj.__class__.__name__ == "Organization":
            raise ValidationError("Tashkilotni o‘chirish bu API orqali bajarilmaydi.")
        for relation in obj._meta.related_objects:
            if relation.on_delete != models.CASCADE and relation.on_delete != models.PROTECT:
                continue
            accessor = relation.get_accessor_name()
            related = getattr(obj, accessor)
            if hasattr(related, "all") and related.all().exists():
                return Response(
                    {"detail": "Obyektga bog‘liq yozuvlar mavjud. Avval ularni ko‘rib chiqing."},
                    status=409,
                )
        if obj.__class__.__name__ == "RecoveryResource":
            from apps.plans.models import Strategy

            if any(
                str(obj.pk) in strategy.resource_requirements
                for strategy in Strategy.objects.filter(
                    organization=request.user.organization, is_deleted=False
                )
            ):
                return Response(
                    {"detail": "Resurs tiklash strategiyasida ishlatilmoqda."}, status=409
                )
        if obj.__class__.__name__ in {"BusinessProcess", "Asset"}:
            from django.db.models import Q

            from apps.processes.models import Dependency

            typ = "PROCESS" if obj.__class__.__name__ == "BusinessProcess" else "ASSET"
            if (
                Dependency.objects.filter(organization=request.user.organization, is_deleted=False)
                .filter(Q(from_type=typ, from_id=obj.pk) | Q(to_type=typ, to_id=obj.pk))
                .exists()
            ):
                return Response(
                    {"detail": "Obyekt bog‘liqlik xaritasida ishlatilmoqda."}, status=409
                )
        if obj.__class__.__name__ in {"Asset", "RecoveryResource", "Strategy"}:
            from apps.simulation.models import Scenario

            for scenario in Scenario.objects.filter(
                organization=request.user.organization, is_deleted=False
            ):
                referenced = (
                    obj.pk in scenario.disrupted_asset_ids
                    if obj.__class__.__name__ == "Asset"
                    else str(obj.pk) in scenario.available_resources
                    if obj.__class__.__name__ == "RecoveryResource"
                    else obj.pk in scenario.recovery_options
                )
                if referenced:
                    return Response({"detail": "Obyekt faol ssenariyda ishlatilmoqda."}, status=409)
        before = self.get_serializer(obj).data
        try:
            if hasattr(obj, "soft_delete"):
                obj.soft_delete()
            else:
                obj.delete()
        except ProtectedError:
            return Response({"detail": "Bog‘liq yozuvlar mavjud."}, status=409)
        record_audit(
            request,
            action="DELETE",
            entity=obj.__class__.__name__,
            entity_id=before["id"],
            before_state=before,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
