# Deploy, health va backup

## Amaldagi konfiguratsiya haqida topilgan dalil

`frontend/public/_redirects`: `/api/*` → `https://adolat-99us.onrender.com/api/:splat`
va undan keyin SPA fallback. Frontendda /api/v1 nisbiy yo‘l ishlatiladi; login va
eksport bir origin proksi orqali. `netlify.toml` mavjud frontend/ buildini ko‘rsatadi.
Tashqi Dashboard hisoblariga kirilmagan; konfiguratsiya faol ekani tasdiqlanmaydi.

Renderning joriy Markdown/HTML hujjati va JSON schema so‘rovlari 403 bo‘ldi.
`render.yaml.example` — faqat ko‘rib chiqish shabloni; schema/CLI validatsiyasi
bajarilmagan, amaldagi xizmat nomini taxmin qilib boshqarishga ulanmagan.

## Production muhit

- `DEBUG=false`; kamida 50 belgili maxfiy `SECRET_KEY`ni platformadan bering.
- `DATABASE_URL` haqiqiy PostgreSQL ulanishi bo‘lsin; production SQLite rad etiladi.
- `ALLOWED_HOSTS`: amaldagi backend domeni, protokolsiz.
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`: aniq HTTPS frontend originlari.
  Mavjud yo‘naltirishga ko‘ra frontend `https://safeguardity.netlify.app` bo‘lishi
  mumkin; haqiqiy sayt domeni Dashboardda tekshirilib shunga mos kiritilsin.
- `DATABASE_SSL_REQUIRE=true` tashqi TLSli DB uchun; ichki ulanish talabi boshqacha
  bo‘lsa provayderning tasdiqlangan ko‘rsatmasiga moslang. TLSni ko‘r-ko‘rona o‘chirmang.
- Same-origin Netlify proksisi bilan `COOKIE_SAMESITE=Lax`; cookie Secure va HttpOnly.
  APIga to‘g‘ridan-to‘g‘ri cross-site murojaat uchun None/Secure hamda browser uchinchi
  tomon cookie siyosati alohida tekshirilishi kerak. Tavsiya: same-origin proksi.
- HTTPS redirect, HSTS, nosniff va clickjacking himoyasi yoqilgan. TLS termination
  uchun ishonchli platforma X-Forwarded-Proto uzatishi zarur.
- `.env` fayli versiya nazoratiga kirmaydi. Productionda demo seed ishlamaydi.
  Boshlang‘ich hisob uchun interaktiv bootstrap buyrug‘i yoki faqat birinchi migrate
  paytida BCMS_INITIAL_ADMIN_PASSWORD beriladigan opt-in eski migratsiya mavjud;
  maxfiy qiymatni ish tugagach platformadan olib tashlang.

Backend alohida Render web service bo‘lsa:

```bash
# Root directory: backend
pip install -r requirements.txt
python manage.py collectstatic --noinput
# Alohida pre-deploy yoki boshqaruv qadamida:
python manage.py migrate --noinput
# Run:
gunicorn bcms_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 60
```

Django o‘zi ham UIni bersin desangiz deploy buildida `frontend` uchun Node/npm va
`npm ci && npm run build` qadamini ham bajaring. Faqat API deployida frontend buildi
bo‘lmasa `/` JSON holatini beradi; health uchun `/healthz`dan foydalaning.

`/healthz` — process tirikligi (200). `/readyz` — DB SELECT1 va pending migrations
yo‘qligi (200/503). Istisno tafsiloti va DB ulanish qiymati tashqariga chiqarilmaydi.
API javoblari private/no-store; PDF/DOCX xotirada generatsiya qilinadi. Import fayllari vaqtinchalik passiv parserda tekshiriladi; doimiy
media sifatida saqlanmaydi. Preview TTL/cleanup va tashqi dalil ombori talablari
ENTERPRISE_OPERATIONS.mdga yozilgan. SQLite production ephemeral disk uchun qo‘llanmaydi.

## PostgreSQL backup va tiklash

DB credentialni buyruq argumentiga yoki tarixiga yozmang; himoyalangan `PGSERVICE`
profilidan yoki faqat joriy shellga kiritilgan `PGHOST/PGUSER/PGDATABASE/PGPASSWORD`
qiymatlaridan foydalaning. Parol fayli bo‘lsa ruxsat 0600.

```bash
# Mos PG klient versiyasi; PGSERVICE kerakli manbani tanlaydi.
pg_dump --format=custom --file=bcms-backup.dump
# Alohida, bo‘sh restore_test bazasini operator yaratadi.
# So‘ng shell profilini TEST bazaga o‘zgartiring va qayta tekshiring:
pg_restore --no-owner --no-privileges --dbname=restore_test bcms-backup.dump
```

Restore hech qachon real production bazasida sinov uchun bajarilmaydi. Sinovdan
so‘ng jadvallar soni, migratsiya holati, tenantlar, BIA vaqtlarining muvofiqligi,
reja snapshotlari va eksportlarni tekshiring. Backup ham shaxsiy ma’lumot;
shifrlangan, cheklangan ombor, saqlash muddati va qayta tiklash davri belgilang.

SQLite lokal nusxa uchun ishlayotgan DB faylini oddiy copy qilish o‘rniga Python
sqlite3 backup API yoki sqlite `.backup`dan foydalaning. Shu ishda foydalanuvchi
bazasi faqat read-only ochilib alohida test nusxaga backup qilindi; migratsiyalar
faqat shu nusxaga qo‘llandi. PostgreSQL pg_dump/pg_restore sinovi ham alohida lokal
serverda bajarildi; natija test hisobotida.

Tashqi deployni yakunlash uchun kerak bo‘ladigan ma’lumotlar: mavjud Render xizmat
identifikatori/huquqi, Netlify sayt huquqi, haqiqiy PostgreSQL ulanishi, HTTPS domenlari
va SECRET_KEY. Bu ishda ular olinmagan, pulli resurs yaratilmagan.

Enterprise v1.1 deploy/rollback va OIDC/HMAC sozlamalari: ENTERPRISE_OPERATIONS.md.
