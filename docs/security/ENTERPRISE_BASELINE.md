# Enterprise v1.1 — boshlang‘ich audit (2026-10-28)

Manba: 09fcd7d; toza `work`dan `feat/enterprise-pilot-v1-1` ochildi.
Ishlab turgan DB va tashqi deploy o‘zgartirilmadi.

## Inventar

Django apps: authentication, organizations, processes, bia, risks, engine, plans,
simulation, reports, core. API `/api/v1`; router resurslari `/` bilan; auth,
hisobot va tahlil yo‘llari `/`siz. Barcha ro‘yxatlar tenant bo‘yicha sahifalanadi.
TenantSerializer FKlarni, TenantViewSet/DomainPermission rol va egani tekshiradi.
Model ro‘yxati: User, Organization/Department/Service, BusinessProcess/Asset/
Dependency, BIAAssessment/BIAImpact, Risk/Control, RecoveryResource/ScheduleRun,
Strategy/ContinuityPlan/PlanStep, Scenario/Exercise/SimulationRun, AuditLog.
Frontend App sessiya/hash navigatsiyasi, Workspace CRUD/ustalar, Dashboard va
Analysis haqiqiy API bilan ishlaydi. backend_fastapi tarixiy va faol emas.

Mavjud himoyalar: session+CSRF, cookie rotatsiyasi, 8 soat sessiya, RBAC,
tenant FK validatsiyasi, soft delete, atomar nested writes, tasdiqlangan BIA/reja
immutability, revision, reja snapshot, auditdagi maxfiy kalitlarni olib tashlash,
HTTPS/HSTS/nosniff/frame himoyasi, health/readiness.

Yetishmaganlar: umumiy login limiti; upload/import; strukturali BIA dalillari;
generic vazifalar; incident; monitoring adapter; OIDC; CI va pilot hujjatlari.
Saqlanadigan ilmiy cheklovlar docs/ALGORITHMS.mdda: RTO < MTPD, priority
0.40/0.25/0.20/0.15, risk 1..25, dependency yo‘nalishi, evristika va simulyatsiya.

## Topilmalar va xavfsizlik darvozasi

- Login limiti LocMemCache bilan workerlar orasida bo‘linadi. LoginRateBucket
  shartli atomar UPDATE bilan umumiy bazada sanaydi; Redis lokal majburiy emas.
  10/minut/peer fixed window; chegara atrofida ikki oynaning limiti mumkin.
- Audit IPsi tekshirilmagan X-Forwarded-Forni qabul qilgan. Endi REMOTE_ADDR;
  ishonchli ingress haqiqiy peer manzilini sozlashi kerak. Kiruvchi soxta header
  rate limitni ham, audit manbasini ham almashtira olmaydi.
- Production hosts, key length va HTTPS originlar endi fail-closed tekshiriladi.
- Mavjud testlar oldingi P0 tenant/role/approval regressiyalarini qamraydi;
  auditda yangi tasdiqlangan tenant bypass aniqlanmadi. Bu penetration audit emas.

Bazaviy backend: dastlab pypdf yo‘q, dev talablar o‘rnatilgach **86 passed**.
Bazaviy frontend: **10 passed**, lint/typecheck/build bajarildi.
P0 regressiyalari va yakuniy tekshiruv docs/ENTERPRISE_V1_1_RELEASE.mdga yoziladi.

## Migratsiya va operatsion tavakkal

Faqat additive/reversible migratsiyalar. Login counter ma’lumoti vaqtinchalik;
`purge_login_limits`ni kunlik operator jadvaliga qo‘ying. O‘tkazib yuborish faol
limitni buzmaydi, lekin jadval o‘sadi. DB unavailable bo‘lsa login 503.
Multiworker contention va production trafik yuki alohida stagingda o‘lchansin.
DB runtime user superuser emas; DDL alohida migratsiya roli orqali bajarilsin.
BIA/reja tarixini yo‘qotuvchi migratsiya yoki production ma’lumotiga yozish yo‘q.
