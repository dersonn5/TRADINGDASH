import type { CSSProperties } from "react";

// Estilos repetidos nos artboards de design/v2/*.dc.html.

export const CARD: CSSProperties = {
  padding: "24px",
  borderRadius: "16px",
  background: "var(--s1)",
  border: "1px solid var(--bd)",
  display: "flex",
  flexDirection: "column",
  gap: "16px",
};

export const LBL: CSSProperties = {
  fontSize: "12px",
  fontWeight: 500,
  letterSpacing: "0.06em",
  textTransform: "uppercase",
  color: "var(--tx3)",
};

export const H2: CSSProperties = { fontSize: "16px", fontWeight: 600 };

export const PILL_PEQUENA: CSSProperties = {
  flexShrink: 0,
  fontSize: "11px",
  padding: "4px 10px",
  borderRadius: "999px",
  background: "var(--s2)",
  border: "1px solid var(--bd)",
  color: "var(--tx3)",
};

// Grupo de botoes segmentado (Compra / Venda, Tendencia / Range...)
export const SEGMENTADO: CSSProperties = {
  display: "flex",
  gap: "4px",
  padding: "4px",
  background: "var(--bg)",
  border: "1px solid var(--bd)",
  borderRadius: "12px",
};

export function opcaoSegmentada(sel: boolean, desativado = false): CSSProperties {
  return {
    flexGrow: 1,
    height: "40px",
    padding: "0 14px",
    border: 0,
    borderRadius: "9px",
    fontFamily: "inherit",
    fontSize: "13px",
    cursor: desativado ? "not-allowed" : "pointer",
    background: sel ? "var(--ac)" : "transparent",
    color: sel ? "var(--onac)" : "var(--tx2)",
    fontWeight: sel ? 600 : 400,
  };
}

// Chip (gatilho, contexto, filtros)
export function chip(sel: boolean, desativado = false): CSSProperties {
  return {
    height: "36px",
    padding: "0 14px",
    borderRadius: "999px",
    fontFamily: "inherit",
    fontSize: "13px",
    cursor: desativado ? "not-allowed" : "pointer",
    background: sel ? "var(--ac)" : "transparent",
    color: sel ? "var(--onac)" : "var(--tx2)",
    border: `1px solid ${sel ? "var(--ac)" : "var(--bd)"}`,
    fontWeight: sel ? 600 : 400,
  };
}

export const INPUT: CSSProperties = {
  height: "44px",
  boxSizing: "border-box",
  padding: "0 14px",
  borderRadius: "10px",
  border: "1px solid var(--bd)",
  background: "var(--bg)",
  color: "var(--tx)",
  fontFamily: "inherit",
  fontSize: "15px",
  fontVariantNumeric: "tabular-nums",
  width: "100%",
};

export function botaoPrimario(ativo: boolean): CSSProperties {
  return {
    height: "44px",
    padding: "0 22px",
    borderRadius: "12px",
    border: 0,
    fontFamily: "inherit",
    fontSize: "14px",
    fontWeight: 600,
    cursor: ativo ? "pointer" : "not-allowed",
    background: ativo ? "var(--ac)" : "var(--s2)",
    color: ativo ? "var(--onac)" : "var(--tx3)",
  };
}

export const BOTAO_SECUNDARIO: CSSProperties = {
  height: "40px",
  padding: "0 16px",
  borderRadius: "10px",
  border: "1px solid var(--bd)",
  background: "transparent",
  color: "var(--tx)",
  fontFamily: "inherit",
  fontSize: "13px",
  cursor: "pointer",
};
