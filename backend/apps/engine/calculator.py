"""Django adapters for the shared, framework-independent research model."""
from decimal import Decimal
from bcms_domain import scientific as model
from bcms_domain import graph as domain_graph
from apps.processes.models import BusinessProcess, Asset, Dependency


class RiskCalculator:
    calculate_score = staticmethod(model.risk_score)
    @staticmethod
    def classify_risk(score, low_thresh=6, med_thresh=14):
        return model.classify_risk(score, low_thresh, med_thresh)
    normalize_risk = staticmethod(model.normalize_risk)


class BIAEvaluator:
    DEFAULT_WEIGHTS = model.BIA_WEIGHTS

    @classmethod
    def evaluate_impact_norm(cls, bia, max_acceptable_loss=Decimal('500000000'), weights=None):
        return model.impact_components(list(bia.impacts.values()), max_acceptable_loss, weights)


class DependencyAnalyzer:
    @staticmethod
    def build_graph(organization):
        return domain_graph.build_graph(
            list(BusinessProcess.objects.filter(organization=organization, is_deleted=False).values_list('id', flat=True)),
            list(Asset.objects.filter(organization=organization, is_deleted=False).values_list('id', flat=True)),
            Dependency.objects.filter(organization=organization, is_deleted=False).values())

    @classmethod
    def calculate_dependency_norm(cls, organization, process_id):
        graph = cls.build_graph(organization)
        return domain_graph.dependency_norm(graph, process_id, sum(n.startswith('PROCESS:') for n in graph))


class PriorityEngine:
    WEIGHTS = model.WEIGHTS
    T_MAX_HOURS = model.T_MAX

    @classmethod
    def calculate_priority(cls, process):
        org = process.organization
        bia = process.bia_assessments.filter(organization=org, is_deleted=False).order_by('-revision', '-id').first()
        fields = ('rto_hours', 'mtpd_hours', 'rpo_minutes', 'backup_interval_minutes')
        graph = DependencyAnalyzer.build_graph(org)
        result = model.priority(
            criticality=process.criticality, bia={f: getattr(bia, f) for f in fields} if bia else None,
            impacts=list(bia.impacts.values()) if bia else [], max_loss=org.max_acceptable_loss,
            risks=list(process.risks.filter(organization=org, is_deleted=False).values_list('likelihood', 'impact')),
            dependency_norm=domain_graph.dependency_norm(graph, process.id, sum(n.startswith('PROCESS:') for n in graph)),
            tmax=cls.T_MAX_HOURS)
        result['warnings'].extend(graph.graph['warnings'])
        return dict(process_id=process.id, process_name=process.name, **result)


class StrategyEvaluator:
    @staticmethod
    def evaluate_strategies(target_rto_hours, target_rpo_minutes, candidate_strategies):
        return model.evaluate_strategies(target_rto_hours, target_rpo_minutes, candidate_strategies)
