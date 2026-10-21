import csv
import io

import networkx as nx
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import serializers, views
from rest_framework.response import Response

from apps.authentication.permissions import IsTenantMember
from apps.bia.models import BIAAssessment
from apps.core.audit import record_audit
from apps.plans.models import ContinuityPlan, Strategy
from apps.processes.models import Asset, BusinessProcess, Dependency
from apps.risks.models import Risk
from apps.simulation.models import Exercise


def org_objects(cls, org):
    qs = cls.objects.filter(organization=org)
    if hasattr(cls, "is_deleted"):
        qs = qs.filter(is_deleted=False)
    return qs


class OrganizationDashboardReportView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        org = request.user.organization
        processes = org_objects(BusinessProcess, org)
        risks = org_objects(Risk, org)
        plans = org_objects(ContinuityPlan, org)
        exercises = org_objects(Exercise, org)
        since = request.query_params.get("since")
        until = request.query_params.get("until")
        date_field = serializers.DateField()
        if since:
            since = date_field.run_validation(since)
        if until:
            until = date_field.run_validation(until)
        if since and until and since > until:
            raise serializers.ValidationError(
                {"since": "Boshlanish sanasi tugash sanasidan keyin bo‘lmasin."}
            )
        if since:
            risks, plans, exercises = (
                risks.filter(created_at__date__gte=since),
                plans.filter(created_at__date__gte=since),
                exercises.filter(exercise_date__gte=since),
            )
        if until:
            risks, plans, exercises = (
                risks.filter(created_at__date__lte=until),
                plans.filter(created_at__date__lte=until),
                exercises.filter(exercise_date__lte=until),
            )
        latest = {}
        for bia in (
            org_objects(BIAAssessment, org)
            .order_by("process_id", "-revision", "-id")
            .select_related("process")
        ):
            latest.setdefault(bia.process_id, bia)
        total = processes.count()
        published = plans.filter(status__in=["PUBLISHED", "APPROVED"])
        with_plan = set(published.values_list("process_id", flat=True))
        observed = exercises.exclude(planned_recovery_hours=None)
        observed_count = observed.count()
        met = sum(e.actual_recovery_hours <= e.planned_recovery_hours for e in observed)
        summary = {
            "total_processes": total,
            "critical_processes": processes.filter(criticality="CRITICAL").count(),
            "total_assets": org_objects(Asset, org).count(),
            "total_risks": risks.count(),
            "high_risks_count": sum(
                r.risk_score > (org.risk_medium_threshold if org else 14) for r in risks
            ),
            "unplanned_processes_count": processes.exclude(pk__in=with_plan).count(),
            "rpo_gap_count": sum(b.has_rpo_gap for b in latest.values()),
            "bia_covered_processes": len(latest),
            "bia_coverage_percent": round(100 * len(latest) / total, 1) if total else None,
            "approved_bias_count": sum(b.status == "APPROVED" for b in latest.values()),
            "published_plans_count": published.count(),
            "overdue_plans_count": published.filter(
                review_due_date__lt=timezone.localdate()
            ).count(),
            "completed_exercises_count": exercises.count(),
            "open_findings_count": exercises.filter(findings_closed=False)
            .exclude(findings="")
            .count(),
            "rto_observed_count": observed_count,
            "rto_met_count": met,
            "rto_compliance_percent": round(100 * met / observed_count, 1)
            if observed_count
            else None,
        }
        return Response(
            {
                "organization": org.name if org else "",
                "is_demo": org.is_demo if org else False,
                "summary": summary,
                "period": {
                    "since": since,
                    "until": until,
                    "inventory": "Joriy saqlangan yozuvlar; sanalar risk/reja yaratilishi va mashq sanasiga qo‘llanadi.",
                },
                "definitions": {
                    "bia_coverage_percent": "Eng so‘nggi BIA mavjud jarayonlar / jami jarayonlar × 100.",
                    "high_risks_count": "Ordinal ehtimollik × ta’sir tashkilotning o‘rta chegarasidan katta.",
                    "rto_compliance_percent": "Saqlangan RTOdan oshmagan kuzatilgan mashqlar / maqsadi ma’lum mashqlar × 100.",
                    "open_findings_count": "Kamchilik yozilgan va yopilmagan mashqlar soni.",
                    "rpo_gap_count": "Har jarayonning so‘nggi BIAida backup oralig‘i > RPO.",
                },
            }
        )


class WorkflowView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        org = request.user.organization
        procs = org_objects(BusinessProcess, org)
        ids = set(procs.values_list("id", flat=True))
        bias = org_objects(BIAAssessment, org)
        strategies = org_objects(Strategy, org)
        plans = org_objects(ContinuityPlan, org)
        approved = plans.filter(status__in=["APPROVED", "PUBLISHED"])
        from apps.engine.models import ScheduleRun

        last_run = org_objects(ScheduleRun, org).first()
        latest_bias = {}
        for bia in bias.order_by("process_id", "-revision", "-id"):
            latest_bias.setdefault(bia.process_id, bia)
        bia_complete = (
            bool(ids)
            and ids.issubset(latest_bias)
            and all(
                b.rationale.strip() and b.data_source.strip() and b.impacts.exists()
                for b in latest_bias.values()
            )
        )
        data = [
            (
                "organization",
                "Tashkilot",
                bool(
                    org
                    and org.contact_details
                    and org.departments.exists()
                    and org.services.exists()
                ),
                ["Tashkilot aloqalari, bo‘lim va xizmatni kiriting."],
            ),
            (
                "processes",
                "Jarayonlar",
                bool(ids)
                and not procs.filter(
                    Q(owner=None) | Q(department=None) | Q(description="")
                ).exists(),
                ["Jarayon nomi, tavsifi, bo‘limi va mas’ulini to‘ldiring."],
            ),
            (
                "dependencies",
                "Aktivlar va bog‘liqliklar",
                org_objects(Asset, org).exists() and org_objects(Dependency, org).exists(),
                ["Aktiv va aniq yo‘nalishli bog‘liqlik kiriting."],
            ),
            (
                "bia",
                "BIA",
                bia_complete,
                ["Har bir jarayon uchun BIA, vaqt bo‘yicha ta’sir, sabab va manbani kiriting."],
            ),
            (
                "risks",
                "Risklar",
                bool(ids)
                and ids.issubset(set(org_objects(Risk, org).values_list("process_id", flat=True))),
                ["Har bir jarayon riskini baholang."],
            ),
            (
                "strategies",
                "Strategiya",
                bool(ids) and ids.issubset(set(strategies.values_list("process_id", flat=True))),
                ["Har bir jarayon uchun tiklash variantini kiriting."],
            ),
            (
                "schedule",
                "Tiklash rejasi",
                bool(last_run and last_run.results.get("constrained", {}).get("feasible")),
                ["Resurs va budjet bilan bajariladigan jadval hisoblang."],
            ),
            (
                "approval",
                "Tasdiqlash",
                bool(ids) and ids.issubset(set(approved.values_list("process_id", flat=True))),
                ["Jarayonlar rejasini to‘ldirib, rahbariyatga tasdiqlating."],
            ),
            (
                "exercise",
                "Mashq",
                org_objects(Exercise, org).exists(),
                ["Tasdiqlangan reja bo‘yicha kuzatilgan mashq natijasini saqlang."],
            ),
        ]
        steps = [
            {"key": key, "label": label, "complete": bool(done), "missing": [] if done else missing}
            for key, label, done, missing in data
        ]
        return Response(
            {
                "steps": steps,
                "completed": sum(s["complete"] for s in steps),
                "total": len(steps),
                "saved": True,
            }
        )


class DependencyGraphView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        org = request.user.organization
        nodes = [
            {"id": f"{kind}:{obj.pk}", "label": obj.name, "type": kind, "object_id": obj.pk}
            for kind, cls in [("PROCESS", BusinessProcess), ("ASSET", Asset)]
            for obj in org_objects(cls, org)
        ]
        valid = {n["id"] for n in nodes}
        edges = [
            {
                "id": d.pk,
                "source": f"{d.from_type}:{d.from_id}",
                "target": f"{d.to_type}:{d.to_id}",
                "criticality": d.dependency_criticality,
            }
            for d in org_objects(Dependency, org)
        ]
        graph = nx.DiGraph()
        graph.add_nodes_from(valid)
        graph.add_edges_from(
            (e["source"], e["target"])
            for e in edges
            if e["source"] in valid and e["target"] in valid and e["criticality"] == "MANDATORY"
        )
        cycles = [sorted(c) for c in nx.strongly_connected_components(graph) if len(c) > 1]
        for n in nodes:
            n["affected_nodes"] = sorted(nx.ancestors(graph, n["id"]))
        return Response(
            {
                "nodes": nodes,
                "edges": edges,
                "cycles": cycles,
                "direction": "source targetga bog‘liq; target uzilsa source ta’sirlanadi.",
            }
        )


class ProcessCSVView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        from apps.processes.views import BusinessProcessViewSet

        # Reuse exactly the same search/filter/order behavior as the process list.
        view = BusinessProcessViewSet()
        view.request, view.format_kwarg = request, None
        queryset = view.filter_queryset(view.get_queryset())
        output = io.StringIO()
        writer = csv.writer(output)

        def safe(value):
            s = str(value or "")
            return "'" + s if s.lstrip().startswith(("=", "+", "-", "@", "\t", "\r", "\n")) else s

        writer.writerow(["ID", "Jarayon", "Xizmat", "Muhimlik", "Holat"])
        for p in queryset.select_related("service"):
            writer.writerow(
                [
                    p.pk,
                    safe(p.name),
                    safe(p.service.name),
                    safe(p.get_criticality_display()),
                    safe(p.get_status_display()),
                ]
            )
        record_audit(
            request, action="EXPORT", entity="BusinessProcess", after_state={"format": "CSV"}
        )
        response = HttpResponse(
            "\ufeff" + output.getvalue(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="jarayonlar.csv"'
        return response


class RiskMatrixView(views.APIView):
    permission_classes = [IsTenantMember]

    def get(self, request):
        matrix = [[0 for _ in range(5)] for _ in range(5)]
        for risk in org_objects(Risk, request.user.organization):
            matrix[risk.likelihood - 1][risk.impact - 1] += 1
        return Response(
            {
                "matrix": matrix,
                "definition": "Qator: ordinal ehtimollik 1–5. Ustun: ta’sir 1–5. Katak: saqlangan risklar soni.",
                "thresholds": {
                    "low": request.user.organization.risk_low_threshold,
                    "medium": request.user.organization.risk_medium_threshold,
                },
            }
        )
