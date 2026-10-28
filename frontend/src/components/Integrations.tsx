import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { User } from "../types";
type Row = Record<string, any>;
export function Integrations({
  user,
  onNavigate,
}: {
  user: User;
  onNavigate: (key: string) => void;
}) {
  const [integrations, setIntegrations] = useState<Row[]>([]);
  const [alerts, setAlerts] = useState<Row[]>([]);
  const [deliveries, setDeliveries] = useState<Row[]>([]);
  const [severity, setSeverity] = useState("");
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const lock = useRef(false);
  const load = useCallback(async () => {
    const [i, a, d] = await Promise.all([
      api.integrations(),
      api.list("monitoring-alerts", `page=${page}&severity=${severity}`),
      api.list("monitoring-deliveries"),
    ]);
    setIntegrations(i);
    setAlerts(a.results);
    setCount(a.count);
    setDeliveries(d.results);
  }, [severity, page]);
  useEffect(() => {
    void load().catch((e) => setError(e.message));
  }, [load]);
  const act = async (id: number, action: string) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await api.action("monitoring-alerts", id, action);
      await load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      lock.current = false;
      setBusy(false);
    }
  };
  return (
    <section className="card enterprise-panel">
      <h2>Monitoring integratsiyalari</h2>
      {error && <p role="alert">{error}</p>}
      <p>
        Operator imzolangan Alertmanager relay manbasini backendda sozlaydi.
        HMAC kalitlari deployment secret orqali beriladi. Tashqi manba bilan
        haqiqiy ulanish alohida tekshiriladi.
      </p>
      {!integrations.length && <p>Monitoring manbasi hali sozlanmagan.</p>}
      {integrations.map((i) => (
        <div className="card enterprise-panel" key={i.id}>
          <h3>{i.name}</h3>
          <p>
            Adapter: {i.provider}; holat:{" "}
            {!i.enabled
              ? "O‘chirilgan"
              : !i.secret_configured
                ? "Kalit sozlanmagan"
                : "Qabul qilish yoqilgan"}
            .
          </p>
          <p>
            So‘nggi muvaffaqiyatli hodisa:{" "}
            {i.last_success_at
              ? new Date(i.last_success_at).toLocaleString("uz")
              : "Hali qayd etilmagan"}
            .
          </p>
          <p>
            Webhook manzili: <code>/api/v1/monitoring/webhook/{i.id}</code>
          </p>
        </div>
      ))}
      <label>
        Ogohlantirish jiddiyligi
        <select
          className="input-field"
          value={severity}
          onChange={(e) => {
            setSeverity(e.target.value);
            setPage(1);
          }}
        >
          {[
            ["", "Barchasi"],
            ["LOW", "Past"],
            ["MEDIUM", "O‘rta"],
            ["HIGH", "Yuqori"],
            ["CRITICAL", "Kritik"],
          ].map(([key, label]) => (
            <option key={key} value={key}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Ogohlantirish</th>
              <th>Jiddiylik / manba vaqti</th>
              <th>Qabul qilish</th>
              <th>Hodisa</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.id}>
                <td>
                  {a.title}
                  <p>{a.description}</p>
                </td>
                <td>
                  {a.severity}
                  <p>{new Date(a.source_timestamp).toLocaleString("uz")}</p>
                </td>
                <td>
                  {a.acknowledged_at
                    ? "Qabul qilingan"
                    : ["ADMIN", "BCMS_MANAGER"].includes(user.role) && (
                        <button
                          className="btn btn-secondary"
                          disabled={busy}
                          onClick={() => void act(a.id, "acknowledge")}
                        >
                          Qabul qilish
                        </button>
                      )}
                </td>
                <td>
                  {a.incident ? (
                    <button
                      className="btn btn-secondary"
                      onClick={() => onNavigate("incidents")}
                    >
                      Hodisa #{a.incident}
                    </button>
                  ) : (
                    ["ADMIN", "BCMS_MANAGER"].includes(user.role) && (
                      <button
                        className="btn btn-primary"
                        disabled={busy}
                        onClick={() => void act(a.id, "convert")}
                      >
                        Hodisa yaratish
                      </button>
                    )
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
      <h3>So‘nggi qabul qilish diagnostikasi</h3>
      <p>
        Noto‘g‘ri qatorlar boshqa to‘g‘ri ogohlantirishlarni to‘xtatmaydi.
        Tuzatilgan payload yangi hodisa IDsi bilan qayta yuboriladi.
      </p>
      {deliveries.length ? (
        deliveries.map((d) => (
          <p key={d.id}>
            {d.event_id} · {d.status} ·{" "}
            {new Date(d.received_at).toLocaleString("uz")}
            {d.invalid_rows.length
              ? ` · Xato qatorlar: ${d.invalid_rows.map((r: Row) => r.row ?? "envelope").join(", ")}`
              : ""}
          </p>
        ))
      ) : (
        <p>Hali hodisa kelmagan.</p>
      )}
    </section>
  );
}
