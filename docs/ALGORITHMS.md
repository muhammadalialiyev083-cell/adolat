# Algoritmlar va taxminlar

## BIA va ustuvorlik

Moliyaviy ta’sir: min(1, zarar / tashkilotning max_acceptable_loss qiymati).
Operatsion/majburiyat/obro‘ ballari: (ball−1)/4, ball 1..5.
BIA ta’siri — eng katta baholangan vaqt oralig‘idagi normallashtirilgan qiymatlar
vaznli yig‘indisi. Standart vaznlar 0.35 / 0.25 / 0.20 / 0.20; har BIAda sozlanadi,
har biri 0..1 va yig‘indisi 1. Mezonga oid dalillar foydalanuvchi tomonidan kiritiladi.

Ustuvorlik = 0.40·ta’sir + 0.25·shoshilinchlik + 0.20·risk + 0.15·bog‘liqlik.
Shoshilinchlik = max(0, 1−min(1,RTO/72 soat)).
Risk = (eng katta saqlangan risk balli−1)/24.
Bog‘liqlik = mazkur jarayonga bog‘liq boshqa jarayonlar/(jami jarayonlar−1),
yagona jarayon uchun 0. NetworkX ancestors — `from depends on to` yo‘nalishiga mos.
BIA, ta’sir yoki risk yo‘q bo‘lsa score null va INSUFFICIENT_DATA; soxta default ball yo‘q.

RTO — xizmatni tiklash uchun maqsadli muddat. RPO — maqbul ma’lumot yo‘qotilishining
vaqt chegarasi. MTPD — chidab bo‘lmas oqibatlar chegarasi. RTO < MTPD; RPO RTOga
nisbatan cheklanmaydi. RPO gap: backup oralig‘i > RPO, faqat data_recovery_applicable.
Tavsiya maydoni serverga tegishli; ilmiy asoslangan vaqt tavsiyasi uchun dalil va
mezonlar yetishmasa u bo‘sh qoladi. Mas’ul kiritgan/rahbariyat tasdiqlagan qiymatlar alohida.

## Risk

Risk = ordinal ehtimollik × ta’sir, 1..25. Past ≤6, o‘rta 7..14, yuqori ≥15;
tashkilot chegaralari sozlanadi (1 ≤ past < o‘rta <25).
Qoldiq risk = qoldiq ehtimollik × qoldiq ta’sir; ikkalasi birga kiritiladi.
Bu statistik ehtimollik yoki kutilgan pul zarari emas. BIA bilan umumiy process FK
orqali bog‘langan; BIA va risk ikki xil baholash.

## Tiklash jadvallari

`deterministic-list-v1` — deterministik evristika, global optimallik da’vosi yo‘q.
Kirish bir marta olinib ScheduleRun.input_snapshotda saqlanadi. Har ikkala usul
bir xil variantlar, budjet, mutaxassislar, quvvat, bandlik va RTO/RPOdan foydalanadi.
Vaqtlar soniyalardan ehtiyotkor ravishda butun daqiqalarga o‘tkaziladi.

Variant tanlash: mas’ul tanlagan variantlar bo‘lsa shu to‘plam; aks holda barcha
variantlardan xarajat va ID bo‘yicha eng arzon mos variant. Tayyorgarlik+tiklash
RTOga, tegishli bo‘lsa RPOga, resurs quvvatiga va qolgan budjetga mosligi tekshiriladi.
Mas’ul tanlagan variantning amaldagi shartlarini tasdiqlashi zarur; erkin matnli
shartlar avtomatik tashqi infratuzilma tekshiruvi deb talqin qilinmaydi.

A: muhimlik, mavjud ustuvorlik indeksi va ID tartibida ketma-ket tiklash.
Bog‘liqlik tartibi yakunda mustaqil tekshiriladi; buzilsa feasible=false.
B: avval zarur jarayonlar; so‘ng shu muhimlik tartibida resursning eng erta bo‘sh
oralig‘iga joylash. Har intervalda jami talab quvvatdan oshmasligi tekshiriladi.
Bir-biriga bog‘liq bo‘lmagan ishlar quvvat yetarli bo‘lsa parallel bajariladi.
Boshlanish hodisa vaqtidan o‘tgan daqiqalarda; bandlik tugashi eng erta vaqtni cheklaydi.

Majburiy dependency sikllari kuchli bog‘langan komponentlar orqali aniqlanadi.
Sikl bo‘lsa jadval chiqarilmaydi; cheksiz qidiruv yo‘q. Ixtiyoriy bog‘liqlik
majburiy prerequisite emas. Yo‘q BIA/variant, tanqis resurs/budjet, bloklangan
prerequisite yoki RTO buzilishi muvaffaqiyat hisoblanmaydi. Har natija vaqtlar,
resurslar, xarajat, izoh, buzilish va resurs bandligi ulushini beradi.

`evaluate-strategy`ning eski OPTIMAL_FOUND javob kodi API mosligi uchun saqlandi;
selection_scope faqat berilgan nomzodlar orasidagi eng arzon mos variantni anglatadi.
Bu kod umumiy jadvalning matematik optimal ekanini bildirmaydi.

## Simulyatsiya va takrorlash

Faqat saqlangan bog‘liqlik grafigi bo‘ylab cascade va yuqoridagi jadval hisobi;
hech qanday server/tarmoq buyruqlari yo‘q. Mavjud resurs va ruxsat etilgan variant
ssenariydan olinadi. Umumiy mutaxassis quvvati ssenariy hisobi uchun 1 deb olinadi
(javobda ko‘rsatiladi). Mashqdagi haqiqiy kuzatuvlar Exercisega alohida yoziladi.
SimulationRun hisob kirishlarini/natijalarini saqlaydi; uni tahrirlash API yo‘q.

`benchmark_schedules` uchta sun’iy misolni 10 marta solishtiradi: parallel ish,
prerequisite va resurs tanqisligi. Hisoblash vaqti perf_counter bilan o‘lchanadi;
input hash, nusxa, algoritm versiyasi va ikki usulning barcha natijalari chiqadi.
Yaxshilanish oldindan natijaga yozilmaydi. Insonning reja tuzish vaqti o‘lchanmagan.
