import { useEffect, useRef, useState } from 'react';
import { api } from '../api/client';
import type { User } from '../types';

type Data = Record<string, any>;
const empty = (): Data => ({process:'', rto_hours:'', mtpd_hours:'', rpo_minutes:'', backup_interval_minutes:'', rationale:'', questionnaire:{}, evidence:[], impacts:[], status:'DRAFT', evidence_required:true});
const questionFields = [['business_objective','Biznes maqsadi'], ['operating_schedule','Ish jadvali'], ['minimum_service_level','Minimal maqbul xizmat darajasi'], ['dependency_assumptions','Bog‘liqlik farazlari'], ['recovery_prerequisites','Tiklash shartlari'], ['service_delivery_impact','Xizmatga tavsifiy ta’sir']];
const evidenceFields = [['title','Dalil nomi'],['source_reference','Manba havolasi yoki hujjat raqami'],['responsible_person','Mas’ul shaxs'],['collection_date','Yig‘ish sanasi'],['assessment_date','Baholash sanasi'],['justification','Asos va izoh']];

export function BIAQuestionnaire({user}: {user: User}) {
  const [processes, setProcesses] = useState<Data[]>([]);
  const [versions, setVersions] = useState<Data[]>([]);
  const [data, setData] = useState<Data>(empty);
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [notes, setNotes] = useState('');
  const [search, setSearch] = useState('');
  const lock = useRef(false);
  const refresh = async () => setVersions((await api.list('bia', 'page_size=100&ordering=-revision')).results);
  useEffect(() => { let active = true; api.list('processes', `page_size=100&search=${encodeURIComponent(search)}`).then(r => {if(active) setProcesses(r.results);}).catch(e => {if(active) setError(e.message);}); return () => {active=false;}; }, [search]);
  useEffect(() => {void refresh().catch(e => setError(e.message));}, []);
  const run = async (action: () => Promise<void>) => {
    if(lock.current) return; lock.current=true; setBusy(true); setError(''); setNotice('');
    try {await action();} catch(e) {setError(e instanceof Error ? e.message : 'Saqlab bo‘lmadi.');} finally {lock.current=false;setBusy(false);}
  };
  const process = processes.find(p => p.id === Number(data.process));
  const locked = data.status === 'APPROVED';
  const canWrite = ['ADMIN','BCMS_MANAGER'].includes(user.role) || (user.role === 'PROCESS_OWNER' && (!data.process || process?.owner === user.id));
  const canApprove = ['ADMIN','APPROVER'].includes(user.role);
  const set = (key: string, value: unknown) => setData(prev => ({...prev,[key]:value}));
  const save = async () => {
    const result = data.id ? await api.update('bia', data.id, data) : await api.create('bia', data);
    setData(result); setNotice('Qoralama saqlandi.'); await refresh();
  };
  const review = (decision: string) => void run(async () => {setData(await api.action('bia', data.id, 'review', {decision, notes})); await refresh(); setNotice('Ko‘rib chiqish natijasi saqlandi.');});
  return <section className="card enterprise-panel" aria-labelledby="bia-questionnaire-title">
    <h2 id="bia-questionnaire-title">Dalillarga asoslangan BIA so‘rovnomasi</h2>
    <p>RTO &lt; MTPD. Tavsifiy xizmat ta’siri hisoblash vaznlariga qo‘shilmaydi. Qiymatlarni mas’ul shaxs dalil asosida kiritadi.</p>
    {error && <p role="alert">{error}</p>}{notice && <p role="status">{notice}</p>}
    <div className="enterprise-grid"><label>Versiya tarixi<select className="input-field" value={data.id || ''} onChange={e => {setData(versions.find(v => v.id === Number(e.target.value)) || empty()); setStep(0); setError('');}}><option value="">Yangi so‘rovnoma</option>{versions.map(v => <option key={v.id} value={v.id}>{v.process_name} · v{v.revision} · {v.status}</option>)}</select></label>
      <label>Jarayonni qidirish<input className="input-field" value={search} onChange={e => setSearch(e.target.value)} /></label></div>
    <ol className="enterprise-steps" aria-label="BIA bosqichlari">{['Jarayon','Ta’sir','Tiklash maqsadlari','Dalillar','Ko‘rib chiqish'].map((label,i) => <li key={label} aria-current={step === i ? 'step':undefined}><button className="btn btn-ghost" type="button" onClick={() => setStep(i)}>{i+1}. {label}</button></li>)}</ol>
    {locked && <p role="status">Tasdiqlangan v{data.revision} o‘zgarmaydi. Tuzatish uchun yangi versiya yarating.</p>}
    {data.review_notes && <p>Ko‘rib chiqish izohi: {data.review_notes}</p>}
    <fieldset disabled={locked || !canWrite || busy} style={{border:0,padding:0,minWidth:0}}>
      {step === 0 && <div className="enterprise-grid"><label>Biznes jarayoni *<select className="input-field" value={data.process} onChange={e => set('process', Number(e.target.value))}><option value="">Tanlang</option>{processes.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label>
        <div><p>Bo‘lim: {process?.department_name || process?.department || '—'}; mas’ul: {process?.owner_name || process?.owner || '—'}; xizmat: {process?.service_name || process?.service || '—'}.</p><p>Ish jadvali: {process?.working_hours || 'Kiritilmagan'}</p></div>
        {questionFields.slice(0,2).map(([key,label]) => <label key={key}>{label}<textarea className="input-field" value={data.questionnaire[key] || ''} onChange={e => set('questionnaire', {...data.questionnaire,[key]:e.target.value})} /></label>)}</div>}
      {step === 1 && <>
        <p>Har bir vaqt oralig‘i uchun haqiqiy baholashni kiriting. Ballar 1–5. Moliyaviy zarar UZSda; taxmin bo‘lsa dalilda farazlarni ko‘rsating.</p>
        {data.impacts.map((impact: Data,index: number) => <div className="enterprise-grid" key={index}>{[['horizon_hours','Uzilish davomiyligi (soat)'],['financial_loss','Moliyaviy zarar (UZS)'],['operational_score','Operatsion ta’sir'],['legal_score','Huquqiy ta’sir'],['reputational_score','Obro‘ga ta’sir']].map(([key,label]) => <label key={key}>{label}<input className="input-field" type="number" min={key.endsWith('score') ? 1:0} max={key.endsWith('score') ? 5:undefined} step={key.endsWith('score') ? '1':'0.01'} value={impact[key]} onChange={e => set('impacts', data.impacts.map((r: Data,i: number) => i === index ? {...r,[key]:e.target.value}:r))} /></label>)}<button type="button" className="btn btn-ghost" onClick={() => set('impacts',data.impacts.filter((_: Data,i: number) => i !== index))}>Oraliqni olib tashlash</button></div>)}
        <button type="button" className="btn btn-secondary" onClick={() => set('impacts',[...data.impacts,{horizon_hours:'',financial_loss:'',operational_score:'',legal_score:'',reputational_score:''}])}>Vaqt oralig‘ini qo‘shish</button>
        <label className="form-label">Xizmatga tavsifiy ta’sir<textarea className="input-field" value={data.questionnaire.service_delivery_impact || ''} onChange={e => set('questionnaire',{...data.questionnaire,service_delivery_impact:e.target.value})} /></label>
      </>}
      {step === 2 && <div className="enterprise-grid">{[['rto_hours','RTO (soat)'],['mtpd_hours','MTPD (soat)'],['rpo_minutes','RPO (daqiqa)'],['backup_interval_minutes','Zaxiralash oralig‘i (daqiqa)']].map(([key,label]) => <label key={key}>{label} *<input className="input-field" type="number" min="0" step={key.endsWith('hours')?'0.01':'1'} value={data[key]} onChange={e => set(key,e.target.value)} /></label>)}
        {questionFields.slice(2,5).map(([key,label]) => <label key={key}>{label}<textarea className="input-field" value={data.questionnaire[key] || ''} onChange={e => set('questionnaire',{...data.questionnaire,[key]:e.target.value})} /></label>)}
        <label>Maqsadlarni asoslash<textarea className="input-field" value={data.rationale} onChange={e => set('rationale',e.target.value)} /></label></div>}
      {step === 3 && <>
        <p>Fayl ilovasi o‘rniga nazorat ostidagi dalilga havola kiriting. Dalil sifati mas’ul bahosi; forensik tasdiq emas.</p>
        {data.evidence.map((evidence: Data,index: number) => <div className="enterprise-grid" key={index} style={{marginBottom:24}}>{evidenceFields.map(([key,label]) => <label key={key}>{label}<input className="input-field" type={key.endsWith('date')?'date':'text'} value={evidence[key]} onChange={e => set('evidence',data.evidence.map((r: Data,i: number) => i === index?{...r,[key]:e.target.value}:r))} /></label>)}
          <label>Dalil turi<select className="input-field" value={evidence.type} onChange={e => set('evidence',data.evidence.map((r: Data,i: number) => i === index?{...r,type:e.target.value}:r))}>{[['DOCUMENT','Hujjat'],['INTERVIEW','Suhbat'],['MEASUREMENT','O‘lchov'],['REGULATION','Me’yoriy hujjat'],['OTHER','Boshqa']].map(([key,label]) => <option value={key} key={key}>{label}</option>)}</select></label>
          <label>Dalil sifati<select className="input-field" value={evidence.quality} onChange={e => set('evidence',data.evidence.map((r: Data,i: number) => i === index?{...r,quality:e.target.value}:r))}>{[['LOW','Past'],['MEDIUM','O‘rta'],['HIGH','Yuqori']].map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          <p>Ko‘rib chiqish: {evidence.review_status || 'UNREVIEWED'}</p><button type="button" className="btn btn-ghost" onClick={() => set('evidence',data.evidence.filter((_: Data,i: number) => i !== index))}>Dalilni olib tashlash</button>
        </div>)}
        <button type="button" className="btn btn-secondary" onClick={() => set('evidence',[...data.evidence,{title:'',type:'DOCUMENT',source_reference:'',responsible_person:'',collection_date:'',assessment_date:'',justification:'',quality:'LOW'}])}>Dalil qo‘shish</button>
      </>}
    </fieldset>
    {step === 4 && <>
      <p>Jarayon: {process?.name || data.process_name || 'Tanlanmagan'}; RTO: {data.rto_hours || '—'} soat; MTPD: {data.mtpd_hours || '—'} soat; RPO: {data.rpo_minutes || '—'} daqiqa.</p>
      <p>Ta’sir oraliqlari: {data.impacts.length}; dalillar: {data.evidence.length}; holat: {data.status}.</p>
      <p>Yetishmayotgan dalillar: {data.missing_evidence?.join(', ') || (data.evidence.length ? 'Saqlashda tekshiriladi':'Dalil kiritilmagan')}.</p>
      {data.id && <p><a href={`/api/v1/bia/${data.id}/summary/`}>Baholash xulosasini yuklash (JSON)</a></p>}
      {data.id && canApprove && !locked && <div><label>Ko‘rib chiqish izohi<textarea className="input-field" value={notes} onChange={e => setNotes(e.target.value)} /></label>
        <button className="btn btn-primary" disabled={busy} onClick={() => void run(async () => {const r = await api.approveBIA(data.id); setData(r.bia); await refresh(); setNotice('BIA tasdiqlandi.');})}>Tasdiqlash</button>{' '}
        <button className="btn btn-secondary" disabled={busy || !notes.trim()} onClick={() => review('request_changes')}>O‘zgartirish so‘rash</button>{' '}
        <button className="btn btn-secondary" disabled={busy || !notes.trim()} onClick={() => review('reject')}>Rad etish</button>
      </div>}
    </>}
    <div style={{display:'flex',gap:12,flexWrap:'wrap',marginTop:24}}>
      {step > 0 && <button className="btn btn-secondary" onClick={() => setStep(step-1)}>Oldingi</button>}
      {step < 4 && <button className="btn btn-primary" onClick={() => setStep(step+1)}>Keyingi</button>}
      {canWrite && !locked && <button className="btn btn-secondary" disabled={busy || !data.process} onClick={() => void run(save)}>{busy?'Saqlanmoqda…':'Qoralamani saqlash'}</button>}
      {data.id && canWrite && <button className="btn btn-secondary" disabled={busy} onClick={() => void run(async () => {setData(await api.action('bia',data.id,'revise')); setStep(0); await refresh();})}>Yangi versiya</button>}
    </div>
  </section>;
}
