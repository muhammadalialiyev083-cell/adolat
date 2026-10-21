# Audit va funksional matritsa

Boshlang‘ich audit: git holati toza, mavjud branch `work`; alohida `feat/bcms-connected-workflow` yaratildi. Mavjud foydalanuvchi o‘zgarishlari o‘chirilmagan. Brend RiskGuard saqlandi. AGENTS/READMEdagi eski Django versiyasi, demo parol va test soni haqidagi da’volar kodga mos emas edi. Faol Django API, parallel tarixiy FastAPI katalogi, 8 tabli eski UI, session+Basic aralash auth va faqat ayrim yaratish amallari topildi.

P0: user role bypass, FK/numeric dependency tenant cheklovi, approval bypass, tasdiqlangan reja tahriri, xavfli demo parol. P1: nested update, validatsiya, jadval/resurs/nusxalar, wizard, eksport va mashq. P2: o‘zbekcha formalar, server paging/search, milliy light dizayn, mobil/fokus/error. Tuzatilgan yo‘llar quyida.

C=create, R=list/detail, U=update, D=delete; barcha R tenant a’zolariga. UI yo‘llari `/#/<resource>`. Oddiy routerlar oxirida `/` talab qiladi. Delete bog‘liq/approved yozuv bo‘lsa 400/409 bilan rad etilishi ham tekshirilgan natijadir.

| Sahifa | Amal | API | Ruxsat (yozish) | Model | Test | Holat |
|---|---|---|---|---|---|---|
| Tashkilot profili | R | `GET /api/v1/organizations/, /{id}/` | ADMIN | Organization | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Tashkilot profili | U | `PATCH /api/v1/organizations/{id}/` | ADMIN | Organization | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bo‘limlar | C | `POST /api/v1/departments/` | ADMIN/BCMS_MANAGER | Department | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bo‘limlar | R | `GET /api/v1/departments/, /{id}/` | ADMIN/BCMS_MANAGER | Department | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bo‘limlar | U | `PATCH /api/v1/departments/{id}/` | ADMIN/BCMS_MANAGER | Department | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bo‘limlar | D | `DELETE /api/v1/departments/{id}/` | ADMIN/BCMS_MANAGER | Department | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xizmatlar | C | `POST /api/v1/services/` | ADMIN/BCMS_MANAGER | Service | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xizmatlar | R | `GET /api/v1/services/, /{id}/` | ADMIN/BCMS_MANAGER | Service | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xizmatlar | U | `PATCH /api/v1/services/{id}/` | ADMIN/BCMS_MANAGER | Service | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xizmatlar | D | `DELETE /api/v1/services/{id}/` | ADMIN/BCMS_MANAGER | Service | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xodimlar va rollar | C | `POST /api/v1/users/` | ADMIN | User | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xodimlar va rollar | R | `GET /api/v1/users/, /{id}/` | ADMIN | User | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xodimlar va rollar | U | `PATCH /api/v1/users/{id}/` | ADMIN | User | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Xodimlar va rollar | D(deaktivatsiya) | `DELETE /api/v1/users/{id}/` | ADMIN | User | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Jarayonlar | C | `POST /api/v1/processes/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BusinessProcess | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Jarayonlar | R | `GET /api/v1/processes/, /{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BusinessProcess | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Jarayonlar | U | `PATCH /api/v1/processes/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BusinessProcess | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Jarayonlar | D | `DELETE /api/v1/processes/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BusinessProcess | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Aktivlar | C | `POST /api/v1/assets/` | ADMIN/BCMS_MANAGER | Asset | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Aktivlar | R | `GET /api/v1/assets/, /{id}/` | ADMIN/BCMS_MANAGER | Asset | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Aktivlar | U | `PATCH /api/v1/assets/{id}/` | ADMIN/BCMS_MANAGER | Asset | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Aktivlar | D | `DELETE /api/v1/assets/{id}/` | ADMIN/BCMS_MANAGER | Asset | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bog‘liqliklar | C | `POST /api/v1/dependencies/` | ADMIN/BCMS_MANAGER | Dependency | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bog‘liqliklar | R | `GET /api/v1/dependencies/, /{id}/` | ADMIN/BCMS_MANAGER | Dependency | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bog‘liqliklar | U | `PATCH /api/v1/dependencies/{id}/` | ADMIN/BCMS_MANAGER | Dependency | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Bog‘liqliklar | D | `DELETE /api/v1/dependencies/{id}/` | ADMIN/BCMS_MANAGER | Dependency | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| BIA | C | `POST /api/v1/bia/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BIAAssessment/BIAImpact | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| BIA | R | `GET /api/v1/bia/, /{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BIAAssessment/BIAImpact | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| BIA | U | `PATCH /api/v1/bia/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BIAAssessment/BIAImpact | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| BIA | D | `DELETE /api/v1/bia/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | BIAAssessment/BIAImpact | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Risklar | C | `POST /api/v1/risks/` | ADMIN/BCMS_MANAGER/RISK_ANALYST yoki o‘z PROCESS_OWNER | Risk | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Risklar | R | `GET /api/v1/risks/, /{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST yoki o‘z PROCESS_OWNER | Risk | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Risklar | U | `PATCH /api/v1/risks/{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST yoki o‘z PROCESS_OWNER | Risk | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Risklar | D | `DELETE /api/v1/risks/{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST yoki o‘z PROCESS_OWNER | Risk | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Nazorat choralari | C | `POST /api/v1/controls/` | ADMIN/BCMS_MANAGER/RISK_ANALYST | Control | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Nazorat choralari | R | `GET /api/v1/controls/, /{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST | Control | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Nazorat choralari | U | `PATCH /api/v1/controls/{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST | Control | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Nazorat choralari | D | `DELETE /api/v1/controls/{id}/` | ADMIN/BCMS_MANAGER/RISK_ANALYST | Control | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Strategiyalar | C | `POST /api/v1/strategies/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Strategy | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Strategiyalar | R | `GET /api/v1/strategies/, /{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Strategy | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Strategiyalar | U | `PATCH /api/v1/strategies/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Strategy | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Strategiyalar | D | `DELETE /api/v1/strategies/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Strategy | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Resurslar | C | `POST /api/v1/resources/` | ADMIN/BCMS_MANAGER | RecoveryResource | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Resurslar | R | `GET /api/v1/resources/, /{id}/` | ADMIN/BCMS_MANAGER | RecoveryResource | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Resurslar | U | `PATCH /api/v1/resources/{id}/` | ADMIN/BCMS_MANAGER | RecoveryResource | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Resurslar | D | `DELETE /api/v1/resources/{id}/` | ADMIN/BCMS_MANAGER | RecoveryResource | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Rejalar | C | `POST /api/v1/plans/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | ContinuityPlan/PlanStep | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Rejalar | R | `GET /api/v1/plans/, /{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | ContinuityPlan/PlanStep | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Rejalar | U | `PATCH /api/v1/plans/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | ContinuityPlan/PlanStep | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Rejalar | D | `DELETE /api/v1/plans/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | ContinuityPlan/PlanStep | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Ssenariylar | C | `POST /api/v1/scenarios/` | ADMIN/BCMS_MANAGER | Scenario | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Ssenariylar | R | `GET /api/v1/scenarios/, /{id}/` | ADMIN/BCMS_MANAGER | Scenario | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Ssenariylar | U | `PATCH /api/v1/scenarios/{id}/` | ADMIN/BCMS_MANAGER | Scenario | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Ssenariylar | D | `DELETE /api/v1/scenarios/{id}/` | ADMIN/BCMS_MANAGER | Scenario | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Mashqlar | C | `POST /api/v1/exercises/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Exercise | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Mashqlar | R | `GET /api/v1/exercises/, /{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Exercise | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Mashqlar | U | `PATCH /api/v1/exercises/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Exercise | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Mashqlar | D | `DELETE /api/v1/exercises/{id}/` | ADMIN/BCMS_MANAGER yoki o‘z PROCESS_OWNER | Exercise | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Audit | R | `GET /api/v1/audit-logs/, /{id}/` | Tashkilot a’zosi; faqat R | AuditLog | test_auth_rbac (immutability); Chromium | Implementatsiya + avtomatlashtirilgan qamrov |
| Hisoblash tarixi | R | `GET /api/v1/simulation-runs/, /{id}/` | Tashkilot a’zosi; faqat R | SimulationRun | test_connected_workflow; test_auth_rbac; Chromium navigatsiya | Implementatsiya + avtomatlashtirilgan qamrov |
| Login | Kirish/noto‘g‘ri login | `POST /api/v1/auth/login` | Anonim + CSRF | User/Session/Audit | full_csrf_journey, login_throttle; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Sessiya | Reload/me/logout | `GET /api/v1/auth/me; POST /auth/logout` | Sessiya | Session | test_auth_rbac/client.test; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Parol | Yangilash | `POST /api/v1/auth/password` | Joriy foydalanuvchi + eski parol | User | full_csrf_journey | Tekshirilgan; tashqi deploy bundan mustasno |
| BIA | Tasdiqlash/yangi versiya | `POST /api/v1/bia/{id}/approve/; revise/` | Tasdiqlash ADMIN/APPROVER; revise yozuvchi | BIAAssessment | bia_approval_flow; full_csrf_journey | Tekshirilgan; tashqi deploy bundan mustasno |
| BIA | Ustuvorlik tartibi | `POST /api/v1/analyses/priority` | Tenant a’zosi | BIA/Risk/Dependency | priority_formula; missing_data; UI | Tekshirilgan; tashqi deploy bundan mustasno |
| Risk | Ballni baholash | `POST /api/v1/analyses/evaluate-risk` | Tenant a’zosi | Saqlanmaydigan tekshiruv | bad_engine_input; phase3 | Tekshirilgan; tashqi deploy bundan mustasno |
| Strategiya | Nomzodlarni baholash | `POST /api/v1/analyses/evaluate-strategy` | Tenant a’zosi | Saqlanmaydigan tekshiruv | phase3_strategy_evaluation | Tekshirilgan; tashqi deploy bundan mustasno |
| Risk matritsasi | Katak/filtr | `GET /api/v1/reports/risk-matrix; GET /risks/?likelihood=&impact=` | Tenant a’zosi | Risk | nested_steps_controls_exercises; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Bog‘liqlik xaritasi | Tugun/ta’sir/sikl/qidiruv | `GET /api/v1/dependency-graph` | Tenant a’zosi | Process/Asset/Dependency | cross_org_reads; cycles; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Jadval | Hisoblash/saqlash | `POST /api/v1/schedule-runs/` | ADMIN/BCMS_MANAGER | ScheduleRun | full_csrf_journey; hand_computed/capacity/cycles | Tekshirilgan; tashqi deploy bundan mustasno |
| Jadval | Oxirgi saqlangan natija | `GET /api/v1/schedule-runs/` | Tenant a’zosi | ScheduleRun | full_csrf_journey; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Reja | Tasdiqlash/yangi versiya/arxiv | `POST /api/v1/plans/{id}/publish/; revise/; archive/` | Tasdiqlash/arxiv ADMIN/APPROVER; revise yozuvchi | ContinuityPlan | full_csrf_journey; state_machine | Tekshirilgan; tashqi deploy bundan mustasno |
| Reja | PDF/DOCX | `GET /api/v1/plans/{id}/export_pdf/; export_docx/` | Tenant a’zosi | Plan.snapshot | full_csrf_journey; multipage_unicode | Tekshirilgan; tashqi deploy bundan mustasno |
| Ssenariy | Xavfsiz hisoblash/tarix | `POST /api/v1/scenarios/{id}/simulate/; GET /simulation-runs/` | ADMIN/BCMS_MANAGER hisoblaydi | Scenario/SimulationRun | phase4; simulation_history | Tekshirilgan; tashqi deploy bundan mustasno |
| Usta | Bosqich/missing/oldinga-qaytish | `GET /api/v1/workflow` | Tenant a’zosi | Tenant inventari | full_csrf_journey; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Dashboard | KPI/davr/filtrli drilldown | `GET /api/v1/reports/organization?since=&until=` | Tenant a’zosi | Barcha domenlar | full_csrf_journey; report_consolidation; Chromium | Tekshirilgan; tashqi deploy bundan mustasno |
| Jarayonlar | Qidiruvli CSV eksport | `GET /api/v1/reports/processes.csv?search=&ordering=` | Tenant a’zosi | BusinessProcess | csv_formula; cross_org_reads | Tekshirilgan; tashqi deploy bundan mustasno |
| Umumiy UI | Loading/empty/error/retry | `/api/v1Tegishli GET/POST` | Joriy rol | Tegishli model | client.test; Chromium 503/retry | Tekshirilgan; tashqi deploy bundan mustasno |
| Umumiy UI | Dirty dialog/klaviatura/mobil | `/api/v1Forma va responsive shell` | Joriy rol | Client holati | Chromium dirty/Escape/390px | Tekshirilgan; tashqi deploy bundan mustasno |
| Health | Liveness/readiness | `GET /healthz; /readyz` | Anonim; maxfiy tafsilotsiz | DB/migrations | Lokal HTTP smoke; production sozlama check | Tekshirilgan; tashqi deploy bundan mustasno |

Izoh: matritsa umumiy komponent testlarini ham ko‘rsatadi; har bir sahifaning har bir kombinatsiyasi alohida browser E2E bilan qamrab olingan degan da’vo yo‘q. Tashqi hisoblar, bibliografiya va production yuk tekshiruvlari LIMITATIONS.mdga ajratilgan.
