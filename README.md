# BCMS Designer — Biznes Uzluksizligini Boshqarish Tizimi

Farg‘ona davlat texnika universiteti magistrlik dissertatsiyasi doirasidagi dasturiy platforma.  
**Mavzu:** Tashkilotlarda biznes uzluksizligini boshqarish tizimini loyihalash dasturini ishlab chiqish  
**Magistrant:** Aliyev Muhammadali G‘ulomjon o‘g‘li  
**Ilmiy rahbar:** Turdimatov Mamirjon Mirzayevich  
**Mutaxassislik:** 70610302 – Axborot xavfsizligi  

---

## 1. Texnologik Stek va Arxitektura
- **Arxitektura:** Modular Monolith
- **Backend:** Python 3.12 + Django 6.1.2 + Django REST Framework 3.18.3
- **Frontend:** React 18 + TypeScript + Vite + Lucide Icons (Dark Enterprise UI)
- **Ma'lumotlar bazasi:** PostgreSQL (ishlab chiqarish) / SQLite (portativ avtotestlar)
- **Graf tahlili:** NetworkX
- **Hisobot va eksport:** ReportLab (PDF generator) + python-docx

---

## 2. Majburiy 12 ta Modul (To'liq Ishga Tushirilgan)
1. **FR-01: Kirish va Rollar (RBAC)** — 6 ta rol (`ADMIN`, `BCMS_MANAGER`, `PROCESS_OWNER`, `RISK_ANALYST`, `APPROVER`, `AUDITOR`).
2. **FR-02: Tashkilot Profili** — Bo'limlar, filiallar, xizmatlar, xavfsiz yo'qotish chegarasi ($L_{\max}$) va vaqt mintaqasi.
3. **FR-03: Jarayonlar Reestri** — Kritiklik (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`), xizmatlar, holati va mas'ullar.
4. **FR-04: Aktivlar va Bog'liqliklar** — Server, Tizim, Xodim, Provayder va $G=(V, E)$ yo'naltirilgan bog'liqlik graflari.
5. **FR-05: BIA So'rovnomasi** — $RTO \le MTPD$ qat'iy mantiqiy tekshiruvi, $RPO$ va zaxiralash oraliqlari, Rahbariyat tasdiqlash oqimi (`/approve`).
6. **FR-06: Risk Reestri & 5x5 Matritsa** — $\text{Likelihood} \times \text{Impact} = \text{RiskScore}$ (1..25), qoldiq risk va risk kamayishi $\Delta R$.
7. **FR-07: Hisoblash Yadrosi** — Tadqiqot gipotezasi formulasi:  
   $$\text{Priority} = 0.40 \cdot \text{Impact\_norm} + 0.25 \cdot \text{Urgency\_norm} + 0.20 \cdot \text{Risk\_norm} + 0.15 \cdot \text{Dependency\_norm}$$  
   Hujjat 10.1 algoritmi: $\text{rpo\_gap}$ aniqlash va ogohlantirish.
8. **FR-08: Tiklash Strategiyalari** — $RTO_{\text{est}} \le RTO_{\text{target}}$ va $RPO_{\text{est}} \le RPO_{\text{target}}$ shartlarini qanoatlantiruvchi eng kam xarajatli yechimni tavsiya etish.
9. **FR-09: BCP/DRP Rejalari** — Versiyalangan rejalar, qadamlar, rasmiy e'lon qilish va 1-klikli PDF eksport.
10. **FR-10: Ssenariy Simulyatsiyasi** — Nosoz aktiv bo'yicha zanjirsimon ta'sir tahlili (T-06: 3 ta qaram jarayon nosozligi va RTO buzilishlari).
11. **FR-11: Dashboard** — Tashkilot bo'yicha kritik jarayonlar, yuqori xavflar, rejasi yo'q jarayonlar va RPO buzilishlari statistikasi.
12. **FR-12: Audit Jurnali** — O'zgartirib yoki o'chirib bo'lmaydigan (Immutable) xavfsizlik jurnali: actor, role, action, entity, timestamp, IP.

---

## 3. TDD Qabul Sinovlari Natijalari (19 ta test, 100% muvaffaqiyatli)
| Test ID | Tavsif | Natija |
|---|---|---|
| **T-01** | Jarayon, egasi va aktivlar kiritiladi va bog'lanadi | **PASSED** |
| **T-02** | RTO=4 h, MTPD=12 h kiritiladi -> Qabul qilinadi | **PASSED** |
| **T-03** | RTO=18 h, MTPD=12 h kiritiladi -> 400 Xatolik (RTO <= MTPD buzilgan) | **PASSED** |
| **T-04** | Ehtimollik=4, Ta'sir=5 kiritiladi -> Risk balli = 20 (High) | **PASSED** |
| **T-05** | RPO=60 min, Backup=360 min -> RPO Gap ogohlantirishi beriladi | **PASSED** |
| **T-06** | Yagona server uzilganda 3 ta xizmat ta'sirlanishi hisoblanadi | **PASSED** |
| **T-07** | Reja tasdiqlanib e'lon qilinadi -> Audit jurnali yoziladi | **PASSED** |
| **T-08** | Begona tashkilot ma'lumotlariga kirish bloklanadi (404/403) | **PASSED** |
| **T-09** | Nazorat chorasi qo'shilib qoldiq risk qayta baholanadi | **PASSED** |
| **T-10** | Reja to'liq PDF formatida eksport qilinadi | **PASSED** |
| **FR-01..12** | Auth, RBAC, Immutability, Priority Score, Algo sample, Dashboard | **PASSED** |

---

## 4. Dasturni Ishga Tushirish Yo'riqnomasi

### Backendni ishga tushirish:
```powershell
cd c:\dissertatsiya\backend
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" manage.py runserver 127.0.0.1:8000
```

### Avtotestlarni qayta tekshirish:
```powershell
cd c:\dissertatsiya\backend
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -m pytest
```

### Namunaviy demo foydalanuvchilar (Parol: `Admin123!`):
- `admin` — Administrator (Muhammadali Aliyev)
- `bcms_manager` — BCMS Menejeri
- `director` — Rahbariyat / Tasdiqlovchi (Mamirjon Turdimatov)
