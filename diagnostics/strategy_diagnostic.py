"""
Diagnóstico Funil das estratégias ICT.

Roda candle-by-candle (M5) no histórico disponível com diagnostic_enabled=True,
agrega quantas vezes cada gate matou o sinal, e gera relatório markdown.

Uso:
    python -m diagnostics.strategy_diagnostic

Output:
    diagnostics/reports/funnel_silver_bullet_YYYYMMDD_HHMMSS.md
    diagnostics/reports/funnel_london_sweep_YYYYMMDD_HHMMSS.md
"""
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.data_loader import DataLoader  # noqa: E402
from strategies.silver_bullet_nq import SilverBulletNQ, SilverBulletConfig  # noqa: E402
from strategies.london_sweep_xau import LondonSweepXAU, LondonSweepConfig  # noqa: E402
from strategies.silver_bullet_xau import SilverBulletXAU, SilverBulletXAUConfig  # noqa: E402
from strategies.london_sweep_nq import LondonSweepNQ, LondonSweepNQConfig  # noqa: E402
from strategies.session_configs import (
    make_sb_nq_am, make_sb_nq_lunch, make_sb_nq_close,
    make_sb_xau_am, make_sb_xau_lunch, make_sb_xau_close
)


REPORTS_DIR = Path(__file__).resolve().parent / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_multi_tf(loader: DataLoader, symbol: str, start: str, end: str) -> dict:
    return {
        "1m": loader.load_data(symbol, "1m", start, end),
        "5m": loader.load_data(symbol, "5m", start, end),
        "15m": loader.load_data(symbol, "15m", start, end),
        "1h": loader.load_data(symbol, "1h", start, end),
        "1d": loader.load_data(symbol, "1d", start, end),
    }


def diagnose_strategy(strategy, data: dict, name: str) -> dict:
    """
    Walk candle-by-candle no M5 e coleta gate logs.
    """
    df_5m = data["5m"]
    df_15m = data["15m"]
    df_1h = data["1h"]
    df_1d = data["1d"]
    df_1m = data.get("1m", pd.DataFrame())

    if df_5m.empty:
        print(f"[{name}] Sem dados M5, abortando.")
        return {}

    strategy.diagnostic_enabled = True

    # Agregadores
    gate_pass_count = Counter()     # gate_name -> quantos candles passaram
    gate_fail_count = Counter()     # gate_name -> quantos candles falharam
    gate_fail_reasons = defaultdict(Counter)  # gate -> Counter(reason)
    funnel_order = []               # ordem dos gates conforme aparecem
    signals = []
    near_miss = []                  # candles que passaram >=80% dos gates mas falharam

    # Iterar a partir do candle 50 (precisa de histórico)
    total_evaluated = 0
    for i in range(50, len(df_5m)):
        current_time = df_5m.index[i]

        history_5m = df_5m.iloc[: i + 1]
        history_15m = df_15m[df_15m.index <= current_time] if not df_15m.empty else df_15m
        history_1h = df_1h[df_1h.index <= current_time] if not df_1h.empty else df_1h
        history_1d = df_1d[df_1d.index <= current_time] if not df_1d.empty else df_1d
        history_1m = df_1m[df_1m.index <= current_time] if not df_1m.empty else df_1m

        try:
            signal = strategy.evaluate(history_5m, history_15m, history_1h, history_1d, history_1m)
        except Exception as e:
            print(f"[{name}] erro no candle {current_time}: {e}")
            continue

        total_evaluated += 1
        gates = strategy.last_gates or []

        # Track funnel order (primeira vez que vê um gate)
        for g in gates:
            if g["name"] not in funnel_order:
                funnel_order.append(g["name"])

        # Contagem
        for g in gates:
            if g["passed"]:
                gate_pass_count[g["name"]] += 1
            else:
                gate_fail_count[g["name"]] += 1
                gate_fail_reasons[g["name"]][g["reason"]] += 1

        # Signal
        if signal is not None:
            signals.append({
                "timestamp": current_time,
                "action": signal.action,
                "entry": signal.entry_price,
                "sl": signal.stop_loss,
                "tp": signal.take_profit,
            })

        # Near-miss: passou >=80% dos gates aplicados mas falhou
        if gates and signal is None:
            passed = sum(1 for g in gates if g["passed"])
            total = len(gates)
            if total > 0 and passed / total >= 0.8 and total >= 4:
                failed_gate = next((g for g in gates if not g["passed"]), None)
                near_miss.append({
                    "timestamp": current_time,
                    "passed_count": passed,
                    "total_gates": total,
                    "failed_gate": failed_gate["name"] if failed_gate else "?",
                    "failed_reason": failed_gate["reason"] if failed_gate else "",
                })

    return {
        "name": name,
        "total_evaluated": total_evaluated,
        "funnel_order": funnel_order,
        "gate_pass_count": dict(gate_pass_count),
        "gate_fail_count": dict(gate_fail_count),
        "gate_fail_reasons": {k: dict(v) for k, v in gate_fail_reasons.items()},
        "signals": signals,
        "near_miss": near_miss,
        "data_range": (df_5m.index.min(), df_5m.index.max()),
        "candles_total": len(df_5m),
    }


def write_report(result: dict, output_path: Path):
    name = result["name"]
    funnel = result["funnel_order"]
    pass_c = result["gate_pass_count"]
    fail_c = result["gate_fail_count"]
    reasons = result["gate_fail_reasons"]

    total = result["total_evaluated"]

    lines = []
    lines.append(f"# Relatório Funil — {name}")
    lines.append("")
    lines.append(f"**Período analisado:** {result['data_range'][0]} → {result['data_range'][1]}")
    lines.append(f"**Candles M5 totais:** {result['candles_total']}")
    lines.append(f"**Candles avaliados (após warmup 50):** {total}")
    lines.append(f"**Sinais gerados:** {len(result['signals'])}")
    lines.append("")

    # --- Funnel table ---
    lines.append("## Funil de Gates (ordem de avaliação)")
    lines.append("")
    lines.append("| # | Gate | Avaliados | Passaram | Falharam | % Pass |")
    lines.append("|---|---|---:|---:|---:|---:|")

    for idx, gate in enumerate(funnel, 1):
        p = pass_c.get(gate, 0)
        f = fail_c.get(gate, 0)
        evaluated = p + f
        pct = (p / evaluated * 100) if evaluated > 0 else 0.0
        lines.append(f"| {idx} | `{gate}` | {evaluated} | {p} | {f} | {pct:.1f}% |")

    lines.append("")

    # --- Top killers ---
    lines.append("## Top 5 Gates que mais mataram sinais")
    lines.append("")
    sorted_killers = sorted(fail_c.items(), key=lambda x: -x[1])[:5]
    if sorted_killers:
        lines.append("| Rank | Gate | Falhas | % do total |")
        lines.append("|---|---|---:|---:|")
        for rank, (gate, count) in enumerate(sorted_killers, 1):
            pct = count / total * 100 if total > 0 else 0
            lines.append(f"| {rank} | `{gate}` | {count} | {pct:.1f}% |")
    lines.append("")

    # --- Reasons breakdown ---
    lines.append("## Motivos de Falha (top 3 por gate)")
    lines.append("")
    for gate in funnel:
        if fail_c.get(gate, 0) == 0:
            continue
        lines.append(f"### `{gate}` ({fail_c[gate]} falhas)")
        top_reasons = sorted(reasons.get(gate, {}).items(), key=lambda x: -x[1])[:3]
        for reason, count in top_reasons:
            r = reason if reason else "(sem motivo)"
            lines.append(f"- {count}x: {r}")
        lines.append("")

    # --- Near-miss ---
    nm = result["near_miss"]
    lines.append(f"## Near-misses (passaram >=80% dos gates) — {len(nm)} candles")
    lines.append("")
    if nm:
        lines.append("| Timestamp | Gates passados | Gate que matou | Motivo |")
        lines.append("|---|---:|---|---|")
        for entry in nm[:30]:  # top 30 mais recentes
            ts = entry["timestamp"]
            lines.append(f"| {ts} | {entry['passed_count']}/{entry['total_gates']} | `{entry['failed_gate']}` | {entry['failed_reason']} |")
    lines.append("")

    # --- Signals ---
    lines.append(f"## Sinais Gerados ({len(result['signals'])})")
    lines.append("")
    if result["signals"]:
        lines.append("| Timestamp | Ação | Entry | SL | TP |")
        lines.append("|---|---|---:|---:|---:|")
        for s in result["signals"]:
            lines.append(f"| {s['timestamp']} | {s['action']} | {s['entry']:.2f} | {s['sl']:.2f} | {s['tp']:.2f} |")
    else:
        lines.append("_Zero sinais. Veja seção 'Top 5 Gates' pra identificar onde calibrar._")
    lines.append("")

    # --- Recommendation ---
    lines.append("## Recomendação de Calibração")
    lines.append("")
    if sorted_killers:
        top = sorted_killers[0]
        lines.append(f"**Gate mais letal:** `{top[0]}` ({top[1]} falhas)")
        lines.append("")
        lines.append("Próximo passo sugerido:")
        lines.append(f"1. Relaxar/remover gate `{top[0]}` temporariamente")
        lines.append(f"2. Re-rodar este diagnóstico")
        lines.append(f"3. Se sample chegar a >=30 sinais, rodar backtest e medir PF")
        lines.append(f"4. Se PF ainda fraco, voltar e calibrar gate com critério mais inteligente")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    print("=" * 60)
    print(" DIAGNOSTICO FUNIL DAS ESTRATEGIAS ICT")
    print("=" * 60)

    loader = DataLoader()

    # Tentar pegar o range máximo disponível nos parquets
    # Os dados em cache cobrem ~25-30 dias (abr-mai 2026)
    start_date = "2026-04-19"
    end_date = "2026-05-19"

    print(f"\nPeriodo: {start_date} -> {end_date}")
    print()

    # Pre-loading data
    nq_data = load_multi_tf(loader, "I:NDX", start_date, end_date)
    xau_data = load_multi_tf(loader, "C:XAUUSD", start_date, end_date)

    # 1. London Session Sweeps
    print("[1/8] London Sweep (XAUUSD)...")
    if not xau_data["5m"].empty:
        ls_xau = LondonSweepXAU(LondonSweepConfig())
        res = diagnose_strategy(ls_xau, xau_data, "London Sweep XAU")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_london_sweep_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n[2/8] London Sweep (NDX)...")
    if not nq_data["5m"].empty:
        ls_nq = LondonSweepNQ(LondonSweepNQConfig())
        res = diagnose_strategy(ls_nq, nq_data, "London Sweep NQ")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_london_sweep_nq_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    # 2. Silver Bullet NQ Sessions
    print("\n[3/8] Silver Bullet NQ — NY AM...")
    if not nq_data["5m"].empty:
        sb_nq_am = make_sb_nq_am()
        res = diagnose_strategy(sb_nq_am, nq_data, "Silver Bullet NQ — NY AM")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_nq_am_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n[4/8] Silver Bullet NQ — NY Lunch...")
    if not nq_data["5m"].empty:
        sb_nq_lunch = make_sb_nq_lunch()
        res = diagnose_strategy(sb_nq_lunch, nq_data, "Silver Bullet NQ — NY Lunch")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_nq_lunch_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n[5/8] Silver Bullet NQ — NY Close...")
    if not nq_data["5m"].empty:
        sb_nq_close = make_sb_nq_close()
        res = diagnose_strategy(sb_nq_close, nq_data, "Silver Bullet NQ — NY Close")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_nq_close_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    # 3. Silver Bullet XAU Sessions
    print("\n[6/8] Silver Bullet XAU — NY AM...")
    if not xau_data["5m"].empty:
        sb_xau_am = make_sb_xau_am()
        res = diagnose_strategy(sb_xau_am, xau_data, "Silver Bullet XAU — NY AM")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_xau_am_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n[7/8] Silver Bullet XAU — NY Lunch...")
    if not xau_data["5m"].empty:
        sb_xau_lunch = make_sb_xau_lunch()
        res = diagnose_strategy(sb_xau_lunch, xau_data, "Silver Bullet XAU — NY Lunch")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_xau_lunch_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n[8/8] Silver Bullet XAU — NY Close...")
    if not xau_data["5m"].empty:
        sb_xau_close = make_sb_xau_close()
        res = diagnose_strategy(sb_xau_close, xau_data, "Silver Bullet XAU — NY Close")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = REPORTS_DIR / f"funnel_silver_bullet_xau_close_{ts}.md"
        write_report(res, out_path)
        print(f"  -> {out_path}")
        print(f"  Sinais gerados: {len(res['signals'])}")
        if res["gate_fail_count"]:
            top = sorted(res["gate_fail_count"].items(), key=lambda x: -x[1])[0]
            print(f"  Top killer: {top[0]} ({top[1]} falhas)")

    print("\n" + "=" * 60)
    print(" Concluido. Veja relatorios em diagnostics/reports/")
    print("=" * 60)


if __name__ == "__main__":
    main()
