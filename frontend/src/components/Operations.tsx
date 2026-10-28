import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { User } from "../types";
import { ResourcePanel } from "./Workspace";
type Row = Record<string, any>;
const LABELS: Record<string, string> = {
  OPEN: "Ochiq",
  IN_PROGRESS: "Bajarilmoqda",
  BLOCKED: "To‘silgan",
  DONE: "Bajarilgan",
  CANCELLED: "Bekor qilingan",
  DETECTED: "Aniqlangan",
  TRIAGED: "Saralangan",
  INVESTIGATING: "Tekshirilmoqda",
  CONTAINED: "Cheklangan",
  RECOVERY_IN_PROGRESS: "Tiklanmoqda",
  MONITORING: "Kuzatilmoqda",
  RESOLVED: "Hal qilingan",
  CLOSED: "Yopilgan",
};
const INCIDENT_NEXT: Record<string, string[]> = {
  DETECTED: ["TRIAGED"],
  TRIAGED: ["INVESTIGATING"],
  INVESTIGATING: ["CONTAINED"],
  CONTAINED: ["RECOVERY_IN_PROGRESS"],
  RECOVERY_IN_PROGRESS: ["MONITORING"],
  MONITORING: ["RESOLVED"],
  RESOLVED: ["CLOSED", "INVESTIGATING"],
  CLOSED: ["TRIAGED"],
};
const TASK_NEXT: Record<string, string[]> = {
  OPEN: ["IN_PROGRESS", "BLOCKED", "CANCELLED"],
  IN_PROGRESS: ["BLOCKED", "DONE", "CANCELLED"],
  BLOCKED: ["IN_PROGRESS", "CANCELLED"],
  DONE: ["OPEN"],
  CANCELLED: ["OPEN"],
};

export function Management({
  user,
  onNavigate,
  onChanged,
}: {
  user: User;
  onNavigate: (key: string, query?: string) => void;
  onChanged: () => void;
}) {
  const [dashboard, setDashboard] = useState<Row | null>(null);
  const [tasks, setTasks] = useState<Row[]>([]);
  const [status, setStatus] = useState("");
  const [overdue, setOverdue] = useState(false);
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [assignee, setAssignee] = useState("");
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Row | null>(null);
  const [notes, setNotes] = useState("");
  const [evidence, setEvidence] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const load = useCallback(async () => {
    const [d, t] = await Promise.all([
      api.management(),
      api.list(
        "tasks",
        new URLSearchParams({
          ...(status ? { status } : {}),
          overdue: String(overdue),
          page: String(page),
          ...(assignee ? { assigned_to: assignee } : {}),
          ordering: "due_date",
        }).toString(),
      ),
    ]);
    setDashboard(d);
    setTasks(t.results);
    setCount(t.count);
  }, [status, overdue, page, assignee]);
  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, [load]);
  const changed = () => {
    void load().catch((e) => setError(e.message));
    onChanged();
  };
  const managers = ["ADMIN", "BCMS_MANAGER"].includes(user.role);
  return (
    <div className="enterprise-panel">
      {error && <p role="alert">{error}</p>}
      <section className="card enterprise-panel">
        <h2>Tasdiqlar va majburiyatlar</h2>
        <p>
          Ko‘rsatkichlar saqlangan yozuvlardan olinadi. Vazifa bajarilishi domen
          tasdig‘ini almashtirmaydi.
        </p>
        <div className="enterprise-grid">
          {Object.entries({
            pending_bia: "Kutilayotgan BIA",
            pending_plans: "Kutilayotgan rejalar",
            overdue_tasks: "Muddati o‘tgan vazifalar",
            incomplete_evidence: "Yetishmayotgan dalillar",
            open_findings: "Ochiq mashq kamchiliklari",
            unreviewed_high_risks: "Ko‘rilmagan yuqori risklar",
            upcoming_reviews: "30 kun ichidagi reja ko‘rigi",
          }).map(([key, label]) => (
            <div className="card enterprise-panel" key={key}>
              <strong>{dashboard?.counts[key] ?? "—"}</strong>
              <p>{label}</p>
            </div>
          ))}
        </div>
        <h3>Tasdiqlash navbati</h3>
        {dashboard?.pending_bia.map((r: Row) => (
          <p key={`bia-${r.id}`}>
            <button
              className="btn btn-secondary"
              onClick={() => onNavigate("bia-questionnaire")}
            >
              {r.process__name} · BIA v{r.revision}
            </button>
          </p>
        ))}
        {dashboard?.pending_plans.map((r: Row) => (
          <p key={`plan-${r.id}`}>
            <button
              className="btn btn-secondary"
              onClick={() => onNavigate("plans")}
            >
              {r.title}
            </button>
          </p>
        ))}
        <h3>So‘nggi qarorlar</h3>
        {dashboard?.recent_decisions.length ? (
          dashboard.recent_decisions.map((r: Row, i: number) => (
            <p key={i}>
              {r.entity === "BIAAssessment"
                ? "BIA baholash"
                : "Uzluksizlik rejasi"}{" "}
              #{r.entity_id} ·{" "}
              {r.action === "APPROVE" ? "Tasdiqlangan" : "Ko‘rib chiqilgan"} ·{" "}
              {new Date(r.timestamp).toLocaleString("uz")}
            </p>
          ))
        ) : (
          <p>Saqlangan qarorlar yo‘q.</p>
        )}
      </section>
      <section className="card enterprise-panel">
        <h2>Biriktirilgan vazifalar</h2>
        <div className="enterprise-grid">
          <label>
            Holat
            <select
              className="input-field"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="">Barchasi</option>
              {Object.keys(TASK_NEXT).map((s) => (
                <option key={s} value={s}>
                  {LABELS[s]}
                </option>
              ))}
            </select>
          </label>
          <label>
            Mas’ul IDsi
            <input
              className="input-field"
              type="number"
              min="1"
              value={assignee}
              onChange={(e) => {
                setAssignee(e.target.value);
                setPage(1);
              }}
            />
          </label>
        </div>
        <label>
          <input
            type="checkbox"
            checked={overdue}
            onChange={(e) => {
              setOverdue(e.target.checked);
              setPage(1);
            }}
          />{" "}
          Faqat muddati o‘tganlar
        </label>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Vazifa</th>
                <th>Mas’ul</th>
                <th>Holat</th>
                <th>Muddat</th>
                <th>Amal</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => (
                <tr key={task.id}>
                  <td>{task.title}</td>
                  <td>{task.assigned_name}</td>
                  <td>{LABELS[task.status]}</td>
                  <td>{task.due_date || "—"}</td>
                  <td>
                    {user.role !== "AUDITOR" &&
                      (managers || task.assigned_to === user.id) && (
                        <button
                          className="btn btn-secondary"
                          onClick={() => {
                            setSelected(task);
                            setNotes(task.resolution_notes);
                            setEvidence(task.completion_evidence);
                          }}
                        >
                          Bajarilishni yangilash
                        </button>
                      )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          <button
            className="btn btn-secondary"
            disabled={page === 1}
            onClick={() => setPage(page - 1)}
          >
            Oldingi
          </button>{" "}
          {page} · {count} yozuv{" "}
          <button
            className="btn btn-secondary"
            disabled={page * 20 >= count}
            onClick={() => setPage(page + 1)}
          >
            Keyingi
          </button>
        </p>
        {selected && (
          <div className="card enterprise-panel">
            <h3>{selected.title}</h3>
            <label>
              Yechim izohi
              <textarea
                className="input-field"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </label>
            <label>
              Bajarish dalili
              <textarea
                className="input-field"
                value={evidence}
                onChange={(e) => setEvidence(e.target.value)}
              />
            </label>
            <p>Holatni tanlang:</p>
            {TASK_NEXT[selected.status]
              .filter((s) => managers || !["OPEN", "CANCELLED"].includes(s))
              .map((s) => (
                <button
                  key={s}
                  className="btn btn-secondary"
                  disabled={busy}
                  onClick={async () => {
                    if (lock.current) return;
                    lock.current = true;
                    setBusy(true);
                    try {
                      await api.update("tasks", selected.id, {
                        status: s,
                        resolution_notes: notes,
                        completion_evidence: evidence,
                      });
                      setSelected(null);
                      changed();
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      lock.current = false;
                      setBusy(false);
                    }
                  }}
                >
                  {LABELS[s]}
                </button>
              ))}
          </div>
        )}
      </section>
      {managers && (
        <ResourcePanel resource="tasks" user={user} onChanged={changed} />
      )}
    </div>
  );
}

export function IncidentWorkspace({
  user,
  onChanged,
}: {
  user: User;
  onChanged: () => void;
}) {
  const [incidents, setIncidents] = useState<Row[]>([]);
  const [selected, setSelected] = useState<Row | null>(null);
  const [error, setError] = useState("");
  const [reason, setReason] = useState("");
  const [evidence, setEvidence] = useState({
    title: "",
    source_reference: "",
    custody_note: "",
    sha256: "",
  });
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const load = useCallback(
    async () =>
      setIncidents(
        (await api.list("incidents", "page_size=100&ordering=-detected_at"))
          .results,
      ),
    [],
  );
  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, [load]);
  const changed = () => {
    void load().catch((e) => setError(e.message));
    onChanged();
  };
  const write = async (action: () => Promise<Row>) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      setSelected(await action());
      changed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  const canEdit =
    selected &&
    (["ADMIN", "BCMS_MANAGER"].includes(user.role) ||
      (selected.owner === user.id &&
        !["AUDITOR", "APPROVER"].includes(user.role)));
  return (
    <div>
      <ResourcePanel resource="incidents" user={user} onChanged={changed} />
      <section className="card enterprise-panel">
        <h2>Hodisa javobi va dalillar</h2>
        {error && <p role="alert">{error}</p>}
        <label>
          Hodisa
          <select
            aria-label="Hodisa"
            className="input-field"
            value={selected?.id || ""}
            onChange={(e) =>
              setSelected(
                incidents.find((r) => r.id === Number(e.target.value)) || null,
              )
            }
          >
            <option value="">Tanlang (eng so‘nggi 100 yozuv)</option>
            {incidents.map((r) => (
              <option key={r.id} value={r.id}>
                {r.title} · {LABELS[r.status]}
              </option>
            ))}
          </select>
        </label>
        {selected && (
          <>
            <p>
              Hodisa: {selected.identifier}; aniqlanish:{" "}
              {new Date(selected.detected_at).toLocaleString("uz")}; manba:{" "}
              {selected.reporting_source || "Kiritilmagan"}; holat:{" "}
              {LABELS[selected.status]}.
            </p>
            <h3>Tasdiqlangan tiklash maqsadlari</h3>
            {selected.recovery_objectives.length ? (
              selected.recovery_objectives.map((r: Row) => (
                <p key={r.bia_id}>
                  Jarayon #{r.process_id} · BIA v{r.revision}: RTO{" "}
                  {r.rto_seconds} s; RPO {r.rpo_seconds} s; MTPD{" "}
                  {r.mtpd_seconds} s.
                </p>
              ))
            ) : (
              <p>Tasdiqlangan bog‘liq BIA yo‘q.</p>
            )}
            <h3>Tiklash vazifalari</h3>
            {selected.recovery_tasks.map((r: Row) => (
              <p key={r.id}>
                {r.title} · {LABELS[r.status]}
              </p>
            ))}
            <div className="enterprise-grid">
              {[
                ["business_impact", "Biznesga ta’sir"],
                ["containment_actions", "Cheklash choralari"],
                ["recovery_verification", "Kuzatilgan tiklash tekshiruvi"],
                ["resolution_summary", "Yechim xulosasi"],
                ["lessons_learned", "Olingan saboqlar"],
              ].map(([key, label]) => (
                <label key={key}>
                  {label}
                  <textarea
                    className="input-field"
                    disabled={!canEdit || busy}
                    value={selected[key]}
                    onChange={(e) =>
                      setSelected({ ...selected, [key]: e.target.value })
                    }
                  />
                </label>
              ))}
            </div>
            {canEdit && (
              <>
                <label>
                  Qayta ochish sababi
                  <input
                    className="input-field"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                  />
                </label>
                <p>Ruxsat etilgan keyingi holatlar:</p>
                {[selected.status, ...INCIDENT_NEXT[selected.status]].map(
                  (status) => (
                    <button
                      className="btn btn-secondary"
                      key={status}
                      disabled={busy}
                      onClick={() =>
                        void write(() =>
                          api.update("incidents", selected.id, {
                            ...Object.fromEntries(
                              [
                                "business_impact",
                                "containment_actions",
                                "recovery_verification",
                                "resolution_summary",
                                "lessons_learned",
                              ].map((k) => [k, selected[k]]),
                            ),
                            status,
                            ...(reason.trim() ? { reopen_reason: reason } : {}),
                          }),
                        )
                      }
                    >
                      {status === selected.status
                        ? "Javobni saqlash"
                        : LABELS[status]}
                    </button>
                  ),
                )}
              </>
            )}
            <h3>Dalillar va saqlash zanjiri</h3>
            <p>
              Havolalar operator tomonidan kiritilgan. Fayl yaxlitligi yoki
              forensik tasdiq bajarilgan deb hisoblanmaydi.
            </p>
            {selected.evidence.map((r: Row, i: number) => (
              <p key={i}>
                {r.title} · {r.source_reference} · {r.recorded_at} · muallif #
                {r.recorded_by} · {r.custody_note}
              </p>
            ))}
            {canEdit && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void write(() =>
                    api.action(
                      "incidents",
                      selected.id,
                      "evidence",
                      Object.fromEntries(
                        Object.entries(evidence).filter(([, v]) => v),
                      ),
                    ),
                  );
                }}
              >
                <div className="enterprise-grid">
                  {[
                    ["title", "Dalil nomi"],
                    ["source_reference", "Nazorat ostidagi manba"],
                    ["custody_note", "Qabul/topshirish izohi"],
                    ["sha256", "SHA-256 (operator qaydi, ixtiyoriy)"],
                  ].map(([key, label]) => (
                    <label key={key}>
                      {label}
                      <input
                        className="input-field"
                        required={key !== "sha256"}
                        value={evidence[key as keyof typeof evidence]}
                        onChange={(e) =>
                          setEvidence({ ...evidence, [key]: e.target.value })
                        }
                      />
                    </label>
                  ))}
                </div>
                <button className="btn btn-primary" disabled={busy}>
                  Dalil qaydini qo‘shish
                </button>
              </form>
            )}
          </>
        )}
      </section>
    </div>
  );
}
