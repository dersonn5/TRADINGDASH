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
      className={`uppercase select-none ${className}`}
      style={{
        fontSize: "12px",
        fontWeight: 500,
        letterSpacing: "0.06em",
        color: "var(--tx3)",
        lineHeight: 1.3,
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
          padding: "32px 40px 4px 40px",
          display: "flex",
          flexDirection: "column",
          gap: "6px",
        }}
      >
        <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", flexWrap: "wrap", gap: "16px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            {eyebrow ? (
              typeof eyebrow === "string" ? (
                <span style={{ fontSize: "13px", color: "var(--tx3)" }}>{eyebrow}</span>
              ) : (
                eyebrow
              )
            ) : null}
            <h1
              style={{
                margin: 0,
                fontSize: "30px",
                fontWeight: 600,
                letterSpacing: "-0.02em",
                color: "var(--tx)",
              }}
            >
              {title}
            </h1>
          </div>
          {right && <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>{right}</div>}
        </div>
      </div>
      <div
        style={{
          padding: "20px 40px 40px 40px",
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
        gap: "12px",
        flexWrap: "wrap",
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
        padding: "16px 18px",
        borderRadius: "14px",
        border: "1px solid var(--bd)",
        background: "var(--s1)",
        display: "flex",
        flexDirection: "column",
        gap: "6px",
        minWidth: "140px",
        flex: "1 1 140px",
        ...style,
      }}
      {...props}
    >
      {typeof label === "string" ? <InstLabel>{label}</InstLabel> : label}
      <div className="tabular" style={{ fontSize: "20px", fontWeight: 600, color }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: "12px", color: "var(--tx3)" }}>{sub}</div>}
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
        border: "1px solid var(--bd)",
        background: "var(--s1)",
        borderRadius: "16px",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
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
      className={`tabular ${className}`}
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
      className={`tabular uppercase ${className}`}
      style={{
        fontSize: "11px",
        fontWeight: 600,
        letterSpacing: "0.04em",
        padding: "4px 10px",
        borderRadius: "999px",
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
        border: `1px solid ${t.border}`,
        background: t.bg,
        borderRadius: "14px",
        padding: "18px 22px",
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        ...style,
      }}
      {...props}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "12px" }}>
        <span
          style={{
            fontSize: "16px",
            fontWeight: 600,
            color: t.text,
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
              <span style={{ fontSize: "13px", color: t.text, lineHeight: 1.5 }}>
                ·
              </span>
              <span style={{ fontSize: "13px", color: "var(--tx2)", lineHeight: 1.5 }}>
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
        border: "1px solid var(--bd)",
        borderRadius: "16px",
        background: "var(--s1)",
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
              borderBottom: "1px solid var(--bd)",
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
  return (
    <tr
      className={`hover:bg-[var(--inst-hover)] transition-colors ${className}`}
      style={{
        borderBottom: "1px solid var(--bd)",
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
        padding: "14px 16px",
        fontSize: "13px",
        color: "var(--tx)",
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
        border: "1px dashed var(--bd)",
        borderRadius: "14px",
        padding: "32px 24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        color: "var(--tx3)",
        fontSize: "13px",
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
