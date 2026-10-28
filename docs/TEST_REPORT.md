# Tekshiruv hisoboti · 2026-10-21

Sinovlar original bazaga tegmagan alohida SQLite/PostgreSQL muhitlarida bajarildi.
Haqiqiy production DB ishlatilmadi. Branch: `feat/bcms-connected-workflow`.

| Tekshiruv | Kuzatilgan natija |
|---|---|
| Boshlang‘ich frontend | Build va 10 client testi o‘tdi |
| Yakuniy Django check | Xatosiz |
| Production settings check --deploy --fail-level WARNING | Xatosiz; faqat sozlama tekshiruvi, tashqi deploy emas |
| Makemigrations --check --dry-run | Model/migratsiya farqi yo‘q |
| Backend SQLite | 86/86 o‘tdi; to‘liq yo‘l va xavfsizlik regressiyalari |
| Backend PostgreSQL | Alohida lokal PostgreSQLda 86/86 o‘tdi |
| Frontend client | 10/10 o‘tdi |
| ESLint / TypeScript | O‘tdi |
| Ruff | Backend va brauzer sinov kodi o‘tdi |
| Vite production build | O‘tdi |
| Mavjud SQLite struktura nusxasiga migration | O‘tdi; jadvallardagi avvalgi yozuvlar saqlandi |
| PDF/DOCX | Fayllar parser bilan ochildi, o‘zbekcha mazmun va snapshot tekshirildi |
| Chromium | Quyidagi amallar real UI bilan bajarildi |
| PostgreSQL backup/restore | pg_dump/pg_restore; 4 jarayon va 4 normalizatsiyalangan BIA tiklandi |

## Qamrov

To‘liq API yo‘li: CSRF login → yangi tashkilot → bo‘lim → xizmat → jarayon →
aktiv/bog‘liqlik → BIA/ta’sir → risk/nazorat → resurs/strategiya → jadval → reja →
BIA va reja tasdig‘i → yangi versiya → ssenariy/simulyatsiya → mashq →
PDF/DOCX/CSV → parolni yangilash → logout.

Qo‘shimcha testlar: cross-tenant FK va numeric dependency, ID/qidiruv/eksport,
superuser tenant chegarasi; auditor va qolgan rollar; owner hijacking; approval
status bypass; oxirgi admin; user deaktivatsiyasi; session/CSRF rotatsiyasi;
login cheklovi va maxfiy ma’lumotsiz audit; manfiy/nol/NaN/boundary qiymatlar;
vaznlar va BIA vaqt oraliqlari; nested update/transaction rollback; o‘chirish
konflikti; search/order/paging; kanonik soniyalar; CSV formula injection.

Hisoblash natijalari qo‘lda belgilangan misollar bilan tekshirildi: 60 daqiqalik
ikkita ish, 1/2 birlik quvvat, prerequisite tartibi, parallel/ketma-ket vaqtlar,
resurs bandligi, sikl, budjet/quvvat yetishmasligi va RTO buzilishi.
Assertionlar tekshirilayotgan funksiyaning o‘zi bilan ishlab chiqarilmagan.

Mavjud muvaffaqiyatli publish testlari endi to‘liq reja va tasdiqlangan BIA bilan
fixture oladi; audit/status/PDF assertionlari olib tashlanmadi. Initial-admin
testidagi tarixiy model snapshoti amaldagi test schema bilan moslashtirildi.

## Brauzer

`frontend/tests/browser_smoke.py`, Chromium `/usr/bin/chromium`, 1440×1000 va
390×844 viewportlar. Noto‘g‘ri va to‘g‘ri login, menyular, ma’lumot yaratish,
reload orqali qayta olish, tahrirlash, saqlanmagan formani bekor qilish va Escape,
API 503 xabari/retry, mobil gorizontal overflow, logout, auditor yozish amali
ko‘rinmasligi va sessiya tugashi tekshiriladi. Sahifa JS xatolari yig‘iladi.

Playwright browser download domeni 403 bo‘ldi, lekin muhitdagi mavjud Chromium
bilan sinov bajarildi. Test o‘tkazilmagan deb yashirilmaydi: haqiqiy browser ishlatildi.

## Chegaralar

API to‘liq yo‘li integratsion testda; barcha mumkin bo‘lgan brauzer amallari va
har brauzer/OS kombinatsiyasi to‘liq E2E qamrovida emas. Production trafik,
ko‘p worker rate limiting, real tashqi deploy va penetration test bajarilmadi.
Ilmiy manba va Renderning joriy platforma schema tekshiruvi tarmoq siyosati bilan bloklangan.

## Enterprise Pilot v1.1 · 2026-10-28

To‘liq `bash scripts/check.sh`: Ruff, Django check/migration drift, SQLite
**144 passed, 1 skipped** (PG-only concurrency), frontend lint/typecheck,
**13 client test**, build o‘tdi. PostgreSQL 17.11 UTF-8: **145 passed**, jumladan
8 parallel worker/20 login urinishidan 10 ruxsat. Eski va yangi Chromium smoke
sinovlari o‘tdi; enterprise JS xatolari 0. Production settings deploy-check o‘tdi;
bu production deploy yoki real korporativ xizmat tasdig‘i emas.

Original lokal SQLite faqat read-only backup orqali olingan nusxada migratsiya
oldinga/orqaga/oldinga sinovidan o‘tdi; 24 tarix/domen jadvali soni, 3 user/4 process/
1 plan saqlandi. Alohida PostgreSQL pg_dump/pg_restoreda approved BIA va plan
snapshotlari aynan saqlandi. Synthetic fixturelar haqiqiy pilot natijasi emas.

PyPI production va dev auditlari yakuniy 0 ma’lum zaiflik; npm audit 0. Dev pypdf
6.21.1dagi 3 CVE 6.21.2ga yangilash bilan bartaraf qilindi. Gitleaks 8.30.1,
staged tracked source: no leaks found. Tarixdagi barcha commitlar skan qilingan
deb da’vo qilinmaydi. To‘liq scope/cheklovlar ENTERPRISE_V1_1_RELEASE.mdda.
