/**
 * Modelo da tela Visao Geral: transforma os trades do mes em tudo que o desenho
 * mostra. Espelha o renderVals() de design/v2/Main.dc.html, com dados reais.
 * Funcao pura, sem Supabase — testada em scripts/verify.ts.
 */
import {
  NOMES_CONTEXTOS,
  NOMES_ESTRATEGIAS,
  NOMES_GATILHOS,
  TradeMetricas,
  calcularDrawdown,
  calcularRTrade,
  calcularRiscoTrade,
  classificarFaixaHorario,
  fimDaFaixa,
  formatarBRL,
  formatarPct,
  formatarR,
  media,
  mediana,
  somar,
  temDesvio,
} from "./metricas";

export interface TradeVG extends TradeMetricas {
  data: string; // YYYY-MM-DD da sessao
}

const COR_POS = "var(--actx)";
const COR_NEG = "var(--negtx)";
const FILL_POS = "var(--ac)";
const FILL_NEG = "var(--neg)";
// zero e neutro: sem trade nao e ganho
const cor = (x: number) => (x > 0 ? COR_POS : x < 0 ? COR_NEG : "var(--tx)");
const fill = (x: number) => (x >= 0 ? FILL_POS : FILL_NEG);
const CORES_K = ["var(--k1)", "var(--k2)", "var(--k3)", "var(--k4)", "var(--k5)"];
const MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"];

function rDoTrade(t: TradeMetricas) {
  return calcularRTrade(Number(t.pontos_real ?? 0), calcularRiscoTrade(Number(t.entrada), Number(t.stop)));
}
const pnl = (t: TradeMetricas) => Number(t.pnl_real ?? 0);
const risco = (t: TradeMetricas) => calcularRiscoTrade(Number(t.entrada), Number(t.stop));
const diaMes = (iso: string) => {
  const [, m, d] = iso.split("-");
  return `${d}/${m}`;
};
const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;

function tipoDesvio(t: TradeMetricas) {
  if (t.antecipou_stop) return "Antecipou o stop";
  if (t.mudou_alvo) return "Mudou o alvo";
  if (t.parcial_emocional) return "Parcial emocional";
  return "Fora do plano";
}

export function montarVisaoGeral(trades: TradeVG[], anteriores: TradeVG[], ano: number, mes: number, hojeIso: string) {
  const n = trades.length;
  const nomeMes = MESES[mes - 1];
  const nomeMesAnt = MESES[(mes + 10) % 12];
  const rs = trades.map(rDoTrade);
  const pnls = trades.map(pnl);
  const total = somar(pnls);
  const totalR = somar(rs);
  const ganhos = somar(pnls.filter((p) => p > 0));
  const perdas = -somar(pnls.filter((p) => p < 0));
  const wins = pnls.filter((p) => p > 0);
  const losses = pnls.filter((p) => p < 0);
  const D = calcularDrawdown(pnls);
  const DR = calcularDrawdown(rs);
  const payoff = losses.length ? media(wins) / Math.abs(media(losses)) : null;
  const pf = perdas > 0 ? ganhos / perdas : null;
  const num = (x: number | null) => (x === null ? "—" : x.toFixed(2).replace(".", ","));

  // mes anterior, para as variacoes
  const nA = anteriores.length;
  const pnlA = somar(anteriores.map(pnl));
  const rsA = anteriores.map(rDoTrade);
  const ganhosA = somar(anteriores.map(pnl).filter((p) => p > 0));
  const perdasA = -somar(anteriores.map(pnl).filter((p) => p < 0));
  // rodape dos KPIs e a comparacao com o mes anterior: deixar claro que nao e o mes aberto
  const semAnt = `Mês anterior (${nomeMesAnt}): sem trades`;
  const kpis = [
    { label: "Resultado", valor: formatarBRL(total), cor: cor(total), sub: `${formatarR(totalR)} no mês`, delta: nA ? `${formatarBRL(total - pnlA)} contra ${nomeMesAnt}` : semAnt },
    { label: "Trades", valor: String(n), cor: "var(--tx)", sub: `${formatarPct(n ? wins.length / n : 0)} de acerto`, delta: nA ? `${nomeMesAnt}: ${plural(nA, "trade", "trades")} · ${formatarPct(anteriores.filter((t) => pnl(t) > 0).length / nA)}` : semAnt },
    { label: "Expectativa", valor: formatarR(n ? totalR / n : 0), cor: cor(totalR), sub: `por trade · payoff ${num(payoff)}`, delta: nA ? `${nomeMesAnt}: ${formatarR(somar(rsA) / nA)}` : semAnt },
    { label: "Profit factor", valor: num(pf), cor: "var(--tx)", sub: `${formatarBRL(ganhos, false)} ganhos · ${formatarBRL(perdas, false)} perdas`, delta: nA ? `${nomeMesAnt}: ${num(perdasA > 0 ? ganhosA / perdasA : null)}` : semAnt },
    { label: "Drawdown máximo", valor: formatarBRL(-D.maxDrawdown), cor: COR_NEG, sub: `${formatarR(-DR.maxDrawdown)} no pior trecho`, delta: nA ? `${nomeMesAnt}: ${formatarBRL(-calcularDrawdown(anteriores.map(pnl)).maxDrawdown)}` : semAnt },
  ];

  // Curva de capital (688 x 250)
  const W = 688, H = 250, pl = 64, pr = 12, pt = 24, pb = 30;
  const acum = (f: (t: TradeVG) => boolean) => {
    const a = [0];
    trades.forEach((t) => a.push(a[a.length - 1] + (f(t) ? pnl(t) : 0)));
    return a;
  };
  const cum = acum(() => true);
  const series = {
    C: acum((t) => t.strategy_id === "varrida_barra_10"),
    B: acum((t) => t.strategy_id === "continuidade_tendencia"),
    A: acum((t) => t.strategy_id === "reversao_htf"),
  };
  const todos = [...cum, ...series.A, ...series.B, ...series.C];
  const amplitude = Math.max(...todos) - Math.min(0, ...todos) || 1;
  const passo = [50, 100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000].find((p) => p >= amplitude / 3.5) ?? 20000;
  const top = Math.max(passo, Math.ceil(Math.max(...todos) / passo) * passo);
  const bot = Math.min(0, Math.floor(Math.min(...todos) / passo) * passo);
  const X = (i: number) => pl + (i * (W - pl - pr)) / Math.max(n, 1);
  const Y = (v: number) => pt + ((top - v) / (top - bot)) * (H - pt - pb);
  const path = (a: number[]) => a.map((v, i) => `${i ? "L" : "M"}${X(i).toFixed(1)} ${Y(v).toFixed(1)}`).join(" ");
  const ticks: { y: string; yt: string; label: string }[] = n ? [] : [{ y: Y(0).toFixed(1), yt: (Y(0) + 4).toFixed(1), label: "0" }];
  if (n) for (let v = bot; v <= top; v += passo) ticks.push({ y: Y(v).toFixed(1), yt: (Y(v) + 4).toFixed(1), label: v === 0 ? "0" : v < 0 ? `−${formatarBRL(-v, false)}` : formatarBRL(v, false) });
  const pico = Math.max(...cum);
  const iPico = cum.indexOf(pico);
  const idxRotulos = n <= 5 ? Array.from({ length: n }, (_, i) => i + 1) : [1, Math.round(n * 0.25), Math.round(n * 0.5), Math.round(n * 0.75), n];
  const temDD = D.maxDrawdown > 0;
  const curva = {
    W, H, vb: `0 0 ${W} ${H}`, x0: pl, x1: W - pr, lx: pl - 10,
    d: path(cum), A: path(series.A), B: path(series.B), C: path(series.C),
    area: `${path(cum)} L${X(n).toFixed(1)} ${Y(0).toFixed(1)} L${X(0).toFixed(1)} ${Y(0).toFixed(1)} Z`,
    temDD, ddx: X(D.picoIndex).toFixed(1), ddw: (X(D.valeIndex) - X(D.picoIndex)).toFixed(1), ddy: 4, ddh: H - pb - 4,
    ddlx: ((X(D.picoIndex) + X(D.valeIndex)) / 2).toFixed(1), ddty: 16, ddTxt: formatarBRL(-D.maxDrawdown),
    ticks, xly: H - 8,
    xl: Array.from(new Set(idxRotulos)).filter((i) => i >= 1).map((i) => ({ x: X(i).toFixed(1), label: diaMes(trades[i - 1].data), anchor: (i === n ? "end" : "middle") as "end" | "middle" })),
    endx: X(n).toFixed(1), endy: Y(cum[n]).toFixed(1),
    frase: n
      ? `Pico de ${formatarBRL(pico)}${iPico > 0 ? ` em ${diaMes(trades[iPico - 1].data)}` : ""}${temDD ? ` · pior trecho ${formatarBRL(-D.maxDrawdown)} (${diaMes(trades[Math.max(D.picoIndex, 1) - 1].data)} → ${diaMes(trades[D.valeIndex - 1].data)})` : " · sem drawdown"}`
      : "Sem trades no mês ainda",
  };

  // Por estrategia
  const todasEstrategias = ["varrida_barra_10", "continuidade_tendencia", "reversao_htf"];
  const ids = n ? todasEstrategias.filter((id) => trades.some((t) => t.strategy_id === id)) : todasEstrategias;
  const estr = ids.map((id) => {
    const ts = trades.filter((t) => t.strategy_id === id);
    const p = somar(ts.map(pnl));
    const rm = media(ts.map(rDoTrade));
    return {
      id, nome: NOMES_ESTRATEGIAS[id] ?? id, n: ts.length, pnl: p, pnlTxt: formatarBRL(p), cor: cor(p),
      rm: formatarR(rm), rmCor: cor(rm), acerto: formatarPct(ts.length ? ts.filter((t) => pnl(t) > 0).length / ts.length : 0),
      dd: formatarBRL(-calcularDrawdown(ts.map(pnl)).maxDrawdown), stop: ts.length ? `${Math.round(mediana(ts.map(risco)))} pts` : "—",
      nTxt: plural(ts.length, "trade", "trades"), wN: 0,
    };
  }).sort((a, b) => b.n - a.n);
  const maxN = Math.max(1, ...estr.map((e) => e.n));
  estr.forEach((e) => (e.wN = Math.round((e.n / maxN) * 300)));
  const maisN = [...estr].sort((a, b) => b.n - a.n)[0];
  const maisP = [...estr].sort((a, b) => b.pnl - a.pnl)[0];
  const pior = [...estr].sort((a, b) => a.pnl - b.pnl)[0];
  const estrFrase = n ? `Mais trades: ${maisN.nome} (${maisN.n}) · mais resultado: ${maisP.nome}` : "Nenhum trade no mês ainda";
  const tabFrase = !n
    ? "Os resultados por estratégia aparecem com o primeiro trade fechado"
    : estr.length > 1
      ? `${maisP.nome} carrega o mês com ${maisP.pnlTxt}; ${pior.nome}${pior.pnl < 0 ? " está negativa: " : " tem o menor resultado: "}${pior.pnlTxt}`
      : `${maisP.nome}: ${maisP.pnlTxt} no mês`;
  const tot = {
    n, acerto: formatarPct(n ? wins.length / n : 0), rm: formatarR(n ? totalR / n : 0), rmCor: cor(totalR),
    pnl: formatarBRL(total), cor: cor(total), dd: formatarBRL(-D.maxDrawdown), stop: n ? `${Math.round(mediana(trades.map(risco)))} pts` : "—",
  };

  // Por horario (504 x 220)
  const faixas = ["10:00", "10:15", "10:30", "10:45", "11:00", "11:15"];
  const hb = faixas.map((f) => {
    const ts = trades.filter((t) => classificarFaixaHorario(t.hora_entrada) === f);
    return { f, n: ts.length, rm: ts.length ? media(ts.map(rDoTrade)) : 0 };
  });
  const hmax = Math.max(1, Math.ceil(Math.max(...hb.map((b) => Math.abs(b.rm))) * 2) / 2);
  const hpt = 20, hpb = 50, plotH = 220 - hpt - hpb, y0 = hpt + plotH / 2, slot = (504 - 36) / 6;
  const bars = hb.map((b, i) => {
    const h = (Math.abs(b.rm) / hmax) * (plotH / 2);
    const cx = 36 + i * slot + slot / 2;
    return {
      f: b.f, cx: cx.toFixed(1), x: (cx - 22).toFixed(1), y: (b.rm >= 0 ? y0 - h : y0).toFixed(1),
      h: Math.max(h, b.n ? 2 : 0).toFixed(1), fill: fill(b.rm), val: b.n ? formatarR(b.rm) : "—",
      vy: (b.rm >= 0 ? y0 - h - 6 : y0 + h + 14).toFixed(1), nTxt: plural(b.n, "trade", "trades"),
    };
  });
  const melhor = [...hb].filter((b) => b.n).sort((a, b) => b.rm - a.rm)[0];
  const hmaxTxt = String(hmax).replace(".", ",");
  const hora = {
    bars, y0: y0.toFixed(1), y0t: (y0 + 4).toFixed(1), yTop: hpt + 4, yBot: (hpt + plotH + 4).toFixed(1),
    topTxt: `+${hmaxTxt}R`, botTxt: `−${hmaxTxt}R`,
    frase: melhor ? `Melhor faixa: ${melhor.f}–${fimDaFaixa(melhor.f)} · ${formatarR(melhor.rm)} médio · ${plural(melhor.n, "trade", "trades")}` : "Nenhum trade dentro da janela",
    pequena: Boolean(melhor) && melhor!.n < 10,
  };

  // Gatilhos (anel)
  const comGatilho = trades.filter((t) => t.gatilho);
  const circ = 2 * Math.PI * 66;
  let acc = 0;
  const gk = Object.keys(NOMES_GATILHOS)
    .map((k) => {
      const ts = comGatilho.filter((t) => t.gatilho === k);
      return { nome: NOMES_GATILHOS[k], n: ts.length, rm: media(ts.map(rDoTrade)) };
    })
    .filter((g) => g.n)
    .sort((a, b) => b.n - a.n)
    .map((g, i) => {
      const len = (g.n / comGatilho.length) * circ;
      const seg = Math.max(len - 3, 0);
      const item = {
        ...g, dash: `${seg.toFixed(1)} ${(circ - seg).toFixed(1)}`, off: (-acc).toFixed(1), cor: CORES_K[i % 5],
        pct: formatarPct(g.n / comGatilho.length), rmTxt: formatarR(g.rm), rmCor: cor(g.rm),
      };
      acc += len;
      return item;
    });
  const melhorG = [...gk].filter((g) => g.n >= 2).sort((a, b) => b.rm - a.rm)[0];
  const itensGatilho = gk.length
    ? gk
    : Object.keys(NOMES_GATILHOS).map((k, i) => ({
        nome: NOMES_GATILHOS[k], n: 0, rm: 0, dash: `0 ${circ.toFixed(1)}`, off: "0", cor: CORES_K[i % 5],
        pct: "0%", rmTxt: "—", rmCor: "var(--tx3)",
      }));
  const gat = {
    n: comGatilho.length, itens: itensGatilho,
    frase: gk.length
      ? `Mais usado: ${gk[0].nome} (${gk[0].n} de ${comGatilho.length})${melhorG ? ` · paga mais: ${melhorG.nome} ${formatarR(melhorG.rm)}` : ""}`
      : "Nenhum trade com gatilho registrado",
    semGatilho: n - comGatilho.length,
  };

  // Stops (392 x 200)
  const SB = [
    { l: "< 150", a: 0, b: 150 }, { l: "150–199", a: 150, b: 200 }, { l: "200–249", a: 200, b: 250 },
    { l: "250–299", a: 250, b: 300 }, { l: "300+", a: 300, b: Infinity },
  ];
  const med = Math.round(mediana(trades.map(risco)));
  const cont = SB.map((s) => trades.filter((t) => risco(t) >= s.a && risco(t) < s.b).length);
  const cmax = Math.max(1, ...cont);
  const sslot = 392 / 5;
  const acima = trades.filter((t) => risco(t) >= 250).length;
  const stops = {
    bars: SB.map((s, i) => {
      const h = (cont[i] / cmax) * 120;
      const cx = i * sslot + sslot / 2;
      return { l: s.l, n: cont[i], cx: cx.toFixed(1), x: (cx - 26).toFixed(1), y: (160 - h).toFixed(1), h: Math.max(h, 2).toFixed(1), vy: (160 - h - 8).toFixed(1), fill: n && med >= s.a && med < s.b ? "var(--k1)" : "var(--k4)" };
    }),
    frase: n ? `Stop mediano ${med} pts · ${plural(acima, "stop", "stops")} de 250 pts ou mais` : "Nenhum stop registrado no mês",
  };

  // Calendario: semanas de segunda a sexta que cobrem o mes
  const porDia: Record<string, number> = {};
  trades.forEach((t) => (porDia[t.data] = (porDia[t.data] ?? 0) + pnl(t)));
  const vmax = Math.max(1, ...Object.values(porDia).map(Math.abs));
  const primeiro = new Date(Date.UTC(ano, mes - 1, 1));
  const desloc = (primeiro.getUTCDay() + 6) % 7; // 0 = segunda
  // segunda-feira da semana do dia 1 (se o dia 1 cai no fim de semana, comeca na segunda seguinte)
  const seg = desloc <= 4 ? new Date(Date.UTC(ano, mes - 1, 1 - desloc)) : new Date(Date.UTC(ano, mes - 1, 1 + (7 - desloc)));
  const cells: Array<Record<string, string | number>> = [];
  const ultimo = new Date(Date.UTC(ano, mes, 0));
  let r = 0;
  for (let semana = new Date(seg); semana <= ultimo; semana = new Date(semana.getTime() + 7 * 864e5), r++) {
    for (let c = 0; c < 5; c++) {
      const d = new Date(semana.getTime() + c * 864e5);
      const iso = d.toISOString().slice(0, 10);
      const fora = d.getUTCMonth() !== mes - 1;
      const futuro = !fora && iso > hojeIso;
      const v = fora ? undefined : porDia[iso];
      const x = c * 76, y = 22 + r * 48;
      cells.push({
        x, y, tx: x + 8, ty: y + 16, vx: x + 62, vy: y + 34, d: String(d.getUTCDate()),
        dcor: fora ? "var(--tx3)" : "var(--tx2)",
        v: v === undefined ? "" : `${v > 0 ? "+" : v < 0 ? "−" : ""}${Math.abs(Math.round(v)).toLocaleString("pt-BR")}`,
        fill: v === undefined ? "var(--s2)" : fill(v),
        op: v === undefined ? (fora || futuro ? 0.35 : 1) : (0.18 + 0.42 * (Math.abs(v) / vmax)).toFixed(2),
        so: fora || futuro ? 0 : 1,
      });
    }
  }
  const dias = Object.keys(porDia);
  const diasPos = dias.filter((d) => porDia[d] > 0).length;
  const melhorDia = [...dias].sort((a, b) => porDia[b] - porDia[a])[0];
  const cal = {
    altura: 22 + r * 48,
    dow: ["Seg", "Ter", "Qua", "Qui", "Sex"].map((l, i) => ({ l, x: i * 76 + 35 })),
    cells,
    frase: melhorDia ? `${diasPos} de ${dias.length} ${dias.length === 1 ? "dia positivo" : "dias positivos"} · melhor: ${diaMes(melhorDia)} ${formatarBRL(porDia[melhorDia])}` : "Nenhum dia operado no mês ainda",
  };

  // Disciplina
  const desv = trades.filter(temDesvio);
  const noPlano = n - desv.length;
  const custo = somar(desv.map((t) => Math.max(0, Number(t.pnl_plano ?? t.pnl_real ?? 0) - pnl(t))));
  const disc = {
    pct: n ? formatarPct(noPlano / n) : "—", sub: `${noPlano} de ${plural(n, "trade", "trades")} no plano`,
    w: n ? Math.round((noPlano / n) * 280) : 0,
    frase: !n ? "Sem trades para medir ainda" : desv.length === 0 ? "Todos os trades seguiram o plano" : custo > 0 ? `Desvios custaram ${formatarBRL(custo, false)} no mês` : `${plural(desv.length, "desvio", "desvios")} do plano, sem custo medido`,
    itens: desv.map((t) => ({ data: diaMes(t.data), tipo: tipoDesvio(t), custo: formatarBRL(-Math.max(0, Number(t.pnl_plano ?? t.pnl_real ?? 0) - pnl(t))) })),
  };

  // Setup C e contexto
  const grupo = (ts: TradeVG[], nome: string) => {
    const rm = media(ts.map(rDoTrade));
    return { nome, n: ts.length, acerto: `${formatarPct(ts.length ? ts.filter((t) => pnl(t) > 0).length / ts.length : 0)} acerto`, rm: ts.length ? formatarR(rm) : "—", cor: cor(rm) };
  };
  const tsC = trades.filter((t) => t.strategy_id === "varrida_barra_10");
  const modos = ["C1", "C2"].map((m) => grupo(tsC.filter((t) => t.setup_c_modo === m), m));
  const ctx = Object.keys(NOMES_CONTEXTOS).map((k) => grupo(trades.filter((t) => t.contexto_1h === k), NOMES_CONTEXTOS[k]));
  const sc = {
    modos, ctx,
    frase: tsC.length ? `C1 ${modos[0].rm} × C2 ${modos[1].rm} por trade` : "Sem trades do Setup C ainda",
    pequena: tsC.length > 0 && tsC.length < 10,
  };

  const resumo = n
    ? `${nomeMes[0].toUpperCase()}${nomeMes.slice(1)} está em ${formatarBRL(total)} com ${plural(n, "trade", "trades")} (${formatarR(totalR)}).${maisP ? ` ${maisP.nome} carrega o mês` : ""}${melhor ? `; o melhor horário é ${melhor.f}–${fimDaFaixa(melhor.f)}.` : "."}`
    : `${nomeMes[0].toUpperCase()}${nomeMes.slice(1)} ainda não tem trades fechados. Os números aparecem aqui conforme você fecha trades pelo checklist.`;

  return { n, resumo, kpis, curva, estr, estrFrase, tabFrase, tot, hora, gat, stops, cal, disc, sc };
}

export type VisaoGeral = ReturnType<typeof montarVisaoGeral>;
