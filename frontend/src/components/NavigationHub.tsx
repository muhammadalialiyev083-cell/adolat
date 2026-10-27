import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  FolderOpen,
  Info,
  LockKeyhole,
  RefreshCw,
  Search,
  ShieldCheck,
  Star,
} from "lucide-react";
import { api } from "../api/client";

type Navigate = (key: string) => void;
type Group = "Tashkilot" | "Risk va BIA" | "Tiklash" | "Nazorat";
type CatalogItem = {
  key: string;
  title: string;
  description: string;
  group: Group;
  tags: string;
};
type WorkflowStep = {
  key: string;
  label: string;
  complete: boolean;
  missing?: string[];
};
type WorkflowResponse = {
  completed: number;
  total: number;
  steps: WorkflowStep[];
};
type SetupTask = {
  title: string;
  description: string;
  destination: string;
  checkKey?: string;
};
type SetupStage = {
  title: string;
  shortTitle: string;
  description: string;
  tasks: SetupTask[];
};

const GROUPS: Group[] = ["Tashkilot", "Risk va BIA", "Tiklash", "Nazorat"];

export const MODULE_CATALOG: CatalogItem[] = [
  { key: "organizations", title: "Tashkilot profili", description: "Tashkilot ma’lumotlari, risk chegaralari va tiklash budjeti", group: "Tashkilot", tags: "profil sozlash kompaniya" },
  { key: "departments", title: "Bo‘limlar", description: "Tashkilotning tashkiliy tuzilmasi", group: "Tashkilot", tags: "struktura" },
  { key: "users", title: "Xodimlar va rollar", description: "Mas’ul shaxslar va ruxsat darajalari", group: "Tashkilot", tags: "foydalanuvchi xodim huquq" },
  { key: "services", title: "Xizmatlar", description: "Tashkilot taqdim etadigan muhim xizmatlar", group: "Tashkilot", tags: "service" },
  { key: "processes", title: "Biznes jarayonlari", description: "Jarayonlar, egalari va kritikligi", group: "Tashkilot", tags: "jarayon faoliyat" },
  { key: "assets", title: "Aktivlar", description: "Server, tarmoq, bino va boshqa resurslar", group: "Tashkilot", tags: "server qurilma" },
  { key: "dependencies", title: "Bog‘liqlik xaritasi", description: "Jarayon va aktivlar o‘rtasidagi bog‘liqliklar", group: "Risk va BIA", tags: "graf tarmoq" },
  { key: "bia", title: "Biznesga ta’sir (BIA)", description: "RTO, RPO va MTPD ko‘rsatkichlarini baholash", group: "Risk va BIA", tags: "ta'sir tahlil rto rpo mtpd" },
  { key: "risks", title: "Risklar reyestri", description: "Tahdidlar, ehtimollik va ta’sir baholari", group: "Risk va BIA", tags: "xavf tahdid risk" },
  { key: "controls", title: "Nazorat choralari", description: "Riskka javob va kamaytirish choralarini yuritish", group: "Risk va BIA", tags: "control" },
  { key: "strategies", title: "Tiklash strategiyalari", description: "Muqobil tiklash variantlarini solishtirish", group: "Tiklash", tags: "recovery variant" },
  { key: "resources", title: "Tiklash resurslari", description: "Tiklash ishlariga ajratilgan resurslar", group: "Tiklash", tags: "recovery xodim resurs" },
  { key: "schedule", title: "Tiklash jadvali", description: "Tiklash vazifalarining ketma-ketligi", group: "Tiklash", tags: "schedule reja" },
  { key: "plans", title: "Uzluksizlik rejalari", description: "BCP rejalari va tasdiqlash jarayoni", group: "Tiklash", tags: "bcp hujjat reja" },
  { key: "scenarios", title: "Uzilish ssenariylari", description: "Hodisa va uzilish holatlari", group: "Tiklash", tags: "uzilish stsenariy" },
  { key: "simulation-runs", title: "Simulyatsiya natijalari", description: "Ssenariylar bo‘yicha hisoblangan natijalar", group: "Tiklash", tags: "simulation sinov" },
  { key: "exercises", title: "Mashqlar", description: "Tiklash mashqlari va topilgan kamchiliklar", group: "Nazorat", tags: "test mashq" },
  { key: "audit-logs", title: "Audit jurnali", description: "Tizimdagi harakatlar va o‘zgarishlar tarixi", group: "Nazorat", tags: "audit log nazorat" },
  { key: "password", title: "Parolni almashtirish", description: "Hisob xavfsizligi sozlamalari", group: "Nazorat", tags: "parol himoya maxfiylik" },
  { key: "wizard", title: "BCMS loyihalash ustasi", description: "Server tekshiradigan ish jarayoni tayyorligi", group: "Nazorat", tags: "workflow tayyorlik" },
];

const SETUP_STAGES: SetupStage[] = [
  {
    title: "Organization Setup",
    shortTitle: "Tashkilot",
    description: "Avval tashkilot profilini va muhim jarayonlarni kiriting.",
    tasks: [
      { title: "Tashkilot profilini sozlash", description: "Faoliyat sohasi, chegaralar va tiklash budjetini tekshiring.", destination: "organizations", checkKey: "organization" },
      { title: "Bo‘lim va xizmatlarni kiritish", description: "Jarayonlar uchun tashkiliy asosni yarating.", destination: "services" },
      { title: "Muhim biznes jarayonlarini aniqlash", description: "Jarayon egasi va muhimlik darajasini ko‘rsating.", destination: "processes", checkKey: "processes" },
    ],
  },
  {
    title: "Risk & BIA Setup",
    shortTitle: "Risk va BIA",
    description: "Bog‘liqliklarni, uzilish ta’sirini va tahdidlarni baholang.",
    tasks: [
      { title: "Bog‘liqliklarni xaritalash", description: "Jarayon va aktivlar o‘rtasidagi aloqalarni kiriting.", destination: "dependencies", checkKey: "dependencies" },
      { title: "BIA va RTO/RPO/MTPD", description: "Ta’sir bahosi, ma’lumot manbasi va tiklash maqsadlarini belgilang.", destination: "bia", checkKey: "bia" },
      { title: "Risklarni baholash", description: "Tahdidlar, ehtimollik va ta’sir qiymatlarini kiriting.", destination: "risks", checkKey: "risks" },
    ],
  },
  {
    title: "Recovery Planning Setup",
    shortTitle: "Tiklash",
    description: "Tiklash variantlari, jadval va rejalarni tayyorlang.",
    tasks: [
      { title: "Tiklash strategiyalari", description: "Tiklash muddatlari va resurs talablarini taqqoslang.", destination: "strategies", checkKey: "strategies" },
      { title: "Tiklash jadvali", description: "Vazifalar ketma-ketligi va cheklovlarni tekshiring.", destination: "schedule", checkKey: "schedule" },
      { title: "Rejani tasdiqlash", description: "Kerakli tasdiqlarni haqiqiy ish jarayonida oling.", destination: "plans", checkKey: "approval" },
      { title: "Mashq va sinovlar", description: "Tiklash rejasini sinab, natijalarni qayd eting.", destination: "exercises", checkKey: "exercise" },
    ],
  },
  {
    title: "Privacy & Verification",
    shortTitle: "Tekshiruv",
    description: "Maxfiylik bo‘yicha tashkiliy nazoratlarni ko‘rib chiqing va ish jarayoni holatini tekshiring.",
    tasks: [
      { title: "Foydalanuvchi ruxsatlarini ko‘rib chiqish", description: "Hisob va rollarni tekshiring. Bu amal avtomatik xavfsizlik auditi emas.", destination: "users" },
      { title: "Audit jurnalini ko‘rish", description: "Kim va qachon o‘zgarish kiritganini tekshiring.", destination: "audit-logs" },
      { title: "BCMS tayyorligini tekshirish", description: "Serverdagi mavjud tekshiruv bosqichlarini oching.", destination: "wizard" },
    ],
  },
];

function getFavoriteKeys(): string[] {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem("bcms-catalog-favorites") || "[]");
    return Array.isArray(saved)
      ? saved.filter((key): key is string => typeof key === "string" && MODULE_CATALOG.some((item) => item.key === key))
      : [];
  } catch {
    return [];
  }
}

function useCatalogFavorites() {
  const [favorites, setFavorites] = useState<string[]>(getFavoriteKeys);
  useEffect(() => {
    try {
      localStorage.setItem("bcms-catalog-favorites", JSON.stringify(favorites));
    } catch {
      // Preference storage is optional: navigation still works without it.
    }
  }, [favorites]);
  const toggleFavorite = useCallback((key: string) => {
    setFavorites((current) => current.includes(key)
      ? current.filter((item) => item !== key)
      : [...current, key]);
  }, []);
  return { favorites, toggleFavorite };
}

function CatalogCard({
  item,
  favorite,
  onToggleFavorite,
  onNavigate,
}: {
  item: CatalogItem;
  favorite: boolean;
  onToggleFavorite: (key: string) => void;
  onNavigate: Navigate;
}) {
  return (
    <article className="hub-module-card">
      <div className="hub-module-head">
        <span className="hub-group-pill">{item.group}</span>
        <button
          type="button"
          className="hub-star"
          aria-label={favorite ? item.title + " saralanganlardan chiqarish" : item.title + " saralanganlarga qo‘shish"}
          aria-pressed={favorite}
          title={favorite ? "Saralanganlardan chiqarish" : "Saralanganlarga qo‘shish"}
          onClick={() => onToggleFavorite(item.key)}
        >
          <Star size={17} fill={favorite ? "currentColor" : "none"} />
        </button>
      </div>
      <h3>{item.title}</h3>
      <p>{item.description}</p>
      <button type="button" className="hub-open" onClick={() => onNavigate(item.key)}>
        Bo‘limni ochish <ArrowRight size={16} />
      </button>
    </article>
  );
}

export function ModuleCatalog({ onNavigate }: { onNavigate: Navigate }) {
  const [search, setSearch] = useState("");
  const [group, setGroup] = useState<Group | "Barchasi">("Barchasi");
  const [favoritesOnly, setFavoritesOnly] = useState(false);
  const { favorites, toggleFavorite } = useCatalogFavorites();
  const filtered = useMemo(() => MODULE_CATALOG.filter((item) => {
    const matchGroup = group === "Barchasi" || item.group === group;
    const matchFavorite = !favoritesOnly || favorites.includes(item.key);
    const query = search.trim().toLocaleLowerCase("uz");
    const matchText = !query || [item.title, item.description, item.tags, item.group]
      .join(" ").toLocaleLowerCase("uz").includes(query);
    return matchGroup && matchFavorite && matchText;
  }), [search, group, favorites, favoritesOnly]);

  return (
    <section className="hub-page">
      <div className="hub-hero">
        <div className="hub-hero-icon"><FolderOpen size={23} /></div>
        <div>
          <h2>Interaktiv modullar katalogi</h2>
          <p>Kerakli BCMS modulini toping, saralang va bir bosishda oching.</p>
        </div>
      </div>
      <div className="hub-filters">
        <label className="hub-search">
          <Search size={18} aria-hidden="true" />
          <span className="sr-only">Modullarni qidirish</span>
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Modul, funksiya yoki kalit so‘z…" type="search" />
        </label>
        <label className="hub-filter-select">
          <span>Yo‘nalish</span>
          <select value={group} onChange={(event) => setGroup(event.target.value as Group | "Barchasi")}>
            <option value="Barchasi">Barcha yo‘nalishlar</option>
            {GROUPS.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
          </select>
        </label>
        <button type="button" className={"hub-filter-toggle" + (favoritesOnly ? " selected" : "")} aria-pressed={favoritesOnly} onClick={() => setFavoritesOnly((value) => !value)}>
          <Star size={16} fill={favoritesOnly ? "currentColor" : "none"} />
          Saralanganlar ({favorites.length})
        </button>
      </div>
      <div className="hub-results" role="status">{filtered.length} ta modul topildi</div>
      {filtered.length ? (
        <div className="hub-cards">
          {filtered.map((item) => (
            <CatalogCard key={item.key} item={item} favorite={favorites.includes(item.key)} onToggleFavorite={toggleFavorite} onNavigate={onNavigate} />
          ))}
        </div>
      ) : (
        <div className="hub-empty">
          <p>Tanlangan mezonlar bo‘yicha modul topilmadi.</p>
          <button type="button" className="btn btn-primary" onClick={() => { setSearch(""); setGroup("Barchasi"); setFavoritesOnly(false); }}>Filtrlarni tozalash</button>
        </div>
      )}
      <p className="hub-note"><Info size={15} /> Saralangan modullar ushbu brauzerda saqlanadi; tashkilot ma’lumotlari katalogda nusxalanmaydi.</p>
    </section>
  );
}

export function ModuleMenu({ onNavigate }: { onNavigate: Navigate }) {
  const [expanded, setExpanded] = useState<Group>("Tashkilot");
  const { favorites } = useCatalogFavorites();
  const quick = favorites.length
    ? MODULE_CATALOG.filter((item) => favorites.includes(item.key)).slice(0, 5)
    : MODULE_CATALOG.filter((item) => ["processes", "bia", "risks", "plans"].includes(item.key));
  return (
    <section className="hub-page">
      <div className="hub-hero">
        <div className="hub-hero-icon"><FolderOpen size={23} /></div>
        <div>
          <h2>Menyu — BCMS ish maydoni</h2>
          <p>Modullar yo‘nalishlar bo‘yicha guruhlangan. Kerakli guruhni oching.</p>
        </div>
      </div>
      <div className="hub-quick">
        <h3>{favorites.length ? "Saralangan bo‘limlar" : "Tezkor o‘tish"}</h3>
        <div className="hub-quick-actions">
          {quick.map((item) => (
            <button type="button" key={item.key} onClick={() => onNavigate(item.key)}>{item.title}<ArrowRight size={15} /></button>
          ))}
        </div>
      </div>
      <div className="hub-accordion">
        {GROUPS.map((group) => {
          const items = MODULE_CATALOG.filter((item) => item.group === group);
          const isExpanded = expanded === group;
          return (
            <section key={group} className="hub-accordion-section">
              <button type="button" className="hub-accordion-trigger" aria-expanded={isExpanded} onClick={() => setExpanded(group)}>
                <span><strong>{group}</strong><small>{items.length} ta modul</small></span>
                <ChevronRight size={19} className={isExpanded ? "expanded" : ""} />
              </button>
              {isExpanded && <div className="hub-menu-grid">
                {items.map((item) => (
                  <button type="button" className="hub-menu-link" key={item.key} onClick={() => onNavigate(item.key)}>
                    <strong>{item.title}</strong><span>{item.description}</span><ArrowRight size={15} />
                  </button>
                ))}
              </div>}
            </section>
          );
        })}
      </div>
      <div className="hub-bottom-actions">
        <button type="button" className="btn btn-primary" onClick={() => onNavigate("initial-setup")}>Boshlang‘ich sozlash <ArrowRight size={16} /></button>
        <button type="button" className="btn btn-secondary" onClick={() => onNavigate("catalog")}>Katalogga o‘tish</button>
      </div>
    </section>
  );
}

export function InitialSetupWizard({
  onNavigate,
  revision,
}: {
  onNavigate: Navigate;
  revision: number;
}) {
  const [activeStage, setActiveStage] = useState(0);
  const [workflow, setWorkflow] = useState<WorkflowResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result: WorkflowResponse = await api.workflow();
      if (!result || !Array.isArray(result.steps)) throw new Error("Server ish jarayoni holatini qaytarmadi.");
      setWorkflow(result);
    } catch (err) {
      setWorkflow(null);
      setError(err instanceof Error ? err.message : "Tekshiruv natijasi olinmadi.");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { void load(); }, [load, revision]);
  const stage = SETUP_STAGES[activeStage];
  const status = useMemo(() => new Map((workflow?.steps || []).map((step) => [step.key, step])), [workflow]);
  const verifiedCount = typeof workflow?.completed === "number" ? workflow.completed : 0;
  const verifiedTotal = typeof workflow?.total === "number" ? workflow.total : 0;
  return (
    <section className="hub-page">
      <div className="hub-hero">
        <div className="hub-hero-icon"><ClipboardCheck size={23} /></div>
        <div>
          <h2>Initial System Setup Wizard</h2>
          <p>Tashkilotdan boshlab tiklash rejalarigacha — 4 bosqichli yo‘riqnoma.</p>
        </div>
      </div>
      <div className="setup-shell">
        <div className="setup-intro">
          <div><span className="hub-group-pill">Bosqich {activeStage + 1}/4</span><h3>{stage.title}</h3><p>{stage.description}</p></div>
          <button type="button" className="hub-refresh" onClick={() => void load()} disabled={loading}><RefreshCw size={16} className={loading ? "animate-spin" : ""} /> Holatni yangilash</button>
        </div>
        <div className="setup-steps" aria-label="Sozlash bosqichlari">
          {SETUP_STAGES.map((entry, index) => (
            <button
              type="button"
              key={entry.title}
              aria-current={activeStage === index ? "step" : undefined}
              className={"setup-step" + (activeStage === index ? " active" : "")}
              onClick={() => setActiveStage(index)}
            >
              <span className="setup-step-number">{index + 1}</span>
              <span>{entry.shortTitle}</span>
            </button>
          ))}
        </div>
        <div className="setup-progress-track" aria-hidden="true"><div style={{ width: ((activeStage + 1) / 4 * 100) + "%" }} /></div>
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="setup-readiness" role="status">
          {workflow
            ? <><CheckCircle2 size={18} /> Backend ish jarayoni tekshiruvi: <strong>{verifiedCount}/{verifiedTotal}</strong> bosqich bajarilgan.</>
            : <>Server holati hali tekshirilmagan. Ma’lumot mavjud bo‘lmasa, bosqichlar bajarilgan deb belgilanmaydi.</>}
        </div>
        <div className="setup-task-list">
          {stage.tasks.map((task) => {
            const check = task.checkKey ? status.get(task.checkKey) : undefined;
            return (
              <div className="setup-task" key={task.title}>
                <div className={"setup-task-indicator" + (check?.complete ? " complete" : "")}>
                  {check?.complete ? <CheckCircle2 size={20} /> : <span aria-hidden="true">•</span>}
                </div>
                <div className="setup-task-copy">
                  <strong>{task.title}</strong>
                  <p>{task.description}</p>
                  <small>{check?.complete ? "Server tekshiruvida bajarilgan" : check ? (check.missing?.join(" ") || "Tekshiruv yakunlanmagan") : task.checkKey ? "Server holati noma’lum" : "Qo‘lda ko‘rib chiqiladigan vazifa"}</small>
                </div>
                <button type="button" className="hub-open" onClick={() => onNavigate(task.destination)}>Ochish <ArrowRight size={15} /></button>
              </div>
            );
          })}
        </div>
        {activeStage === 3 && (
          <div className="setup-privacy">
            <LockKeyhole size={21} />
            <div>
              <strong>Maxfiylik eslatmasi</strong>
              <p>Parol, aloqa ma’lumotlari, risk tavsiflari va ichki izohlarni uchinchi tomon analitikasiga yubormang. Matnni vizual yashirish haqiqiy kirish nazorati o‘rnini bosmaydi. Bu sahifa maxfiylik auditi yoki sertifikatlash o‘tkazmaydi.</p>
              <button type="button" className="hub-open" onClick={() => onNavigate("password")}>Parolni boshqarish <ShieldCheck size={16} /></button>
            </div>
          </div>
        )}
        <div className="setup-footer">
          <button type="button" className="btn btn-secondary" disabled={activeStage === 0} onClick={() => setActiveStage((current) => Math.max(0, current - 1))}><ChevronLeft size={16} /> Orqaga</button>
          {activeStage < 3
            ? <button type="button" className="btn btn-primary" onClick={() => setActiveStage((current) => Math.min(3, current + 1))}>Keyingi bosqich <ChevronRight size={16} /></button>
            : <button type="button" className="btn btn-primary" onClick={() => onNavigate("catalog")}>Modullar katalogiga o‘tish <ArrowRight size={16} /></button>}
        </div>
      </div>
      <p className="hub-note"><Info size={15} /> 4 bosqichli yo‘riqnoma yangi ma’lumotlarni o‘zi saqlamaydi: har bir vazifa mavjud, ruxsatlar bilan himoyalangan modulga olib boradi. Bajarilish holati serverdagi ish jarayonidan olinadi.</p>
    </section>
  );
}
