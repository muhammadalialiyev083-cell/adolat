"""Canonical research assumptions; these weights are not prescribed by ISO 22301."""
from decimal import Decimal, InvalidOperation
import json
import math

WEIGHTS = dict(impact=0.40, urgency=0.25, risk=0.20, dependency=0.15)
BIA_WEIGHTS = dict(financial=0.35, operational=0.25, legal=0.20, reputational=0.20)
T_MAX = 72.0


def number(value, name, *, positive=False):
    try:
        if isinstance(value, bool):
            raise ValueError
        result = Decimal(str(value))
        if not result.is_finite() or result < 0 or (positive and result == 0):
            raise ValueError
        return result
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError(f"{name} must be a finite {'positive' if positive else 'nonnegative'} number") from None


def ordinal(value, name):
    result = number(value, name)
    if result != int(result) or not 1 <= result <= 5:
        raise ValueError(f"{name} must be an integer in 1..5")
    return int(result)


def risk_score(likelihood, impact):
    return ordinal(likelihood, 'likelihood') * ordinal(impact, 'impact')


def classify_risk(score, low=6, medium=14):
    if not 1 <= score <= 25 or not 1 <= low < medium < 25:
        raise ValueError('Invalid risk score or thresholds')
    return 'low' if score <= low else 'medium' if score <= medium else 'high'


def normalize_risk(score):
    score = number(score, 'risk_score')
    if not 1 <= score <= 25:
        raise ValueError('risk_score must be in 1..25')
    return float((score - 1) / 24)


def recovery_constraints(rto, mtpd, rpo, backup):
    rto, mtpd = number(rto, 'rto_hours'), number(mtpd, 'mtpd_hours')
    rpo, backup = number(rpo, 'rpo_minutes'), number(backup, 'backup_interval_minutes')
    if rto > mtpd:
        raise ValueError('RTO must not exceed MTPD')
    return backup > rpo


def impact_components(impacts, max_loss, weights=None):
    w = weights if weights is not None else BIA_WEIGHTS
    validate_weights(w, BIA_WEIGHTS)
    maximum = number(max_loss, 'max_acceptable_loss', positive=True)
    if not impacts:
        return dict(impact_norm=0.0, financial_norm=0.0, operational_norm=0.0,
                    legal_norm=0.0, reputational_norm=0.0, horizon_used=0.0)
    row = max(impacts, key=lambda i: number(i['horizon_hours'], 'horizon_hours'))
    parts = {'financial': min(1.0, float(number(row['financial_loss'], 'financial_loss') / maximum))}
    for key in ('operational', 'legal', 'reputational'):
        parts[key] = (ordinal(row[key + '_score'], key + '_score') - 1) / 4
    return {'impact_norm': round(sum(w[k] * parts[k] for k in w), 4),
            **{k + '_norm': round(v, 4) for k, v in parts.items()},
            'horizon_used': float(row['horizon_hours'])}


def validate_weights(weights, keys=WEIGHTS):
    if set(weights) != set(keys) or any(not math.isfinite(v) or v < 0 for v in weights.values()) or not math.isclose(sum(weights.values()), 1, abs_tol=1e-9):
        raise ValueError('Weights must be finite, nonnegative and sum to one')


def priority(*, criticality, bia, impacts, max_loss, risks, dependency_norm, tmax=T_MAX):
    warnings = []
    if bia is None:
        # Explicit legacy prior retained for API compatibility, not measured BIA evidence.
        impact = 0.5 if criticality in ('CRITICAL', 'HIGH') else 0.2
        rto, mtpd, gap = 24.0, 48.0, False
        warnings.append('MISSING_BIA: legacy prior B=0.5 (CRITICAL/HIGH), otherwise 0.2; RTO=24h, MTPD=48h; RPO unknown')
    else:
        gap = recovery_constraints(bia['rto_hours'], bia['mtpd_hours'], bia['rpo_minutes'], bia['backup_interval_minutes'])
        rto, mtpd = float(bia['rto_hours']), float(bia['mtpd_hours'])
        impact = impact_components(impacts, max_loss)['impact_norm']
        if not impacts:
            warnings.append('MISSING_BIA_IMPACTS: B=0 is an unmeasured placeholder, not evidence of no impact')
    risk = normalize_risk(max(risk_score(*r) for r in risks)) if risks else 0.1
    if not risks:
        warnings.append('MISSING_RISK: legacy prior R=0.1, not evidence of low risk')
    dep = float(number(dependency_norm, 'dependency_norm'))
    if dep > 1:
        raise ValueError('dependency_norm must be in [0,1]')
    urgency = 1 - min(1.0, rto / float(number(tmax, 'tmax', positive=True)))
    operands = dict(impact_norm=impact, urgency_norm=round(urgency, 4), risk_norm=round(risk, 4), dependency_norm=round(dep, 4))
    # Final score uses the published operands so its explanation reproduces the equation.
    score = round(sum(WEIGHTS[k] * operands[k + '_norm'] for k in WEIGHTS), 4)
    return dict(priority_score=score, operands=operands, weights=dict(WEIGHTS),
                parameters=dict(rto_hours=rto, mtpd_hours=mtpd, has_rpo_gap=gap),
                formula_version='1.1 (BCMS research hypothesis)', warnings=warnings,
                explanation='U = 0.40B + 0.25T + 0.20R + 0.15D; B: BIA impact, T: recovery urgency, R: maximum registered risk, D: registered process dependents')


def evaluate_strategies(target_rto, target_rpo, candidates):
    target_rto = number(target_rto, 'target_rto_hours')
    target_rpo = number(target_rpo, 'target_rpo_minutes')
    if not isinstance(candidates, list):
        raise ValueError('strategies must be a list')
    feasible, rejected = [], []
    for s in candidates:
        if not isinstance(s, dict) or not isinstance(s.get('name'), str) or not s['name'].strip():
            raise ValueError('Each strategy requires a nonempty name')
        rto = number(s.get('estimated_rto_hours'), 'estimated_rto_hours')
        rpo = number(s.get('estimated_rpo_minutes'), 'estimated_rpo_minutes')
        cost = number(s.get('cost', s.get('estimated_cost')), 'cost')
        rto_ok, rpo_ok = rto <= target_rto, rpo <= target_rpo
        row = {**s, 'cost_val': float(cost), 'estimated_cost': float(cost), 'estimated_cost_exact': str(cost),
               'rto_compliant': rto_ok, 'rpo_compliant': rpo_ok}
        reasons = ([] if rto_ok else ['RTO_EXCEEDED']) + ([] if rpo_ok else ['RPO_EXCEEDED'])
        if reasons:
            rejected.append({**row, 'reasons': reasons})
        else:
            feasible.append(row)
    # Decimal comparison avoids float rounding changing cost order; other keys break ties reproducibly.
    def key(s):
        return (Decimal(s['estimated_cost_exact']), s['name'],
                str(s.get('id', s.get('strategy_id', ''))), json.dumps(s, sort_keys=True, default=str))
    feasible.sort(key=key)
    rejected.sort(key=key)
    recommended = feasible[0] if feasible else None
    return dict(recommended_strategy=recommended,
                status='OPTIMAL_FOUND' if recommended else 'NO_FEASIBLE_OPTION',
                decision_status='FEASIBLE_FOUND' if recommended else 'NO_FEASIBLE_OPTION',
                message='Lowest-cost feasible recovery strategy under the specified RTO/RPO constraints.' if recommended else 'No candidate satisfies the specified RTO/RPO constraints.',
                feasible_candidates=feasible, rejected_candidates=rejected,
                estimated_cost=recommended['estimated_cost'] if recommended else None,
                observations=[f"{r['name']}: {', '.join(r['reasons'])}" for r in rejected],
                assumptions=['Costs share a currency and estimation horizon; estimates are supplied inputs.',
                             'Resource availability, joint dependencies and execution uncertainty are not optimized.',
                             'OPTIMAL_FOUND is a legacy compatibility label; it does not imply global optimality.'])
