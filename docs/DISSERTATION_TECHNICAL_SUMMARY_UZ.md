# III bob uchun texnik natijalar: RiskGuard / BCMS Designer

## Arxitektura va tadqiqot chegarasi

Tizim biznes uzluksizligini boshqarish jarayonlarini qo‘llab-quvvatlovchi modulli monolit sifatida ishlab chiqilgan. Amaldagi server qismi Django REST Framework asosida, foydalanuvchi interfeysi React, TypeScript va Vite vositalarida tashkil etilgan. FastAPI varianti muqobil amalga oshirish sifatida saqlangan. Ikki backend bir vaqtning o‘zida ishlashi shart emas va ularning ma’lumotlar bazasi sxemalari o‘zaro almashtirilmaydi. Hisoblash qoidalari ORM va HTTP qatlamlariga bog‘liq bo‘lmagan `bcms_domain` paketida ifodalangan.

## Matematik algoritmlar

Risk balli ehtimollik va ta’sirning 1–5 oralig‘idagi baholari ko‘paytmasi bilan aniqlanadi. Bazaviy talqinda 1–6 past, 7–14 o‘rta va 15–25 yuqori risk hisoblanadi. Normallashtirilgan risk `(ball−1)/24` orqali hisoblanadi.

Jarayon ustuvorligi `U=0.40B+0.25T+0.20R+0.15D` modeli yordamida baholanadi. BIA tarkibidagi moliyaviy, operatsion, huquqiy va reputatsion ta’sir vaznlari mos ravishda 0.35, 0.25, 0.20 va 0.20 ni tashkil etadi. Moliyaviy zarar tashkilotning ruxsat etilgan zarar chegarasiga nisbatan, ordinal ko‘rsatkichlar esa `(baholash−1)/4` orqali normallashtiriladi. Tiklash shoshilinchligi `T=1−min(1,RTO/72)` ko‘rinishida aniqlanadi.

Mazkur vaznlar hamda 72 soatlik rejalashtirish gorizonti tadqiqotning boshlang‘ich farazlaridir. ISO 22301 ularning aynan shu qiymatlarda bo‘lishini belgilamaydi. Hisoblangan natijalarning mavjudligi modelning ilmiy jihatdan optimal ekanini tasdiqlamaydi. Yetishmayotgan ma’lumotlar uchun tarixiy moslikni saqlovchi taxminiy qiymatlar ochiq ogohlantirish bilan ko‘rsatiladi.

## Bog‘liqlikka asoslangan simulyatsiya

Yo‘naltirilgan grafda `PROCESS:A → ASSET:B` qirrasi A jarayonining B aktiviga bog‘liqligini bildiradi. Aktiv uzilganda unga bevosita yoki tranzitiv bog‘langan jarayonlar aniqlanadi. Sikllar cheksiz aylanishga, takroriy yo‘llar esa ikki marta sanashga olib kelmaydi. Faqat joriy tashkilotning faol obyektlari hisobga olinadi.

Izolyatsiyalangan aktiv uchun tasdiqlangan ta’sirlar soni nol bo‘ladi. Graf bo‘sh yoki to‘liq bo‘lmaganda bu natija tashkilot xavfsizligi dalili sifatida talqin qilinmaydi; ma’lumot sifati bo‘yicha ogohlantirish chiqariladi. Bunday ssenariylar real uzilish tajribasi emas, ro‘yxatga olingan bog‘liqliklar asosidagi hisoblash modelidir.

## Tiklash strategiyasini tanlash

Strategiya faqat taxminiy RTO belgilangan RTO dan va taxminiy RPO belgilangan RPO dan oshmaganida yaroqli deb hisoblanadi. Yaroqli variantlar orasidan ko‘rsatilgan taxminiy xarajati eng kichik variant tanlanadi. Narxi yoki vaqti ko‘rsatilmagan, manfiy yoki yaroqsiz sonli kirishlar rad etiladi. Teng xarajatlarda deterministik tartiblash qo‘llanadi; moliyaviy solishtirish Decimal aniqligida bajariladi.

Natija cheklovlar bajarilishi, rad etish sabablari va model taxminlari bilan tushuntiriladi. Bu resurslar taqsimoti, umumiy infratuzilma sig‘imi yoki noaniq tiklash vaqtlarini birgalikda optimallashtiradigan global model emas. Zaxiralash intervalining RPO dan oshishi ogohlantirish beradi, biroq intervalning o‘zi tiklashga muvofiqlikni isbotlamaydi.

## Xavfsizlik va ishonchlilik

FastAPI production rejimida majburiy konfiguratsiya bo‘lmasa ishga tushmaydi. Umumiy statik secret qiymatlar olib tashlangan, debug rejimi cheklangan va ruxsat etilgan originlar aniq belgilanadi. Django uchun ham production key va database tekshiruvlari kiritilgan. Session yozuvlarida CSRF tokenlari, tashkilot chegaralaridagi havolalarni tekshirish hamda o‘chirilgan obyektlarni hisobdan chiqarish qo‘llanadi. Demo-user yaratish vositalari production uchun taqiqlangan. Amaldagi audit, login va initial-admin mexanizmlari saqlangan.

## Eksperimental metodika va tekshirilgan natijalar

Django va SQLAlchemy adapterlari bir xil sun’iy BIA, risk va graf ma’lumotlari bilan tekshiriladi. Tayanch misolda B=0.62, T=0.9444, R=0.7917, D=1 hamda U=0.7924 qiymatlari ikkala amalga oshirishda mos keladi. Vaznlar ±0.05 ga o‘zgartirilib, qolgan vaznlar qayta normallashtiriladi; alohida komponent ablyatsiyasi, T_MAX va risk chegaralari bo‘yicha sezgirlik tahlillari bajariladi.

Noyob identifikatorlar tartibi uchun Kendall tau-a, asl sonli ballardagi tengliklarni hisobga olish uchun Kendall tau-b qo‘llanadi. Barcha qiymatlar teng bo‘lganda korrelyatsiya aniqlanmagan deb qaytariladi. Tau-b misollari mustaqil SciPy hisoblari bilan solishtirilgan. Qayta bajariladigan sun’iy ma’lumotlar va hosil qilingan natijalar repozitoriyda saqlanadi.

Aniq test sonlari, bajarilgan buyruqlar va cheklangan tekshiruvlar `TEST_RESULTS.md` da qayd etiladi. Avtomatlashtirilgan testlar dasturiy qoidalarning belgilangan misollarda bajarilishini tekshiradi; ular real tashkilotdagi samaradorlik, vaqt tejalishi, ekspert bahosi yoki ustunlik foizini isbotlamaydi.

## Cheklovlar va istiqboldagi ishlar

Ma’lumot sifati, yetishmayotgan BIA/risk taxminlari, graf qamrovi va tiklash baholarining ishonchliligi natijalarga ta’sir qiladi. PostgreSQL va haqiqiy hostingdagi integratsiya alohida tekshirishni talab etadi. Keyingi ishlar uchun mustaqil ekspert baholashi, tashkilotga tegishli empirik ma’lumotlar, tiklash mashqlari va resurs cheklovlarini hisobga oluvchi modellar taklif etilishi mumkin. Ushbu vazifada bunday empirik tajribalar o‘tkazilgani da’vo qilinmaydi.
