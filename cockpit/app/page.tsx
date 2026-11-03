"use client";

import * as React from "react";
import { listarTradesDoMes, listarTradesFechados, getDataSaoPaulo } from "@/lib/copa-db";
import { montarVisaoGeral, TradeVG } from "@/lib/visao-geral";
import { CARD } from "@/components/v2/estilos";
import { VisaoGeralConteudo } from "@/components/v2/visao-geral-conteudo";

// Espelho de design/v2/Main.dc.html.

const MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];

function mesAnterior(ano: number, mes: number) {
  return mes === 1 ? { ano: ano - 1, mes: 12 } : { ano, mes: mes - 1 };
}

// "tudo" = todos os trades fechados, sem comparação com mês anterior e sem meta
type Selecao = { ano: number; mes: number } | "tudo";

export default function VisaoGeralPage() {
  const hojeIso = getDataSaoPaulo();
  const [anoHoje, mesHoje] = hojeIso.split("-").map(Number);
  const [sel, setSel] = React.useState<Selecao>({ ano: anoHoje, mes: mesHoje });
  const [dados, setDados] = React.useState<{ atual: TradeVG[]; anterior: TradeVG[] } | null>(null);
  const [erro, setErro] = React.useState<string | null>(null);
  const [atualizado, setAtualizado] = React.useState("");

  const opcoes = React.useMemo(() => {
    const lista = [{ ano: anoHoje, mes: mesHoje }];
    for (let i = 0; i < 2; i++) lista.unshift(mesAnterior(lista[0].ano, lista[0].mes));
    return lista;
  }, [anoHoje, mesHoje]);

  const chave = sel === "tudo" ? "tudo" : `${sel.ano}-${sel.mes}`;

  React.useEffect(() => {
    let vivo = true;
    setDados(null);
    setErro(null);
    const busca =
      sel === "tudo"
        ? listarTradesFechados().then((atual) => [atual, []] as const)
        : (() => {
            const ant = mesAnterior(sel.ano, sel.mes);
            return Promise.all([listarTradesDoMes(sel.ano, sel.mes), listarTradesDoMes(ant.ano, ant.mes)]);
          })();
    busca
      .then(([atual, anterior]) => {
        if (!vivo) return;
        setDados({ atual: atual as TradeVG[], anterior: anterior as TradeVG[] });
        setAtualizado(new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date()));
      })
      .catch((e) => vivo && setErro(e.message || "Erro ao carregar os trades"));
    return () => {
      vivo = false;
    };
    // a chave resume sel (o objeto muda de referência a cada clique)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave]);

  const vg = React.useMemo(
    () =>
      dados
        ? sel === "tudo"
          ? montarVisaoGeral(dados.atual, [], anoHoje, mesHoje, hojeIso, "tudo")
          : montarVisaoGeral(dados.atual, dados.anterior, sel.ano, sel.mes, hojeIso)
        : null,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [dados, chave, hojeIso]
  );

  const titulo = sel === "tudo" ? "Todo o período" : `${MESES[sel.mes - 1]} ${sel.ano}`;
  const estiloBotao = (ativo: boolean): React.CSSProperties => ({
    height: "36px", padding: "0 16px", border: 0, borderRadius: "8px", fontFamily: "inherit", fontSize: "13px", cursor: "pointer",
    background: ativo ? "var(--ac)" : "transparent", color: ativo ? "var(--onac)" : "var(--tx2)", fontWeight: ativo ? 600 : 400,
  });

  return (
    <>
      <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between", gap: "24px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
          <span style={{ fontSize: "13px", color: "var(--tx3)" }}>
            {titulo}
            {atualizado ? ` · atualizado ${atualizado}` : ""}
          </span>
          <h1 style={{ margin: 0, fontSize: "30px", fontWeight: 600, letterSpacing: "-0.02em" }}>Visão Geral</h1>
        </div>
        <div role="group" aria-label="Mês" style={{ display: "flex", gap: "4px", padding: "4px", background: "var(--s1)", border: "1px solid var(--bd)", borderRadius: "12px" }}>
          {opcoes.map((o) => {
            const ativo = sel !== "tudo" && o.ano === sel.ano && o.mes === sel.mes;
            return (
              <button key={`${o.ano}-${o.mes}`} type="button" aria-pressed={ativo} onClick={() => setSel(o)} style={estiloBotao(ativo)}>
                {MESES[o.mes - 1]}
              </button>
            );
          })}
          <button type="button" aria-pressed={sel === "tudo"} onClick={() => setSel("tudo")} style={estiloBotao(sel === "tudo")}>
            Tudo
          </button>
        </div>
      </div>

      {erro ? (
        <div style={{ ...CARD, color: "var(--negtx)", fontSize: "14px" }}>{erro}</div>
      ) : !vg ? (
        <div style={{ ...CARD, alignItems: "center", padding: "48px", color: "var(--tx3)", fontSize: "14px" }}>Carregando…</div>
      ) : (
        <VisaoGeralConteudo vg={vg} />
      )}
    </>
  );
}
