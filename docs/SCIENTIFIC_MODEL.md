# Canonical BCMS research model, version 1.1

The shared implementation is `backend/bcms_domain/`. Django is the production/reference backend: the Render service uses `backend/`, the browser requests Django's CSRF contract, and `TEXNIK_TOPSHIRIQ.md` specifies Django REST Framework. FastAPI remains an independently tested alternative, not a second service needed by Django.

## Inputs and normalization

`U = 0.40B + 0.25T + 0.20R + 0.15D`. These weights, BIA weights and the 72-hour planning horizon are baseline research assumptions. ISO 22301 does not prescribe them. All operands are in [0,1]. Output operands and the final score use four decimal places; the final score is calculated from the published operands so clients can reproduce the equation.

- **B:** use the highest-horizon impact observation of the latest active BIA revision (revision descending, ID descending). Financial normalization is `min(1, loss / organization.max_acceptable_loss)`. The loss scale must be positive; losses and time horizons must be finite and nonnegative. Operational, legal and reputational ordinal scores are integers 1–5, normalized as `(score-1)/4`. BIA composition is `0.35 financial + 0.25 operational + 0.20 legal + 0.20 reputational`. Highest horizon is the historical sampling rule; it need not be closest to MTPD, and is not proof that every impact dimension increases monotonically.
- **T:** `1-min(1,RTO/T_MAX)`, with baseline `T_MAX=72 hours`.
- **R:** maximum registered active process risk, normalized as `(score-1)/24`, where `score=likelihood*impact`. Both inputs must be integers 1–5. Baseline risk classes: 1–6 low, 7–14 medium, 15–25 high. Configured organizational classification thresholds remain sensitivity parameters; they do not change fixed risk normalization.
- **D:** count distinct active process ancestors of the process in the validated depends-on graph, divided by `N-1`; zero when `N<=1`. All registered edge criticalities are included, preserving the Django model. OPTIONAL edges therefore model potential propagation, not guaranteed failure; redundancy and conditional failover are not represented.

Records from other tenants and soft-deleted records are excluded. A dangling/deleted/foreign graph endpoint cannot act as a bridge between valid nodes. Duplicate edges collapse; cycles terminate safely and do not duplicate processes. IDs break equal-score ranking ties.

## Missing data and invalid data

For compatibility with the deployed Django model, missing BIA uses an explicitly warned prior: B=0.5 for HIGH/CRITICAL, otherwise B=0.2; RTO=24h and MTPD=48h. Missing risk uses the warned prior R=0.1. A BIA with no impact rows uses B=0 with a warning; this does not establish zero impact. An unregistered dependency contributes zero confirmed graph influence, with graph coverage warnings. These values are imputations, not measured organizational evidence. Invalid numerical inputs fail validation rather than being silently normalized into a valid-looking score.

`RTO<=MTPD` remains required. Backup interval greater than RPO produces an RPO-gap warning. Backup frequency alone cannot establish recovery compliance: restore success, replication lag, recoverability and operational evidence remain outside this rule.

## Cascade simulation

`PROCESS:A -> ASSET:B` means A depends on B. Failure of B affects its process ancestors, directly and transitively. A valid isolated asset yields zero confirmed process impacts. Empty/incomplete graphs and unavailable endpoints yield explicit warnings, never organization-wide fallback disruption or a claim of organizational safety. Unknown, foreign and deleted disrupted asset identifiers are rejected with the same generic message. The count represents confirmed registered paths, not a probability forecast.

Responses preserve historical fields and add `warnings`, `data_quality_status` (`INCOMPLETE` or `REGISTERED_GRAPH_ONLY`) and `simulation_status` (`CONFIRMED_IMPACT` or `NO_CONFIRMED_IMPACT`). Even REGISTERED_GRAPH_ONLY does not establish real-world completeness. Missing BIA breach targets use the warned legacy priors. BIA/plan lookups are tenant-scoped. Django additionally reports MTPD breaches; FastAPI's existing shape is retained.

## Recovery strategy decision

A complete candidate needs a name, estimated RTO, estimated RPO and explicitly supplied cost (`cost`, or `estimated_cost`). All must be finite and nonnegative. Feasible means estimated RTO <= target RTO **and** estimated RPO <= target RPO. Among feasible candidates minimize supplied estimated cost, using Decimal comparison before any legacy float serialization. `estimated_cost_exact` preserves its decimal representation. Equal costs are resolved by name, stable identifier and canonical serialized content, independently of input order.

Return feasible and rejected candidates, rejection reasons, compliance booleans, recommended candidate, estimated cost and assumptions. No feasible option gives `NO_FEASIBLE_OPTION`. `OPTIMAL_FOUND` remains only as a legacy status; the additive `decision_status=FEASIBLE_FOUND` and message mean **lowest-cost feasible recovery strategy under the specified RTO/RPO constraints**. This does not optimize joint resource allocation, capacities, dependency scheduling or uncertain recovery estimates. Currency and estimation horizon must be comparable. No cost is invented for missing input. Stored historical zero costs cannot reveal whether their old database default was used; FastAPI requires explicit candidate confirmation for them.

## Statistical methods and reproducibility

`kendall_tau` compares permutations of unique IDs: it is tau-a, with no score ties represented. For backward compatibility empty/singleton rank lists return 1 by agreement convention, not a statistical estimate. `kendall_tau_b` instead accepts paired numerical score vectors:

`tau_b = (C-D)/sqrt((C+D+T_x)(C+D+T_y))`.

Ties in both variables enter neither tie-only count. Constant vectors or fewer than two observations return `None` (JSON null), meaning undefined. Nonfinite values and incompatible lengths are rejected. Tests compare tied-score examples with SciPy; SciPy is a test dependency only.

Weight sensitivity perturbs each baseline weight by ±0.05 and proportionally renormalizes the other three without prematurely rounding weights. Ablation sets exactly one weight to zero and renormalizes the rest. Results expose normalized weights, tau-a on deterministic ID order and tau-b on actual scores. Rounding scores can itself create ties; the reported score vectors define those ties. T_MAX sweeps use 48/72/96h, and threshold sweeps vary low=5/6/7 and medium=13/14/15. These are parameter checks, not evidence that the baseline is optimal.

Run from repository root:

```bash
python scripts/run_scientific_experiments.py --output /tmp/bcms-experiments.json
cmp /tmp/bcms-experiments.json docs/experiments/reference_results.json
```

`tests/sensitivity_reference.json` is a fixed synthetic six-process operand dataset. `tests/scientific_reference.json` defines identical raw BIA/risk input for both ORM adapters: B=.62, T=.9444, R=.7917, D=1 and U=.7924. Generated experiment results are actual software output, not pilot observations, expert validation, causal evidence or a claim of scientific superiority.
