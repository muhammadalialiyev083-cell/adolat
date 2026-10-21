# AGENTS.md · RiskGuard BCMS Designer

Maintain the existing Django modular monolith (`backend/`) and React/TS/Vite
frontend (`frontend/`). `backend_fastapi/` is historical and is not the active API.
See README and docs/PROGRESS.md for current verified state. Never reset user data.

## Commands

Use Python 3.12 and an isolated virtual environment. Install
`backend/requirements-dev.txt`. Configure `.env` from the empty `.env.example`;
local `DEBUG=true`, generated SECRET_KEY, explicit ALLOWED_HOSTS. Production
requires PostgreSQL, SECRET_KEY, DEBUG=false and exact origins.

- `cd backend && python manage.py check && python -m pytest`
- `cd backend && python manage.py makemigrations --check --dry-run`
- `cd frontend && npm run lint && npm run typecheck && npm test && npm run build`
- `python -m ruff check backend/apps backend/bcms_backend backend/tests`
- `bash scripts/check.sh` from repo root with environment configured.
- Explicit local demo: `python manage.py seed_demo_data` with BCMS_DEMO_PASSWORD;
  never production, never reset existing passwords. No shared default password.
- First real organization: interactive `bootstrap_organization` command.

Django can serve frontend/dist through WhiteNoise. Run npm build after UI edits.
Vite dev proxies /api to 127.0.0.1:8000. Auth/analysis/report/workflow paths lack a
trailing slash; router resources/actions require it. Lists are paginated;
page_size defaults to 20, maximum 100. Server-side search/order/filter contract is
in each viewset. Hash routes preserve the current workspace page.

## Invariants

Session + CSRF authentication; no Basic auth or frontend-stored tokens. All tenant
relations use TenantSerializer. TenantViewSet enforces DomainPermission, owner
policy, atomic writes, auditing and protected deletion. Cross-tenant IDs return
404. Even superusers stay in their organization for ordinary API resources.

RTO < MTPD. Risk ordinal score = likelihood × impact, 1..25. Priority weights
0.40/0.25/0.20/0.15 stay explicit; missing evidence returns null. Canonical time
fields are integer seconds; compatible hour/minute API fields remain.

Dependency from → to means from depends on to. Mandatory cycles must not yield a
successful schedule. ScheduleRun stores identical A/B inputs, constraints and
algorithm version. No mathematical optimality claim for the scheduling heuristic.

Published/approved/archive plan content is immutable through the API. Export
uses snapshot; editing creates a new draft. Latest BIA must be approved before
publishing a complete plan. Audit is read-only; never log passwords/tokens.
Synthetic data/results must be labeled. Never claim unrun tests or external deploys.
