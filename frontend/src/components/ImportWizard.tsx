import { useState } from 'react';
import { api } from '../api/client';
import type { User } from '../types';

const ENTITIES = [['departments', 'Bo‘limlar'], ['services', 'Xizmatlar'], ['processes', 'Jarayonlar'], ['assets', 'Aktivlar'], ['dependencies', 'Bog‘liqliklar'], ['resources', 'Tiklash resurslari']];
const LABELS: Record<string, string> = {key: 'Tashqi barqaror kalit', name: 'Nomi', service: 'Xizmat IDsi', owner: 'Mas’ul IDsi', department: 'Bo‘lim IDsi', description: 'Tavsif', head_name: 'Bo‘lim boshlig‘i', type: 'Aktiv turi', kind: 'Resurs turi', capacity: 'Quvvat', from_type: 'Manba turi', from_id: 'Manba IDsi', to_type: 'Bog‘liq obyekt turi', to_id: 'Bog‘liq obyekt IDsi', notes: 'Izohlar'};
type PreviewRow = {row: number; key: string; data: Record<string, unknown>; existing_id: number | null; errors: unknown};
const hasErrors = (row: PreviewRow) => Object.keys(row.errors as object).length > 0;

export function ImportWizard({user}: {user: User}) {
  const [entity, setEntity] = useState('departments');
  const [file, setFile] = useState<File | null>(null);
  const [batch, setBatch] = useState<any>(null);
  const [mapping, setMapping] = useState<Record<string, string>>({});
  const [rows, setRows] = useState<PreviewRow[]>([]);
  const [decisions, setDecisions] = useState<Record<string, string>>({});
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [summary, setSummary] = useState<any>(null);
  const [confirmed, setConfirmed] = useState(false);
  const run = async (action: () => Promise<void>) => {
    if (busy) return;
    setBusy(true); setError('');
    try { await action(); } catch (e) { setError(e instanceof Error ? e.message : 'Import bajarilmadi.'); }
    finally { setBusy(false); }
  };
  if (!['ADMIN', 'BCMS_MANAGER'].includes(user.role)) return <p>Import uchun administrator yoki BCMS menejeri huquqi kerak.</p>;
  const reset = () => {setStep(0); setBatch(null); setRows([]); setSummary(null); setError(''); setConfirmed(false);};
  return <section className="card enterprise-panel" aria-labelledby="import-title">
    <h2 id="import-title">Tashkilot ma’lumotlarini import qilish</h2>
    <ol className="enterprise-steps" aria-label="Import bosqichlari">{['Fayl yuklash', 'Ustunlarni moslash', 'Tekshirish', 'Tasdiqlash'].map((label, i) => <li key={label} aria-current={step === i ? 'step' : undefined}>{i + 1}. {label}</li>)}</ol>
    <p>CSV (UTF-8) yoki XLSX: 2 MB, 1000 qator, 40 ustungacha. Formula va tashqi havolali workbook qabul qilinmaydi. Vaqtinchalik nusxa 30 daqiqaga amal qiladi.</p>
    {error && <p role="alert">{error}</p>}
    {step === 0 && <form onSubmit={e => {e.preventDefault(); void run(async () => {
      if (!file) return;
      const result = await api.uploadImport(entity, file); setBatch(result);
      setMapping(Object.fromEntries(result.fields.filter((field: string) => result.headers.includes(field)).map((field: string) => [field, field])));
      setStep(1);
    });}}>
      <label className="form-label" htmlFor="import-entity">Resurs</label>
      <select id="import-entity" className="input-field" value={entity} onChange={e => setEntity(e.target.value)}>{ENTITIES.map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select>
      <p><a href={`/api/v1/imports/templates/${entity}`}>CSV shabloni</a> · <a href={`/api/v1/imports/templates/${entity}?file_format=xlsx`}>Excel shabloni</a></p>
      <p>«key» — tizimdagi o‘zgarmas tashqi kalit. FK ustunlariga shu tashkilotning mavjud IDlarini kiriting. Avval bo‘lim/xizmat/aktivlarni import qiling. Mavjud nom bilan moslik yangilash sifatida ko‘rsatiladi.</p>
      <label htmlFor="import-file" className="form-label">Fayl</label>
      <input id="import-file" type="file" accept=".csv,.xlsx" required onChange={e => setFile(e.target.files?.[0] || null)} />
      <button type="submit" className="btn btn-primary" disabled={busy || !file}>{busy ? 'Yuklanmoqda…' : 'Davom etish'}</button>
    </form>}
    {step === 1 && <form onSubmit={e => {e.preventDefault(); void run(async () => {
      const result = await api.previewImport(batch.id, mapping); setRows(result.rows);
      setDecisions(Object.fromEntries(result.rows.map((r: PreviewRow) => [String(r.row), hasErrors(r) || r.existing_id ? 'skip' : 'create']))); setStep(2);
    });}}>
      <p>{batch.count} qator. Majburiy maydonlar * bilan belgilangan.</p>
      <div className="enterprise-grid">{batch.fields.map((field: string) => <label key={field}>{LABELS[field] || field}{batch.required.includes(field) ? ' *' : ''}
        <select className="input-field" required={batch.required.includes(field)} value={mapping[field] || ''} onChange={e => setMapping(prev => { const next = {...prev}; if (e.target.value) next[field] = e.target.value; else delete next[field]; return next; })}>
          <option value="">Moslanmagan</option>{batch.headers.map((header: string) => <option key={header}>{header}</option>)}
        </select></label>)}</div>
      <div className="table-scroll"><table><caption>Fayldagi dastlabki qatorlar</caption><thead><tr>{batch.headers.map((h: string) => <th key={h}>{h}</th>)}</tr></thead><tbody>{batch.sample.map((row: string[], i: number) => <tr key={i}>{row.map((value,j) => <td key={j}>{value}</td>)}</tr>)}</tbody></table></div>
      <button className="btn btn-primary" disabled={busy}>{busy ? 'Tekshirilmoqda…' : 'Tekshirish va ko‘rish'}</button>
    </form>}
    {step === 2 && <>
      <p>{rows.filter(r => !hasErrors(r)).length} yaroqli; {rows.filter(hasErrors).length} xato. Mavjud yozuvlar sukut bo‘yicha o‘tkaziladi; yangilashni har qatorda aniq tanlang.</p>
      <div className="table-scroll"><table><thead><tr><th>Qator / kalit</th><th>Mos yozuv / ma’lumot</th><th>Xatolar</th><th>Amal</th></tr></thead><tbody>{rows.map(row => <tr key={row.row}>
        <td>{row.row}: {row.key}</td><td>{row.existing_id ? `ID ${row.existing_id}` : 'Yangi'} · {String(row.data.name || row.data.from_id || '')}</td>
        <td>{hasErrors(row) ? JSON.stringify(row.errors) : 'Yaroqli'}</td>
        <td><select className="input-field" aria-label={`${row.row}-qator amali`} value={decisions[row.row]} onChange={e => setDecisions({...decisions, [row.row]: e.target.value})}><option value="skip">O‘tkazish</option>{!hasErrors(row) && <option value={row.existing_id ? 'update' : 'create'}>{row.existing_id ? 'Yangilash' : 'Yaratish'}</option>}</select></td>
      </tr>)}</tbody></table></div>
      <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>Moslashga qaytish</button>
      <button type="button" className="btn btn-primary" onClick={() => setStep(3)}>Yakuniy ko‘rish</button>
    </>}
    {step === 3 && !summary && <>
      <p>Yaratish: {Object.values(decisions).filter(x => x === 'create').length}; yangilash: {Object.values(decisions).filter(x => x === 'update').length}; o‘tkazish: {Object.values(decisions).filter(x => x === 'skip').length}.</p>
      <p>Barcha tanlangan yozuvlar bitta tranzaksiyada saqlanadi. Keyingi o‘zgarish aniqlansa, butun import bekor qilinadi.</p>
      <label><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /> Tanlangan o‘zgarishlarni saqlashni tasdiqlayman.</label>
      <p><button type="button" className="btn btn-secondary" onClick={() => {setStep(2); setConfirmed(false);}}>Qaytish</button> <button type="button" className="btn btn-primary" disabled={busy || !confirmed} onClick={() => void run(async () => setSummary(await api.commitImport(batch.id, decisions)))}>{busy ? 'Saqlanmoqda…' : 'Importni tasdiqlash'}</button></p>
    </>}
    {summary && <div role="status"><h3>Import saqlandi</h3><p>Yaratildi: {summary.created}; yangilandi: {summary.updated}; o‘tkazildi: {summary.skipped}.</p></div>}
    {step > 0 && <button type="button" className="btn btn-ghost" onClick={reset} disabled={busy}>Yangi import</button>}
  </section>;
}
