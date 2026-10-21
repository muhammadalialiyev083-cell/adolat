import React, { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { User } from "../types";

type Row = Record<string, any>;
type Field = {
  key: string;
  label: string;
  type?: string;
  required?: boolean;
  options?: [string, string][];
  source?: string;
  min?: number;
  hint?: string;
};
type Config = {
  title: string;
  fields: Field[];
  columns: [string, string][];
  order?: string;
};
const f = (
  key: string,
  label: string,
  type = "text",
  extra: Partial<Field> = {},
): Field => ({ key, label, type, ...extra });
const relation = (
  key: string,
  label: string,
  source: string,
  required = false,
) => f(key, label, "relation", { source, required });
const options = (key: string, label: string, values: [string, string][]) =>
  f(key, label, "select", { options: values });
const statusOptions: [string, string][] = [
  ["ACTIVE", "Faol"],
  ["UNDER_REVIEW", "Ko‘rib chiqishda"],
  ["INACTIVE", "Nofaol"],
];
const roleOptions: [string, string][] = [
  ["ADMIN", "Tashkilot administratori"],
  ["BCMS_MANAGER", "BCMS menejeri"],
  ["PROCESS_OWNER", "Jarayon egasi"],
  ["RISK_ANALYST", "Risk tahlilchisi"],
  ["APPROVER", "Tasdiqlovchi"],
  ["AUDITOR", "Auditor / ko‘ruvchi"],
];
const processField = relation("process", "Jarayon", "processes", true);
const ownerField = relation("owner", "Mas’ul", "users");
export const CONFIGS: Record<string, Config> = {
  "simulation-runs": {
    title: "Simulyatsiya natijalari",
    fields: [],
    columns: [
      ["scenario_title", "Ssenariy"],
      ["created_at", "Hisoblangan vaqt"],
      ["algorithm_version", "Algoritm versiyasi"],
    ],
    order: "-created_at",
  },
  organizations: {
    title: "Tashkilot profili",
    fields: [
      f("name", "Tashkilot nomi", "text", { required: true }),
      f("sector", "Faoliyat sohasi", "text", { required: true }),
      f("contact_details", "Aloqa ma’lumotlari", "textarea"),
      f("timezone", "Vaqt mintaqasi"),
      f(
        "max_acceptable_loss",
        "Moliyaviy ta’sirni normallashtirish chegarasi (UZS)",
        "number",
        { min: 1 },
      ),
      f("risk_low_threshold", "Past risk chegarasi", "number", { min: 1 }),
      f("risk_medium_threshold", "O‘rta risk chegarasi", "number", { min: 2 }),
      f("recovery_budget", "Tiklash budjeti (UZS)", "number", { min: 0 }),
    ],
    columns: [
      ["name", "Tashkilot"],
      ["sector", "Soha"],
      ["contact_details", "Aloqalar"],
    ],
  },
  departments: {
    title: "Bo‘limlar",
    fields: [
      f("name", "Bo‘lim nomi", "text", { required: true }),
      f("head_name", "Bo‘lim boshlig‘i"),
    ],
    columns: [
      ["name", "Bo‘lim"],
      ["head_name", "Boshliq"],
    ],
  },
  services: {
    title: "Xizmatlar",
    fields: [
      f("name", "Xizmat nomi", "text", { required: true }),
      f("description", "Tavsif", "textarea"),
      ownerField,
    ],
    columns: [
      ["name", "Xizmat"],
      ["owner_name", "Mas’ul"],
    ],
  },
  users: {
    title: "Xodimlar va foydalanuvchilar",
    fields: [
      f("username", "Login", "text", { required: true }),
      f("password", "Parol (yangi hisob uchun majburiy)", "password"),
      f("first_name", "Ism"),
      f("last_name", "Familiya"),
      f("email", "Email", "email"),
      f("phone", "Telefon"),
      f("is_active", "Hisob faol", "checkbox"),
      options("role", "Rol", roleOptions),
      relation("department", "Bo‘lim", "departments"),
    ],
    columns: [
      ["username", "Login"],
      ["first_name", "Ism"],
      ["role_display", "Rol"],
      ["phone", "Telefon"],
    ],
  },
  processes: {
    title: "Biznes jarayonlari",
    fields: [
      f("name", "Jarayon nomi", "text", { required: true }),
      f("description", "Tavsif", "textarea", { required: true }),
      relation("service", "Xizmat", "services", true),
      relation("department", "Bo‘lim", "departments"),
      ownerField,
      f("working_hours", "Ishlash vaqti"),
      f("critical_periods", "Muhim davrlar", "textarea"),
      f("required_staff", "Kerakli xodimlar soni", "number", { min: 1 }),
      f("resource_notes", "Resurs va yetkazib beruvchilar talabi", "textarea"),
      f("data_recovery_applicable", "Ma’lumot tiklash tegishli", "checkbox"),
      options("criticality", "Muhimlik", [
        ["CRITICAL", "Juda muhim"],
        ["HIGH", "Yuqori"],
        ["MEDIUM", "O‘rta"],
        ["LOW", "Past"],
      ]),
      options("status", "Holat", statusOptions),
    ],
    columns: [
      ["name", "Jarayon"],
      ["service_name", "Xizmat"],
      ["owner_name", "Mas’ul"],
      ["criticality_display", "Muhimlik"],
      ["status", "Holat"],
    ],
    order: "name",
  },
  assets: {
    title: "Aktivlar",
    fields: [
      f("name", "Aktiv nomi", "text", { required: true }),
      options("type", "Turi", [
        ["SERVER", "Server"],
        ["SYSTEM", "Dastur"],
        ["DATABASE", "Ma’lumotlar bazasi"],
        ["NETWORK", "Tarmoq"],
        ["FACILITY", "Bino"],
        ["POWER", "Elektr ta’minoti"],
        ["COMMUNICATION", "Aloqa"],
        ["PERSONNEL", "Xodim / jamoa"],
        ["VENDOR", "Yetkazib beruvchi"],
      ]),
      f("description", "Tavsif", "textarea"),
      ownerField,
    ],
    columns: [
      ["name", "Aktiv"],
      ["type_display", "Turi"],
      ["owner_name", "Mas’ul"],
    ],
  },
  dependencies: {
    title: "Bog‘liqliklar",
    fields: [
      options("from_type", "Bog‘liq obyekt turi", [
        ["PROCESS", "Jarayon"],
        ["ASSET", "Aktiv"],
      ]),
      relation("from_id", "Bog‘liq obyekt", "from", true),
      options("to_type", "Zarur obyekt turi", [
        ["ASSET", "Aktiv"],
        ["PROCESS", "Jarayon"],
      ]),
      relation("to_id", "Zarur obyekt", "to", true),
      options("dependency_criticality", "Bog‘liqlik darajasi", [
        ["MANDATORY", "Majburiy"],
        ["OPTIONAL", "Zaxirali / ixtiyoriy"],
      ]),
      f("notes", "Izoh", "textarea"),
    ],
    columns: [
      ["from_label", "Bog‘liq obyekt"],
      ["to_label", "Zarur obyekt"],
      ["dependency_criticality", "Daraja"],
    ],
    order: "id",
  },
  bia: {
    title: "Biznesga ta’sir tahlili",
    fields: [
      processField,
      f("revision", "Versiya raqami", "number", { min: 1 }),
      f("rto_hours", "RTO — tiklash uchun maqsadli muddat (soat)", "number", {
        min: 0.01,
        required: true,
      }),
      f(
        "mtpd_hours",
        "MTPD — chidab bo‘lmas oqibat chegarasi (soat)",
        "number",
        { min: 0.01, required: true },
      ),
      f(
        "rpo_minutes",
        "RPO — maqbul ma’lumot yo‘qotilishi (daqiqa)",
        "number",
        {
          min: 0,
          hint: "Faqat ma’lumot tiklash tegishli jarayonlarda qo‘llanadi.",
        },
      ),
      f("backup_interval_minutes", "Backup oralig‘i (daqiqa)", "number", {
        min: 0,
      }),
      f("rationale", "Baholash sababi", "textarea", { required: true }),
      f("data_source", "Ma’lumot manbasi", "textarea", { required: true }),
      f("impact_weights", "Mezon vaznlari", "weights"),
      f("impacts", "Uzilish davomiyligi bo‘yicha ta’sir", "impacts"),
      options("status", "Holat", [
        ["DRAFT", "Qoralama"],
        ["SUBMITTED", "Tasdiqlashga yuborish"],
        ["REJECTED", "Rad etilgan"],
      ]),
      f("comments", "Izoh", "textarea"),
    ],
    columns: [
      ["process_name", "Jarayon"],
      ["revision", "Versiya"],
      ["rto_hours", "RTO, soat"],
      ["mtpd_hours", "MTPD, soat"],
      ["status", "Holat"],
    ],
    order: "-revision",
  },
  risks: {
    title: "Risklar reyestri",
    fields: [
      processField,
      relation("asset", "Bog‘langan aktiv", "assets"),
      f("threat", "Tahdid", "text", { required: true }),
      f("vulnerability", "Zaiflik", "textarea"),
      f("likelihood", "Ehtimollik (ordinal 1–5 ball)", "number", {
        min: 1,
        required: true,
      }),
      f("impact", "Ta’sir (1–5 ball)", "number", { min: 1, required: true }),
      f("likelihood_residual", "Qoldiq ehtimollik (1–5)", "number", { min: 1 }),
      f("impact_residual", "Qoldiq ta’sir (1–5)", "number", { min: 1 }),
      ownerField,
      f("evidence", "Baholash dalili", "textarea"),
      f("treatment", "Riskka javob chorasi", "textarea"),
      f("due_date", "Chora muddati", "date"),
      options("status", "Holat", [
        ["IDENTIFIED", "Aniqlangan"],
        ["ASSESSED", "Baholangan"],
        ["MITIGATED", "Chora qo‘llangan"],
        ["ACCEPTED", "Qabul qilingan"],
      ]),
    ],
    columns: [
      ["threat", "Tahdid"],
      ["process_name", "Jarayon"],
      ["risk_score", "Boshlang‘ich ball"],
      ["residual_risk_score", "Qoldiq ball"],
      ["risk_class", "Daraja"],
    ],
    order: "-id",
  },
  controls: {
    title: "Nazorat choralari",
    fields: [
      relation("risk", "Risk", "risks", true),
      f("title", "Chora nomi", "text", { required: true }),
      f("description", "Tavsif", "textarea"),
      ownerField,
      f("due_date", "Muddat", "date"),
      options("status", "Holat", [
        ["PLANNED", "Rejalashtirilgan"],
        ["IN_PROGRESS", "Bajarilmoqda"],
        ["IMPLEMENTED", "Joriy etilgan"],
        ["EFFECTIVE", "Samarali"],
      ]),
      f("effectiveness_evidence", "Samaradorlik dalili", "textarea"),
    ],
    columns: [
      ["title", "Chora"],
      ["status_display", "Holat"],
      ["due_date", "Muddat"],
    ],
  },
  strategies: {
    title: "Tiklash strategiyalari",
    fields: [
      processField,
      f("name", "Variant nomi", "text", { required: true }),
      options("kind", "Tiklash usuli", [
        ["BACKUP", "Backupdan tiklash"],
        ["INFRASTRUCTURE", "Zaxira infratuzilma"],
        ["WORKPLACE", "Muqobil ish joyi"],
        ["MANUAL", "Vaqtinchalik qo‘lda bajarish"],
        ["SUPPLIER", "Muqobil yetkazib beruvchi"],
      ]),
      f("description", "Tavsif", "textarea"),
      f("estimated_rto_hours", "Tiklash davomiyligi (soat)", "number", {
        min: 0.01,
        required: true,
      }),
      f("estimated_rpo_minutes", "Ma’lumot yo‘qotilishi (daqiqa)", "number", {
        min: 0,
        required: true,
      }),
      f("estimated_cost", "Xarajat (UZS)", "number", {
        min: 0,
        required: true,
      }),
      f("preparation_minutes", "Tayyorgarlik vaqti (daqiqa)", "number", {
        min: 0,
      }),
      f("staff_required", "Kerakli mutaxassislar", "number", { min: 1 }),
      f("resource_requirements", "Kerakli resurslar va miqdor", "resources"),
      f("conditions", "Qo‘llash shartlari", "textarea"),
      f("is_selected", "Mas’ul tanlagan variant", "checkbox"),
    ],
    columns: [
      ["name", "Variant"],
      ["process_name", "Jarayon"],
      ["estimated_rto_hours", "Davomiylik, soat"],
      ["estimated_cost", "Xarajat, UZS"],
    ],
  },
  resources: {
    title: "Tiklash resurslari",
    fields: [
      f("name", "Resurs nomi", "text", { required: true }),
      options("kind", "Turi", [
        ["STAFF", "Mutaxassis"],
        ["EQUIPMENT", "Uskuna"],
        ["LOCATION", "Ish joyi"],
      ]),
      f("capacity", "Bir vaqtdagi quvvat", "number", {
        min: 1,
        required: true,
      }),
      f(
        "available_from_minutes",
        "Mavjud bo‘lish vaqti (hodisadan so‘ng, daqiqa)",
        "number",
        { min: 0 },
      ),
      f("unavailable_until_minutes", "Bandlik tugashi (daqiqa)", "number", {
        min: 0,
      }),
    ],
    columns: [
      ["name", "Resurs"],
      ["capacity", "Quvvat"],
      ["available_from_minutes", "Mavjud, daqiqa"],
      ["unavailable_until_minutes", "Band, daqiqa"],
    ],
  },
  plans: {
    title: "Uzluksizlik rejalari",
    fields: [
      processField,
      f("title", "Reja nomi", "text", { required: true }),
      f("version", "Versiya", "text", { required: true }),
      f("scope", "Maqsad va qamrov", "textarea", { required: true }),
      f("activation_conditions", "Ishga tushirish shartlari", "textarea", {
        required: true,
      }),
      f("contacts", "Mas’ullar va aloqalar", "textarea", { required: true }),
      f("temporary_procedures", "Vaqtinchalik ish tartibi", "textarea", {
        required: true,
      }),
      f("return_to_normal", "Normal holatga qaytish", "textarea", {
        required: true,
      }),
      f("verification_criteria", "Tekshirish mezonlari", "textarea", {
        required: true,
      }),
      relation("schedule_run", "Saqlangan tiklash jadvali", "schedule-runs"),
      f("review_due_date", "Keyingi ko‘rib chiqish muddati", "date"),
      f("steps", "Tiklash bosqichlari", "steps"),
      options("status", "Holat", [
        ["DRAFT", "Qoralama"],
        ["IN_REVIEW", "Ko‘rib chiqishda"],
      ]),
    ],
    columns: [
      ["title", "Reja"],
      ["process_name", "Jarayon"],
      ["version", "Versiya"],
      ["status_display", "Holat"],
      ["review_due_date", "Ko‘rib chiqish muddati"],
    ],
  },
  scenarios: {
    title: "Uzilish ssenariylari",
    fields: [
      f("title", "Ssenariy nomi", "text", { required: true }),
      f("description", "Hodisa tavsifi", "textarea"),
      options("kind", "Hodisa turi", [
        ["SERVER", "Server nosozligi"],
        ["POWER", "Elektr uzilishi"],
        ["INTERNET", "Internet uzilishi"],
        ["MALWARE", "Zararli dastur sababli uzilish"],
        ["SUPPLIER", "Yetkazib beruvchi ishlamasligi"],
        ["COMBINED", "Bir nechta uzilish"],
      ]),
      f("disrupted_asset_ids", "Ta’sirlangan aktivlar", "multiple", {
        source: "assets",
      }),
      f("estimated_outage_hours", "Taxminiy uzilish (soat)", "number", {
        min: 0,
        required: true,
      }),
      f("event_time", "Hodisa vaqti", "datetime-local"),
      f("available_resources", "Mavjud resurslar va quvvat", "resources"),
      f("recovery_options", "Mavjud tiklash variantlari", "multiple", {
        source: "strategies",
      }),
      f("is_synthetic", "Sun’iy ssenariy", "checkbox"),
    ],
    columns: [
      ["title", "Ssenariy"],
      ["estimated_outage_hours", "Uzilish, soat"],
      ["is_synthetic", "Sun’iy ma’lumot"],
    ],
  },
  exercises: {
    title: "Mashqlar va takomillashtirish",
    fields: [
      relation("plan", "Tasdiqlangan reja", "plans", true),
      relation("scenario", "Ssenariy", "scenarios"),
      f("exercise_date", "Mashq sanasi", "date", { required: true }),
      f("actual_recovery_hours", "Kuzatilgan tiklanish (soat)", "number", {
        min: 0.01,
        required: true,
      }),
      options("outcome", "Natija", [
        ["SUCCESS", "Muvaffaqiyatli"],
        ["PARTIAL", "Qisman"],
        ["FAILED", "Muvaffaqiyatsiz"],
      ]),
      f("resource_shortages", "Resurs tanqisligi", "textarea"),
      f("unfinished_tasks", "Bajarilmagan vazifalar", "textarea"),
      f("findings", "Aniqlangan kamchiliklar", "textarea"),
      f("improvement_actions", "Takomillashtirish choralari", "textarea"),
      f("findings_closed", "Kamchiliklar bartaraf etildi", "checkbox"),
      f("is_synthetic", "Sun’iy / o‘quv mashqi", "checkbox"),
    ],
    columns: [
      ["plan_title", "Reja"],
      ["exercise_date", "Sana"],
      ["planned_recovery_hours", "Maqsad, soat"],
      ["actual_recovery_hours", "Kuzatilgan, soat"],
      ["outcome_display", "Natija"],
    ],
  },
  "audit-logs": {
    title: "Audit jurnali",
    fields: [],
    columns: [
      ["actor_username", "Foydalanuvchi"],
      ["action", "Amal"],
      ["entity", "Obyekt"],
      ["entity_id", "ID"],
      ["timestamp", "Vaqt"],
    ],
    order: "-timestamp",
  },
};
const defaults: Row = {
  is_active: true,
  timezone: "Asia/Tashkent",
  max_acceptable_loss: 500000000,
  risk_low_threshold: 6,
  risk_medium_threshold: 14,
  capacity: 1,
  required_staff: 1,
  staff_required: 1,
  revision: 1,
  version: "1.0",
  rpo_minutes: 60,
  backup_interval_minutes: 60,
  preparation_minutes: 0,
  available_from_minutes: 0,
  unavailable_until_minutes: 0,
  data_recovery_applicable: true,
  is_synthetic: true,
};
const labelFor = (row: Row) =>
  row.name ||
  row.title ||
  row.threat ||
  row.username ||
  `${row.id} · ${row.algorithm_version || ""}`;
const textValue = (value: any): string =>
  value == null || value === ""
    ? "—"
    : typeof value === "boolean"
      ? value
        ? "Ha"
        : "Yo‘q"
      : String(value);
const translations: Record<string, string> = {
  DRAFT: "Qoralama",
  IN_REVIEW: "Ko‘rib chiqishda",
  SUBMITTED: "Yuborilgan",
  APPROVED: "Tasdiqlangan",
  PUBLISHED: "E’lon qilingan",
  ARCHIVED: "Arxivlangan",
  REJECTED: "Rad etilgan",
  ACTIVE: "Faol",
  INACTIVE: "Nofaol",
  UNDER_REVIEW: "Ko‘rib chiqishda",
  MANDATORY: "Majburiy",
  OPTIONAL: "Zaxirali",
  high: "Yuqori",
  medium: "O‘rta",
  low: "Past",
};
export function canWrite(user: User, resource: string) {
  if (["users", "organizations"].includes(resource))
    return user.role === "ADMIN";
  if (["ADMIN", "BCMS_MANAGER"].includes(user.role))
    return !["audit-logs", "simulation-runs"].includes(resource);
  if (user.role === "RISK_ANALYST")
    return ["risks", "controls"].includes(resource);
  return (
    user.role === "PROCESS_OWNER" &&
    ["processes", "bia", "risks", "strategies", "plans", "exercises"].includes(
      resource,
    )
  );
}
function useChoices(fields: Field[]) {
  const [choices, setChoices] = useState<Record<string, Row[]>>({});
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const sources = [
      ...new Set(
        fields.flatMap((field) =>
          field.source && !["from", "to"].includes(field.source)
            ? [field.source]
            : field.type === "steps"
              ? ["users"]
              : field.type === "resources"
                ? ["resources"]
                : [],
        ),
      ),
    ];
    if (fields.some((field) => ["from", "to"].includes(field.source || "")))
      sources.push("processes", "assets");
    Promise.all(
      [...new Set(sources)].map(async (source) => {
        let rows: Row[] = [];
        let page = 1;
        let more = true;
        while (more) {
          const response = await api.list(
            source,
            `page_size=100&page=${page++}`,
          );
          rows = rows.concat(response.results);
          more = !!response.next;
        }
        return [source, rows] as const;
      }),
    )
      .then((results) => {
        if (active) setChoices(Object.fromEntries(results));
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [fields]);
  return { choices, error };
}

function RepeatedField({
  field,
  value,
  onChange,
  choices,
}: {
  field: Field;
  value: any;
  onChange: (value: any) => void;
  choices: Record<string, Row[]>;
}) {
  if (field.type === "weights") {
    const weights =
      value && Object.keys(value).length
        ? value
        : { financial: 0.35, operational: 0.25, legal: 0.2, reputational: 0.2 };
    return (
      <div className="compact-grid">
        {[
          ["financial", "Moliyaviy"],
          ["operational", "Operatsion"],
          ["legal", "Majburiyatlar"],
          ["reputational", "Obro‘"],
        ].map(([key, label]) => (
          <label key={key}>
            {label}
            <input
              aria-label={`${label} vazni`}
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={weights[key]}
              onChange={(e) =>
                onChange({ ...weights, [key]: Number(e.target.value) })
              }
            />
          </label>
        ))}
        <small>
          Vaznlar yig‘indisi 1. Moliyaviy zarar tashkilot chegarasiga, ballar
          (ball−1)/4 bilan normallashtiriladi.
        </small>
      </div>
    );
  }
  if (field.type === "resources")
    return (
      <div className="compact-grid">
        {(choices.resources || []).length ? (
          choices.resources.map((r) => (
            <label key={r.id}>
              {r.name} (quvvat {r.capacity})
              <input
                type="number"
                min="0"
                step="1"
                value={value?.[r.id] ?? 0}
                onChange={(e) => {
                  const next = { ...value, [r.id]: Number(e.target.value) };
                  if (!next[r.id]) delete next[r.id];
                  onChange(next);
                }}
              />
            </label>
          ))
        ) : (
          <p>Avval «Tiklash resurslari» bo‘limida resurs kiriting.</p>
        )}
      </div>
    );
  const rows: Row[] = value || [];
  const isImpact = field.type === "impacts";
  const columns = isImpact
    ? [
        ["horizon_hours", "Uzilish, soat"],
        ["financial_loss", "Zarar, UZS"],
        ["operational_score", "Operatsion (1–5)"],
        ["legal_score", "Majburiyatlar (1–5)"],
        ["reputational_score", "Obro‘ (1–5)"],
      ]
    : [
        ["sequence", "Tartib"],
        ["title", "Bosqich nomi"],
        ["description", "Tavsif"],
        ["expected_duration_minutes", "Davomiylik, daqiqa"],
      ];
  const update = (index: number, key: string, v: any) =>
    onChange(rows.map((row, i) => (i === index ? { ...row, [key]: v } : row)));
  return (
    <div>
      {rows.map((row, i) => (
        <fieldset key={i} className="nested-row">
          <legend>
            {isImpact ? "Vaqt oralig‘i" : "Bosqich"} {i + 1}
          </legend>
          <div className="compact-grid">
            {columns.map(([key, label]) => (
              <label key={key}>
                {label}
                <input
                  aria-label={`${label} ${i + 1}`}
                  required
                  type={
                    ["title", "description"].includes(key) ? "text" : "number"
                  }
                  min={key.includes("score") ? 1 : 0}
                  max={key.includes("score") ? 5 : undefined}
                  step={
                    key === "horizon_hours" || key === "financial_loss"
                      ? "0.01"
                      : "1"
                  }
                  value={row[key] ?? ""}
                  onChange={(e) =>
                    update(
                      i,
                      key,
                      ["title", "description"].includes(key)
                        ? e.target.value
                        : Number(e.target.value),
                    )
                  }
                />
              </label>
            ))}
            {!isImpact && (
              <label>
                Mas’ul
                <select
                  value={row.assigned_to || ""}
                  onChange={(e) =>
                    update(
                      i,
                      "assigned_to",
                      e.target.value ? Number(e.target.value) : null,
                    )
                  }
                >
                  <option value="">Tanlanmagan</option>
                  {(choices.users || []).map((user) => (
                    <option key={user.id} value={user.id}>
                      {labelFor(user)}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => onChange(rows.filter((_, index) => index !== i))}
          >
            Qatorni olib tashlash
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        className="btn btn-secondary"
        onClick={() =>
          onChange([
            ...rows,
            isImpact
              ? {
                  horizon_hours: 1,
                  financial_loss: 0,
                  operational_score: 1,
                  legal_score: 1,
                  reputational_score: 1,
                }
              : {
                  sequence: rows.length + 1,
                  title: "",
                  description: "",
                  expected_duration_minutes: 30,
                  assigned_to: null,
                },
          ])
        }
      >
        {isImpact ? "Vaqt oralig‘i qo‘shish" : "Bosqich qo‘shish"}
      </button>
    </div>
  );
}

function Editor({
  resource,
  row,
  user,
  onClose,
  onSaved,
}: {
  resource: string;
  row: Row | null;
  user: User;
  onClose: () => void;
  onSaved: () => void;
}) {
  const config = CONFIGS[resource];
  const { choices, error: choiceError } = useChoices(config.fields);
  const [data, setData] = useState<Row>(() =>
    Object.fromEntries(
      config.fields.map((field) => [
        field.key,
        row?.[field.key] ??
          defaults[field.key] ??
          (field.type === "checkbox"
            ? false
            : field.type === "multiple" ||
                ["impacts", "steps"].includes(field.type || "")
              ? []
              : field.type === "resources" || field.type === "weights"
                ? {}
                : (field.options?.[0]?.[0] ?? "")),
      ]),
    ),
  );
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const dirty = useRef(false);
  const panel = useRef<HTMLDivElement>(null);
  const submitLock = useRef(false);
  const close = useCallback(() => {
    if (
      !dirty.current ||
      window.confirm("Saqlanmagan o‘zgarishlar yo‘qoladi. Yopilsinmi?")
    )
      onClose();
  }, [onClose]);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const first = panel.current?.querySelector<HTMLElement>(
      "input,select,textarea,button",
    );
    first?.focus();
    const unload = (e: BeforeUnloadEvent) => {
      if (dirty.current) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
      }
      if (e.key === "Tab") {
        const targets = Array.from(
          panel.current?.querySelectorAll<HTMLElement>(
            "button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled)",
          ) || [],
        );
        const first = targets[0],
          last = targets[targets.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("beforeunload", unload);
    window.addEventListener("keydown", key);
    return () => {
      window.removeEventListener("beforeunload", unload);
      window.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, [close]);
  const change = (key: string, value: any) => {
    dirty.current = true;
    setData((prev) => ({ ...prev, [key]: value }));
  };
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitLock.current) return;
    submitLock.current = true;
    setBusy(true);
    setError("");
    try {
      const payload: Row = {};
      for (const field of config.fields) {
        const value = data[field.key];
        if (field.type === "password" && !value) continue;
        payload[field.key] =
          field.type === "relation" ||
          field.type === "number" ||
          field.type === "date" ||
          field.type === "datetime-local"
            ? value === ""
              ? null
              : field.type === "number" || field.type === "relation"
                ? Number(value)
                : field.type === "datetime-local"
                  ? new Date(value).toISOString()
                  : value
            : value;
      }
      if (user.role === "PROCESS_OWNER" && resource === "processes")
        payload.owner = user.id;
      if (row) await api.update(resource, row.id, payload);
      else await api.create(resource, payload);
      dirty.current = false;
      onSaved();
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      submitLock.current = false;
    }
  };
  return (
    <div className="modal-overlay">
      <div
        ref={panel}
        className="modal-panel workspace-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="edit-title"
      >
        <div className="modal-header">
          <h2 id="edit-title">
            {row ? "Tahrirlash" : "Yangi yozuv"} · {config.title}
          </h2>
          <button
            className="btn btn-secondary"
            onClick={close}
            disabled={busy}
            aria-label="Yopish"
          >
            ×
          </button>
        </div>
        <form onSubmit={submit}>
          <div className="modal-body form-grid">
            {(error || choiceError) && (
              <p className="form-error" role="alert">
                {error || choiceError}
              </p>
            )}
            {config.fields.map((field) => {
              const id = `field-${field.key}`;
              const source = ["from", "to"].includes(field.source || "")
                ? data[`${field.source}_type`] === "PROCESS"
                  ? "processes"
                  : "assets"
                : field.source;
              let rows = choices[source || ""] || [];
              if (resource === "exercises" && source === "plans")
                rows = rows.filter((r) =>
                  ["APPROVED", "PUBLISHED"].includes(r.status),
                );
              if (user.role === "PROCESS_OWNER" && source === "processes")
                rows = rows.filter((r) => r.owner === user.id);
              return (
                <div
                  className={
                    [
                      "textarea",
                      "impacts",
                      "steps",
                      "weights",
                      "resources",
                    ].includes(field.type || "")
                      ? "form-group wide"
                      : "form-group"
                  }
                  key={field.key}
                >
                  <label htmlFor={id}>
                    {field.label}
                    {field.required ? " *" : ""}
                  </label>
                  {["weights", "resources", "steps", "impacts"].includes(
                    field.type || "",
                  ) ? (
                    <RepeatedField
                      field={field}
                      value={data[field.key]}
                      onChange={(v) => change(field.key, v)}
                      choices={choices}
                    />
                  ) : field.type === "textarea" ? (
                    <textarea
                      id={id}
                      required={field.required}
                      value={data[field.key] || ""}
                      onChange={(e) => change(field.key, e.target.value)}
                      rows={3}
                    />
                  ) : ["select", "relation", "multiple"].includes(
                      field.type || "",
                    ) ? (
                    <select
                      id={id}
                      multiple={field.type === "multiple"}
                      required={field.required}
                      value={data[field.key] ?? ""}
                      onChange={(e) =>
                        change(
                          field.key,
                          field.type === "multiple"
                            ? Array.from(e.target.selectedOptions).map((o) =>
                                Number(o.value),
                              )
                            : field.type === "relation"
                              ? e.target.value
                                ? Number(e.target.value)
                                : null
                              : e.target.value,
                        )
                      }
                    >
                      {field.type === "relation" && (
                        <option value="">Tanlang</option>
                      )}
                      {field.type === "select"
                        ? field.options?.map(([value, label]) => (
                            <option key={value} value={value}>
                              {label}
                            </option>
                          ))
                        : rows.map((r) => (
                            <option key={r.id} value={r.id}>
                              {labelFor(r)}
                            </option>
                          ))}
                    </select>
                  ) : field.type === "checkbox" ? (
                    <input
                      id={id}
                      type="checkbox"
                      checked={!!data[field.key]}
                      onChange={(e) => change(field.key, e.target.checked)}
                    />
                  ) : (
                    <input
                      id={id}
                      type={field.type}
                      min={field.min}
                      step={field.type === "number" ? "any" : undefined}
                      required={
                        field.required ||
                        (resource === "users" &&
                          field.key === "password" &&
                          !row)
                      }
                      autoComplete={
                        field.type === "password" ? "new-password" : undefined
                      }
                      value={
                        field.type === "datetime-local" && data[field.key]
                          ? data[field.key].slice(0, 16)
                          : (data[field.key] ?? "")
                      }
                      onChange={(e) => change(field.key, e.target.value)}
                    />
                  )}{" "}
                  {field.hint && <small>{field.hint}</small>}
                </div>
              );
            })}
          </div>
          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              disabled={busy}
              onClick={close}
            >
              Bekor qilish
            </button>
            <button
              className="btn btn-primary"
              disabled={busy || !!choiceError}
              type="submit"
            >
              {busy ? "Saqlanmoqda…" : "Saqlash"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ResourcePanel({
  resource,
  user,
  onChanged,
}: {
  resource: string;
  user: User;
  onChanged: () => void;
}) {
  const config = CONFIGS[resource];
  const [rows, setRows] = useState<Row[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [ordering, setOrdering] = useState(config.order || "id");
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editor, setEditor] = useState<Row | null | undefined>();
  const [detail, setDetail] = useState<Row | null>(null);
  const [refresh, setRefresh] = useState(0);
  const currentRequest = useRef(0);
  const lock = useRef(false);
  const reload = () => {
    setRefresh((v) => v + 1);
    onChanged();
  };
  useEffect(() => {
    const request = ++currentRequest.current;
    let active = true;
    const timer = setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const query = new URLSearchParams({
          page: String(page),
          search,
          ordering,
        });
        const hashQuery = location.hash.split("?")[1];
        if (hashQuery)
          new URLSearchParams(hashQuery).forEach((v, k) => query.set(k, v));
        if (filter)
          query.set(resource === "assets" ? "type" : "status", filter);
        const response = await api.list(resource, query.toString());
        if (active && request === currentRequest.current) {
          setRows(response.results);
          setCount(response.count);
        }
      } catch (e) {
        if (active && request === currentRequest.current)
          setError((e as Error).message);
      } finally {
        if (active && request === currentRequest.current) setLoading(false);
      }
    }, 200);
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [resource, page, search, ordering, filter, refresh]);
  const act = async (run: () => Promise<unknown>) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await run();
      if (
        result &&
        typeof result === "object" &&
        "affected_processes" in result
      )
        setDetail(result as Row);
      reload();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      lock.current = false;
    }
  };
  const writable = canWrite(user, resource);
  const approver = ["ADMIN", "APPROVER"].includes(user.role);
  return (
    <section className="card resource-panel" aria-label={config.title}>
      <div className="card-header">
        <div>
          <h2 className="card-title">{config.title}</h2>
          <p className="card-subtitle">
            {count} ta saqlangan yozuv ·{" "}
            {user.role === "AUDITOR"
              ? "Faqat ko‘rish"
              : "Tashkilotingiz ma’lumotlari"}
          </p>
        </div>
        {writable && resource !== "organizations" && (
          <button className="btn btn-primary" onClick={() => setEditor(null)}>
            Yangi yozuv
          </button>
        )}
      </div>
      <div className="resource-toolbar">
        <label>
          Qidiruv
          <input
            type="search"
            placeholder="Nom yoki tavsif"
            value={search}
            onChange={(e) => {
              setPage(1);
              setSearch(e.target.value);
            }}
          />
        </label>
        <label>
          Saralash
          <select
            value={ordering}
            onChange={(e) => {
              setPage(1);
              setOrdering(e.target.value);
            }}
          >
            <option value={config.order || "id"}>Asosiy tartib</option>
            <option value="id">Avval eskilari</option>
            <option value="-id">Avval yangilari</option>
          </select>
        </label>
        {config.fields.find((f) => f.key === "status" && f.options) && (
          <label>
            Holat
            <select
              value={filter}
              onChange={(e) => {
                setPage(1);
                setFilter(e.target.value);
              }}
            >
              <option value="">Barchasi</option>
              {[
                ...(config.fields.find((f) => f.key === "status")?.options ||
                  []),
                ...(["plans", "bia"].includes(resource)
                  ? [
                      ["APPROVED", "Tasdiqlangan"],
                      ...(resource === "plans"
                        ? [
                            ["PUBLISHED", "E’lon qilingan"],
                            ["ARCHIVED", "Arxivlangan"],
                          ]
                        : []),
                    ]
                  : []),
              ].map(([v, l]) => (
                <option value={v} key={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        )}
        <button
          className="btn btn-secondary"
          onClick={() => setRefresh((v) => v + 1)}
        >
          Yangilash
        </button>
        {resource === "processes" && (
          <a
            className="btn btn-secondary"
            href={`/api/v1/reports/processes.csv?search=${encodeURIComponent(search)}&ordering=${encodeURIComponent(ordering)}`}
          >
            CSV eksport
          </a>
        )}
      </div>
      {error && (
        <div className="form-error" role="alert">
          {error}
          <button
            className="btn btn-secondary"
            onClick={() => setRefresh((v) => v + 1)}
          >
            Qayta urinish
          </button>
        </div>
      )}
      {loading ? (
        <p className="panel-message" role="status">
          Yuklanmoqda…
        </p>
      ) : rows.length === 0 ? (
        <div className="panel-message">
          {search || filter
            ? "Mos yozuv topilmadi."
            : "Hali ma’lumot kiritilmagan."}
        </div>
      ) : (
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                {config.columns.map(([key, label]) => (
                  <th key={key}>{label}</th>
                ))}
                <th>Amallar</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const locked = ["APPROVED", "PUBLISHED", "ARCHIVED"].includes(
                  row.status,
                );
                const own = user.role !== "PROCESS_OWNER" || (resource === "processes" ? row.owner === user.id : row.process_owner_id === user.id);
                return (
                  <tr key={row.id}>
                    {config.columns.map(([key]) => (
                      <td key={key}>
                        {translations[row[key]] || textValue(row[key])}
                      </td>
                    ))}
                    <td>
                      <div className="row-actions">
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={() => setDetail(row)}
                        >
                          Ko‘rish
                        </button>
                        {writable && own && !locked && (
                          <>
                            <button
                              className="btn btn-secondary btn-sm"
                              onClick={() => setEditor(row)}
                            >
                              Tahrirlash
                            </button>
                            {resource !== "organizations" && (
                              <button
                                className="btn btn-danger btn-sm"
                                disabled={busy}
                                onClick={() => {
                                  if (
                                    window.confirm(
                                      "Yozuv o‘chirilsinmi? Bog‘langan yozuvlar mavjud bo‘lsa amal rad etiladi.",
                                    )
                                  )
                                    void act(() =>
                                      api.remove(resource, row.id),
                                    );
                                }}
                              >
                                O‘chirish
                              </button>
                            )}
                          </>
                        )}
                        {approver &&
                          ((resource === "bia" &&
                            ["DRAFT", "SUBMITTED"].includes(row.status)) ||
                            (resource === "plans" &&
                              ["DRAFT", "IN_REVIEW"].includes(row.status))) && (
                            <button
                              className="btn btn-success btn-sm"
                              disabled={busy}
                              onClick={() =>
                                void act(() =>
                                  api.action(
                                    resource,
                                    row.id,
                                    resource === "bia" ? "approve" : "publish",
                                  ),
                                )
                              }
                            >
                              Tasdiqlash
                            </button>
                          )}
                        {writable &&
                          ["plans", "bia"].includes(resource) &&
                          locked && (
                            <button
                              className="btn btn-secondary btn-sm"
                              disabled={busy}
                              onClick={() =>
                                void act(() =>
                                  api.action(resource, row.id, "revise"),
                                )
                              }
                            >
                              Yangi versiya
                            </button>
                          )}
                        {resource === "plans" && (
                          <>
                            <a
                              className="btn btn-secondary btn-sm"
                              href={`/api/v1/plans/${row.id}/export_pdf/`}
                            >
                              PDF
                            </a>
                            <a
                              className="btn btn-secondary btn-sm"
                              href={`/api/v1/plans/${row.id}/export_docx/`}
                            >
                              DOCX
                            </a>
                            {approver &&
                              ["PUBLISHED", "APPROVED"].includes(
                                row.status,
                              ) && (
                                <button
                                  className="btn btn-secondary btn-sm"
                                  disabled={busy}
                                  onClick={() =>
                                    void act(() =>
                                      api.action(resource, row.id, "archive"),
                                    )
                                  }
                                >
                                  Arxivlash
                                </button>
                              )}
                          </>
                        )}
                        {resource === "scenarios" && writable && (
                          <button
                            className="btn btn-primary btn-sm"
                            disabled={busy}
                            onClick={() =>
                              void act(() =>
                                api.action(resource, row.id, "simulate"),
                              )
                            }
                          >
                            Xavfsiz simulyatsiya
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <div className="pagination">
        <button
          className="btn btn-secondary"
          disabled={page === 1 || loading}
          onClick={() => setPage((p) => p - 1)}
        >
          Oldingi
        </button>
        <span>
          {page} / {Math.max(1, Math.ceil(count / 20))}
        </span>
        <button
          className="btn btn-secondary"
          disabled={page * 20 >= count || loading}
          onClick={() => setPage((p) => p + 1)}
        >
          Keyingi
        </button>
      </div>
      {editor !== undefined && (
        <Editor
          resource={resource}
          row={editor}
          user={user}
          onClose={() => setEditor(undefined)}
          onSaved={reload}
        />
      )}{" "}
      {detail && (
        <Detail
          row={detail}
          title={config.title}
          onClose={() => setDetail(null)}
        />
      )}
    </section>
  );
}

function Detail({
  row,
  title,
  onClose,
}: {
  row: Row;
  title: string;
  onClose: () => void;
}) {
  const fields = Object.values(CONFIGS).flatMap((c) => c.fields);
  const labels = Object.fromEntries(fields.map((f) => [f.key, f.label]));
  return (
    <div className="modal-overlay">
      <div
        className="modal-panel workspace-modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-header">
          <h2>{labelFor(row) || title}</h2>
          <button autoFocus className="btn btn-secondary" onClick={onClose}>
            Yopish
          </button>
        </div>
        <div className="modal-body detail-grid">
          {Object.entries(row)
            .filter(
              ([key]) =>
                ![
                  "snapshot",
                  "organization",
                  "is_deleted",
                  "password",
                ].includes(key),
            )
            .map(([key, value]) => (
              <div key={key}>
                <strong>
                  {labels[key] ||
                    (
                      {
                        process_name: "Jarayon",
                        approved_by_name: "Tasdiqlovchi",
                        approved_at: "Tasdiqlangan vaqt",
                        created_at: "Yaratilgan",
                        updated_at: "Yangilangan",
                        actual_recovery_hours: "Kuzatilgan tiklanish",
                        affected_processes: "Ta’sirlangan jarayonlar",
                        target_rto_hours: "Maqsadli RTO",
                        rto_breached: "RTO buzilgan",
                      } as Row
                    )[key] ||
                    key}
                </strong>
                {typeof value === "object" && value !== null ? (
                  <pre>{JSON.stringify(value, null, 2)}</pre>
                ) : (
                  <p>{translations[value] || textValue(value)}</p>
                )}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}

export function GraphPanel() {
  const [graph, setGraph] = useState<Row | null>(null),
    [error, setError] = useState(""),
    [selected, setSelected] = useState<Row | null>(null),
    [search, setSearch] = useState("");
  const load = () =>
    api
      .graph()
      .then(setGraph)
      .catch((e) => setError(e.message));
  useEffect(() => {
    void load();
  }, []);
  const nodes = (graph?.nodes || []).filter((n: Row) =>
    n.label.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Bog‘liqlik xaritasi</h2>
          <p>{graph?.direction}</p>
        </div>
        <button className="btn btn-secondary" onClick={load}>
          Yangilash
        </button>
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <div className="modal-body">
        <label>
          Tugun qidirish
          <input value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        {graph?.cycles?.length > 0 && (
          <p className="form-error">
            Majburiy sikl mavjud:{" "}
            {graph?.cycles
              .map((cycle: string[]) => cycle.join(" → "))
              .join("; ")}
            . Jadval uchun siklni bartaraf eting.
          </p>
        )}
        {nodes.length > 0 && (
          <div
            className="graph-svg-scroll"
            aria-label="Yo‘naltirilgan bog‘liqlik grafigi"
          >
            <svg
              width="1000"
              height={Math.max(
                150,
                Math.ceil(Math.min(nodes.length, 60) / 3) * 120,
              )}
              role="img"
              aria-label="Bog‘liq obyektdan zarur obyektga yo‘nalgan o‘qlar"
            >
              <defs>
                <marker
                  id="dep-arrow"
                  markerWidth="9"
                  markerHeight="9"
                  refX="8"
                  refY="4.5"
                  orient="auto"
                >
                  <path d="M0,0 L9,4.5 L0,9 Z" fill="#6c8ca2" />
                </marker>
              </defs>
              {(graph?.edges || []).map((edge: Row) => {
                const from = nodes
                    .slice(0, 60)
                    .findIndex((n: Row) => n.id === edge.source),
                  to = nodes
                    .slice(0, 60)
                    .findIndex((n: Row) => n.id === edge.target);
                if (from < 0 || to < 0) return null;
                return (
                  <path
                    key={edge.id}
                    d={`M${(from % 3) * 320 + 160},${Math.floor(from / 3) * 120 + 80} L${(to % 3) * 320 + 160},${Math.floor(to / 3) * 120 + 20}`}
                    stroke="#6c8ca2"
                    fill="none"
                    strokeWidth="1.5"
                    strokeDasharray={
                      edge.criticality === "OPTIONAL" ? "6 4" : undefined
                    }
                    markerEnd="url(#dep-arrow)"
                  />
                );
              })}
              {nodes.slice(0, 60).map((node: Row, index: number) => (
                <g
                  key={node.id}
                  role="button"
                  tabIndex={0}
                  aria-label={node.label}
                  onClick={() => setSelected(node)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      setSelected(node);
                    }
                  }}
                  transform={`translate(${(index % 3) * 320 + 25},${Math.floor(index / 3) * 120 + 20})`}
                >
                  <rect
                    width="270"
                    height="60"
                    rx="8"
                    fill="var(--color-bg-card)"
                    stroke={selected?.id === node.id ? "#087f86" : "#9bb8c7"}
                    strokeWidth="2"
                  />
                  <text x="12" y="23">
                    {node.type === "PROCESS" ? "Jarayon" : "Aktiv"} ·{" "}
                    {node.object_id}
                  </text>
                  <text x="12" y="45">
                    {node.label.length > 31
                      ? node.label.slice(0, 30) + "…"
                      : node.label}
                  </text>
                  <title>{node.label}</title>
                </g>
              ))}
            </svg>
            {nodes.length > 60 && (
              <small>
                Grafda dastlabki 60 tugun ko‘rsatiladi. Qidiruvdan foydalaning;
                barcha tugunlar quyidagi ro‘yxatda mavjud.
              </small>
            )}
          </div>
        )}
        <div className="graph-list">
          {nodes.map((node: Row) => (
            <button
              key={node.id}
              className={`graph-node ${selected?.id === node.id ? "selected" : ""}`}
              onClick={() => setSelected(node)}
            >
              <span>{node.type === "PROCESS" ? "Jarayon" : "Aktiv"}</span>
              <strong>{node.label}</strong>
              <small>{node.affected_nodes.length} ta bog‘liq tugun</small>
            </button>
          ))}
          {graph && !nodes.length && (
            <p>Hali tugunlar yo‘q yoki qidiruvga mos kelmadi.</p>
          )}
        </div>
        {selected && (
          <div className="graph-detail">
            <h3>{selected.label}</h3>
            <p>Uzilganda ta’sirlanadigan obyektlar:</p>
            <ul>
              {selected.affected_nodes.map((id: string) => (
                <li key={id}>
                  {graph?.nodes.find((n: Row) => n.id === id)?.label || id}
                </li>
              ))}
            </ul>
            <p>To‘g‘ridan-to‘g‘ri bog‘liqliklar:</p>
            {graph?.edges
              .filter(
                (e: Row) =>
                  e.source === selected.id || e.target === selected.id,
              )
              .map((e: Row) => (
                <p key={e.id}>
                  {graph.nodes.find((n: Row) => n.id === e.source)?.label} →{" "}
                  {graph.nodes.find((n: Row) => n.id === e.target)?.label} ·{" "}
                  {translations[e.criticality]}
                </p>
              ))}
          </div>
        )}
      </div>
    </section>
  );
}

export function SchedulerPanel({
  user,
  onChanged,
}: {
  user: User;
  onChanged: () => void;
}) {
  const [staff, setStaff] = useState(1),
    [budget, setBudget] = useState(""),
    [run, setRun] = useState<Row | null>(null),
    [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const lock = useRef(false);
  useEffect(() => {
    api
      .list("schedule-runs")
      .then((r) => setRun(r.results[0] || null))
      .catch((e) => setError(e.message));
  }, []);
  const calculate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      setRun(
        await api.create("schedule-runs", {
          staff_capacity: staff,
          ...(budget !== "" ? { budget } : {}),
        }),
      );
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      lock.current = false;
    }
  };
  return (
    <section className="card">
      <div className="card-header">
        <div>
          <h2>Tiklash jadvali va usullar taqqoslanishi</h2>
          <p>
            Bir xil kirish ma’lumotlari · vaqt daqiqalarda · xarajat UZS ·
            deterministik evristika
          </p>
        </div>
      </div>
      <div className="modal-body">
        {["ADMIN", "BCMS_MANAGER"].includes(user.role) && (
          <form className="resource-toolbar" onSubmit={calculate}>
            <label>
              Bir vaqtdagi mutaxassislar
              <input
                type="number"
                min="1"
                required
                value={staff}
                onChange={(e) => setStaff(Number(e.target.value))}
              />
            </label>
            <label>
              Budjet (bo‘sh bo‘lsa tashkilot sozlamasi)
              <input
                type="number"
                min="0"
                step="0.01"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              />
            </label>
            <button className="btn btn-primary" disabled={busy}>
              {busy ? "Hisoblanmoqda…" : "Hisoblash va saqlash"}
            </button>
          </form>
        )}
        {error && (
          <p role="alert" className="form-error">
            {error}
          </p>
        )}
        {!run && !busy && (
          <p>
            Hali hisoblash bajarilmagan. Avval BIA, strategiya va resurslarni
            to‘ldiring.
          </p>
        )}
        {run && (
          <>
            <p>
              Saqlangan hisob №{run.id} · {run.algorithm_version} ·{" "}
              {new Date(run.created_at).toLocaleString("uz-UZ")}
            </p>
            <div className="comparison-grid">
              {Object.entries(run.results).map(
                ([method, result]: [string, any]) => (
                  <div key={method} className="comparison-card">
                    <h3>
                      {method === "baseline"
                        ? "A · Muhimlik bo‘yicha navbat"
                        : "B · Bog‘liqlik va resurslar"}
                    </h3>
                    <p
                      className={
                        result.feasible ? "success-text" : "error-text"
                      }
                    >
                      {result.feasible
                        ? "Bajariladigan jadval"
                        : "Cheklovlar bajarilmagan"}
                    </p>
                    <p>
                      {result.makespan_minutes} daqiqa · {result.total_cost} UZS
                      · {result.rto_breaches} ta RTO buzilishi
                    </p>
                    <p>Hisoblash: {result.runtime_ms} ms</p>
                    <div className="table-scroll">
                      <table className="data-table">
                        <thead>
                          <tr>
                            <th>Jarayon</th>
                            <th>Boshlanish</th>
                            <th>Tugash</th>
                            <th>RTO</th>
                            <th>Resurslar</th>
                          </tr>
                        </thead>
                        <tbody>
                          {result.rows.map((row: Row) => (
                            <tr key={row.process_id}>
                              <td>
                                {row.process_name}
                                <small>{row.strategy_name}</small>
                              </td>
                              <td>{row.start_minutes}</td>
                              <td>{row.end_minutes}</td>
                              <td>
                                {row.rto_breached ? "Buzilgan" : "Bajarilgan"} (
                                {row.target_rto_minutes})
                              </td>
                              <td>
                                {Object.entries(row.assigned_resources)
                                  .map(
                                    ([id, n]) =>
                                      `${run.input_snapshot.resources[id]?.name || id}: ${n}`,
                                  )
                                  .join(", ")}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {result.constraints.map((c: Row, i: number) => (
                      <p key={i} className="form-error">
                        {c.process_id ? `${c.process_id}-jarayon: ` : ""}
                        {c.detail}
                      </p>
                    ))}
                    <p>
                      Resurs bandligi:{" "}
                      {Object.entries(result.utilization)
                        .map(
                          ([id, n]) =>
                            `${run.input_snapshot.resources[id]?.name || id}: ${Math.round(Number(n) * 100)}%`,
                        )
                        .join("; ")}
                    </p>
                  </div>
                ),
              )}
            </div>
            <details>
              <summary>
                Kirish ma’lumotlari nusxasi va algoritm versiyasi
              </summary>
              <pre>{JSON.stringify(run.input_snapshot, null, 2)}</pre>
            </details>
          </>
        )}
      </div>
    </section>
  );
}

export function Wizard({
  onNavigate,
  revision,
}: {
  onNavigate: (resource: string) => void;
  revision: number;
}) {
  const [data, setData] = useState<Row | null>(null),
    [error, setError] = useState("");
  useEffect(() => {
    api
      .workflow()
      .then(setData)
      .catch((e) => setError(e.message));
  }, [revision]);
  const mapping: Row = {
    organization: "organizations",
    processes: "processes",
    dependencies: "dependencies",
    bia: "bia",
    risks: "risks",
    strategies: "strategies",
    schedule: "schedule",
    approval: "plans",
    exercise: "exercises",
  };
  return (
    <section className="card wizard-card">
      <div className="card-header">
        <div>
          <h2>BCMS loyihalash ustasi</h2>
          <p>
            {data
              ? `${data.completed} / ${data.total} bosqich bajarilgan. Saqlangan ma’lumotlar bilan keyin davom etishingiz mumkin.`
              : "Bosqichlar tekshirilmoqda…"}
          </p>
        </div>
      </div>
      {error && (
        <p className="form-error" role="alert">
          {error}
        </p>
      )}
      <ol className="wizard-steps">
        {data?.steps.map((step: Row, index: number) => (
          <li key={step.key} className={step.complete ? "complete" : ""}>
            <button onClick={() => onNavigate(mapping[step.key])}>
              <span>{step.complete ? "✓" : index + 1}</span>
              <strong>{step.label}</strong>
              <small>
                {step.complete ? "Bajarilgan" : step.missing.join(" ")}
              </small>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function PasswordPanel() {
  const [old, setOld] = useState(""),
    [password, setPassword] = useState(""),
    [message, setMessage] = useState(""),
    [busy, setBusy] = useState(false);
  return (
    <section className="card">
      <div className="card-header">
        <h2>Parolni almashtirish</h2>
      </div>
      <form
        className="modal-body form-grid"
        onSubmit={async (e) => {
          e.preventDefault();
          if (busy) return;
          setBusy(true);
          setMessage("");
          try {
            const result = await api.password(old, password);
            setMessage(result.message);
            setOld("");
            setPassword("");
          } catch (e) {
            setMessage((e as Error).message);
          } finally {
            setBusy(false);
          }
        }}
      >
        <label>
          Joriy parol
          <input
            type="password"
            autoComplete="current-password"
            required
            value={old}
            onChange={(e) => setOld(e.target.value)}
          />
        </label>
        <label>
          Yangi parol
          <input
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="btn btn-primary" disabled={busy}>
          Parolni saqlash
        </button>
        <p role="status">{message}</p>
      </form>
    </section>
  );
}
