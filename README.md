# RiskGuard · BCMS Designer

Tashkilotlarda biznes uzluksizligini loyihalash: tashkilot → jarayon va aktivlar →
BIA → risk → tiklash strategiyasi va resurslar → taqqoslanadigan jadval →
versiyalangan reja → tasdiqlash → xavfsiz simulyatsiya/mashq → hisobot.
Mavjud RiskGuard nomi va Django/React arxitekturasi saqlandi.

Dastlabki loyiha: Farg‘ona davlat texnika universiteti magistrlik dissertatsiyasi;
Aliyev Muhammadali G‘ulomjon o‘g‘li, ilmiy rahbar Turdimatov Mamirjon Mirzayevich;
70610302 — Axborot xavfsizligi.

Django **5.2.18**, DRF **3.18.3**, Python **3.12**; React **18**, TypeScript/Vite.
Lokal SQLite va alohida PostgreSQLda tekshirilgan. `backend_fastapi/` tarixiy,
faol mahsulotning ishga tushirish yo‘liga kirmaydi.

## Enterprise Pilot v1.1 nomzodi

Xavfsiz CSV/XLSX import, dalilli BIA ustasi, rahbariyat/vazifalar, hodisalar,
imzolangan monitoring adapteri, OIDC va yangi UzHi login qo‘shildi. Production
deploy yoki real tashkilot piloti bajarilmadi. Holat va tashqi tekshiruvlar:
[Enterprise release](docs/ENTERPRISE_V1_1_RELEASE.md), [API/UI](docs/ENTERPRISE_API.md),
[operator yo‘riqnomasi](docs/ENTERPRISE_OPERATIONS.md), [pilot hujjatlari](docs/pilot/PILOT_CHARTER.md).

Reproduktiv o‘rnatish: `pip install -r backend/requirements-dev.lock`; production
uchun `backend/requirements.lock`. Dev auditida pypdf 6.21.2ga yangilandi.

## Lokal o‘rnatish

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cp .env.example .env
```

`.env`da quyidagilarni to‘ldiring (namunadagi qolgan bo‘sh qatorlarni olib tashlang):

- `DEBUG=true`
- `SECRET_KEY`: `python -c "import secrets; print(secrets.token_urlsafe(48))"` bilan o‘zingiz yarating.
- `ALLOWED_HOSTS=localhost,127.0.0.1,testserver`
- `DATABASE_URL`ni olib tashlasangiz lokal `backend/db.sqlite3` ishlatiladi;
  yangi mustaqil baza uchun `sqlite:////absolute/path/local.sqlite3` kiriting.
- Lokal HTTP uchun cookie sozlamasi avtomatik Lax; production talablari boshqa.

```bash
cd backend
python manage.py migrate
python manage.py bootstrap_organization --name "Mening tashkilotim" --sector "Ta’lim" --username tashkilot_admin
# Parol terminalda yashirin kiritiladi; standart parol yo‘q.
cd ../frontend
npm ci
npm run build
cd ../backend
python manage.py runserver 127.0.0.1:8000
```

`http://127.0.0.1:8000` — tayyor frontend va API bir manzilda.
Frontend ishlab chiqish uchun `cd frontend && npm run dev`: Vite `/api`ni Django :8000ga uzatadi.
Frontend har o‘zgarganda Django orqali ko‘rish uchun `npm run build`ni takrorlang.
Windowsda virtual muhitni `.venv\Scripts\Activate.ps1` orqali faollashtiring.

## Alohida o‘quv to‘plami

Faqat alohida DEBUG=true bazada, foydalanuvchi tanlagan kuchli parol bilan:

```bash
# BCMS_DEMO_PASSWORD ni .envda o‘zingiz belgilang; terminal tarixiga parol yozmang.
cd backend
python manage.py seed_demo_data
```

Hisoblar: `demo_admin`, `demo_manager`, `demo_owner`, `demo_auditor`, `demo_approver`.
Buyruq mavjud parollarni almashtirmaydi, productionda rad etiladi.
Sun’iy universitet, to‘rtta jarayon, BIA/risk/strategiyalar, resurs va olti ssenariy yaratiladi.
Tasdiqlangan reja yoki muvaffaqiyatli mashq avtomatik to‘qilmaydi.

## Ishchi yo‘l

1. Tashkilot aloqalari, bo‘lim, xodim/rol va xizmatlarni kiriting.
2. Jarayon mas’uli, tavsifi, bo‘limi, ish vaqti va resurslarini aniqlang.
3. Aktiv va yo‘naltirilgan bog‘liqliklarni kiriting: A → B — A ishlashi uchun B zarur.
4. BIAda vaqt bo‘yicha ta’sir, sabab, manba va RTO/MTPD/RPOni kiriting. RTO < MTPD.
5. Risk va nazorat choralarini baholang; ehtimollik 1–5 ordinal ball.
6. Tiklash resurslari va strategiya variantlarini kiriting; jadvalda A/B usullarini hisoblang.
7. Rejani to‘ldiring, saqlangan jadvalga bog‘lang va BIAni tasdiqlang. So‘ng rejani tasdiqlang.
8. Tasdiqlangan nusxa tahrirlanmaydi: «Yangi versiya» qoralama yaratadi.
9. Simulyatsiya faqat hisoblashdir. Mashqda kuzatilgan vaqt va kamchiliklarni alohida saqlang.
10. PDF/DOCX/CSV yoki dashboarddan haqiqiy saqlangan ma’lumotlarni oling.

## Tekshiruv

```bash
# Faollashtirilgan virtual muhit, to‘ldirilgan lokal .env bilan:
bash scripts/check.sh
# Yoki backend/ ichida: python -m pytest
# frontend/ ichida: npm run lint && npm run typecheck && npm test && npm run build
```

2026-10-21 holatida 86 backend testi SQLite va alohida PostgreSQLda,
10 frontend client testi, Chromium smoke sinovi, lint/typecheck/build o‘tdi.
To‘liq yo‘l integratsion API testida bajariladi. Brauzer sinovi alohida buyruq:

```bash
# Avval alohida demo bazani ishga tushiring, frontendni build qiling.
# BCMS_E2E_PASSWORD va BCMS_E2E_USERNAME ni muhitga o‘zingiz bering.
# Linuxda mavjud Chromium manzili BCMS_CHROMIUM_PATH bilan o‘zgartiriladi.
python frontend/tests/browser_smoke.py
```

Bu sinov demo muhitida yangi bo‘lim yaratadi; real tashkilot bazasida ishlatmang.
PostgreSQL testini mavjud ajratilgan test serveri bilan takrorlash:
`DATABASE_URL`, `DATABASE_SSL_REQUIRE`, `DEBUG=true`ni moslab `cd backend && python -m pytest`.
Django faqat `test_...` bazani yaratadi; production ulanishini testga bermang.

```bash
cd backend
python manage.py benchmark_schedules --repeats 10 --output ../work/experiment-results.json
```

Tajriba sun’iy: bir xil kirish, ikkita usul, o‘lchangan hisoblash vaqti va cheklovlar.
Reja tayyorlashning inson vaqti o‘lchanmagan; haqiqiy tashkilot samaradorligi isbotlanmagan.

## Hujjatlar

- [Topshirish hisoboti](docs/DELIVERY_REPORT.md)
- [Audit va funksional matritsa](docs/FUNCTIONAL_MATRIX.md)
- [Arxitektura va rollar](docs/ARCHITECTURE.md)
- [Algoritmlar va taxminlar](docs/ALGORITHMS.md)
- [Ilmiy tayanch va tekshirish holati](docs/SOURCES.md)
- [Deploy va backup](docs/DEPLOY_BACKUP.md)
- [Test hisoboti](docs/TEST_REPORT.md)
- [Ma’lum cheklovlar](docs/LIMITATIONS.md)
- [Ish davomiyligi](docs/PROGRESS.md)

Render yoki Netlifyga bu ish davomida tashqi deploy qilinmadi. Mavjud Netlify API
yo‘naltirishi saqlandi; `render.yaml.example` faqat tekshirish uchun nomzod shablon.
ISO sertifikati yoki to‘liq standart muvofiqligi da’vo qilinmaydi.
