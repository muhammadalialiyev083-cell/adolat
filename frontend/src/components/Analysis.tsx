import { useEffect, useState } from "react";
import { api } from "../api/client";

export function RiskMatrix({
  onNavigate,
}: {
  onNavigate: (key: string, query?: string) => void;
}) {
  const [data, setData] = useState<any>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api
      .riskMatrix()
      .then(setData)
      .catch((e) => setError(e.message));
  }, []);
  return (
    <section className="card">
      <div className="card-header">
        <h2>5 × 5 risk matritsasi</h2>
      </div>
      <div className="modal-body">
        <p>{data?.definition}</p>
        {error && (
          <p className="form-error" role="alert">
            {error}
          </p>
        )}
        <div
          className="risk-matrix"
          role="group"
          aria-label="Ehtimollik va ta’sir bo‘yicha risklar"
        >
          {data?.matrix.map((row: number[], i: number) =>
            row.map((count: number, j: number) => {
              const score = (i + 1) * (j + 1);
              const level =
                score <= data.thresholds.low
                  ? "Past"
                  : score <= data.thresholds.medium
                    ? "O‘rta"
                    : "Yuqori";
              return (
                <button
                  key={`${i}-${j}`}
                  className={`risk-cell risk-${level === "Past" ? "low" : level === "O‘rta" ? "medium" : "high"}`}
                  aria-label={`Ehtimollik ${i + 1}, ta’sir ${j + 1}: ${count} ta risk, ${level}`}
                  onClick={() =>
                    onNavigate("risks", `likelihood=${i + 1}&impact=${j + 1}`)
                  }
                >
                  <small>
                    E{i + 1} × T{j + 1}
                  </small>
                  <strong>{count}</strong>
                  <span>{level}</span>
                </button>
              );
            }),
          )}
        </div>
        <small>
          E — ordinal ehtimollik, T — ta’sir. Katakka bosib tegishli risklarni
          oching.
        </small>
      </div>
    </section>
  );
}
export function BIARanking() {
  const [data, setData] = useState<any>(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  async function calculate() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      setData(await api.getPriorityAnalysis());
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Muhim jarayonlarni tartiblash</h2>
          <p>
            0.40 × ta’sir + 0.25 × shoshilinchlik + 0.20 × risk + 0.15 ×
            bog‘liqlik
          </p>
        </div>
        <button
          className="btn btn-secondary"
          disabled={busy}
          onClick={calculate}
        >
          {busy ? "Hisoblanmoqda…" : "Tartiblashni hisoblash"}
        </button>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      {data && (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Jarayon</th>
                <th>Ustuvorlik indeksi</th>
                <th>Baholash holati</th>
              </tr>
            </thead>
            <tbody>
              {data.ranked_processes.map((p: any) => (
                <tr key={p.process_id}>
                  <td>{p.process_name}</td>
                  <td>{p.priority_score ?? "—"}</td>
                  <td>
                    {p.status === "INSUFFICIENT_DATA"
                      ? `Yetishmaydi: ${p.missing.join(", ")}`
                      : "Saqlangan baholashlardan hisoblandi"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="modal-body">
        <p>
          Moliyaviy ta’sir tashkilot chegarasiga nisbatan; 1–5 ballar (ball−1)/4
          bilan normallashtiriladi. Shoshilinchlik: max(0, 1−RTO/72 soat). Risk:
          (ball−1)/24. Bog‘liqlik: ta’sirlanadigan jarayonlar/(jami−1).
        </p>
        <small>
          Bu ilovada tanlangan ochiq formula; ISO algoritmi yoki maqolalarning
          aynan takrori emas.
        </small>
      </div>
    </section>
  );
}
