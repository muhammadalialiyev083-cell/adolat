# Metrikalar va yig‘ish tartibi

Bazaviy/yakuniy sana, tenant, filtr, hisoblash versiyasi va dalil havolasi saqlansin.
0 denominator bo‘lsa natija N/A; bo‘sh ma’lumot 100% yoki nol muvaffaqiyatsizlik emas.

| Metrika | Ta’rif / manba |
|---|---|
| BIA qamrovi | Eng so‘nggi tasdiqlangan BIAga ega faol jarayon / doiradagi faol jarayon ×100 |
| Reja qamrovi | Tasdiqlangan/published rejali jarayon / doiradagi jarayon ×100 |
| Risk bahosi | ASSESSED/MITIGATED/ACCEPTED risklar va jami son alohida |
| Ochiq kamchilik | Exercise.findings bo‘sh emas va findings_closed=false |
| Muddati o‘tgan vazifa | due_date < bugun, status DONE/CANCELLED emas |
| Mashq bajarilishi | Haqiqiy bajarilgan / kelishilgan mashqlar ×100; denominator pilot reyestridan |
| Tiklash vaqti/RTO | Kuzatilgan Exercise.actual_recovery_seconds vs tasdiqlangan reja/BIA snapshot |
| Reja ishlab chiqish vaqti | Kuzatilgan start/finish, faol ish daqiqalari, tanaffuslar alohida |
| User vazifa vaqti | UAT amal start/finish, yordam soni va yakun holati |
| Foydalanish qulayligi | Anonim rozilikli 1–5 baho, respondent soni va erkin izoh |

Management API kutilayotgan tasdiq, overdue, kamchilik, risk va reja ko‘rik sonini
saqlangan yozuvlardan beradi. Inson vaqtini dastur avtomatik o‘lchagan deb
da’vo qilinmaydi: UAT kotibi nazoratli kuzatuv varag‘ida qayd qiladi.
Sun’iy mashqlar va real kuzatuvlar alohida cohort; simulyatsiya natijasi real tiklash emas.
