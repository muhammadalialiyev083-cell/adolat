# Backend consistency and deployment contract

## Architecture confirmed

The active frontend uses `/api/v1`, credentialed sessions and `/auth/csrf`. Render's root is `backend/` and its entrypoint is `bcms_backend.wsgi`. The technical requirements identify Django. FastAPI is retained as an alternative implementation; neither its database schema nor its migration history is interchangeable with Django's. Do not point both migration systems at the same database.

Canonical scientific code lives in `backend/bcms_domain`, inside Render's existing backend root. Django imports it directly. FastAPI installs the package through its requirements: run `pip install -r requirements.txt` **from `backend_fastapi/`** with the sibling `backend/` directory present. A FastAPI deployment must check out the whole repository (or install a built bcms-domain distribution); a backend_fastapi-only isolated root without that sibling is unsupported. The shared package imports no ORM or web framework; graph traversal uses the existing NetworkX dependency.

## Mathematical discrepancies resolved

| Dimension | Previous Django | Previous FastAPI | Canonical implementation |
|---|---|---|---|
| BIA choice | Latest revision | Smallest RTO | Latest active revision, ID tie-break |
| Impact B | Highest-horizon BIA weighted composite | Categorical criticality, dataset min-max | Django BIA model and 0.35/.25/.20/.20 weights |
| Urgency T | 1-min(1,RTO/72) | Inverse RTO, dataset min-max | Fixed 72h baseline |
| Risk R | (max score-1)/24 | Dataset min-max; .5 for constant dimension | Fixed 1–25 scale; range validation |
| Dependency D | Process ancestors/(N-1) | Count outgoing mandatory dependencies, dataset min-max | Distinct process ancestors/(N-1) |
| Missing BIA/risk | Imputed B/R and time priors | Categorical/default inputs and cohort normalization | Explicit Django legacy priors plus warnings |
| Ranking ties | Implicit query ordering | Implicit query ordering | Score descending, process ID ascending |
| Graph edges | depends-on | Reversed for failure traversal | depends-on everywhere; ancestors for failure impact |
| No traversal results | Zero | All organization processes | Zero confirmed impacts, coverage warnings |
| Strategy | Constrained minimum cost; missing cost default zero | Stored strategy list only | Shared validated constrained-cost decision |

No cohort min-max normalization remains. Adding an unrelated process cannot rescale B, T or R; D can change because its documented denominator is the number of active tenant processes. Four-decimal operand-first scoring may change the last decimal compared with the old Django unrounded intermediate calculation. Formula version 1.1 records this reproducibility choice. Existing FastAPI scores can change materially; consumers should regenerate them and must not compare old/new rankings as if the formula were unchanged.

## API compatibility

Django keeps its single-process priority object and organization ranking wrapper. FastAPI keeps `ranked_processes`, adding weights, parameters, warnings, formula version and explanation to each ranked object. The frontend's styling and navigation are preserved; simulation warnings are rendered explicitly. Upstream login/session fixes and initial-admin migration were incorporated unchanged.

Both strategy endpoints accept `{target_rto_hours,target_rpo_minutes,strategies:[...]}`. Django keeps legacy response names, including `recommended_strategy` and `OPTIMAL_FOUND`; additive fields clarify feasibility and limitations. Invalid strategy payloads return 400 in Django and 422 in FastAPI. FastAPI also preserves its legacy `{process_id,strategy_id?}` request: candidates are read from that tenant/process, targets from its latest BIA unless explicitly supplied; its `process_id` and `strategies` response fields remain. Evaluation never changes `is_selected`. Missing BIA/targets are a validation error. Historical stored zero-cost candidates require explicit confirmation through the supplied-candidate contract.

FastAPI now exposes `/auth/csrf`; signed-session unsafe requests require `X-CSRFToken`, and untrusted Origin headers are rejected. Login rotates the token. Non-browser session clients must fetch it before authenticated writes. This intentional security tightening aligns with the browser's existing CSRF header contract. Production cookies require HTTPS; test clients remain explicitly configured for local test mode.

## Reference verification

`backend/tests/test_backend_consistency.py` executes the same graph and numerical fixtures against actual Django and SQLAlchemy adapters in isolated databases. Coverage includes direct/transitive/cyclic/duplicate paths, isolated assets, incomplete graphs, foreign/deleted identifiers and tenant-scoped BIA/plan selection. Both adapters must produce the identical operands and score stored in `tests/scientific_reference.json`. Domain tests and both API suites exercise the shared strategy contract. See `TEST_RESULTS.md` for actual commands and counts.

Remaining limitations: soft-delete and tenant filters are enforced in affected services, but there is no database-level row security or complete audit of every legacy router. FastAPI remains an alternative requiring a deployment/security review before replacing the deployed Django service. No production deployment or production database access was performed.
