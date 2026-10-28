# RiskGuard Enterprise Pilot v1.1 — ko‘rib chiqish nomzodi

2026-10-28. Branch: feat/enterprise-pilot-v1-1. Boshlang‘ich commit: 09fcd7d.
Django 5.2/DRF/Python 3.12 va React 18/TS/Vite saqlandi. backend_fastapi o‘zgarmadi.
**Productionga deploy yoki real tashkilot piloti bajarilmadi.** Ushbu PR texnik
nomzod; tashqi konfiguratsiya, haqiqiy UAT va operator qarorisiz pilot qabul qilinmaydi.

## Tekshirilgan funksiyalar

| Feature | Implementation | Automated Tests | Live Validation | Deployment Status |
|---|---|---|---|---|
| Shared login throttling, strict production config | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Tenant FK/M2M, role va approval locking | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| CSV/XLSX 4 bosqichli import, stable key, rollback | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Dalilli BIA, review, snapshot, revision, summary | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Management approval queue va tasklar | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Incident lifecycle, evidence metadata, recovery links | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| HMAC Alertmanager relay adapter, dedup, diagnostics | IMPLEMENTED | TESTED | REQUIRES EXTERNAL CONFIGURATION | REQUIRES EXTERNAL CONFIGURATION |
| OIDC Code/state/nonce/PKCE, stable subject mapping | IMPLEMENTED | TESTED | REQUIRES EXTERNAL CONFIGURATION | REQUIRES EXTERNAL CONFIGURATION |
| Enterprise login, mobile/themes/accessibility flows | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Additive migration, backup/restore compatibility | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| CI + dependency locks/audit/secret scan configuration | IMPLEMENTED | TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Pilot charter, UAT, metrics va 12 hujjat | IMPLEMENTED | NOT TESTED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION |
| Haqiqiy intervyu, pilot o‘lchovi va qabul imzolari | BLOCKED | NOT TESTED | REQUIRES EXTERNAL CONFIGURATION | BLOCKED |

TESTED — lokal/izolyatsiyalangan test dalili; real provider yoki production tayyorligi emas.
CI konfiguratsiyasi lokal ekvivalentlar bilan tekshirildi; GitHub runner natijasi PRda alohida.

## Kuzatilgan tekshiruvlar

- Bazaviy test: 86 backend, 10 frontend client testi. Dastlab dev pypdf paketi yo‘q
  edi; requirements o‘rnatilgach qayta bajarildi.
- Yakuniy SQLite: **144 passed, 1 skipped** (faqat PostgreSQL concurrency testi).
- Yakuniy PostgreSQL 17.11 UTF-8: **145 passed**, jumladan 8 parallel worker orqali 20 urinishda
  aynan 10 ruxsatli atomar login counter. Test server dastlab SQL_ASCII bilan
  ochilgan edi; UTF-8 alohida cluster bilan to‘g‘rilandi.
- Django check, makemigrations --check --dry-run; production check --deploy
  --fail-level WARNING; Ruff; frontend lint/typecheck/client/build bajarildi.
- `bash scripts/check.sh` to‘liq bajarildi. Frontend client: **13 passed**.
- Enterprise Chromium: login/xato/rate/service, visibility, empty input,
  duplicate-submit, keyboard Enter, mobile/light/dark/reduced-motion, SSO discovery
  fixture, safe protected return, real import/BIA/task/incident, integration status,
  session expiration/logout. JS errors: **0**. Screenshots: screenshots/enterprise-v1-1/.
- Mavjud Chromium smoke: navigation/persistence/edit/dirty form/API outage/mobile/logout/auditor oqimlari o‘tdi.
- Original SQLite read-only backup nusxasida forward → reverse → forward:
  24 domen/tarix jadvali soni saqlandi; avvalgi 3 user, 4 process, 1 plan.
  Django permission/contenttype jadvallari yangi modellar sabab tabiiy ko‘payadi.
- Alohida PostgreSQL pg_dump/pg_restore: sintetik user/process/task/incident,
  audit, import key va approved BIA/plan snapshotlari tiklanib solishtirildi.
- PyPI audit: 29 production va 58 dev dependency, yakuniy **0 ma’lum zaiflik**.
  Dastlab pypdf 6.21.1da 3 CVE topildi; 6.21.2ga yangilandi. npm audit: **0**.
  Audit natijalari docs/security/ ichida; bu noma’lum zaiflik yo‘qligi kafolati emas.
- Gitleaks 8.30.1 staged tracked source scan: **no leaks found** (git tarixining to‘liq auditi emas).

## Xavfsizlik va integratsiya chegaralari

Login limiti barcha worker uchun umumiy DB conditional UPDATE; raw IP emas HMAC key.
Ingress peer manzilini to‘g‘ri yetkazishi, fixed-window burst va proxy ortidagi
foydalanuvchilar uchun staging load tekshiruvi zarur. DB failure loginni yopadi.
Tashkilotsiz superuser tenant APIga kirmaydi; tenant M2M ham tekshiriladi.
Approved draft edit/delete approval bilan lock orqali serializatsiya qilinadi.
Audit credential nomlarini redakt qiladi; production logger body/queryni chiqarmaydi.
Proxy/Gunicorn access loglarida callback queryni operator ham yashirishi kerak.

Import fayli doimiy media emas; preview TTL 30 daqiqa, commitda tozalanadi,
`purge_imports` kamida har 15 daqiqada kerak. Har commit atomar, mavjud yozuv
explicit update bilan; stale preview rollback. Risk/BIA import qo‘shilmadi.
Legacy BIA APIga evidence_required=false moslik saqlandi; dalilli yangi usta bu
flagni yoqadi va o‘chira olmaydi. Asosiy recovery qiymatlarisiz draft modelga yozilmaydi.
Approved tarixiy evidence to‘qilmaydi. 0.40/0.25/0.20/0.15, risk ordinal, RTO < MTPD,
dependency yo‘nalishi, scheduler va simulyatsiya cheklovlari o‘zgarmadi.

OIDC testlarida haqiqiy RS256/JWK tekshiruvi mock HTTP provider transportida bajarildi.
Real Entra/Keycloak tenantiga ulanish yo‘q. Operator-reviewed subject → mavjud
active tenant user; auto provisioning/role claim mapping yo‘q. Required groups
signed claimda tekshiriladi. Native LDAP, IdP global/back-channel logout qo‘shilmadi.
Provider/identity o‘chirilishi keyingi requestda sessiyani bekor qiladi; IdPdagi
uzoq group revokesi mahalliy policy yoki qayta login orqali boshqariladi.

Monitoring reference adapter imzolangan relay talab qiladi; oddiy Alertmanager
webhook o‘zi bu imzoni bermaydi. Hech qanday real monitoring ulanishi tekshirilmadi.
Scheduled pull, qo‘shimcha providerlar va intruziv infratuzilma amallari yo‘q.
Evidence hash operator metama’lumoti; forensic verification yoki WORM kafolati emas.

## Qolgan ish va pilotga kirish shartlari

- Haqiqiy tashkilot, manba inventar, mas’ullar, review siyosati va UAT qatnashchilari.
- Staging HTTPS, PostgreSQL least privilege, cleanup schedule, backup retention va alertlar.
- IdP client/redirect/group claim/subject mapping; monitoring relay/HMAC secret va NTP.
- Real provider UAT, productionga o‘xshash load/security baholashi va barcha browser/OS kombinatsiyalari.
- Katta dataset uchun ayrim 100 yozuvli selector/history UXni kengaytirish.
- Pilot interview, observed recovery, inson ish vaqti/usability o‘lchovi va qabul qarori.

Bu ishda live DB, DNS, live secrets, pulli cloud resurslar va production deployga
tegilmadi. PR merge qilinmaydi. Operator yo‘riqnomasi: ENTERPRISE_OPERATIONS.md;
API/UI: ENTERPRISE_API.md va FRONTEND_ENTERPRISE.md; pilot: pilot/.
