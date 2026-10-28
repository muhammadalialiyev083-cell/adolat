const ROUTES = new Set([
  "dashboard",
  "initial-setup",
  "menu",
  "catalog",
  "wizard",
  "organizations",
  "departments",
  "users",
  "services",
  "processes",
  "assets",
  "dependencies",
  "bia",
  "bia-questionnaire",
  "risks",
  "controls",
  "strategies",
  "resources",
  "schedule",
  "plans",
  "scenarios",
  "simulation-runs",
  "exercises",
  "audit-logs",
  "password",
  "imports",
  "management",
  "incidents",
  "integrations",
]);

export function safeHash(value: unknown): string {
  if (typeof value !== "string" || !value.startsWith("#/"))
    return "#/dashboard";
  const route = value.slice(2).split("?")[0];
  return ROUTES.has(route) ? "#/" + route : "#/dashboard";
}
