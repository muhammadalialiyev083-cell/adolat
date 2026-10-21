# Ma’lum cheklovlar

- Tashqi Render/Netlify xizmatiga kirish yoki deploy bajarilmadi. Amaldagi xizmat
  nomi, DB, tarif va platformadagi muhit qiymatlari tekshirilmagan. API public
  yo‘naltirishi saqlandi; `render.yaml.example` hozirgi Render schema/CLI orqali
  tasdiqlanmagan nomzod, uni mavjud xizmatga ko‘r-ko‘rona sync qilmang.
- Tashqi Render hujjatlari/schema va bibliografik manba so‘rovi muhit siyosati
  tomonidan 403 bilan rad etildi. DOI/to‘liq usullar tasdiqlanmagan.
- Ilmiy natija uchta sun’iy misol va qo‘lda hisoblangan testlardan iborat.
  Real tashkilotda reja tayyorlash vaqti, real avariya yoki xodimlar samaradorligi
  o‘lchanmagan. Heuristika global optimal yechimni kafolatlamaydi.
- Erkin matndagi strategiya shartlari avtomatik tekshirilmaydi. Mutaxassislar umumiy
  quvvat bilan hisoblanadi; aniq malaka, smena, sayohat va geografiya cheklovlari
  resurslarni alohida kiritish orqali qo‘lda ifodalanadi. Simulyatsiyaning umumiy
  mutaxassis quvvati 1 deb ochiq ko‘rsatiladi; alohida jadvalda u sozlanadi.
- Login throttling Django cache orqali bajariladi. Hozirgi LocMemCache har bir
  worker uchun alohida; ko‘p workerli productionda umumiy cache yoki kirish
  proksisida markaziy limit kerak. Bu cheklov sessiya/CSRF/RBACni o‘chirmaydi.
- Audit va tasdiqlangan nusxalar foydalanuvchi API darajasida o‘zgarmas.
  To‘g‘ridan-to‘g‘ri DB administrator huquqidan himoyalangan WORM yoki kriptografik
  dalillar ombori emas. DB operator ruxsatlari va backup alohida boshqariladi.
- Demo va haqiqiy/sun’iy mashq belgisi mavjud. Dashboarddagi mashq ko‘rsatkichlari
  tegishli tenantning barcha saqlangan mashqlarini qamrab oladi; statistik real
  avariya prognozi deb talqin qilinmaydi.
- BIA uchun asoslangan avtomatik RTO/MTPD tavsiyasi hali chiqarilmaydi; tavsiya
  maydoni bo‘sh, mas’ul kiritgan qiymat va tasdiqlash alohida. Bu tanlov dalilsiz
  aniqlik berishdan saqlaydi. Baholash versiyasi va vaqt bo‘yicha ta’sir saqlanadi.
- Graf butun tenant ma’lumotlaridan olinadi; SVGda bir vaqtda 60 tugun. Qidiruv va
  tugunlar ro‘yxati mavjud. Minglab tugun uchun maxsus graph-layout/paging yuk
  testi bajarilmagan. Xuddi shunday, production yuk va penetratsion audit o‘tkazilmadi.
- Email orqali parol tiklash va fayl import/upload kiritilmadi. Parolni o‘zi yoki
  admin almashtiradi; email yuborildi degan yolg‘on xabar yo‘q. Shaxsiy upload
  yo‘qligi sababli ephemeral diskda foydalanuvchi fayli saqlanmaydi.
- Eski API soat/daqiqa maydonlari saqlangan; kanonik soniya maydonlari save/migratsiyada
  hosil bo‘ladi. Xom SQL/bulk update operatori ushbu muvofiqlikni o‘zi saqlashi kerak.
- Qo‘lda tuzilgan reja jadvalga bog‘lanmasdan ham saqlanishi mumkin. Publish uchun
  eng so‘nggi BIA tasdiqlangan va reja majburiy mazmuni to‘liq bo‘lishi kerak;
  bog‘langan jadval mavjud bo‘lsa u bajariladigan bo‘lishi shart. Jadvalsiz reja
  resurs bo‘yicha avtomatik validatsiyadan o‘tgan deb hisoblanmaydi.

Tarixiy `backend_fastapi/` asosiy tekshiruv to‘plamiga kirmaydi. Undagi bazaga ulanish va
maxfiy kalitlarning oldindan yozilgan qiymatlari olib tashlandi, seeder explicit
parol/debug talab qiladi; ushbu eski backend productionga tayyor deb taqdim etilmaydi.
