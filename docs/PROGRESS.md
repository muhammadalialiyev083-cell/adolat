# Ish jarayoni

2026-10-21: `feat/bcms-connected-workflow` branch. Boshlang‘ich git holati toza.
Haqiqiy stek: Django 5.2 talab qilingan, DRF, React 18/TS/Vite; lokal SQLite,
production DATABASE_URL/PostgreSQL. `backend_fastapi` parallel, faol frontend Django API bilan ishlaydi.
Brend: RiskGuard (frontend), BCMS Designer (loyiha tavsifi).

Boshlang‘ich tekshiruv: frontend build va 10 client testi o‘tdi. Python test vositasi
muhitda yo‘q; alohida work/venv tayyorlanmoqda.

P0: user CRUD role bypass, cross-tenant foreign keys, dependency numeric references,
approval status bypass, mutable published plan, hardcoded demo password.
P1: nested BIA update, finite/positive validation, scheduler/resources + snapshots,
wizard readiness, document versions/exports, exercise findings, live dashboards.
P2: all missing CRUD UI, Uzbek labels, light national design, responsive/focus/error states.

Keyingi: tenant-aware serializers + role/ownership policy; model extensions/migrations;
end-to-end API workflow; frontend CRUD/workflow; verification and delivery report.

## Yakuniy holat

P0: tenant FK/numeric refs va role/owner nazorati, session/CSRF, last-admin,
immutable approvals/snapshots, safe seed/provision alias, secret-free defaults.
P1: persistent CRUD, nested updates, seconds normalization + constraints, two
schedulers/snapshots, wizard, BIA/risk analysis, scenario history, exercises,
PDF/DOCX/CSV, backup/restore. P2: Uzbek navy/turquoise light design, graph/matrix,
server search/paging, responsive forms and error/retry/focus states.

Tekshiruv: yakuniy 86 backend testi SQLite/PostgreSQLda; 10 client testi;
ESLint/Ruff/typecheck/build; Chromium smoke; source-copy migrations and separate
PostgreSQL backup/restore. Exact artifacts are included in the delivery evidence.

Original SQLite only opened read-only for backup; user/process/plan counts in
upgrade copy remained 3/4/1. No external service writes, paid resources or deploys.

Qolgan tashqi ish: live Render/Netlify configuration/deploy, current schema and
scientific-source verification. Operational limitations: shared production login
cache, real load/security evaluation, evidence-based automatic BIA recommendations.
See LIMITATIONS.md.

Final browser issue resolution: legacy template caching retained an obsolete Vite
asset filename after rebuild. The HTML shell now reads the current built index
and sends no-cache. Portable browser assertions scope edits to the created row,
so repeated demo runs remain valid. Final SQLite 86 passed (24.49s), PostgreSQL
86 passed (28.28s); client 10 passed, build passed; browser smoke passed.

## 2026-10-28 — Enterprise Pilot v1.1

`feat/enterprise-pilot-v1-1`: bazaviy 86 backend/10 client testi qayta bajarildi.
Shared atomic DB throttling, strict production settings, import va BIA, OIDC login,
task/incident/monitoring, additive migrations, CI, pilot hujjatlari qo‘shildi.
Natija va aniq tekshiruvlar ENTERPRISE_V1_1_RELEASE.mdda. Real production deploy,
IdP/monitoring ulanishi va tashkilot UATsi hali bajarilmagan.
