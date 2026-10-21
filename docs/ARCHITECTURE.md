# Arxitektura va ruxsatlar

Django modular monolit saqlandi. `bcms_backend/urls.py` — /api/v1 router.
`authentication`, `organizations`, `processes`, `bia`, `risks`, `engine`, `plans`,
`simulation`, `reports`, `core` — domenlar. React `App.tsx` login/sessiya/shellni,
`components/Workspace.tsx` umumiy resurs formalari va ish oqimini,
`Dashboard.tsx` KPIlarni, `Analysis.tsx` BIA tartiblash/risk matritsasini boshqaradi.
API chaqiruvlari `src/api/client.ts`da; URL yo‘llari hashda saqlanadi.

## Ma’lumotlar modeli

Organization → Department / Service / User / BusinessProcess / Asset.
BusinessProcess → BIAAssessment → BIAImpact; BusinessProcess → Risk → Control;
BusinessProcess → Strategy; Strategy.resource_requirements → RecoveryResource IDlari.
Dependency: from_type/from_id → to_type/to_id (from **to ga bog‘liq**).
ScheduleRun → kirish nusxasi, A/B natijalar, algoritm versiyasi, muallif.
BusinessProcess → ContinuityPlan → PlanStep; reja previous_version va schedule_run bilan bog‘langan.
Scenario → SimulationRun; Scenario va tasdiqlangan ContinuityPlan → Exercise.
Har tenant yozuvda organization; Control va PlanStep ota yozuv orqali izolyatsiyalanadi.

BIA, strategiya, ssenariy va mashq vaqtlarining kanonik nusxasi butun **soniyalarda**.
Eski soat/daqiqa maydonlari API mosligi uchun saqlandi; `save()` ularni soniyaga
aylantiradi va migratsiya avvalgi yozuvlarni to‘ldiradi. Jadval hisobida butun daqiqalar:
davomiylik yuqoriga, RTO pastga yaxlitlanadi (ehtiyotkor chegaralash).

## Ruxsatlar jadvali

| Amal | Admin | BCMS menejer | Jarayon egasi | Risk tahlilchisi | Tasdiqlovchi | Auditor |
|---|---|---|---|---|---|---|
| Tashkilot ma’lumotlarini o‘qish | Ha | Ha | Ha | Ha | Ha | Ha |
| Profil / foydalanuvchi / rolni o‘zgartirish | Ha | Yo‘q | Yo‘q | Yo‘q | Yo‘q | Yo‘q |
| Bo‘lim / xizmat / aktiv / bog‘liqlik / resurs yozish | Ha | Ha | Yo‘q | Yo‘q | Yo‘q | Yo‘q |
| Jarayon / BIA / strategiya / qoralama reja / mashq yozish | Ha | Ha | Faqat o‘z jarayoni | Yo‘q | Yo‘q | Yo‘q |
| Risk va nazorat chorasi yozish | Ha | Ha | Risk: o‘z jarayoni; control yo‘q | Ha | Yo‘q | Yo‘q |
| BIA / reja tasdiqlash; reja arxivlash | Ha | Yo‘q | Yo‘q | Yo‘q | Ha | Yo‘q |
| Jadval hisoblash / ssenariy simulyatsiyasi | Ha | Ha | Yo‘q | Yo‘q | Yo‘q | Yo‘q |
| PDF/DOCX/CSV eksport, auditni o‘qish | Ha | Ha | Ha | Ha | Ha | Ha |
| Audit / saqlangan hisob natijasini tahrirlash | Yo‘q | Yo‘q | Yo‘q | Yo‘q | Yo‘q | Yo‘q |

Backend `DomainPermission`, `TenantViewSet.get_object` va `TenantSerializer`
qoidalarni tekshiradi. Frontend ko‘rinishi shu tekshiruvning qo‘shimchasidir.
Tashkilotlararo ID — 404; tashqi tashkilot FK yoki raqamli dependency — 400.
Hatto API superuserining oddiy resurs o‘qishi ham o‘z tenantiga cheklangan.
Tashkilotsiz superuser birinchi tashkilotni yaratib o‘ziga biriktirishi mumkin;
oddiy tashkilot admini boshqa tenant ocholmaydi. Yangi tenant uchun xavfsiz
`bootstrap_organization` boshqaruv buyrug‘i mavjud.

## Xavfsizlik va hayot sikli

Sessiya cookie + CSRF yagona usul; Basic auth o‘chirildi. Token localStoragega yozilmaydi.
Login anonim so‘rovda ham CSRF tekshiradi; login/logout/parol yangilanishida token aylanadi.
8 soat sessiya muddati; browser yopilganda tugash; logout server sessiyasini bekor qiladi.
Parol almashganda eski sessiyalar hash orqali yaroqsiz bo‘ladi, joriy sessiya saqlanadi.
Oxirgi faol administratorni pasaytirish/o‘chirish rad etiladi; user delete deaktivatsiya.

Tranzaksiyalar ichki BIA ta’sirlari, reja bosqichlari va auditni birga saqlaydi.
RTO < MTPD, ball diapazonlari, musbat resurs quvvati, bosqich tartibi uchun DB cheklovlari bor.
BaseTenantModel yozuvlari soft-delete; bog‘liq faol yozuv yoki ssenariy bo‘lsa delete 409.
Tasdiqlangan/arxiv reja API orqali tahrirlanmaydi yoki o‘chirilmaydi; PDF/DOCX
snapshotdan olinadi. Eski tasdiqlangan rejalar migratsiyada mavjud mazmun bilan muzlatiladi.
Yangi versiya alohida qoralama; eski approver, vaqt va snapshot saqlanadi.

Audit o‘qish uchun; login, xato login, yozuvlar, rad etilgan ruxsat, tasdiqlash,
simulyatsiya va eksport qayd qilinadi. Yangi yozuvda rolning o‘sha paytdagi qiymati saqlanadi.
Eski auditdagi tarixiy rol ishonchli tiklanmagani uchun bo‘sh qoladi. Maxfiy kalit
nomlari audit payloadidan olib tashlanadi. API javoblari private/no-store.

HTTP xatolar: 400 validatsiya, 403 login/ruxsat/CSRF, 404 tenant doirasida topilmagan,
409 bog‘liqlik/takrorlash konflikti, 429 login chegarasi. Maydon xatolari DRF formatida saqlandi.
