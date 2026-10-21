# Topshirish hisoboti · 2026-10-21

1. **Bajarilgan o‘zgarishlar.** Ish `feat/bcms-connected-workflow` branchida.
   Mavjud RiskGuard/Django/React tuzilmasi saqlandi. Tenant FK/ID nazorati,
   backend RBAC/ownership, CSRF/sessiya, oxirgi administrator himoyasi,
   xavfsiz demo/provision, approval bypass himoyasi va muzlatilgan reja
   snapshotlari qo‘shildi. Formada qidiruv/sahifalash, nested saqlash, validatsiya,
   tranzaksiya va audit ishlaydi. BIA va vaqt normalizatsiyasi, ikki tiklash
   algoritmi, saqlangan hisoblashlar, risk matritsasi va grafik, usta, mashqlar,
   PDF/DOCX/CSV hamda o‘zbekcha milliy light dizayn tayyorlandi.

2. **Ishlaydigan modullar.** Tashkilot/bo‘lim/xodim/rol/xizmat;
   jarayon/aktiv/bog‘liqlik; BIA va tasdiqlash; risk/nazorat; strategiya/resurs;
   A/B tiklash jadvali; reja/versiya/tasdiqlash/arxiv; xavfsiz ssenariy va
   natijalar tarixi; kuzatilgan mashq/kamchilik; dashboard/filtr/eksport/audit.
   Mavjud ma’lumotlar test uchun o‘chirilmagan: original SQLite read-only
   nusxalandi; upgrade nusxada 3 user, 4 process, 1 plan saqlanib qoldi.

3. **Sinov dalillari.** SQLite **86/86** (24.49 s); alohida lokal PostgreSQL
   **86/86** (28.28 s). Client **10/10**. Ruff, ESLint, typecheck, Django check,
   migration check va production build o‘tdi. `check --deploy --fail-level WARNING`
   sozlamalar bo‘yicha xatosiz. Chromium smoke — desktop/mobil, noto‘g‘ri login,
   CRUD/reload, dirty forma/Escape, API 503/retry, logout/auditor/sessiya.
   PDF/DOCX parserlar bilan qayta ochildi, Unicode va ko‘p sahifa mazmuni tekshirildi.
   PostgreSQL pg_dump/pg_restore: 4 process va 4 normalizatsiyalangan BIA tiklandi.
   Bu dalillar production penetratsion/yuk auditi emas.

4. **Ishga tushirish.** Python 3.12 virtual muhitda
   `pip install -r backend/requirements-dev.txt`; `.env.example`dan `.env`
   yarating: DEBUG=true, yangi SECRET_KEY, aniq lokal ALLOWED_HOSTS; bo‘sh
   ortiqcha qatorlarni olib tashlang. Keyin:

   ```bash
   cd backend
   python manage.py migrate
   python manage.py bootstrap_organization --name "Mening tashkilotim" --sector "Ta’lim" --username tashkilot_admin
   cd ../frontend
   npm ci
   npm run build
   cd ../backend
   python manage.py runserver 127.0.0.1:8000
   ```

   Parol interaktiv kiritiladi. To‘liq ko‘rsatma READMEda.
   Alohida demo bazasi uchun BCMS_DEMO_PASSWORDni o‘zingiz belgilang va
   `python manage.py seed_demo_data`ni bajaring; productionda bu buyruq rad etiladi.
   Tekshiruv: virtual muhit faollashtirilgach `bash scripts/check.sh`.

5. **Tashqi kirish bilan tekshirilmagan qismlar.** Render/Netlifyga deploy
   bajarilmadi, pulli resurs yaratilmagan. Mavjud API redirect saqlandi.
   Haqiqiy hosting hisoblari, PostgreSQL production URL, HTTPS domenlar va maxfiy
   kalitlar kerak. Joriy Render schema/hujjatlari va tashqi ilmiy manba so‘rovlari
   tarmoq siyosati bilan 403 bo‘ldi. `render.yaml.example` validatsiyadan o‘tgan
   Blueprint emas; mustaqil ko‘rib chiqish shabloni. DOI va to‘liq maqola usullari
   tasdiqlanmadi; to‘liq ISO muvofiqligi yoki sertifikati da’vo qilinmaydi.

6. **Qolgan aniq cheklovlar.** Ilmiy asoslangan avtomatik RTO/MTPD tavsiyasi
   chiqarilmaydi; mas’ul kiritadi va rahbariyat tasdiqlaydi. Productionda umumiy
   login rate-limit cache/proksi, haqiqiy yuk va xavfsizlik auditi kerak.
   Aniq malaka/smena/geografiya uchun resurslar qo‘lda modellashtiriladi.
   Grafning SVG qismi bir vaqtda 60 tugun; kattaroq to‘plam qidiruv/ro‘yxat orqali.
   Email reset, import va upload kiritilmagan. Tarixiy FastAPI backend asosiy
   regressiya to‘plamiga kirmaydi; faol mahsulot Django. Batafsil LIMITATIONS.md.

Uchta sun’iy tajriba: parallel misolda A=120/B=60 daqiqa; prerequisite misolida
ikkalasi 120 daqiqa, ammo A dependency tartibini buzadi, B bajariladi; resurs
quvvati 0 bo‘lgan misolda ikkala usul ham bajarilmaydi. Bu real tashkilotdagi
samara isboti emas, insonning reja tuzish vaqti o‘lchanmagan.
