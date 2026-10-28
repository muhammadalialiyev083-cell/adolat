import { RiskMatrix, BIARanking } from "./components/Analysis";
import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowLeft,
  ChevronDown,
  Menu,
  PanelLeftClose,
  PanelLeftOpen,
  Search,
  BarChart3,
  BookOpen,
  Building,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  Cpu,
  Database,
  FileText,
  GitBranch,
  Layers,
  FolderOpen,
  ListTree,
  ClipboardCheck,
  LogOut,
  Moon,
  PlayCircle,
  RefreshCw,
  Settings,
  Shield,
  Sun,
  Target,
  Users,
  X,
} from "lucide-react";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api/client";
import { Dashboard } from "./components/Dashboard";
import { UzHiLogo } from "./components/UzHiLogo";
import { ImportWizard } from "./components/ImportWizard";
import { LoginForm } from "./components/LoginForm";
import { Management, IncidentWorkspace } from "./components/Operations";
import { Integrations } from "./components/Integrations";
import { safeHash } from "./api/navigation";
import { BIAQuestionnaire } from "./components/BIAQuestionnaire";
import {
  InitialSetupWizard,
  ModuleCatalog,
  ModuleMenu,
} from "./components/NavigationHub";
import {
  CONFIGS,
  GraphPanel,
  PasswordPanel,
  ResourcePanel,
  SchedulerPanel,
  Wizard,
} from "./components/Workspace";
import type { DashboardSummary } from "./types";

/* ────────────────────────────────────────────────
   THEME HOOK
──────────────────────────────────────────────── */
function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">(() => {
    return (localStorage.getItem("bcms-theme") as "dark" | "light") || "light";
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("bcms-theme", theme);
  }, [theme]);

  const toggle = useCallback(
    () => setTheme((t) => (t === "dark" ? "light" : "dark")),
    [],
  );
  return { theme, toggle };
}

/* ────────────────────────────────────────────────
   TOAST SYSTEM
──────────────────────────────────────────────── */
interface Toast {
  id: number;
  type: "success" | "error";
  message: string;
}

function ToastContainer({
  toasts,
  onDismiss,
}: {
  toasts: Toast[];
  onDismiss: (id: number) => void;
}) {
  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          {t.type === "success" ? (
            <Check
              size={16}
              style={{ flexShrink: 0, color: "var(--color-low)" }}
            />
          ) : (
            <AlertTriangle
              size={16}
              style={{ flexShrink: 0, color: "var(--color-critical)" }}
            />
          )}
          <span style={{ flex: 1, fontSize: 13 }}>{t.message}</span>
          <button
            className="btn-ghost btn-icon"
            style={{ padding: 2 }}
            onClick={() => onDismiss(t.id)}
          >
            <X size={13} />
          </button>
        </div>
      ))}
    </div>
  );
}

/* ────────────────────────────────────────────────
   BADGE HELPER
──────────────────────────────────────────────── */
type TabKey = string;
const NAV_ITEMS: {
  key: TabKey;
  label: string;
  icon: React.ElementType;
  frCode: string;
}[] = [
  { key: "dashboard", label: "Boshqaruv paneli", icon: BarChart3, frCode: "" },
  { key: "imports", label: "Excel / CSV import", icon: Database, frCode: "" },
  {
    key: "management",
    label: "Rahbariyat va vazifalar",
    icon: ClipboardCheck,
    frCode: "",
  },
  {
    key: "incidents",
    label: "Hodisalarni boshqarish",
    icon: AlertTriangle,
    frCode: "",
  },
  {
    key: "integrations",
    label: "Monitoring integratsiyalari",
    icon: Cpu,
    frCode: "",
  },
  {
    key: "initial-setup",
    label: "Boshlang‘ich sozlash (1–4)",
    icon: ClipboardCheck,
    frCode: "",
  },
  { key: "menu", label: "Interaktiv menyu", icon: ListTree, frCode: "" },
  { key: "catalog", label: "Modullar katalogi", icon: FolderOpen, frCode: "" },
  { key: "wizard", label: "BCMS loyihalash ustasi", icon: Target, frCode: "" },
  {
    key: "organizations",
    label: "Tashkilot profili",
    icon: Building,
    frCode: "",
  },
  { key: "departments", label: "Bo‘limlar", icon: Building, frCode: "" },
  { key: "users", label: "Xodimlar va rollar", icon: Users, frCode: "" },
  { key: "services", label: "Xizmatlar", icon: Layers, frCode: "" },
  { key: "processes", label: "Biznes jarayonlari", icon: Layers, frCode: "" },
  { key: "assets", label: "Aktivlar", icon: Database, frCode: "" },
  {
    key: "dependencies",
    label: "Bog‘liqlik xaritasi",
    icon: GitBranch,
    frCode: "",
  },
  { key: "bia", label: "Biznesga ta’sir (BIA)", icon: Clock, frCode: "" },
  {
    key: "bia-questionnaire",
    label: "Dalilli BIA so‘rovnomasi",
    icon: ClipboardCheck,
    frCode: "",
  },
  { key: "risks", label: "Risklar reyestri", icon: AlertTriangle, frCode: "" },
  { key: "controls", label: "Nazorat choralari", icon: Shield, frCode: "" },
  {
    key: "strategies",
    label: "Tiklash strategiyalari",
    icon: Target,
    frCode: "",
  },
  { key: "resources", label: "Tiklash resurslari", icon: Users, frCode: "" },
  { key: "schedule", label: "Tiklash jadvali", icon: Cpu, frCode: "" },
  { key: "plans", label: "Uzluksizlik rejalari", icon: FileText, frCode: "" },
  {
    key: "scenarios",
    label: "Uzilish ssenariylari",
    icon: PlayCircle,
    frCode: "",
  },
  {
    key: "simulation-runs",
    label: "Simulyatsiya natijalari",
    icon: PlayCircle,
    frCode: "",
  },
  { key: "exercises", label: "Mashqlar", icon: CheckCircle2, frCode: "" },
  { key: "audit-logs", label: "Audit jurnali", icon: BookOpen, frCode: "" },
  {
    key: "password",
    label: "Parolni almashtirish",
    icon: Settings,
    frCode: "",
  },
];

const MENU_GROUPS = [
  {
    key: "organization",
    label: "Tashkilot boshqaruvi",
    icon: Building,
    items: [
      "organizations",
      "departments",
      "users",
      "services",
      "processes",
      "assets",
      "imports",
    ],
  },
  {
    key: "analysis",
    label: "Risk va BIA tahlili",
    icon: AlertTriangle,
    items: ["dependencies", "bia", "bia-questionnaire", "risks", "controls"],
  },
  {
    key: "recovery",
    label: "Tiklash va uzluksizlik",
    icon: RefreshCw,
    items: [
      "strategies",
      "resources",
      "schedule",
      "plans",
      "scenarios",
      "simulation-runs",
    ],
  },
  {
    key: "monitoring",
    label: "Monitoring va audit",
    icon: Shield,
    items: [
      "management",
      "incidents",
      "integrations",
      "exercises",
      "audit-logs",
      "password",
    ],
  },
] as const;

function Sidebar({
  activeTab,
  setActiveTab,
  dashboard,
  collapsed,
  onToggleCollapse,
  mobileOpen,
  onMobileClose,
}: {
  activeTab: TabKey;
  setActiveTab: (t: TabKey) => void;
  dashboard: DashboardSummary | null;
  collapsed: boolean;
  onToggleCollapse: () => void;
  mobileOpen: boolean;
  onMobileClose: () => void;
}) {
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedGroups, setExpandedGroups] = useState<string[]>(() => {
    const group = MENU_GROUPS.find((g) =>
      g.items.some((key) => key === location.hash.slice(2).split("?")[0]),
    );
    return group ? [group.key] : ["organization"];
  });
  useEffect(() => {
    const group = MENU_GROUPS.find((g) =>
      g.items.some((key) => key === activeTab),
    );
    if (group)
      setExpandedGroups((prev) =>
        prev.includes(group.key) ? prev : [...prev, group.key],
      );
  }, [activeTab]);
  const search = searchTerm.toLocaleLowerCase("uz").trim();
  const matches = (item: (typeof NAV_ITEMS)[number]) =>
    item.label.toLocaleLowerCase("uz").includes(search);
  const navigateTo = (key: string) => {
    setActiveTab(key);
    onMobileClose();
  };
  const quickKeys = ["dashboard", "initial-setup", "menu", "catalog", "wizard"];
  const quickItems = NAV_ITEMS.filter(
    (item) => quickKeys.includes(item.key) && (!search || matches(item)),
  );
  const toggleGroup = (key: string) => {
    if (collapsed) {
      onToggleCollapse();
      setExpandedGroups((prev) => (prev.includes(key) ? prev : [...prev, key]));
      return;
    }
    setExpandedGroups((prev) =>
      prev.includes(key) ? prev.filter((x) => x !== key) : [...prev, key],
    );
  };
  const navButton = (item: (typeof NAV_ITEMS)[number], isChild = false) => {
    const Icon = item.icon;
    const alert =
      item.key === "risks"
        ? dashboard?.high_risks_count
        : item.key === "bia"
          ? dashboard?.rpo_gap_count
          : 0;
    return (
      <button
        key={item.key}
        type="button"
        title={collapsed ? item.label : undefined}
        aria-current={activeTab === item.key ? "page" : undefined}
        onClick={() => navigateTo(item.key)}
        className={`nav-item spark-nav-link${activeTab === item.key ? " active" : ""}${isChild ? " nested" : ""}`}
      >
        <Icon size={18} className="nav-icon" aria-hidden="true" />
        <span className="spark-nav-label">{item.label}</span>
        {!!alert && !collapsed && <span className="nav-badge">{alert}</span>}
      </button>
    );
  };
  return (
    <motion.aside
      initial={false}
      className={`app-sidebar spark-sidebar${mobileOpen ? " mobile-open" : ""}`}
      aria-label="Asosiy navigatsiya"
    >
      <div className="spark-sidebar-brand">
        <UzHiLogo
          className="uzhi-logo-sidebar"
          onActivate={collapsed && !mobileOpen ? onToggleCollapse : undefined}
        />
        <button
          type="button"
          className="spark-sidebar-collapse"
          aria-label={collapsed ? "Menyuni kengaytirish" : "Menyuni yig‘ish"}
          title={collapsed ? "Menyuni kengaytirish" : "Menyuni yig‘ish"}
          onClick={onToggleCollapse}
        >
          {collapsed ? (
            <PanelLeftOpen size={17} />
          ) : (
            <PanelLeftClose size={17} />
          )}
        </button>
      </div>
      <div className="spark-nav-search">
        <Search size={16} aria-hidden="true" />
        <input
          aria-label="Menyudan modul qidirish"
          placeholder="Modulni qidirish…"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      <nav className="spark-nav-sections">
        <div className="nav-section-label">Ish maydoni</div>
        {quickItems.map((item) => navButton(item))}
        {MENU_GROUPS.map((group) => {
          const matching = NAV_ITEMS.filter(
            (item) =>
              group.items.some((key) => key === item.key) &&
              (!search || matches(item)),
          );
          if (!matching.length) return null;
          const Icon = group.icon;
          const isExpanded =
            expandedGroups.includes(group.key) || Boolean(search);
          return (
            <div key={group.key} className="spark-nav-group">
              <button
                type="button"
                className={`spark-group-toggle${matching.some((i) => i.key === activeTab) ? " group-active" : ""}`}
                aria-expanded={isExpanded}
                title={collapsed ? group.label : undefined}
                onClick={() => toggleGroup(group.key)}
              >
                <Icon size={18} aria-hidden="true" />
                <span className="spark-nav-label">{group.label}</span>
                <ChevronDown
                  className={`spark-group-chevron${isExpanded ? " is-expanded" : ""}`}
                  size={15}
                  aria-hidden="true"
                />
              </button>
              {isExpanded && !collapsed && (
                <div className="spark-nested-list">
                  {matching.map((item) => navButton(item, true))}
                </div>
              )}
            </div>
          );
        })}
        {search &&
          !quickItems.length &&
          !MENU_GROUPS.some((group) =>
            NAV_ITEMS.some(
              (item) =>
                group.items.some((key) => key === item.key) && matches(item),
            ),
          ) && <p className="spark-search-empty">Modul topilmadi</p>}
      </nav>
      <div className="spark-sidebar-bottom">
        <Shield size={16} />
        <span>
          ISO 22301 metodologiyasi
          <br />
          <small>Sertifikat da’vosi emas</small>
        </span>
      </div>
    </motion.aside>
  );
}

/* ────────────────────────────────────────────────
   HEADER
──────────────────────────────────────────────── */
function Header({
  currentUser,
  onLogout,
  onRefresh,
  loading,
  theme,
  onThemeToggle,
  onMenuToggle,
}: {
  currentUser: any;
  onLogout: () => void;
  onRefresh: () => void;
  loading: boolean;
  theme: string;
  onThemeToggle: () => void;
  onMenuToggle: () => void;
}) {
  return (
    <header className="app-header">
      <button
        type="button"
        className="spark-menu-trigger"
        onClick={onMenuToggle}
        aria-label="Navigatsiya menyusini ochish yoki yopish"
      >
        <Menu size={20} />
      </button>
      {/* Organization badge */}
      <div
        className="header-organization"
        style={{ display: "flex", alignItems: "center", gap: 10, flex: 1 }}
      >
        <div
          className="brand-logo"
          style={{ width: 32, height: 32, flexShrink: 0, display: "none" }}
        >
          <Shield size={16} color="white" />
        </div>

        {/* Org Badge */}
        {currentUser?.organization_detail && (
          <div
            className="organization-badge"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              background: "var(--color-bg-card)",
              border: "1px solid var(--color-border)",
              borderRadius: 8,
              padding: "5px 12px",
              fontSize: 12,
              color: "var(--color-text-secondary)",
            }}
          >
            <Building
              size={13}
              style={{ color: "var(--color-brand-primary)", flexShrink: 0 }}
            />
            <span
              style={{
                fontWeight: 600,
                color: "var(--color-text-primary)",
                maxWidth: 240,
              }}
              className="truncate"
            >
              {currentUser.organization_detail.name}
            </span>
            <ChevronRight size={11} />
            <span>{currentUser.organization_detail.sector}</span>
          </div>
        )}
      </div>

      {/* Right controls */}
      <div
        className="header-controls"
        style={{ display: "flex", alignItems: "center", gap: 8 }}
      >
        <span className="session-user">
          {currentUser?.first_name || currentUser?.username}
        </span>

        {currentUser && (
          <div
            style={{
              background: "var(--color-accent-primary-light)",
              border: "1px solid rgba(59,130,246,0.25)",
              borderRadius: 8,
              padding: "5px 10px",
              fontSize: 11,
              fontWeight: 700,
              color: "#60A5FA",
              letterSpacing: "0.04em",
            }}
          >
            {currentUser.role}
          </div>
        )}

        {/* Refresh */}
        <button
          className="theme-toggle"
          onClick={onRefresh}
          title="Ma'lumotlarni yangilash"
          disabled={loading}
        >
          <RefreshCw
            size={15}
            className={loading ? "animate-spin" : ""}
            style={{
              color: loading ? "var(--color-brand-primary)" : undefined,
            }}
          />
        </button>

        {/* Theme Toggle */}
        <button
          className="theme-toggle"
          onClick={onThemeToggle}
          title="Tema o'zgartirish"
        >
          {theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
        </button>
        <button
          className="theme-toggle"
          onClick={onLogout}
          disabled={loading}
          title="Tizimdan chiqish"
          aria-label="Tizimdan chiqish"
        >
          <LogOut size={15} />
        </button>
      </div>
    </header>
  );
}

/* ────────────────────────────────────────────────
   DASHBOARD TAB
──────────────────────────────────────────────── */
const PAGE_META = Object.fromEntries(
  NAV_ITEMS.map((item) => [
    item.key,
    {
      title: item.label,
      desc: "Tashkilotingiz ma’lumotlari asosida biznes uzluksizligini loyihalash.",
      icon: item.icon,
    },
  ]),
);

/* ────────────────────────────────────────────────
   MAIN APP
──────────────────────────────────────────────── */
export function App() {
  const { theme, toggle: toggleTheme } = useTheme();

  const [currentUser, setCurrentUser] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<TabKey>(
    () => location.hash.slice(2).split("?")[0] || "dashboard",
  );
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const pageTrail = useRef<string[]>([]);
  const returnTo = useRef(safeHash(location.hash));
  const toggleSidebar = useCallback(() => {
    if (window.matchMedia("(max-width: 768px)").matches)
      setMobileNavOpen((open) => !open);
    else setSidebarCollapsed((closed) => !closed);
  }, []);
  const [loading, setLoading] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toastIdRef = useRef(0);
  const dataRequestIdRef = useRef(0);

  // Data
  const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);

  // Login state
  const [loginLoading, setLoginLoading] = useState(true);
  const [loginUsername, setLoginUsername] = useState("");
  const [loginNotice, setLoginNotice] = useState(() =>
    new URLSearchParams(location.search).get("auth_error") === "sso_failed"
      ? "Korporativ kirish bajarilmadi. Qayta urinib ko‘ring yoki tashkilot administratoriga murojaat qiling."
      : "",
  );

  const clearUserData = useCallback(() => {
    // Ignore pending responses belonging to the previous session.
    dataRequestIdRef.current += 1;
    setDashboard(null);
    pageTrail.current = [];
    setMobileNavOpen(false);
    setActiveTab("dashboard");
    location.hash = "/dashboard";
    setToasts([]);
  }, []);

  const handleLogin = useCallback(
    (user: any) => {
      clearUserData();
      const destination = returnTo.current;
      location.hash = destination;
      setActiveTab(destination.slice(2));
      setCurrentUser(user);
      setLoginNotice("");
      setLoginLoading(false);
    },
    [clearUserData],
  );

  useEffect(() => {
    const expired = () => {
      returnTo.current = safeHash(location.hash);
      clearUserData();
      setCurrentUser(null);
      setLoginNotice("Sessiya tugagan. Iltimos, qayta kiring.");
    };
    window.addEventListener("bcms:session-expired", expired);
    return () => window.removeEventListener("bcms:session-expired", expired);
  }, [clearUserData]);

  /* Toast helper */
  const showToast = useCallback(
    (message: string, type: "success" | "error" = "success") => {
      const id = ++toastIdRef.current;
      setToasts((prev) => [...prev, { id, type, message }]);
      setTimeout(
        () => setToasts((prev) => prev.filter((t) => t.id !== id)),
        4500,
      );
    },
    [],
  );

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  /* Auth init */
  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const user = await api.getMe();
        if (active) setCurrentUser(user);
      } catch (err) {
        if (
          active &&
          !(err instanceof ApiError && [401, 403].includes(err.status))
        ) {
          setLoginNotice(
            err instanceof Error
              ? err.message
              : "Sessiyani tekshirib bo‘lmadi. Qayta urinib ko‘ring.",
          );
        }
      } finally {
        if (active) setLoginLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  /* Load data */
  const loadData = useCallback(async () => {
    if (!currentUser) return;
    const requestId = ++dataRequestIdRef.current;
    setLoading(true);
    try {
      const dRes = await api.getDashboard();
      if (requestId !== dataRequestIdRef.current) return;
      setDashboard(dRes.summary);
    } catch (err) {
      if (requestId !== dataRequestIdRef.current) return;
      if (err instanceof ApiError && [401, 403].includes(err.status)) {
        const signedOut = await api.getMe().then(
          () => false,
          (error) =>
            error instanceof ApiError && [401, 403].includes(error.status),
        );
        if (requestId !== dataRequestIdRef.current) return;
        if (signedOut) {
          clearUserData();
          setCurrentUser(null);
          setLoginNotice("Sessiya tugagan. Iltimos, tizimga qayta kiring.");
          setLoading(false);
          return;
        }
      }
      showToast(
        err instanceof Error
          ? err.message
          : "Ma'lumotlarni yuklashda xatolik yuz berdi.",
        "error",
      );
    } finally {
      if (requestId === dataRequestIdRef.current) setLoading(false);
    }
  }, [currentUser, showToast, clearUserData]);

  useEffect(() => {
    if (currentUser) loadData();
  }, [currentUser, loadData]);

  /* Actions */
  const handleSwitchUser = async (username = "") => {
    setLoading(true);
    returnTo.current = "#/dashboard";
    try {
      try {
        await api.logout();
      } catch (err) {
        const signedOut =
          err instanceof ApiError &&
          [401, 403].includes(err.status) &&
          (await api.getMe().then(
            () => false,
            (error) =>
              error instanceof ApiError && [401, 403].includes(error.status),
          ));
        if (!signedOut) throw err;
      }
      clearUserData();
      setLoginUsername(username);
      setLoginNotice(
        username
          ? `Hisobni almashtirish uchun "${username}" parolini kiriting.`
          : "Tizimdan muvaffaqiyatli chiqdingiz.",
      );
      setCurrentUser(null);
    } catch (err) {
      showToast(
        err instanceof Error
          ? err.message
          : "Tizimdan chiqib bo‘lmadi. Qayta urinib ko‘ring.",
        "error",
      );
    } finally {
      setLoading(false);
    }
  };

  /* Page meta */
  const meta = PAGE_META[activeTab] || PAGE_META.dashboard;
  const [workspaceRevision, setWorkspaceRevision] = useState(0);
  const changed = useCallback(() => {
    setWorkspaceRevision((value) => value + 1);
    void loadData();
  }, [loadData]);
  const navigate = useCallback((key: string, query = "") => {
    const current = location.hash.slice(2).split("?")[0] || "dashboard";
    if (current !== key) pageTrail.current.push(current);
    location.hash = "/" + key + (query ? "?" + query : "");
    setActiveTab(key);
    setMobileNavOpen(false);
    setWorkspaceRevision((value) => value + 1);
  }, []);
  const goBack = useCallback(() => {
    const destination = pageTrail.current.pop() || "dashboard";
    location.hash = "/" + destination;
    setActiveTab(destination);
    setMobileNavOpen(false);
    setWorkspaceRevision((value) => value + 1);
  }, []);
  useEffect(() => {
    const listener = () => {
      const key = location.hash.slice(2).split("?")[0] || "dashboard";
      setActiveTab(
        NAV_ITEMS.some((item) => item.key === key) ? key : "dashboard",
      );
      setWorkspaceRevision((value) => value + 1);
    };
    window.addEventListener("hashchange", listener);
    return () => window.removeEventListener("hashchange", listener);
  }, []);

  if (loginLoading) {
    return (
      <div
        className="app-shell"
        role="status"
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          minHeight: "100vh",
        }}
      >
        Sessiya tekshirilmoqda...
      </div>
    );
  }

  if (!currentUser) {
    return (
      <LoginForm
        onLogin={handleLogin}
        initialUsername={loginUsername}
        notice={loginNotice}
        theme={theme}
        toggleTheme={toggleTheme}
        returnTo={returnTo.current}
      />
    );
  }

  return (
    <div
      className={`app-shell${sidebarCollapsed ? " sidebar-collapsed" : ""}${mobileNavOpen ? " mobile-nav-open" : ""}`}
    >
      <a className="skip-link" href="#main-content">
        Asosiy mazmunga o‘tish
      </a>
      {/* Toast Notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      {/* Header */}
      <Header
        currentUser={currentUser}
        onLogout={() => handleSwitchUser()}
        onRefresh={() => {
          void loadData();
          changed();
        }}
        loading={loading}
        theme={theme}
        onThemeToggle={toggleTheme}
        onMenuToggle={toggleSidebar}
      />

      {/* Sidebar */}
      {mobileNavOpen && (
        <button
          type="button"
          className="spark-mobile-backdrop"
          aria-label="Menyuni yopish"
          onClick={() => setMobileNavOpen(false)}
        />
      )}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={navigate}
        dashboard={dashboard}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed((closed) => !closed)}
        mobileOpen={mobileNavOpen}
        onMobileClose={() => setMobileNavOpen(false)}
      />

      {/* Main Content */}
      <main className="app-main" id="main-content">
        <div className="page-content">
          {/* Loading bar */}
          {loading && (
            <div
              style={{
                position: "fixed",
                top: 60,
                left: 0,
                right: 0,
                height: 2,
                zIndex: 80,
                background: "linear-gradient(90deg, #2563EB, #0EA5E9, #2563EB)",
                backgroundSize: "200% 100%",
                animation: "loadingBar 1.2s linear infinite",
              }}
            />
          )}

          {/* Context navigation */}
          <div className="spark-breadcrumb-row">
            <button
              type="button"
              className="spark-back-button"
              onClick={goBack}
              disabled={activeTab === "dashboard"}
              aria-label="Oldingi sahifaga qaytish"
            >
              <ArrowLeft size={17} /> Orqaga
            </button>
            <nav aria-label="Sahifa yo‘li" className="spark-breadcrumb">
              <button type="button" onClick={() => navigate("dashboard")}>
                Boshqaruv paneli
              </button>
              {activeTab !== "dashboard" && (
                <>
                  <ChevronRight size={14} aria-hidden="true" />
                  {MENU_GROUPS.some((group) =>
                    group.items.some((item) => item === activeTab),
                  ) && (
                    <>
                      <button type="button" onClick={() => navigate("menu")}>
                        {
                          MENU_GROUPS.find((group) =>
                            group.items.some((item) => item === activeTab),
                          )?.label
                        }
                      </button>
                      <ChevronRight size={14} aria-hidden="true" />
                    </>
                  )}
                  <span aria-current="page">{meta.title}</span>
                </>
              )}
            </nav>
          </div>

          {/* Page Header */}
          <div
            className="page-header"
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
            }}
          >
            <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 10,
                  background: "var(--color-brand-primary-light)",
                  border: "1px solid rgba(8,127,134,0.25)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                  marginTop: 2,
                }}
              >
                <meta.icon size={20} style={{ color: "#087f86" }} />
              </div>
              <div>
                <h1 className="page-title">{meta.title}</h1>
                <p className="page-desc">{meta.desc}</p>
              </div>
            </div>
          </div>

          {/* Tab Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25, ease: "circOut" }}
              className="page-tab"
            >
              {activeTab === "dashboard" && (
                <Dashboard onNavigate={navigate} revision={workspaceRevision} />
              )}
              {activeTab === "initial-setup" && (
                <InitialSetupWizard
                  onNavigate={navigate}
                  revision={workspaceRevision}
                />
              )}
              {activeTab === "menu" && <ModuleMenu onNavigate={navigate} />}
              {activeTab === "catalog" && (
                <ModuleCatalog onNavigate={navigate} />
              )}
              {activeTab === "wizard" && (
                <Wizard onNavigate={navigate} revision={workspaceRevision} />
              )}
              {activeTab === "dependencies" && <GraphPanel />}
              {activeTab === "imports" && <ImportWizard user={currentUser} />}
              {activeTab === "management" && (
                <Management
                  user={currentUser}
                  onNavigate={navigate}
                  onChanged={changed}
                />
              )}
              {activeTab === "incidents" && (
                <IncidentWorkspace user={currentUser} onChanged={changed} />
              )}
              {activeTab === "integrations" && (
                <Integrations user={currentUser} onNavigate={navigate} />
              )}
              {activeTab === "bia-questionnaire" && (
                <BIAQuestionnaire user={currentUser} />
              )}
              {activeTab === "risks" && <RiskMatrix onNavigate={navigate} />}
              {activeTab === "bia" && <BIARanking />}
              {CONFIGS[activeTab] && activeTab !== "incidents" && (
                <ResourcePanel
                  key={
                    workspaceRevision + activeTab + location.hash.split("?")[1]
                  }
                  resource={activeTab}
                  user={currentUser}
                  onChanged={changed}
                />
              )}
              {activeTab === "schedule" && (
                <SchedulerPanel user={currentUser} onChanged={changed} />
              )}
              {activeTab === "password" && <PasswordPanel />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
