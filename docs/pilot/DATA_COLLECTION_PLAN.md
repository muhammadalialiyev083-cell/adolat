# Ma’lumot yig‘ish rejasi

| To‘plam | Manba | Mas’ul | Tekshiruv |
|---|---|---|---|
| Bo‘lim/xizmat/jarayon | Tasdiqlangan inventar | BCMS menejer | Tenant, tashqi key, takrorlash |
| Aktiv va bog‘liqlik | Aktiv reyestri, tizim egasi | IT egasi | from → to: from to ga bog‘liq |
| BIA | Egasi intervyusi, hujjat, o‘lchov | Jarayon egasi | Sana, asos, sifat, RTO < MTPD |
| Risk va nazorat | Risk reyestri | Tahlilchi | 1–5 ordinal ball, qoldiq baho |
| Reja va resurs | Tasdiqlangan yo‘riqnoma | Tiklash rahbari | Immutability, resurs imkoniyati |
| Mashq kuzatuvi | Tabletop protokoli | Mashq kotibi | Sun’iy/kuzatilgan belgi |

Importdan oldin shaxsiy ma’lumotni kamaytiring. CSV UTF-8, XLSX oddiy bitta varaq;
2 MB/1000 qator/40 ustun. Formulani qiymatga almashtirishni manba egasi bajaradi.
FKlar shu tenantning mavjud IDlari; avval ota reyestrlar import qilinadi.
Barqaror `key`ni manba tizim reyestrida saqlang; nom o‘zgarganda key o‘zgarmaydi.

Fayl serverda doimiy saqlanmaydi. Preview qatorlari bazada 30 daqiqa amal qiladi;
commitdan keyin darhol tozalanadi. `purge_imports` kamida har 15 daqiqada ishlashi
operator tomonidan ta’minlanadi. Backupdagi retention tashkilot siyosatiga bog‘liq.
Dalil fayllari tasdiqlangan tashqi omborda, RiskGuardda faqat nazoratli havola.
Har manba uchun egasi, yig‘ish sanasi, maxfiylik darajasi va retention belgilang.
