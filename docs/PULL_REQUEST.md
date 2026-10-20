# Correct BCMS simulation and unify scientific calculations securely

A failed asset without registered dependents previously caused the FastAPI simulator to report every tenant process as disrupted. Both backends now traverse a validated tenant graph and return zero confirmed impacts plus coverage warnings when evidence is missing. Shared scientific calculations, constrained strategy selection and tie-aware statistics make the results reproducible across the two implementations.

## P0 fixes

- Remove the organization-wide simulation fallback; exclude foreign/deleted/dangling graph nodes and validate disrupted assets. Handle transitive paths, duplicates, cycles and deterministic ordering.
- Require production database/signing configuration, reject debug/insecure defaults, restrict credentialed CORS, protect session writes with CSRF and hide secrets/SQL parameters from logs.
- Restrict demo provisioning to explicit local development with a supplied password; preserve existing production users and upstream initial-admin behavior.

## P1 fixes

- Introduce bcms-domain as the framework-independent research model. Preserve priority weights, BIA component weights and the 72-hour horizon, with explicit missing-data warnings and consistent normalization.
- Validate strategy inputs and recommend the lowest-cost feasible candidate under RTO/RPO constraints. Return rejected reasons, exact Decimal cost representation, deterministic ties and model limitations.
- Label ID-order Kendall correctly as tau-a; add numerical-score tau-b with explicit undefined cases and independent SciPy references. Reproduce normalized weight/ablation/T_MAX/threshold experiments from synthetic datasets.
- Display simulation coverage warnings without changing frontend styling or navigation.

## Validation

- Django: 105 passed; includes 20 cases running both real ORM adapters on the same fixtures.
- FastAPI: 46 passed.
- Existing frontend: 10 passed; TypeScript no-emit and production build passed.
- Live Vite/Django login, profile, priority, strategy, simulation, dashboard, PDF and logout checks passed; live Uvicorn health/CSRF checks passed.
- Synthetic experiment JSON reproduced byte-for-byte; pip check and git diff --check passed.

Commands and actual baselines/warnings are in docs/TEST_RESULTS.md. The executable test requirements were installed from backend/requirements-test.txt. New regression files cover graph semantics/tenant isolation, invalid inputs, configuration/log redaction, CSRF, reference numerical equivalence, Decimal cost order and tied-score statistics.

## Compatibility and security

Existing result fields remain. OPTIMAL_FOUND is retained as a compatibility label, with FEASIBLE_FOUND decision status and scientifically limited wording. FastAPI retains its stored-strategy request form and adds the Django supplied-candidate form. Invalid/missing scientific inputs now fail validation; historical zero stored costs require explicit confirmation. FastAPI session clients must fetch /auth/csrf before authenticated writes. These intentional validation/security changes are documented in docs/BACKEND_CONSISTENCY.md.

Production needs securely configured DATABASE_URL, SECRET_KEY and (FastAPI only) SESSION_SECRET before release. Old shared keys and demo credentials must be manually rotated if reused externally. No external credentials were tested or revoked. FastAPI installing its shared package needs the sibling backend directory; the existing Django Render root remains valid.

## Limits and rollback

PostgreSQL/actual Render integration, empirical organizational validation and whole-application penetration testing were not performed. Model weights are research assumptions, not ISO-mandated or proven-optimal values. No schema migration was added by this patch. Revert these feature commits to roll back code; do not delete users, revert unrelated upstream data changes or restore compromised keys. No production deployment or merge is part of this PR.

## Files modified

<details><summary>Complete implementation and documentation file list</summary>

- `AGENTS.md`
- `backend/.env.example`
- `backend/apps/bia/serializers.py`
- `backend/apps/core/management/commands/provision_demo_users.py`
- `backend/apps/core/management/commands/seed_demo_data.py`
- `backend/apps/core/serializers.py`
- `backend/apps/engine/calculator.py`
- `backend/apps/engine/sensitivity.py`
- `backend/apps/engine/views.py`
- `backend/apps/plans/serializers.py`
- `backend/apps/processes/serializers.py`
- `backend/apps/risks/serializers.py`
- `backend/apps/simulation/serializers.py`
- `backend/apps/simulation/simulator.py`
- `backend/apps/simulation/views.py`
- `backend/bcms_backend/settings.py`
- `backend/bcms_domain/__init__.py`
- `backend/bcms_domain/graph.py`
- `backend/bcms_domain/scientific.py`
- `backend/pyproject.toml`
- `backend/requirements-test.txt`
- `backend/tests/test_api_hardening.py`
- `backend/tests/test_backend_consistency.py`
- `backend/tests/test_domain_hardening.py`
- `backend_fastapi/.env.example`
- `backend_fastapi/alembic.ini`
- `backend_fastapi/alembic/env.py`
- `backend_fastapi/app/config.py`
- `backend_fastapi/app/database.py`
- `backend_fastapi/app/main.py`
- `backend_fastapi/app/routers/auth.py`
- `backend_fastapi/app/routers/engine.py`
- `backend_fastapi/app/routers/risks.py`
- `backend_fastapi/app/routers/simulation.py`
- `backend_fastapi/app/schemas/bia.py`
- `backend_fastapi/app/schemas/engine.py`
- `backend_fastapi/app/schemas/risk.py`
- `backend_fastapi/app/schemas/simulation.py`
- `backend_fastapi/app/services/engine.py`
- `backend_fastapi/app/services/graph.py`
- `backend_fastapi/app/services/simulation.py`
- `backend_fastapi/app/utils/csrf.py`
- `backend_fastapi/requirements.txt`
- `backend_fastapi/seed_data.py`
- `backend_fastapi/tests/conftest.py`
- `backend_fastapi/tests/test_engine_hardening.py`
- `backend_fastapi/tests/test_security_config.py`
- `docs/BACKEND_CONSISTENCY.md`
- `docs/DISSERTATION_TECHNICAL_SUMMARY_UZ.md`
- `docs/SCIENTIFIC_MODEL.md`
- `docs/SECURITY_HARDENING.md`
- `docs/TEST_RESULTS.md`
- `docs/experiments/reference_results.json`
- `frontend/src/App.tsx`
- `scripts/run_scientific_experiments.py`
- `tests/scientific_reference.json`
- `tests/sensitivity_reference.json`

</details>
