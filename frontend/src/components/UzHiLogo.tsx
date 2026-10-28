import { useState } from "react";

interface UzHiLogoProps {
  className?: string;
  onActivate?: () => void;
}

export function UzHiLogo({ className = "", onActivate }: UzHiLogoProps) {
  const [active, setActive] = useState(false);

  return (
    <button
      type="button"
      className={`uzhi-logo${active ? " active" : ""} ${className}`.trim()}
      aria-label="UzHi — Uzluksiz Himoya"
      aria-pressed={active}
      title="Nomni ochish yoki yig‘ish"
      onClick={() => {
        setActive((expanded) => !expanded);
        onActivate?.();
      }}
    >
      <svg className="uzhi-logo-mark" width="48" height="48" viewBox="0 0 100 100" fill="none" aria-hidden="true" focusable="false">
        <path d="M17 42 V21 L50 8 L83 21 V42" stroke="#a5f3fc" strokeWidth="6.5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M18 59 C20 75 33 86 50 93 C67 86 80 75 82 59" stroke="#ffffff" strokeWidth="6.5" strokeLinecap="round" />
        <line x1="41" y1="22" x2="41" y2="39" stroke="#00d2d3" strokeWidth="6.5" strokeLinecap="round" />
        <line x1="59" y1="22" x2="59" y2="39" stroke="#00d2d3" strokeWidth="6.5" strokeLinecap="round" />
        <line x1="41" y1="61" x2="41" y2="77" stroke="#00d2d3" strokeWidth="6.5" strokeLinecap="round" />
        <line x1="59" y1="61" x2="59" y2="77" stroke="#00d2d3" strokeWidth="6.5" strokeLinecap="round" />
        <path d="M50 50 C42 39 24 39 24 50 C24 61 42 61 50 50 C58 39 76 39 76 50 C76 61 58 61 50 50 Z" stroke="#00d2d3" strokeWidth="7" strokeLinecap="round" />
      </svg>
      <span className="uzhi-logo-copy" aria-hidden="true">
        <span className="uzhi-wordmark">
          <span className="uz-part">Uz</span><span className="uzhi-expand uzhi-expand-uz">luksiz</span><span className="hi-part">Hi</span><span className="uzhi-expand uzhi-expand-hi">moya</span>
        </span>
        <span className="uzhi-tagline">RISKGUARD | BIZNES UZLUKSIZLIGI LOYIHALASH</span>
      </span>
    </button>
  );
}
