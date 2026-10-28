# Enterprise v1.1 API va UI shartnomasi

Barcha browser yozish amallari session cookie + X-CSRFToken bilan. `/auth/csrf`
token qaytaradi; login/logout tokenni aylantiradi. Token localStorageda saqlanmaydi.
Yo‘llar `/api/v1`ga nisbiy. Router/action oxirida `/`; qolganlarida yo‘q.
Ro‘yxatlar count/results/next, default 20, maksimum 100; server filtrlari tenantdan keyin.

## Import — /#/imports

Faqat ADMIN/BCMS_MANAGER. `POST /imports/upload` multipart entity + file, 2 MB,
1000 qator, 40 ustun, 4000 belgi/cell. CSV UTF-8 yoki bitta varaq XLSX. Makros,
formula, tashqi XML relationship, ZIP bomb va kutilmagan format rad etiladi.
Resurslar: departments/services/processes/assets/dependencies/resources.
Risk/BIA importi qo‘shilmadi: tasdiqlash va dalilni noaniq import bilan chetlab o‘tmaydi.

- `GET /imports/templates/{entity}?file_format=xlsx` yoki querysiz CSV.
- Upload javobi: UUID, headers, sample, count, fields, required, expires_at.
- `POST /imports/{uuid}/preview`: `{mapping:{"key":"External Key",...}}`.
  `rows` qator/kalit/data/existing_id/errorsni beradi; domen yozuvi o‘zgarmaydi.
- `POST /imports/{uuid}/commit`: `{confirm:true,decisions:{"2":"create","3":"update","4":"skip"}}`.
  Har qator aniq qaror oladi; mavjud yozuv uchun faqat update/skip. Hech qachon
  yashirin overwrite yo‘q. Atomar transaction; stale preview yoki xatoda rollback.
  Bajarilgan UUID 30 daqiqa ichida qayta yuborilsa oldingi summary qaytadi.

`key` — tenant/entity doirasidagi o‘zgarmas tashqi kalit (120 belgigacha). Birinchi
moslashda mavjud nom (dependency uchun yo‘nalish va IDlar) tekshiriladi; key keyin
nomdan mustaqil saqlanadi. Ota resurslarni oldin import qiling. FK/endpoint IDlari
shu tenantga tegishli faol yozuv bo‘lishi shart; UI reyestrlaridagi IDlardan foydalaning.
Fayl doimiy saqlanmaydi. DB preview 30 daqiqaga cheklangan; commitda qatorlar tozalanadi.
`purge_imports` kamida har 15 daqiqada operator tomonidan rejalashtiriladi.
Bir foydalanuvchiga 5 ochiq preview. Infrastructure request/body timeout ham qo‘llansin.

## Dalilli BIA — /#/bia-questionnaire

Mavjud `/bia/` CRUD va `/approve/`, `/revise/` saqlandi. Yangi maydonlar:
questionnaire (business_objective, operating_schedule, minimum_service_level,
dependency_assumptions, recovery_prerequisites, service_delivery_impact), evidence,
evidence_required, created_by, review_notes, approved_snapshot, missing_evidence.
Dalil title/type/source_reference/responsible_person/collection_date/assessment_date/
justification/quality/review_statusdan iborat. Maksimum 50 dalil. Sana:
yig‘ish ≤ baholash ≤ bugun. Link yuklanmaydi; dalil fayli tashqi nazoratli omborda.

Dalil/questionnaire kiritish evidence_requiredni yoqadi; keyin uni o‘chirib bo‘lmaydi.
Usta yangi yozuv uchun bu talabni yoqadi. Eski API klientlarining legacy BIA
shartnomasi saqlandi; evidence_required=false legacy yozuvlar dalilli anketa deb
taqdim etilmasin. Approval paytida yangi anketa ta’sirlari, rationale, minimal
xizmat, maqsad, prerequisite, dependency farazlari va dalil tekshiriladi.

`POST /bia/{id}/submit/` → SUBMITTED; `POST /bia/{id}/review/` reviewer tomonidan
`{decision:"reject"|"request_changes",notes:"..."}`; `approve` mavjud role policyda.
Tasdiqlangan evidence REVIEWED; assessment + jarayon konteksti snapshotga olinadi.
Legacy approved yozuv uchun tarixiy dalil to‘qilmaydi. `GET /bia/{id}/summary/` JSON
attachment; approved snapshot mavjud bo‘lsa shu ishlatiladi. Revision dalilni
UNREVIEWED holatda yangi draftga ko‘chiradi. RTO < MTPD va hisoblash vaznlari saqlandi.
`Organization.separation_of_duties` ADMIN orqali yoqiladi: noma’lum muallif yoki
muallif/jarayon egasining o‘z tasdig‘i rad etiladi; BIA va plan uchun bir xil siyosat.

## Rahbariyat — /#/management

`GET /management`: persisted pending BIA/plan, overdue tasks, incomplete evidence,
open findings, high unreviewed risks, 30 kunlik reja ko‘rigi, so‘nggi qarorlar.
PROCESS_OWNER/analyst kabi cheklangan rollar o‘ziga tegishli ma’lumotni oladi.
`/tasks/`: title, description, assigned_to, priority, due_date, entity_type/entity_id,
completion_evidence, resolution_notes. Linked entity ham tenant bo‘yicha tekshiriladi.
Manager yaratadi/qayta biriktiradi; assignee faqat status/dalil/izohni yangilaydi.
OPEN→IN_PROGRESS/BLOCKED/CANCELLED; IN_PROGRESS→BLOCKED/DONE/CANCELLED;
BLOCKED→IN_PROGRESS/CANCELLED; DONE/CANCELLED→OPEN faqat manager.
DONE dalil va izoh talab qiladi. Vazifa domen approvalni o‘zgartirmaydi.
Filtr: assigned_to/status/priority/overdue=true; ordering: due_date/priority/status/id.
O‘chirish yo‘q; CANCELLED bilan tarix saqlanadi.

## Hodisalar — /#/incidents

`/incidents/`: manager create, manager yoki incident owner response update;
auditor/approver o‘qiydi. Incident identifier UUID, immutable detection/occurrence/source,
reporter, owner, type, severity, processes/assets/risks/approved plans, business impact,
containment, recovery verification, resolution, lessons learned saqlanadi.
DETECTED→TRIAGED→INVESTIGATING→CONTAINED→RECOVERY_IN_PROGRESS→MONITORING→RESOLVED→CLOSED.
Triage impact, recovery containment, resolution kuzatuv va xulosa, closure saboq talab qiladi.
RESOLVED→INVESTIGATING yoki CLOSED→TRIAGED faqat manager + reopen_reason bilan.
`POST /incidents/{id}/evidence/`: title/source_reference/custody_note, optional sha256.
Server recorded_at/recorded_by qo‘shadi; append-only, 100 recordgacha. SHA256 operator
qaydi, fayl tekshirildi degani emas. CLOSEDga evidence qo‘shish uchun oldin reopen.
`recovery_objectives` faqat approved BIA; `recovery_tasks` bog‘langan tasklardan.

## Monitoring — /#/integrations

`GET /monitoring/integrations`, `/monitoring-alerts/`, `/monitoring-deliveries/` tenantga
cheklangan. ADMIN/BCMS_MANAGER `/monitoring-alerts/{id}/acknowledge/` va `/convert/`
amallarini bajaradi. Convert bir marta incident yaratadi; takroriy chaqiriq shu IDni beradi.
Webhook va relay imzo shartnomasi ENTERPRISE_OPERATIONS.mdda. Manbada enabled va
secret_configured haqiqiy deployment holati; last_success_at haqiqiy qabul yozuvidan.
Connected yoki live tekshiruv da’vosi yo‘q. Reference fixture SYNTHETIC deb belgilangan.

## Login/OIDC

`POST /auth/sso/discover` organization_code bilan enabled/provider qaytaradi.
Noma’lum/o‘chirilgan/kalitsiz kodda enabled=false, organization ma’lumoti yo‘q.
`POST /auth/sso/{slug}/begin` CSRF bilan; return_to faqat allowlistdagi /#/page;
query/absolute destination dashboardga qaytadi. Backend authorization_url qaytaradi.
GET callback server token almashinuvi, state/nonce/S256 PKCE/RS256 JWK/iss/aud/exp
tekshiruvini Authlib orqali bajaradi. Flow 5 daqiqa; token browser yoki DBga yozilmaydi.
Provider subject mavjud faol tenant userga operator tomonidan bog‘lanadi. Email/domain/
roles claim orqali kirish yoki rol oshirish yo‘q; provisioning default rad etiladi.
SSO provider yoki identity o‘chirilsa keyingi request sessiyani bekor qiladi; group
revokesi uchun qayta login yoki tashkilot sessiya bekor qilish amali zarur.
Logout RiskGuard sessiyasini bekor qiladi; global IdP logout/back-channel qo‘shilmadi.
Native LDAP yo‘q; Entra/Keycloak federation afzal. Local admin login odatdagi CSRF va
throttling bilan qoladi; yashirin bypass yoki email password reset havolasi yo‘q.
