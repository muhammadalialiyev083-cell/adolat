import { useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  BarChart3,
  Building2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  LockKeyhole,
  Moon,
  ShieldCheck,
  Sun,
  Workflow,
} from "lucide-react";
import { api, ApiError } from "../api/client";
import { UzHiLogo } from "./UzHiLogo";
import type { User } from "../types";

export function LoginForm({
  onLogin,
  initialUsername,
  notice,
  theme,
  toggleTheme,
  returnTo,
}: {
  onLogin: (user: User) => void;
  initialUsername: string;
  notice: string;
  theme: string;
  toggleTheme: () => void;
  returnTo: string;
}) {
  const [username, setUsername] = useState(initialUsername);
  const [password, setPassword] = useState("");
  const [visible, setVisible] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [organization, setOrganization] = useState("");
  const [provider, setProvider] = useState<string | null>(null);
  const [ssoNotice, setSSONotice] = useState("");
  const lock = useRef(false);
  const passwordInput = useRef<HTMLInputElement>(null);
  const reducedMotion = useReducedMotion();
  const motionProps = reducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: 16 },
        animate: { opacity: 1, y: 0 },
        transition: { duration: 0.35 },
      };
  const run = async (action: () => Promise<void>) => {
    if (lock.current) return;
    lock.current = true;
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (e) {
      if (e instanceof ApiError && e.status === 429)
        setError(
          "Kirish urinishlari chegarasiga yetildi. Bir daqiqadan keyin qayta urinib ko‘ring.",
        );
      else if (e instanceof ApiError && e.status >= 500)
        setError(
          "Kirish xizmati vaqtincha mavjud emas. Keyinroq qayta urinib ko‘ring.",
        );
      else setError(e instanceof Error ? e.message : "Kirish bajarilmadi.");
    } finally {
      setPassword("");
      setVisible(false);
      setBusy(false);
      lock.current = false;
    }
  };
  return (
    <main className="enterprise-login">
      <section className="login-visual" aria-label="UzHi — Uzluksiz Himoya">
        <UzHiLogo />
        <div className="login-brand-copy">
          <p className="login-eyebrow">UZHI — UZLUKSIZ HIMOYA</p>
          <h1>
            Biznes uzluksizligi — <span>ishonchli boshqaruv</span>
          </h1>
          <p className="login-subtitle">
            Risklar, BIA va tiklash rejalarini yagona xavfsiz platformada
            boshqaring.
          </p>
        </div>
        <motion.div
          className="login-illustration"
          aria-hidden="true"
          animate={reducedMotion ? undefined : { y: [0, -7, 0] }}
          transition={{ duration: 7, repeat: Infinity, ease: "easeInOut" }}
        >
          <div className="login-orbit orbit-one" />
          <div className="login-orbit orbit-two" />
          <svg viewBox="0 0 220 220" fill="none" focusable="false">
            <defs>
              <linearGradient
                id="login-shield-gradient"
                x1="40"
                y1="20"
                x2="180"
                y2="200"
              >
                <stop stopColor="#a5f3fc" />
                <stop offset="1" stopColor="#00d2d3" />
              </linearGradient>
            </defs>
            <path
              d="M110 22 181 48v59c0 43-29 69-71 91-42-22-71-48-71-91V48l71-26Z"
              fill="#0c344a"
              stroke="url(#login-shield-gradient)"
              strokeWidth="2"
            />
            <path
              d="M110 108c-21-32-58-30-58 0s37 32 58 0c21-32 58-30 58 0s-37 32-58 0Z"
              stroke="#00d2d3"
              strokeWidth="8"
              strokeLinecap="round"
            />
            <path
              d="M94 58v24m32-24v24M94 136v24m32-24v24"
              stroke="#a5f3fc"
              strokeWidth="5"
              strokeLinecap="round"
            />
          </svg>
          <div className="login-visual-tag">
            <span /> Dalil → tahlil → tiklash
          </div>
        </motion.div>
        <ul className="login-benefits">
          <li>
            <Workflow size={20} />
            <div>
              <strong>Yagona BCMS muhiti</strong>
              <span>Jarayonlar, aktivlar va uzluksizlik rejalari.</span>
            </div>
          </li>
          <li>
            <BarChart3 size={20} />
            <div>
              <strong>Dalillarga asoslangan tahlil</strong>
              <span>BIA, risklar va tiklash ustuvorliklari.</span>
            </div>
          </li>
          <li>
            <ShieldCheck size={20} />
            <div>
              <strong>Rollar asosida kirish</strong>
              <span>Tashkilot doirasidagi ruxsatlar va audit.</span>
            </div>
          </li>
        </ul>
        <p className="login-visual-footer">
          RiskGuard · Biznes uzluksizligini boshqarish
        </p>
      </section>
      <section className="login-auth" aria-labelledby="login-title">
        <button
          type="button"
          className="login-theme btn-ghost btn-icon"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Yorug‘ mavzu" : "Qorong‘i mavzu"}
        >
          {theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}
        </button>
        <motion.div className="login-card" {...motionProps}>
          <div className="login-mobile-brand">
            <UzHiLogo />
          </div>
          <div className="login-lock">
            <LockKeyhole size={23} />
          </div>
          <p className="login-eyebrow">RISKGUARD ENTERPRISE PILOT · v1.1</p>
          <h2 id="login-title">Xush kelibsiz!</h2>
          <p className="login-intro">
            Ish maydoningizga kirish uchun hisobingizdan foydalaning.
          </p>
          {notice && (
            <p className="login-notice" role="status">
              {notice}
            </p>
          )}
          <form
            noValidate
            onSubmit={(e) => {
              e.preventDefault();
              if (!username.trim() || !password) {
                setError("Foydalanuvchi nomi va parolni kiriting.");
                return;
              }
              void run(async () => {
                const response = await api.login({
                  username: username.trim(),
                  password,
                });
                setPassword("");
                onLogin(response.user);
              });
            }}
            aria-busy={busy}
          >
            <label htmlFor="login-username">Foydalanuvchi nomi</label>
            <input
              className="input-field"
              id="login-username"
              name="username"
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              autoFocus
              required
              disabled={busy}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              aria-describedby={error ? "login-error" : undefined}
            />
            <label htmlFor="login-password">Parol</label>
            <div className="input-wrapper">
              <input
                className="input-field"
                id="login-password"
                ref={passwordInput}
                name="password"
                type={visible ? "text" : "password"}
                autoComplete="current-password"
                required
                disabled={busy}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-describedby={error ? "login-error" : undefined}
              />
              <button
                className="password-toggle"
                type="button"
                disabled={busy}
                aria-controls="login-password"
                aria-pressed={visible}
                aria-label={
                  visible ? "Parolni yashirish" : "Parolni ko'rsatish"
                }
                onClick={() => {
                  setVisible(!visible);
                  passwordInput.current?.focus();
                }}
              >
                {visible ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
            <AnimatePresence>
              {error && (
                <motion.p
                  className="login-error"
                  id="login-error"
                  role="alert"
                  {...motionProps}
                >
                  {error}
                </motion.p>
              )}
            </AnimatePresence>
            <motion.button
              className="btn login-submit"
              type="submit"
              disabled={busy}
              whileHover={reducedMotion ? undefined : { scale: 1.01 }}
              whileTap={reducedMotion ? undefined : { scale: 0.99 }}
            >
              {busy ? (
                <>
                  <LoaderCircle className="login-spinner" size={18} />{" "}
                  Kirilmoqda…
                </>
              ) : (
                <>
                  Tizimga kirish <ArrowRight size={18} />
                </>
              )}
            </motion.button>
          </form>
          <details className="login-sso">
            <summary>
              <Building2 size={16} /> Tashkilot orqali kirish
            </summary>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void run(async () => {
                  const result = await api.discoverSSO(organization.trim());
                  setProvider(result.enabled ? result.provider : null);
                  setSSONotice(
                    result.enabled
                      ? "Tashkilot provayderi sozlangan."
                      : "Ushbu kod uchun korporativ kirish yoqilmagan. Tashkilot administratoriga murojaat qiling.",
                  );
                });
              }}
            >
              <label htmlFor="login-organization">Tashkilot kodi</label>
              <input
                className="input-field"
                id="login-organization"
                autoComplete="organization"
                maxLength={80}
                required
                value={organization}
                onChange={(e) => {
                  setOrganization(e.target.value);
                  setProvider(null);
                  setSSONotice("");
                }}
                disabled={busy}
              />
              <button
                className="btn btn-secondary"
                disabled={busy || !organization.trim()}
              >
                Kirish usulini tekshirish
              </button>
            </form>
            {ssoNotice && <p role="status">{ssoNotice}</p>}
            {provider && (
              <button
                className="btn btn-secondary login-sso-button"
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    const result = await api.beginSSO(provider, "/" + returnTo);
                    window.location.assign(result.authorization_url);
                  })
                }
              >
                <KeyRound size={17} /> Korporativ hisob orqali kirish
              </button>
            )}
          </details>
          <p className="login-help">
            Hisob yoki kirish muammosi bo‘lsa, tashkilot administratoriga
            murojaat qiling.
          </p>
          <footer className="login-card-footer">
            <span>UzHi — Uzluksiz Himoya</span>
            <span>Enterprise Pilot v1.1</span>
          </footer>
        </motion.div>
      </section>
    </main>
  );
}
