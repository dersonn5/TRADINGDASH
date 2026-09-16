import * as React from "react";

export type Tom = "ok" | "now" | "block" | "lock" | "neutro";

export const TOM_MAP: Record<
  Tom,
  { text: string; bg: string; border: string }
> = {
  ok: {
    text: "var(--inst-ok)",
    bg: "var(--inst-ok-bg)",
    border: "var(--inst-ok-line)",
  },
  now: {
    text: "var(--inst-now)",
    bg: "var(--inst-now-bg)",
    border: "var(--inst-now-line)",
  },
  block: {
    text: "var(--inst-block)",
    bg: "var(--inst-block-bg)",
    border: "var(--inst-block-line)",
  },
  lock: {
    text: "var(--inst-lock)",
    bg: "transparent",
    border: "var(--inst-line)",
  },
  neutro: {
    text: "var(--inst-text)",
    bg: "var(--inst-panel)",
    border: "var(--inst-line)",
  },
};

/**
 * <InstLabel> — rótulo mono técnico
 * Fonte mono, 10px, letterSpacing: 0.16em, uppercase, cor --inst-faint
 */
export interface InstLabelProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
}
export function InstLabel({ children, className = "", style, ...props }: InstLabelProps) {
  return (
    <span
      className={`mono uppercase select-none ${className}`}
      style={{
        fontSize: "10px",
        letterSpacing: "0.16em",
        color: "var(--inst-faint)",
        lineHeight: 1.2,
        ...style,
      }}
      {...props}
    >
      {children}
    </span>
  );
}

/**
 * <InstPage> — casca da página do instrumento
 * Cabeçalho com eyebrow e título 23px peso 600, slot right opcional
 */
export interface InstPageProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  right?: React.ReactNode;
  children: React.ReactNode;
}
export function InstPage({ eyebrow, title, right, children, className = "", style, ...props }: InstPageProps) {
  return (
    <div
      className={`-m-4 md:-m-6 flex flex-1 flex-col min-h-[calc(100vh-4rem)] ${className}`}
      style={{
        background: "var(--inst-bg)",
        color: "var(--inst-text)",
        ...style,
      }}
      {...props}
    >
      <div
        style={{
          padding: "24px 28px 18px 28px",
          borderBottom: "1px solid var(--inst-line-2)",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
          background: "var(--inst-bg)",
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {eyebrow ? (typeof eyebrow === "string" ? <InstLabel>{eyebrow}</InstLabel> : eyebrow) : null}
            <h1
              style={{
                margin: 0,
                fontSize: "23px",
                fontWeight: 600,
                letterSpacing: "-0.015em",
                color: "var(--inst-text)",
              }}
            >
              {title}
            </h1>
          </div>
          {right && <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>{right}</div>}
        </div>
      </div>
      <div
        style={{
          padding: "24px 28px 32px 28px",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          flexGrow: 1,
        }}
      >
        {children}
      </div>
    </div>
  );
}

/**
 * <InstBar> e <InstBarCell> — barra de estado do topo com dados do pregão
 */
export interface InstBarProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}
export function InstBar({ children, className = "", style, ...props }: InstBarProps) {
  return (
    <div
      className={className}
      style={{
        display: "flex",
        alignItems: "stretch",
        borderBottom: "1px solid var(--inst-line-2)",
        background: "var(--inst-panel)",
        flexWrap: "wrap",
        margin: "-24px -28px 0 -28px",
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export interface InstBarCellProps extends React.HTMLAttributes<HTMLDivElement> {
  label: React.ReactNode;
  value: React.ReactNode;
  tom?: Tom;
  sub?: React.ReactNode;
}
export function InstBarCell({ label, value, tom, sub, className = "", style, ...props }: InstBarCellProps) {
  const color = tom ? TOM_MAP[tom].text : "var(--inst-text)";
  return (
    <div
      className={className}
      style={{
        padding: "14px 24px",
        borderRight: "1px solid var(--inst-line-2)",
        display: "flex",
        flexDirection: "column",
        gap: "3px",
        minWidth: "140px",
        ...style,
      }}
      {...props}
    >
      {typeof label === "string" ? <InstLabel>{label}</InstLabel> : label}
      <div className="mono tabular" style={{ fontSize: "15px", fontWeight: 600, color }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: "11px", color: "var(--inst-faint)" }}>{sub}</div>}
    </div>
  );
}

/**
 * <InstCard> — painel padrão com borda discreta e padding técnico
 */
export interface InstCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: React.ReactNode;
  right?: React.ReactNode;
  children: React.ReactNode;
}
export function InstCard({ label, right, children, className = "", style, ...props }: InstCardProps) {
  return (
    <div
      className={className}
      style={{
        border: "1px solid var(--inst-line)",
        background: "var(--inst-panel)",
        borderRadius: "3px",
        padding: "20px 22px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        ...style,
      }}
      {...props}
    >
      {(label || right) && (
        <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: "8px" }}>
          {label ? (typeof label === "string" ? <InstLabel>{label}</InstLabel> : label) : <span />}
          {right && <div>{right}</div>}
        </div>
      )}
      {children}
    </div>
  );
}

/**
 * <InstNum> — número formatado em tabular, nunca dança
 * size: sm (13px), md (16px), lg (25px), xl (34px)
 */
export type NumSize = "sm" | "md" | "lg" | "xl";
export interface InstNumProps extends React.HTMLAttributes<HTMLSpanElement> {
  value: React.ReactNode;
  tom?: Tom;
  size?: NumSize;
}
export function InstNum({ value, tom, size = "md", className = "", style, ...props }: InstNumProps) {
  const color = tom ? TOM_MAP[tom].text : "inherit";
  const sizeStyles: Record<NumSize, { fontSize: string; fontWeight: number }> = {
    sm: { fontSize: "13px", fontWeight: 500 },
    md: { fontSize: "16px", fontWeight: 500 },
    lg: { fontSize: "25px", fontWeight: 600 },
    xl: { fontSize: "34px", fontWeight: 600 },
  };
  const { fontSize, fontWeight } = sizeStyles[size];

  return (
    <span
      className={`tabular mono ${className}`}
      style={{
        fontSize,
        fontWeight,
        color,
        letterSpacing: size === "xl" || size === "lg" ? "-0.02em" : "normal",
        ...style,
      }}
      {...props}
    >
      {value}
    </span>
  );
}

/**
 * <InstBadge> — pílula mono de estado
 * Mono 9px, letterSpacing: 0.1em, uppercase, padding 3px 9px, borderRadius 2px
 */
export interface InstBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  tom?: Tom;
  children: React.ReactNode;
}
export function InstBadge({ tom = "neutro", children, className = "", style, ...props }: InstBadgeProps) {
  const t = TOM_MAP[tom];
  return (
    <span
      className={`mono tabular uppercase ${className}`}
      style={{
        fontSize: "9px",
        letterSpacing: "0.1em",
        padding: "3px 9px",
        borderRadius: "2px",
        border: `1px solid ${t.border}`,
        background: t.bg,
        color: t.text,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        lineHeight: 1.2,
        ...style,
      }}
      {...props}
    >
      {children}
    </span>
  );
}

/**
 * <InstBand> — faixa de status com borda esquerda acentuada
 */
export interface InstBandProps extends React.HTMLAttributes<HTMLDivElement> {
  tom?: Tom;
  titulo: React.ReactNode;
  linhas?: string[];
  acao?: React.ReactNode;
}
export function InstBand({ tom = "neutro", titulo, linhas, acao, className = "", style, ...props }: InstBandProps) {
  const t = TOM_MAP[tom];
  return (
    <div
      className={className}
      style={{
        borderLeft: `3px solid ${t.text}`,
        borderTop: `1px solid ${t.border}`,
        borderRight: `1px solid ${t.border}`,
        borderBottom: `1px solid ${t.border}`,
        background: t.bg,
        borderRadius: "3px",
        padding: "17px 22px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        ...style,
      }}
      {...props}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <span
          className="mono tabular"
          style={{
            fontSize: "17px",
            fontWeight: 600,
            color: t.text,
            letterSpacing: "0.02em",
          }}
        >
          {titulo}
        </span>
        {acao && <div>{acao}</div>}
      </div>
      {linhas && linhas.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: "5px" }}>
          {linhas.map((linha, idx) => (
            <div key={idx} style={{ display: "grid", gridTemplateColumns: "14px 1fr", gap: "8px", alignItems: "start" }}>
              <span className="mono tabular" style={{ fontSize: "12px", color: t.text, lineHeight: 1.4 }}>
                —
              </span>
              <span style={{ fontSize: "12px", color: "var(--inst-text-2)", lineHeight: 1.4 }}>
                {linha}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * <InstTable>, <InstRow>, <InstCell> — tabela densa de instrumento
 */
export interface InstTableProps extends React.TableHTMLAttributes<HTMLTableElement> {
  colunas: Array<React.ReactNode | { label: React.ReactNode; align?: "left" | "right" | "center"; width?: string }>;
  children: React.ReactNode;
}
export function InstTable({ colunas, children, className = "", style, ...props }: InstTableProps) {
  return (
    <div
      style={{
        width: "100%",
        overflowX: "auto",
        border: "1px solid var(--inst-line)",
        borderRadius: "3px",
        background: "var(--inst-panel)",
      }}
    >
      <table
        className={className}
        style={{
          width: "100%",
          borderCollapse: "collapse",
          textAlign: "left",
          ...style,
        }}
        {...props}
      >
        <thead>
          <tr
            style={{
              background: "var(--inst-bg)",
              borderBottom: "1px solid var(--inst-line)",
            }}
          >
            {colunas.map((col, idx) => {
              const isObj = typeof col === "object" && col !== null && "label" in col;
              const label = isObj ? (col as any).label : col;
              const align = isObj ? (col as any).align || "left" : "left";
              const width = isObj ? (col as any).width : undefined;
              return (
                <th
                  key={idx}
                  style={{
                    padding: "10px 16px",
                    textAlign: align,
                    width,
                  }}
                >
                  {typeof label === "string" ? <InstLabel>{label}</InstLabel> : label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  );
}

export interface InstRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  tom?: Tom;
  children: React.ReactNode;
}
export function InstRow({ tom, children, className = "", style, ...props }: InstRowProps) {
  const borderLeft = tom ? `2px solid ${TOM_MAP[tom].text}` : undefined;
  return (
    <tr
      className={`hover:bg-[var(--inst-hover)] transition-colors ${className}`}
      style={{
        borderBottom: "1px solid var(--inst-line-soft)",
        borderLeft,
        ...style,
      }}
      {...props}
    >
      {children}
    </tr>
  );
}

export function InstCell({
  children,
  align = "left",
  className = "",
  style,
  ...props
}: React.TdHTMLAttributes<HTMLTableCellElement> & { align?: "left" | "right" | "center" }) {
  return (
    <td
      className={className}
      style={{
        padding: "12px 16px",
        fontSize: "13px",
        color: "var(--inst-text)",
        textAlign: align,
        ...style,
      }}
      {...props}
    >
      {children}
    </td>
  );
}

/**
 * <InstEmpty> — estado vazio com borda tracejada
 */
export interface InstEmptyProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}
export function InstEmpty({ children, className = "", style, ...props }: InstEmptyProps) {
  return (
    <div
      className={className}
      style={{
        border: "1px dashed var(--inst-line-2)",
        borderRadius: "3px",
        padding: "32px 24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        color: "var(--inst-faint)",
        fontSize: "12px",
        lineHeight: 1.5,
        gap: "6px",
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * <InstDivider> — linha divisória de 1px
 */
export function InstDivider({ className = "", style, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={className}
      style={{
        height: "1px",
        background: "var(--inst-line)",
        width: "100%",
        ...style,
      }}
      {...props}
    />
  );
}
