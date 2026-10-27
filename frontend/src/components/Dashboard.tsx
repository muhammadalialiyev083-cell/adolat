import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Layers3,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import { api } from "../api/client";

export function Dashboard({
  onNavigate,
  revision,
}: {
  onNavigate: (key: string, query?: string) => void;
  revision: number;
}) {
  const [report, setReport] = useState<any>(null);
  const [error, setError] = useState("");
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    let active = true;
    setError("");
    const query = new URLSearchParams();
    if (since) query.set("since", since);
    if (until) query.set("until", until);
    api.report(query.toString())
      .then((result) => { if (active) setReport(result); })
      .catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [revision, since, until]);

  const data = report?.summary;
  const unknown = (key: string) =>
    !data ||
    (key === "high_risks_count" && !data.total_risks) ||
    (key === "open_findings_count" && !data.completed_exercises_count) ||
    (key === "rpo_gap_count" && !data.bia_covered_processes) ||
    (key === "overdue_plans_count" && !data.published_plans_count);

  const metrics = [
    ["Juda muhim jarayonlar", "critical_processes", "processes", "criticality=CRITICAL"],
    ["BIA bilan qamrov, %", "bia_coverage_percent", "bia", ""],
    ["Yuqori risklar", "high_risks_count", "risks", "risk_class=high"],
    ["Tasdiqlangan rejalar", "published_plans_count", "plans", "approved=true"],
    ["Ko‘rib chiqish muddati o‘tgan", "overdue_plans_count", "plans", "overdue=true"],
    ["O‘tkazilgan mashqlar", "completed_exercises_count", "exercises", ""],
    ["Ochiq kamchiliklar", "open_findings_count", "exercises", "open_findings=true"],
    ["Mashqlarda RTO bajarilishi, %", "rto_compliance_percent", "exercises", ""],
    ["RPO va backup tafovuti", "rpo_gap_count", "bia", "rpo_gap=true"],
  ];

  const capabilities = [
    { icon: ShieldCheck, label: "Risklarni baholash", text: "Tahdid, ehtimollik va ta’sir bo‘yicha hujjatlashtirilgan tahlil.", page: "risks" },
    { icon: BarChart3, label: "BIA va kritik jarayonlar", text: "RTO, RPO, MTPD va xizmatlar bog‘liqligini aniqlash.", page: "bia" },
    { icon: Layers3, label: "Tiklashni rejalashtirish", text: "Resurslar, strategiyalar, reja va mashqlarni boshqarish.", page: "plans" },
  ];
  const rise = (delay: number) => ({
    initial: reduceMotion ? false : { opacity: 0, y: 18 },
    animate: { opacity: 1, y: 0 },
    transition: { duration: reduceMotion ? 0 : 0.55, delay },
  });

  return (
    <section className="automark-dashboard">
      <div className="automark-hero">
        <div className="automark-aurora aurora-one" aria-hidden="true"/>
        <div className="automark-aurora aurora-two" aria-hidden="true"/>
        <div className="automark-hero-main">
          <motion.div {...rise(0.03)}>
            <span className="automark-eyebrow"><Sparkles size={15}/> UzHi · Business Continuity Management</span>
            <h2>Har bir xavfga <span>tayyor bo‘ling.</span><br/>Har bir jarayonni <span>uzluksiz saqlang.</span></h2>
            <p>Tashkilot risklarini aniqlang, biznesga ta’sirini baholang va tiklash rejalarini yagona boshqaruv muhitida shakllantiring.</p>
            <div className="automark-hero-actions">
              <button type="button" className="automark-cta-primary" onClick={() => onNavigate("initial-setup")}>
                Loyihalashni boshlash <ArrowRight size={18}/>
              </button>
              <button type="button" className="automark-cta-secondary" onClick={() => onNavigate("catalog")}>
                Modullar bilan tanishish <ChevronRight size={17}/>
              </button>
            </div>
            <div className="automark-trust"><LockKeyhole size={15}/> Mavjud rollar, sessiya va ma’lumotlarga kirish siyosati saqlanadi.</div>
          </motion.div>
          <motion.div {...rise(0.18)} className="automark-preview" aria-label="UzHi ish jarayonining namunaviy vizual modeli">
            <div className="automark-preview-top"><span><CircleDot size={13}/> UzHi ish oqimi</span><span className="automark-preview-chip">Namuna ko‘rinish</span></div>
            <div className="automark-orbit" aria-hidden="true">
              <div className="automark-orbit-outer"><div className="automark-orbit-inner"><ShieldCheck size={40}/><span>BCMS</span></div></div>
              <span className="automark-orbit-node node-one"><Activity size={17}/></span>
              <span className="automark-orbit-node node-two"><BarChart3 size={17}/></span>
              <span className="automark-orbit-node node-three"><CheckCircle2 size={17}/></span>
            </div>
            <div className="automark-preview-flow">
              <span><i/>Risk tahlili</span><ChevronRight size={15}/>
              <span><i/>BIA</span><ChevronRight size={15}/>
              <span><i/>Tiklash rejasi</span>
            </div>
            <p>Jarayonlar o‘zaro bog‘langan. Hisoblashlar faqat tasdiqlangan manba ma’lumotlari asosida olib boriladi.</p>
          </motion.div>
        </div>
      </div>

      <div className="automark-section-intro">
        <div><span className="automark-section-kicker">IMKONIYATLAR</span><h3>Boshqaruv jarayonini soddalashtiring</h3><p>Har bir modul tegishli BCMS bosqichiga bevosita olib boradi.</p></div>
      </div>
      <div className="automark-features">
        {capabilities.map((item, index) => {
          const Icon = item.icon;
          return (
            <motion.button type="button" key={item.page} className="automark-feature" onClick={() => onNavigate(item.page)}
              initial={reduceMotion ? false : { opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.18 }}
              transition={{ duration: reduceMotion ? 0 : 0.45, delay: index * 0.07 }}>
              <span className="automark-feature-icon"><Icon size={22}/></span>
              <strong>{item.label}</strong><span>{item.text}</span>
              <span className="automark-feature-link">Modulni ochish <ArrowRight size={16}/></span>
            </motion.button>
          );
        })}
      </div>

      <div className="automark-section-intro automark-metrics-head">
        <div><span className="automark-section-kicker">HAQIQIY KO‘RSATKICHLAR</span><h3>Tashkilotning joriy holati</h3><p>Faqat server tomonidan qaytarilgan ma’lumotlar ko‘rsatiladi.</p></div>
      </div>
      {report?.is_demo && <p className="data-notice">O‘quv universiteti · DEMO ma’lumotlar. Real tashkilot natijasi emas.</p>}
      <div className="resource-toolbar">
        <label>Davr boshi <input type="date" value={since} onChange={(e) => setSince(e.target.value)}/></label>
        <label>Davr oxiri <input type="date" value={until} onChange={(e) => setUntil(e.target.value)}/></label>
        <small>Jarayon va BIA — joriy holat. Risk/reja — yaratilish sanasi, mashq — o‘tkazilgan sana.</small>
      </div>
      {error && <p role="alert" className="form-error">{error}</p>}
      {!report && !error && <p role="status">Ko‘rsatkichlar yuklanmoqda…</p>}
      <div className="dashboard-grid automark-metric-grid">
        {metrics.map(([title, key, resource, query], index) => (
          <motion.button
            key={key}
            className="metric-card automark-metric"
            initial={reduceMotion ? false : { opacity: 0, y: 12 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.12 }}
            transition={{ duration: reduceMotion ? 0 : 0.35, delay: Math.min(index * 0.035, 0.25) }}
            onClick={() => {
              const q = new URLSearchParams(query);
              if (since) q.set("since", since);
              if (until) q.set("until", until);
              onNavigate(resource, q.toString());
            }}
          >
            <span className="metric-label">{title}</span>
            <strong className="metric-value">{unknown(key) ? "—" : (data?.[key] ?? "—")}</strong>
            <small>{unknown(key) || data?.[key] == null ? "Baholash uchun ma’lumot yetarli emas" : "Tegishli yozuvlarni ochish →"}</small>
          </motion.button>
        ))}
      </div>
      <details className="automark-methodology">
        <summary>Ko‘rsatkichlar qanday hisoblanadi? <ChevronRight size={18}/></summary>
        <div className="automark-methodology-body">
          {report?.definitions && Object.entries(report.definitions).map(([key, value]) => <p key={key}>{String(value)}</p>)}
          <p>Baholanmagan holat muammosiz yoki to‘liq tayyor deb hisoblanmaydi. Risk ehtimolligi statistik prognoz emas, ordinal ball.</p>
        </div>
      </details>
    </section>
  );
}
