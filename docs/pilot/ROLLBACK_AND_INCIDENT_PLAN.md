# Pilot rollback va xavfsizlik hodisasi rejasi

Trigger: tenant sizishi, autentifikatsiya buzilishi, tasdiqlangan nusxa o‘zgarishi,
ma’lumot yo‘qolishi, izohlanmagan import yoki xizmat ishlamasligi.
Hodisa egasi/eskalatsiya aloqalari: [tashkilot to‘ldiradi].

1. Operator yangi yozuvlarni to‘xtatadi; zarur integratsiyani o‘chiradi. Faol hodisa
   dalillarini yo‘qotmasdan vaqt, manba va bajarilgan amallarni qayd qiladi.
2. BCMS rahbari ta’sir va xabardor qilish doirasini ma’lumot egasi bilan kelishadi.
3. Backup va auditdan alohida tiklash bazasi yaratiladi. Productionga sinov restore yo‘q.
4. Oldingi build bilan schema mosligi tekshiriladi. Additive migratsiyalarni qoldirish
   odatda xavfsizroq; reverse yangi enterprise yozuvlarini yo‘qotadi.
5. Operator yo‘riqnomadagi oldingi migration targetlariga faqat backup va tasdiqlangan
   oyna bilan qaytadi. User/reja/BIA tarixini o‘chiruvchi reset ishlatilmaydi.
6. Ma’lumot soni, tenant, immutable snapshot, login va eksport tekshiriladi.
7. Homiy qayta ochish qarorini beradi; sabab va takrorlanishni oldini olish vazifasi yoziladi.

Texnik buyruqlar va targetlar: ../ENTERPRISE_OPERATIONS.md. Bu reja live secrets,
DNS yoki production DBni o‘zgartirishga avtomatik ruxsat bermaydi.
