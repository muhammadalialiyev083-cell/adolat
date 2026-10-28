from apps.authentication.views import (
    CSRFTokenView,
    LoginView,
    LogoutView,
    MeView,
    PasswordChangeView,
    UserViewSet,
)
from apps.authentication.oidc import BeginSSOView, CallbackSSOView, DiscoverSSOView
from apps.bia.views import BIAAssessmentViewSet
from apps.imports.views import (
    ImportCommitView,
    ImportPreviewView,
    ImportTemplateView,
    ImportUploadView,
)
from apps.management.views import ManagementDashboardView, TaskViewSet
from apps.incidents.views import IncidentViewSet
from apps.monitoring.views import AlertViewSet, DeliveryViewSet, IntegrationStatusView, WebhookView
from apps.core.views import AuditLogViewSet
from apps.engine.views import (
    EvaluateRiskAlgorithmView,
    EvaluateStrategyView,
    PriorityAnalysisView,
    RecoveryResourceViewSet,
    ScheduleRunViewSet,
)
from apps.organizations.views import (
    DepartmentViewSet,
    OrganizationViewSet,
    ServiceViewSet,
)
from apps.plans.views import ContinuityPlanViewSet, StrategyViewSet
from apps.processes.views import AssetViewSet, BusinessProcessViewSet, DependencyViewSet
from apps.reports.views import (
    DependencyGraphView,
    OrganizationDashboardReportView,
    ProcessCSVView,
    RiskMatrixView,
    WorkflowView,
)
from apps.risks.views import ControlViewSet, RiskViewSet
from apps.simulation.views import ExerciseViewSet, ScenarioViewSet, SimulationRunViewSet
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"incidents", IncidentViewSet, basename="incident")
router.register(r"monitoring-alerts", AlertViewSet, basename="monitoring-alert")
router.register(r"monitoring-deliveries", DeliveryViewSet, basename="monitoring-delivery")
router.register(r"simulation-runs", SimulationRunViewSet, basename="simulation-run")
# Core & Auth
router.register(r"resources", RecoveryResourceViewSet, basename="resource")
router.register(r"schedule-runs", ScheduleRunViewSet, basename="schedule-run")
router.register(r"users", UserViewSet, basename="user")
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"departments", DepartmentViewSet, basename="department")
router.register(r"services", ServiceViewSet, basename="service")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")

# Phase 2: Registry & Assessments
router.register(r"processes", BusinessProcessViewSet, basename="process")
router.register(r"assets", AssetViewSet, basename="asset")
router.register(r"dependencies", DependencyViewSet, basename="dependency")
router.register(r"bia", BIAAssessmentViewSet, basename="bia")
router.register(r"risks", RiskViewSet, basename="risk")
router.register(r"controls", ControlViewSet, basename="control")

# Phase 3 & 4: Plans, Scenarios, Exercises
router.register(r"strategies", StrategyViewSet, basename="strategy")
router.register(r"plans", ContinuityPlanViewSet, basename="plan")
router.register(r"scenarios", ScenarioViewSet, basename="scenario")
router.register(r"exercises", ExerciseViewSet, basename="exercise")


def home(request):
    from django.conf import settings
    from django.http import HttpResponse

    index = settings.BASE_DIR.parent / "frontend/dist/index.html"
    if index.exists():
        response = HttpResponse(
            index.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8"
        )
        response["Cache-Control"] = "no-cache"
        return response
    return JsonResponse({"status": "ok", "service": "RiskGuard BCMS API"})


def health(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        from django.db.migrations.executor import MigrationExecutor

        pending = MigrationExecutor(connection).migration_plan(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )
        return JsonResponse(
            {"status": "migrations_pending" if pending else "ready"}, status=503 if pending else 200
        )
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)


urlpatterns = [
    path("api/v1/monitoring/integrations", IntegrationStatusView.as_view()),
    path("api/v1/monitoring/webhook/<uuid:pk>", WebhookView.as_view()),
    path("api/v1/management", ManagementDashboardView.as_view()),
    path("api/v1/auth/sso/discover", DiscoverSSOView.as_view()),
    path("api/v1/auth/sso/<slug:slug>/begin", BeginSSOView.as_view()),
    path("api/v1/auth/sso/<slug:slug>/callback", CallbackSSOView.as_view()),
    path("api/v1/imports/upload", ImportUploadView.as_view()),
    path("api/v1/imports/<uuid:pk>/preview", ImportPreviewView.as_view()),
    path("api/v1/imports/<uuid:pk>/commit", ImportCommitView.as_view()),
    path("api/v1/imports/templates/<str:entity>", ImportTemplateView.as_view()),
    path("api/v1/reports/risk-matrix", RiskMatrixView.as_view()),
    path("healthz", health),
    path("readyz", ready),
    path("api/v1/auth/password", PasswordChangeView.as_view()),
    path("api/v1/workflow", WorkflowView.as_view()),
    path("api/v1/dependency-graph", DependencyGraphView.as_view()),
    path("api/v1/reports/processes.csv", ProcessCSVView.as_view()),
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    # Autentifikatsiya (FR-01)
    path("api/v1/auth/login", LoginView.as_view(), name="auth-login"),
    path("api/v1/auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("api/v1/auth/me", MeView.as_view(), name="auth-me"),
    path("api/v1/auth/csrf", CSRFTokenView.as_view(), name="auth-csrf"),
    # Hisoblash yadrosi tahlil endpointlari (FR-07, FR-08)
    path("api/v1/analyses/priority", PriorityAnalysisView.as_view(), name="analysis-priority"),
    path(
        "api/v1/analyses/evaluate-risk",
        EvaluateRiskAlgorithmView.as_view(),
        name="analysis-evaluate-risk",
    ),
    path(
        "api/v1/analyses/evaluate-strategy",
        EvaluateStrategyView.as_view(),
        name="analysis-evaluate-strategy",
    ),
    # Dashboard konsolidatsiyasi (FR-11)
    path(
        "api/v1/reports/organization",
        OrganizationDashboardReportView.as_view(),
        name="report-dashboard",
    ),
    # Resurs routerlari
    path("api/v1/", include(router.urls)),
]
