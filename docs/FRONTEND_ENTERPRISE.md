# Enterprise v1.1 foydalanuvchi oqimlari

Asl UzHi logo, navy/teal dizayn, React/TypeScript/Vite va hash navigatsiya saqlandi.

- Kirish: split ekran, mobil bitta ustun, keyboard/Enter, password manager,
  parol ko‘rinishi, loading/duplicate-submit himoyasi, light/dark, reduced motion.
  Xato urinishdan keyin parol tozalanadi. Corporate kod discoverydan so‘ng faqat
  yoqilgan provayder tugmasi chiqadi. Recovery uchun mavjud tashkilot admini;
  bajarilmagan email reset yoki soxta Connected havolasi yo‘q.
- /#/imports: resurs/fayl → ustun moslash → qator/duplicate/FK preview → aniq tasdiq.
  Mavjud yozuvlar sukutda skip. Template va barqaror tashqi key ishlating.
- /#/bia-questionnaire: jarayon → ta’sir → tiklash → dalil → review. Asosiy RTO/MTPD
  kabi majburiy model qiymatlari kiritilgach dalili to‘liq bo‘lmagan draft saqlanadi.
  Dalilsiz numeric default kiritilmaydi. Submit/approve/reject/request changes, versiya
  tarixi va JSON summary mavjud. Asl /#/bia jadval/tahlil ham ishlaydi.
- /#/management: haqiqiy approval queue, countlar, task filter/paging, assignment,
  bajarish dalili va ruxsatli reopen. BIA/reja tasdig‘i alohida domen amali.
- /#/incidents: reyestr, mas’ul, jarayon/aktiv/risk/reja bog‘lanishi, response lifecycle,
  approved recovery objectives, recovery tasklar, append-only dalil metama’lumoti.
- /#/integrations: operator sozlagan manbalar, real last_success_at, severity filter,
  alert acknowledgment, incident conversion va sanitized delivery diagnostikasi.

Menejer yaratish/tayinlash amallarini, assignee o‘z vazifasi progressini, incident
owner o‘z javobini bajaradi. Auditor yozmaydi. Frontend cheklovlari backend
tekshiruvining qo‘shimchasi. Tanlovlar/review ro‘yxati hozir eng ko‘pi 100 yozuv;
BIA process search, CRUD va tasks/alerts paging bor. Juda katta kutubxona uchun
ko‘p bosqichli combobox/paging UX qo‘shimcha ish sifatida qoladi.

Screenshots: screenshots/enterprise-v1-1/ — faqat SYNTHETIC fixture bilan olingan.
SSO discoveryning browser enabled holati fixture; protokol RS256 mock transportida
backendda tekshirildi. Real IdP/monitoring/provider live tasdig‘i emas.
