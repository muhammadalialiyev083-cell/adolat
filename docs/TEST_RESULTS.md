# Executed verification report

Execution date: 2026-10-20. Feature branch: `fix/bcms-scientific-hardening`. Current upstream base: `6d3b0b8` (login/CSRF lifecycle and secure initial-admin changes included). No production deployment, merge or production database access was performed.

## Baselines

At the initial checkout `9cd3739`, Django had **33 passed**, FastAPI **24 passed**, no failures. FastAPI used an explicitly selected disposable SQLite URL. During work two newer main commits were discovered and incorporated; a clean `git archive` of upstream `6d3b0b8` was tested separately: Django **46 passed**, no failures. Thus upstream additions are not presented as newly authored regression tests. The existing frontend suite from the updated upstream was retained intact.

## Final results

| Test suite/check | Passed | Failed | Skipped | Blocked | Notes |
|---|---:|---:|---:|---:|---|
| Django complete pytest suite | 105 | 0 | 0 | 0 | Includes authentication, tenant isolation, BIA/risk, engine, simulation, dashboards, PDF, audit, initial admin and new regressions |
| Cross-backend ORM reference matrix | 20 | 0 | 0 | 0 | Subset of the 105 above; same cases run through actual Django and SQLAlchemy adapters |
| FastAPI complete pytest suite | 46 | 0 | 0 | 0 | Existing 24 plus configuration, CSRF, strategy and API validation regressions |
| Existing frontend tests | 10 | 0 | 0 | 0 | Preserved upstream tests; token rotation/retry, login/session, errors and concurrent bootstrap |
| TypeScript no-emit compilation | Pass | 0 | — | 0 | Exit 0 |
| Frontend production build | Pass | 0 | — | 0 | `tsc && vite build`, Vite 6.4.4 |
| Synthetic experiment reproduction | Pass | 0 | — | 0 | Generated JSON byte-identical to committed reference |
| Live Django/Vite functional requests | Pass | 0 | — | 0 | CSRF login, profile, priority, strategy, simulation warnings, PDF, dashboard and logout |
| Live Uvicorn startup | Pass | 0 | — | 0 | HTTP health and CSRF bootstrap; complete DB-backed API behavior checked in TestClient suite |
| PostgreSQL/Render production integration | — | — | — | Not run | No PostgreSQL service/production credentials selected; SQLite results are not PostgreSQL verification |
| GitHub PR creation | — | — | — | Yes | Git reads work; GraphQL and REST on api.github.com return Forbidden under the current egress policy |

The standalone Django run produced 39 warnings: missing local collectstatic directory in that configuration and a ReportLab Python AST deprecation. The earlier run with collected static assets produced one ReportLab warning. FastAPI produced four dependency/deprecation warnings (Starlette/AnyIO, utcnow usage in legacy endpoints and ReportLab). These were not skipped tests. No expected failures or disabled assertions were introduced. No lint suite is configured.

## Commands actually executed

Python runtime: 3.12.14; Node: 24.19.0; npm: 11.9.0. The combined validation venv is `/workspace/.adolat-fastapi-venv`. Final installed versions: Django 5.2.18, DRF 3.18.3, FastAPI 0.115.6, SQLAlchemy 2.0.36, Pydantic 2.14.1, pydantic-settings 2.7.1, pytest 8.3.4, pytest-django 4.14.0, NetworkX 3.4.2, SciPy 1.18.1 and ReportLab 4.2.5.

From `/workspace/adolat/backend`:

```bash
/workspace/.adolat-fastapi-venv/bin/pip install --cache-dir /workspace/.pip-cache -r requirements-test.txt
DEBUG=true /workspace/.adolat-fastapi-venv/bin/python -m pytest --junitxml=/tmp/bcms-django-results.xml
```

Result: 105 passed, 39 warnings, exit 0. This run uses only the repository's settings and pytest.ini; it does not require an untracked local settings module. A preceding run with `PYTHONPATH=/workspace/.adolat-config DJANGO_SETTINGS_MODULE=adolat_local_settings` also passed all 105, with collected static assets. Test databases are disposable; production migrations were not run. The existing local SQLite instance was migrated to the already-upstream initial-admin migration; its three existing users were preserved and no initial account was created.

From `/workspace/adolat/backend_fastapi`:

```bash
/workspace/.adolat-fastapi-venv/bin/python -m pytest -q
```

Result: 46 passed, four warnings, exit 0. conftest selects test mode and overrides get_db with an in-memory SQLite database. Runtime production configuration is tested by constructing separate Settings instances; application environment is never populated with production credentials.

From `/workspace/adolat/frontend`:

```bash
npm test
./node_modules/.bin/tsc --noEmit
npm run build
```

Results: 10 passed, compilation exit 0 and successful production bundle. Upstream frontend files/tests were preserved after reconciling the already-fixed CSRF issue; this patch adds only simulation warning rendering.

From repository root:

```bash
/workspace/.adolat-fastapi-venv/bin/python scripts/run_scientific_experiments.py --output /tmp/bcms-reproduced-experiments.json
cmp /tmp/bcms-reproduced-experiments.json docs/experiments/reference_results.json
/workspace/.adolat-fastapi-venv/bin/pip check
git diff --check
```

All exited 0. Requirements-test installation was exercised in its documented directory, including the editable shared package. `pip check` reported no broken requirements.

Live services were started with `DEBUG=true .../python manage.py runserver 127.0.0.1:8000 --noreload` from backend/, `npm run dev -- --host 127.0.0.1 --strictPort` from frontend/, and `ENVIRONMENT=test DATABASE_URL=sqlite:///:memory: .../python -m uvicorn app.main:app --host 127.0.0.1 --port 8001` from backend_fastapi/. Internal HTTP requests verified the expected JSON, session/CSRF rotation, a constrained strategy recommendation, simulation warning fields and a `%PDF` export. No public preview links were created.

## Regression scope and limitations

New Django test files contain 18 API/security cases, 20 cross-backend adapter cases and 21 domain/statistical cases. They cover SIM-01..10, the canonical algorithm reference, constraints, missing-data priors, strategy rejection/ties/Decimal precision, independent SciPy tie examples, undefined tau-b, weight normalization and ablation. FastAPI adds fail-closed production settings, log redaction, cookie flags, CSRF enforcement/rotation, invalid payloads and both strategy request forms.

The six-process sensitivity dataset is synthetic. Its actual minimum ID-order tau-a over ±0.05 single-weight perturbations is 0.6; this describes only this supplied dataset. The full normalized weights, score tau-b values, ablations and parameter sweeps are recorded in `experiments/reference_results.json`. No real-world pilot, expert evaluation, time-saving percentage or global model superiority was measured.

Production database connectivity, HTTPS browser behavior on the actual hosted origins, deployment rollback and whole-application penetration testing remain outside the executed verification. A passing SQLite suite does not remove those release checks.
