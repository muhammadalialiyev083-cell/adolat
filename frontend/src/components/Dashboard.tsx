import { useEffect, useState } from "react";
import { api } from "../api/client";
export function Dashboard({
  onNavigate,
  revision,
}: {
  onNavigate: (key: string, query?: string) => void;
  revision: number;
}) {
  const [report, setReport] = useState<any>(null),
    [error, setError] = useState(""),
    [since, setSince] = useState(""),
    [until, setUntil] = useState("");
  useEffect(() => {
    let active = true;
    setError("");
    const query = new URLSearchParams();
    if (since) query.set("since", since);
    if (until) query.set("until", until);
    api
      .report(query.toString())
      .then((r) => {
        if (active) setReport(r);
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [revision, since, until]);
  const data = report?.summary;
  const unknown = (key: string) =>
    !data ||
    (key === "high_risks_count" && !data.total_risks) ||
    (key === "open_findings_count" && !data.completed_exercises_count) ||
    (key === "rpo_gap_count" && !data.bia_covered_processes) ||
    (key === "overdue_plans_count" && !data.published_plans_count);
  const metrics = [
    [
      "Juda muhim jarayonlar",
      "critical_processes",
      "processes",
      "criticality=CRITICAL",
    ],
    ["BIA bilan qamrov, %", "bia_coverage_percent", "bia", ""],
    ["Yuqori risklar", "high_risks_count", "risks", "risk_class=high"],
    ["Tasdiqlangan rejalar", "published_plans_count", "plans", "approved=true"],
    [
      "Ko‘rib chiqish muddati o‘tgan",
      "overdue_plans_count",
      "plans",
      "overdue=true",
    ],
    ["O‘tkazilgan mashqlar", "completed_exercises_count", "exercises", ""],
    [
      "Ochiq kamchiliklar",
      "open_findings_count",
      "exercises",
      "open_findings=true",
    ],
    [
      "Mashqlarda RTO bajarilishi, %",
      "rto_compliance_percent",
      "exercises",
      "",
    ],
    ["RPO va backup tafovuti", "rpo_gap_count", "bia", "rpo_gap=true"],
  ];
  return (
    <section>
      <div className="national-hero">
        <span>RiskGuard · BCMS Designer</span>
        <h2>Uzluksizlik — puxta loyihadan boshlanadi.</h2>
        <p>
          Tashkilotingizning muhim xizmatlari, tiklash maqsadlari va
          tekshirilgan rejalarini bir joyda boshqaring.
        </p>
      </div>
      {report?.is_demo && (
        <p className="data-notice">
          O‘quv universiteti · DEMO ma’lumotlar. Real tashkilot natijasi emas.
        </p>
      )}
      <div className="resource-toolbar">
        <label>
          Davr boshi
          <input
            type="date"
            value={since}
            onChange={(e) => setSince(e.target.value)}
          />
        </label>
        <label>
          Davr oxiri
          <input
            type="date"
            value={until}
            onChange={(e) => setUntil(e.target.value)}
          />
        </label>
        <small>
          Jarayon va BIA — joriy holat. Risk/reja — yaratilish sanasi, mashq —
          o‘tkazilgan sana.
        </small>
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      {!report && !error && <p role="status">Ko‘rsatkichlar yuklanmoqda…</p>}
      <div className="dashboard-grid">
        {metrics.map(([title, key, resource, query]) => (
          <button
            key={key}
            className="metric-card"
            onClick={() => {
              const q = new URLSearchParams(query);
              if (since) q.set("since", since);
              if (until) q.set("until", until);
              onNavigate(resource, q.toString());
            }}
          >
            <span className="metric-label">{title}</span>
            <strong className="metric-value">
              {unknown(key) ? "—" : (data?.[key] ?? "—")}
            </strong>
            <small>
              {unknown(key) || data?.[key] == null
                ? "Baholash uchun ma’lumot yetarli emas"
                : "Tegishli yozuvlarni ochish →"}
            </small>
          </button>
        ))}
      </div>
      <div className="card">
        <div className="card-header">
          <h3>Ko‘rsatkichlar qanday hisoblanadi?</h3>
        </div>
        <div className="modal-body">
          {report?.definitions &&
            Object.entries(report.definitions).map(([key, value]) => (
              <p key={key}>{String(value)}</p>
            ))}
          <p>
            Baholanmagan holat muammosiz yoki to‘liq tayyor deb hisoblanmaydi.
            Risk ehtimolligi statistik prognoz emas, ordinal ball.
          </p>
        </div>
      </div>
    </section>
  );
}
