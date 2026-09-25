"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

// Casca do app: barra lateral e area principal, identicas a design/v2/*.dc.html.

type Item = { href: string; label: string; icon: React.ReactNode };

const svgProps = {
  width: 18,
  height: 18,
  viewBox: "0 0 24 24",
  "aria-hidden": true,
  style: {
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 1.7,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  },
};

const PREGAO: Item[] = [
  { href: "/", label: "Visão Geral", icon: <svg {...svgProps}><path d="M4 20V11M10 20V5M16 20v-6M21 20H3" /></svg> },
  { href: "/pre-sessao", label: "Pré-Sessão", icon: <svg {...svgProps}><path d="M12 3v3M5 9l2 2M19 9l-2 2M3 18h18M7 18a5 5 0 0 1 10 0" /></svg> },
  { href: "/checklist", label: "Checklist", icon: <svg {...svgProps}><path d="M12 3l8 3v6c0 4.5-3.4 8-8 9-4.6-1-8-4.5-8-9V6z" /><path d="M8.5 12l2.5 2.5 4.5-5" /></svg> },
];

const REGISTRO: Item[] = [
  { href: "/trades", label: "Histórico", icon: <svg {...svgProps}><path d="M3 12a9 9 0 1 0 3-6.7" /><path d="M3 4v4h4" /><path d="M12 7v5l3 2" /></svg> },
  { href: "/estrategias", label: "Estratégias", icon: <svg {...svgProps}><path d="M12 3l9 5-9 5-9-5z" /><path d="M3 13l9 5 9-5" /></svg> },
];

const grupoTitulo: React.CSSProperties = {
  padding: "0 12px 6px",
  fontSize: "11px",
  fontWeight: 500,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "var(--tx3)",
};

function NavLink({ item, ativo }: { item: Item; ativo: boolean }) {
  return (
    <Link
      href={item.href}
      aria-current={ativo ? "page" : undefined}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "12px",
        height: "44px",
        padding: "0 12px",
        borderRadius: "10px",
        fontSize: "14px",
        fontWeight: ativo ? 500 : 400,
        textDecoration: "none",
        background: ativo ? "var(--acs)" : "transparent",
        color: ativo ? "var(--actx)" : "var(--tx2)",
      }}
    >
      {item.icon}
      {item.label}
    </Link>
  );
}

function iniciais(nome: string) {
  const partes = nome.trim().split(/\s+/);
  return ((partes[0]?.[0] ?? "") + (partes[1]?.[0] ?? partes[0]?.[1] ?? "")).toUpperCase();
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [escuro, setEscuro] = React.useState(true);
  const [nome, setNome] = React.useState("Anderson");

  React.useEffect(() => {
    const salvo = localStorage.getItem("cognitive-theme");
    const isDark = salvo ? salvo === "dark" : true;
    setEscuro(isDark);
    document.documentElement.classList.toggle("dark", isDark);
    supabase.auth.getUser().then(({ data }) => {
      const meta = data.user?.user_metadata as { name?: string; full_name?: string } | undefined;
      const n = meta?.name || meta?.full_name;
      if (n) setNome(n.split(" ")[0]);
    });
  }, []);

  function alternarTema() {
    const proximo = !escuro;
    setEscuro(proximo);
    document.documentElement.classList.toggle("dark", proximo);
    localStorage.setItem("cognitive-theme", proximo ? "dark" : "light");
  }

  async function sair() {
    await supabase.auth.signOut();
    router.replace("/login");
  }

  if (pathname === "/login") return <>{children}</>;

  const ativo = (href: string) => (href === "/" ? pathname === "/" : pathname.startsWith(href));

  const botaoIcone: React.CSSProperties = {
    width: "36px",
    height: "36px",
    borderRadius: "10px",
    border: "1px solid var(--bd)",
    background: "transparent",
    color: "var(--tx2)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg)", color: "var(--tx)", fontVariantNumeric: "tabular-nums" }}>
      <nav
        aria-label="Principal"
        style={{
          width: "232px",
          flexShrink: 0,
          boxSizing: "border-box",
          padding: "28px 16px 24px",
          borderRight: "1px solid var(--bd)",
          display: "flex",
          flexDirection: "column",
          gap: "32px",
          position: "sticky",
          top: 0,
          height: "100vh",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "0 8px" }}>
          <svg width="30" height="30" viewBox="0 0 30 30" aria-hidden="true">
            <rect x="0.5" y="0.5" width="29" height="29" rx="8" style={{ fill: "var(--acs)", stroke: "var(--ac)", strokeOpacity: 0.45 }} />
            <path d="M6 17h4l3-7 4 12 3-7h4" style={{ fill: "none", stroke: "var(--ac)", strokeWidth: 1.8, strokeLinecap: "round", strokeLinejoin: "round" }} />
          </svg>
          <span style={{ fontSize: "15px", fontWeight: 600, letterSpacing: "-0.01em" }}>Cognitive Trading</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <span style={grupoTitulo}>Pregão</span>
          {PREGAO.map((i) => <NavLink key={i.href} item={i} ativo={ativo(i.href)} />)}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <span style={grupoTitulo}>Registro</span>
          {REGISTRO.map((i) => <NavLink key={i.href} item={i} ativo={ativo(i.href)} />)}
        </div>

        <div style={{ marginTop: "auto", display: "flex", flexDirection: "column", gap: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "0 8px" }}>
            <span style={{ width: "32px", height: "32px", borderRadius: "50%", background: "var(--acs)", color: "var(--actx)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 600, flexShrink: 0 }}>
              {iniciais(nome)}
            </span>
            <span style={{ fontSize: "13px", color: "var(--tx2)", flexGrow: 1 }}>{nome}</span>
            <button type="button" onClick={alternarTema} aria-label={escuro ? "Usar tema claro" : "Usar tema escuro"} title={escuro ? "Tema claro" : "Tema escuro"} style={botaoIcone}>
              {escuro ? (
                <svg {...svgProps} width={16} height={16}><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" /></svg>
              ) : (
                <svg {...svgProps} width={16} height={16}><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
              )}
            </button>
            <button type="button" onClick={sair} aria-label="Sair" title="Sair" style={botaoIcone}>
              <svg {...svgProps} width={16} height={16}><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><path d="M16 17l5-5-5-5" /><path d="M21 12H9" /></svg>
            </button>
          </div>
        </div>
      </nav>

      <main
        style={{
          flexGrow: 1,
          minWidth: 0,
          boxSizing: "border-box",
          padding: "32px 40px 40px",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
        }}
      >
        {children}
      </main>
    </div>
  );
}
