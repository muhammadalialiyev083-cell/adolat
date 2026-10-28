# Rollar va javobgarlik

| Rol | Mas’uliyat | Chegara |
|---|---|---|
| Homiy | Doira, resurs va qabul qarori | Texnik audit o‘rnini bosmaydi |
| Operator | Deployment, backup, IdP/relay sozlamasi | Runtime DB va DDL huquqi ajratiladi |
| ADMIN | Tenant foydalanuvchilari va ruxsatlari | Yashirin tiklash bypassi yo‘q |
| BCMS_MANAGER | Inventar/import, vazifa va hodisa koordinatsiyasi | BIA/reja tasdig‘i berilmagan |
| PROCESS_OWNER | O‘z jarayoni BIA/rejasi; biriktirilgan vazifa | Boshqa egaga yozish yo‘q |
| RISK_ANALYST | Risk va choralarni baholash | Rolni oshira olmaydi |
| APPROVER | BIA/rejani ko‘rib tasdiqlash/rad etish | Dalil va mustaqillik talabiga bo‘ysunadi |
| AUDITOR | Tenant ma’lumot va auditini ko‘rish | Yozish yo‘q |
| Mashq kotibi | Haqiqiy kuzatuv, vaqt va kamchilik dalili | Simulyatsiyani real natija demaydi |

Shaxslar va o‘rinbosarlar [to‘ldiriladi]. Kirish berish/olib tashlash talabini
ma’lumot egasi tasdiqlaydi. Har tashqi subject alohida tenant foydalanuvchisiga
bog‘lanadi. Tashkilotsiz superuser oddiy tenant resurslariga kira olmaydi.
