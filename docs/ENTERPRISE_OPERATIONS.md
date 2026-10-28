# Enterprise v1.1 operator yo‘riqnomasi

Production deploy bu ishda bajarilmadi. Quyidagi tekshiruvlar stagingda operator
va ma’lumot egasi tomonidan haqiqiy konfiguratsiya bilan bajariladi.

## Xavfsiz ishga tushirish

Python 3.12, Django 5.2, PostgreSQL UTF-8. `backend/requirements.lock` barcha
production transitive versiyalarni nazorat qiladi; `pip install -r requirements.lock`.
Dev test talablari requirements-dev.txtda. Frontend `npm ci`, lockfile saqlangan.
DEBUG=false, kamida 50 belgili SECRET_KEY, aniq ALLOWED_HOSTS, HTTPS trusted origins,
Secure/HttpOnly cookie, HSTS va same-origin proxy. .env.exampleda maxfiy qiymat yo‘q.
DB runtime roli superuser/CREATEDB/DDL huquqisiz, faqat kerakli schema DML; migration
uchun alohida vaqtinchalik rol. DB TLS/certificate siyosatini provayder bilan tasdiqlang.

Ingress X-Forwarded-Forni browserdan ko‘chirib ishonmasin; `REMOTE_ADDR` haqiqiy
manba bo‘lishini ishonchli proxy ta’minlasin. Login DBda 10/minut/peer fixed window;
chegarada ikki oynaning burst imkoniyati bor. Bir proxy IP ortidagi barcha loginlar
bo‘linadi: to‘g‘ri peer sozlamasi va staging yuk testi zarur. DB unavailable → login 503.
Redis majburiy emas; hisoblagichlar umumiy PostgreSQLda barcha workerlar uchun atomar.

Operator jadvali: `python manage.py purge_imports` kamida har 15 daqiqa;
`python manage.py purge_login_limits` kunlik (monitoring counterlari ham).
Bu buyruqlar avtomatik tashqi cron yaratmaydi. Preview expiry kirishni darhol yopadi,
cleanup jismoniy tozalashni bajaradi; backup retentionni ham tashkilot belgilaydi.
2 MB/1000 qator importga reverse proxy body limiti va 60 soniyalik request timeout
qo‘ying; stagingda memory/CPU o‘lchang. Raw fayl doimiy media sifatida saqlanmaydi.

/healthz process, /readyz DB+pending migrations. 5xx, 429, readyz503, dead-letter,
DB ulanishi, jadval o‘sishi va cleanup yoshi uchun operator alertlarini sozlang.
Production JSON logger faqat allowlist event/status/exception_type chiqaradi;
body/query/cookie/exception matni yo‘q. Gunicorn/proxy access loglarini ham sozlang:
OIDC callback query (code/state) va Authorization/Cookie hech qachon yozilmasin.
O‘zaro kelishilgan alert/retention chegaralari pilot charterda belgilanadi.

## OIDC operator konfiguratsiyasi

Django operator adminida IdentityProvider yarating: organization, unique slug,
name, exact HTTPS issuer, client_id, client_secret_env, exact HTTPS redirect_uri,
required_groups. Enabled sukutda false. Deploymentda shu secret envni bering;
qiymatni repoga yoki frontendga yozmang. Redirect URI IdPda aynan ro‘yxatdan o‘tsin:
`https://<app-origin>/api/v1/auth/sso/<slug>/callback`. TLS tekshiruvi o‘chirilmaydi.
Issuer/discovery/authorization/token/JWKS domenlariga nazoratli outbound kirish kerak.

Mavjud tenant userni operator ko‘rib bog‘laydi:
`python manage.py link_external_identity --provider <slug> --username <existing-user> --subject <reviewed-subject>`.
Bu buyruq user yaratmaydi yoki rol bermaydi. Group policy bo‘lsa signed ID tokenda
groups claimni IdPda sozlang; missing/invalid claim rad etiladi. So‘ng test IdP UAT.
Bu repositorydagi mock RS256 sinovi real provider tekshiruvini almashtirmaydi.

Local admin recovery: vakolatli operatorning oddiy `changepassword` interaktiv
buyrug‘i; TLS, CSRF va throttling saqlanadi. Recovery hisob egasi, foydalanish sababi
va audit nazorati oldindan belgilanadi. Default parol yoki hidden bypass yo‘q.
Native LDAP qo‘shilmagan; ADni federation orqali ulash tavsiya etiladi.
IdPda bekor qilingan group sessionga darhol yetib kelmaydi; RiskGuard identityni
o‘chirish yoki sessiyalarni operator nazoratida bekor qilish zarur. Max 8 soat sessiya.

## Monitoring reference relay

Operator adminida MonitoringIntegration (tenant, name, alertmanager_hmac,
secret_env, enabled) sozlanadi. Tasodifiy kamida 32 belgili HMAC kalit deploymentda.
Alertmanagerning oddiy webhooki o‘zi bu signature formatini bermaydi: ishonchli
korporativ relay Alertmanager payloadini imzolashi kerak. Reference JSON:
backend/tests/fixtures/alertmanager.json. To‘g‘ridan-to‘g‘ri real ulanish tekshirilmadi.

POST /api/v1/monitoring/webhook/<integration-uuid>, JSON maksimal 256 KiB/50 alert.
Headerlar: X-RiskGuard-Event-Id (ASCII key, 128 belgigacha), X-RiskGuard-Timestamp
(UTC Unix sekund, 5 daqiqalik oyna), X-RiskGuard-Signature (hex SHA256).
Imzo: HMAC-SHA256(secret, timestamp + "." + event_id + "." + raw_body_bytes).
Tenant URLdagi operator bindingdan; payloaddagi organization ID ishlatilmaydi.
60/minut/integration umumiy DB limiti. Har alert status/fingerprint/startsAt/labels/
annotations bilan normalizatsiya qilinadi. labels.process_id/asset_id shu tenantdan.

Replay bir event_id+body uchun idempotent; boshqa body bilan shu ID 409. Bir xil
fingerprint/startsAt/status yangi deliveryda ham ikkinchi alert yaratmaydi.
Noto‘g‘ri qator PARTIAL/DEAD_LETTER diagnostikasiga tushadi; to‘g‘ri qatorlar davom etadi.
Raw payload/credential saqlanmaydi; xatolar sanitized kod. Transient 5xx uchun relay
5/30/120 sekund backoff bilan ko‘pi bilan 3 marta bir event IDni qayta yuborsin.
4xx/schema uchun avtomatik cheksiz retry yo‘q; operator tuzatgan payload yangi ID
bilan yuboriladi. Delivery attempts counteri 100da chegaralangan.
Scheduled pull va boshqa providerlar qo‘shilmadi; MonitoringAdapter kontraktiga yoziladi.

## Upgrade, backup va rollback

1. Yozish oynasi va owner qarorini kelishing; DB shifrlangan backupini oling.
2. Alohida DBga restore qilib tenant/model soni, BIA/reja snapshotlari va eksportni tekshiring.
3. `showmigrations --plan`, `migrate --plan`; frontend build, test va dependency audit.
4. Stagingga migrate; eski API + yangi workflow UAT; keyin alohida production qarori.

Yangi migratsiyalar additive va reverse mumkin. Ammo reverse yangi jadval/dalillarni
olib tashlaydi; oldingi app buildiga qaytib additive schema qoldirish odatda xavfsizroq.
Schema downgrade zarur bo‘lsa avval yangi yozuvlarni eksport/backup qiling, quyidagi
migration targetlarini alohida tiklash bazasida rejalashtiring:

- monitoring zero; management zero; incidents zero (linked alert/tasklarni avval ko‘ring).
- imports zero; bia 0006; plans 0005; organizations 0002; authentication 0003.

`migrate <app> <target> --plan` boshqa app dependencylarini ham ko‘rsatadi; ko‘r-ko‘rona
production reverse yo‘q. Django migration graph bo‘yicha tartibni operator ko‘rib chiqadi.
`pg_dump --format=custom --file=<protected-backup>` va `pg_restore --no-owner --no-privileges`
faqat himoyalangan PG service/env ulanishi bilan; credential argument yoki tarixga yozilmasin.
SQLite lokal nusxa uchun read-only source + sqlite3 backup API ishlating.
Dalil metadata va snapshotlarni tiklash natijasida alohida tekshiring. WORM/forensik
ombor yoki DB administratoriga qarshi kriptografik immutable kafolat berilmaydi.
