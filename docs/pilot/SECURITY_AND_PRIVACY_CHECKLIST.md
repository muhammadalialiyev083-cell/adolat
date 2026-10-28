# Xavfsizlik va maxfiylik tekshiruvi

Har band: [kutilmoqda/o‘tdi/o‘tmadi], mas’ul, sana va dalil havolasi bilan qayd etilsin.

- DEBUG=false; kuchli SECRET_KEY; aniq HTTPS origin va hosts; TLS/cookie/CSRF.
- PostgreSQL UTF-8; runtime roli superuser emas; DDL roli alohida; TLS tekshirilgan.
- Har rolga tegishli huquq; boshqa tenant ID/FK/M2M rad etilishi.
- Mustaqil tasdiqlash siyosati kerak bo‘lsa organization.separation_of_duties yoqilgan.
- Umumiy DB login limiti; ishonchli ingress REMOTE_ADDR; counter cleanup.
- Import limiti, explicit confirmation, rollback va vaqtinchalik ma’lumot cleanup.
- Audit/servis loglarida parol, token, cookie, authorization va query yo‘qligi.
- IdP subject mapping operator tomonidan ko‘rilgan; avtomatik rol/provisioning yo‘q.
- Monitoring HMAC kaliti faqat deploymentda; vaqt sinxron; relay ruxsati tekshirilgan.
- Dalil havolalari cheklangan omborga; faylga kirish va retention alohida boshqarilgan.
- Backup shifrlangan; alohida bazaga restore amalda tekshirilgan.
- Dependency/secret scan, UAT, load va tashqi xavfsizlik baholashi qayd etilgan.

To‘ldirilmagan band o‘tgan hisoblanmaydi. Bu ro‘yxat penetration audit yoki
ISO muvofiqlik sertifikati o‘rnini bosmaydi. Ma’lumot uchun vakolat va qonuniy
asosni tashkilotning ma’lumot egasi tasdiqlaydi.
