# Security hardening and deployment checklist

## Configuration

FastAPI defaults to `ENVIRONMENT=production` and uses Pydantic Settings. Production requires `DATABASE_URL`, independently generated `SECRET_KEY` and `SESSION_SECRET`, each at least 32 characters with at least 12 distinct characters; known development/placeholder patterns and identical keys are rejected. These syntactic checks cannot prove entropy: generate keys with a cryptographically secure generator, not human-chosen phrases. `DEBUG=true` is rejected in production. Database URLs must use a supported PostgreSQL or SQLite scheme; known old development credentials are rejected. SQLite remains a local/test option; persistent production storage should use managed PostgreSQL.

Explicit development/test modes have local SQLite fallbacks and freshly generated ephemeral keys when none are supplied. Persistent local sessions require a private user-generated key. A restart with ephemeral keys invalidates sessions intentionally. Tests select `ENVIRONMENT=test` and an isolated in-memory database before importing the application. `.env.example` contains blanks/placeholders and no usable shared credentials. Never reuse production keys in development/tests.

Django also removes the static development SECRET_KEY. `ENVIRONMENT=production` or Render's `RENDER` indicator enables required database/key checks and rejects debug mode. Local mode retains a fresh ephemeral key fallback. Existing Render deployments must have a strong persistent SECRET_KEY and DATABASE_URL configured before this change is deployed. Other Django hosting providers must explicitly set ENVIRONMENT=production. Both backends disable debug in production; do not expose application tracebacks.

Required production settings:

| Setting | Django | FastAPI |
|---|---|---|
| ENVIRONMENT | production (Render is also detected) | production, the default |
| DATABASE_URL | Required | Required |
| SECRET_KEY | Strong persistent generated key | Strong persistent generated key |
| SESSION_SECRET | Not used | Independent generated key |
| DEBUG | false | false |
| ALLOWED_HOSTS | Actual backend hostnames | Not a FastAPI setting |
| CSRF_TRUSTED_ORIGINS | Exact trusted frontend HTTPS origins | Origin validation uses ALLOWED_ORIGINS |
| CORS_ALLOWED_ORIGINS | Exact trusted frontend HTTPS origins | Not used |
| ALLOWED_ORIGINS | Not used | Comma-separated exact HTTPS origins; empty denies cross-origin reads |

FastAPI rejects wildcard, credential-bearing or path-bearing origins. Production cross-site cookies use Secure, HttpOnly and SameSite=None; development uses Lax cookies over local HTTP. Credentialed writes require session-bound CSRF tokens. `/auth/csrf` bootstraps a token; login clears the previous session/token. Untrusted origins are denied. The deployed Django CSRF/session flow and upstream token rotation handling are preserved. Browsers can still block third-party cookies; using a same-origin reverse proxy is a deployment option, not something CORS headers alone fix.

SQLAlchemy SQL echo is disabled even when local debug is enabled, and parameter hiding is enabled. Settings representations mask SecretStr keys, exclude the database URL and hide input values in validation errors. Do not dump model dictionaries, process environments, connection strings or credential files into logs. Configure hosting/driver logs to exclude sensitive values as well; application-level tests cannot prove an external platform's logging behavior.

## Data integrity in affected components

Both dependency graph adapters exclude soft-deleted records and validate every endpoint against the current tenant's active process/asset set. Invalid failure identifiers are rejected generically. BIA, risks and plans used in priority/simulation are scoped to both organization and process. Dangling or foreign intermediates cannot bridge valid nodes. Django's affected serializers reject foreign/deleted references before writes, and score/time/cost inputs are validated. FastAPI risk creation validates referenced assets, not only processes. There are no destructive migrations in this change.

Demo seeders now require an explicit local development context and a separately supplied DEMO_USER_PASSWORD of at least 12 characters. They refuse production before any writes and never print the password. They are manual local tools; never add them to Render's production start command. Existing local provisioning commands can reset named demo passwords when explicitly invoked; do not run them against user databases. For first production account creation use the upstream opt-in initial-admin migration described in `LOGIN_TUZATISH.md`; this change preserves it and its data-preserving behavior.

## Credential review and manual rotation

The earlier FastAPI config and Alembic INI committed a shared development PostgreSQL credential and static application/session signing keys. Django committed a development signing key. README/AGENTS also documented public demo-account passwords. These are treated as public, not confidential credentials. No evidence establishes that they were real production credentials, and no external credentials were tested or revoked.

If any were reused in a deployment, manually rotate the PostgreSQL account password, SECRET_KEY, SESSION_SECRET and affected demo-account passwords in hosting settings. Rotating signing keys invalidates existing sessions. Removing values from current source does not remove Git history. Audit existing user accounts and disable unused demo accounts through normal administrative controls; do not delete/reset production records as part of applying this patch. Test fixture passwords remain synthetic local-only data.

## Before a production release

1. Review the feature diff and test report; deploy only after approval. Neither production deployment nor merge is automated here.
2. Configure persistent generated keys and the correct database in hosting settings. Keep separate development, test and production databases. Restrict database network/TLS access and confirm backups.
3. Set exact host, CORS and CSRF origins and DEBUG=false. Verify HTTPS proxy handling, cookies and browser CSRF behavior on the actual frontend origin.
4. For Django retain Render root `backend/`, collectstatic and `gunicorn bcms_backend.wsgi:application --bind 0.0.0.0:$PORT`. Do not deploy local override settings or demo seeders. Review the upstream migration history, including opt-in initial admin, before running migrations.
5. FastAPI is an alternative: install the shared package from the sibling backend directory, use its own schema, validate config before starting Uvicorn and review migration output. No PostgreSQL integration/migration was executed by this task.
6. Verify login/logout, tenant boundaries, priority/strategy outputs, warnings, simulation, dashboards, audit logs and PDF export after release. Old FastAPI rankings need recalculation under model v1.1.
7. Keep a reversible release rollback. This patch adds no schema migration. Reverting code does not undo the independent upstream initial-admin migration or delete accounts. Review changed formula/API validation behavior before rolling clients back; keep strengthened credentials.

This is a focused review of the requested components, not a whole-application penetration test. Known review areas outside this patch include broad FastAPI role enforcement and legacy state-transition permissions, global Django superuser behavior in unrelated viewsets, and infrastructure/session revocation policies. Do not treat passing unit tests as a security certification.
