# Pilot UAT ssenariylari

Haqiqiy bajarilish: **kutilmoqda**. Har ssenariy uchun foydalanuvchi/rol, sana,
versiya, kutilgan va kuzatilgan natija, screenshot/API/audit ID, nuqson va qaror yozilsin.

| ID | Amal | Qabul mezoni |
|---|---|---|
| U01 | To‘g‘ri/xato login, logout, sessiya tugashi | Generic xato, password tozalanadi, sessiya bekor |
| U02 | Keyboard, mobil, reduced motion, ikki mavzu | Fokus ko‘rinadi, maydonlar kesilmaydi |
| U03 | CSV/XLSX upload → mapping → preview → confirm | Tasdiqqacha domen yozuvi yo‘q, Unicode saqlanadi |
| U04 | Takroriy key, zararli formula, boshqa tenant FK | Aniq xato; yashirin overwrite yoki sizish yo‘q |
| U05 | Commit o‘rtasida xato / stale preview | Butun import bekor; audit ham atomar |
| U06 | Dalilli BIA qoralama, review, approve | RTO < MTPD; yetishmagan dalil tasdiqqa o‘tmaydi |
| U07 | Tasdiqlangan BIA/rejani tahrirlash, revision | Eski nusxa o‘zgarmaydi, yangi draft |
| U08 | Mustaqil tasdiqlash siyosati | Muallif/egasi o‘zini tasdiqlay olmaydi |
| U09 | Vazifa assign, overdue, DONE, reopen | To‘g‘ri o‘tish va dalil; domen approval o‘zgarmaydi |
| U10 | Hodisa to‘liq hayot sikli, dalil, reopen | Vaqt/manba saqlanadi, closure saboqlarga bog‘liq |
| U11 | Imzolangan relay, replay, aralash paket | Tenant qat’iy, duplicate qo‘shimcha hodisa yaratmaydi |
| U12 | OIDC test IdP, noto‘g‘ri state/nonce/identity | Faqat reviewed subject; rol oshmaydi; local fallback |
| U13 | Tabletop va hisobot | Kuzatilgan vaqt tasdiqlangan RTO bilan solishtiriladi |
| U14 | Backup/restore va oldingi DB upgrade | Tenantlar, dalillar, tarix va snapshotlar saqlanadi |

Avtomatlashtirilgan fixture muvaffaqiyati real foydalanuvchi UAT imzosini almashtirmaydi.
