"""
Backtest Cripto LONGO com o SEGUNDO CÉREBRO
============================================
Roda as estratégias ICT mecânicas (Silver Bullet / Breaker Block / Prop Firm)
sobre 2022-2024 e submete CADA sinal ao segundo cérebro (regras ICT destiladas)
via LLM LOCAL (Ollama). Compara:

  RAW      = todos os sinais mecânicos
  BRAIN    = só os sinais que o segundo cérebro aprovou

Saída: tabela comparativa por setup + relatório consolidado em
backtesting/reports/brain_backtest_<timestamp>.{md,json}

Uso:
    python run_crypto_backtest_brain.py                       # suite padrão, 2022-2024
    python run_crypto_backtest_brain.py --start 2023-01-01 --end 2024-12-31
    python run_crypto_backtest_brain.py --symbols BTC/USDT:USDT --strategies silver_bullet
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import config
from data.data_loader import DataLoader
from backtesting.engine import BacktestEngine, BacktestConfig
from backtesting.metrics import PerformanceMetrics
from strategies.silver_bullet_crypto import SilverBulletCrypto, SilverBulletCryptoConfig
from strategies.breaker_block_crypto import BreakerBlockCrypto, BreakerBlockCryptoConfig
from strategies.prop_firm_2024_crypto import PropFirm2024Crypto, PropFirm2024CryptoConfig
from strategies.ote_crypto import OTECrypto, OTECryptoConfig
from strategies.fvg_crypto import FVGCrypto, FVGCryptoConfig
from strategies.turtle_soup_crypto import TurtleSoupCrypto, TurtleSoupCryptoConfig
from strategies.judas_swing_crypto import JudasSwingCrypto, JudasSwingCryptoConfig
from strategies.po3_crypto import PowerOfThreeCrypto, PowerOfThreeCryptoConfig
from strategies.unicorn_crypto import UnicornCrypto, UnicornCryptoConfig
from strategies.mmxm_crypto import MMXMCrypto, MMXMCryptoConfig
from strategies.london_sweep_crypto import LondonSweepCrypto, LondonSweepCryptoConfig
from strategies.ict_topdown_crypto import ICTTopDownCrypto, ICTTopDownConfig
from core.brain_filter import BrainFilter

ALL_STRATEGIES = ["breaker_block", "silver_bullet", "ote", "fvg", "turtle_soup",
                  "judas_swing", "po3", "unicorn", "mmxm", "london_sweep"]

REPORTS_DIR = Path(__file__).resolve().parent / "backtesting" / "reports"


def build_strategy(symbol: str, strategy: str):
    # Configs tunadas por frequência empírica (probe 2024, alvo >=4 trades/mês):
    #   breaker_block STRICT  -> 6-8/mês (cavalo de batalha)
    #   silver_bullet RELAXED -> 2.2/mês (gates opcionais off p/ subir amostra)
    other = "BTC/USDT:USDT" if symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    if strategy == "silver_bullet":
        s = SilverBulletCrypto(SilverBulletCryptoConfig(
            min_sl_distance_percent=0.005, min_rr=1.5,
            require_daily_bias=False, require_premium_discount=False, require_smt=False))
    elif strategy == "breaker_block":
        s = BreakerBlockCrypto(BreakerBlockCryptoConfig(
            min_sl_distance_percent=0.005, sl_buffer_percent=0.001, min_rr=2.0,
            require_daily_bias=True, require_sweep=True))
    elif strategy == "prop_firm_2024":
        s = PropFirm2024Crypto(PropFirm2024CryptoConfig(
            min_sl_distance_percent=0.005, sl_buffer_percent=0.001, min_rr=2.0,
            require_daily_bias=False))
    elif strategy == "ote":
        s = OTECrypto(OTECryptoConfig())
    elif strategy == "fvg":
        s = FVGCrypto(FVGCryptoConfig())
    elif strategy == "turtle_soup":
        s = TurtleSoupCrypto(TurtleSoupCryptoConfig())
    elif strategy == "judas_swing":
        s = JudasSwingCrypto(JudasSwingCryptoConfig())
    elif strategy == "po3":
        s = PowerOfThreeCrypto(PowerOfThreeCryptoConfig())
    elif strategy == "unicorn":
        s = UnicornCrypto(UnicornCryptoConfig())
    elif strategy == "mmxm":
        s = MMXMCrypto(MMXMCryptoConfig())
    elif strategy == "london_sweep":
        s = LondonSweepCrypto(LondonSweepCryptoConfig())
    elif strategy == "ict_topdown":
        s = ICTTopDownCrypto(ICTTopDownConfig())
    else:
        raise ValueError(f"strategy desconhecida: {strategy}")
    s.name = f"{strategy}_crypto_{symbol.split('/')[0].lower()}"
    s.symbol = symbol
    s.correlated_symbol = other
    return s


def load_candles(loader: DataLoader, symbol: str, start: str, end: str, need_1m: bool = False):
    c5 = loader.load_data(symbol, "5m", start, end)
    c1d = loader.load_data(symbol, "1d", start, end)
    if c5.empty or c1d.empty:
        return None
    c15 = c5.resample("15min").agg({"open": "first", "high": "max", "low": "min",
                                    "close": "last", "volume": "sum"}).dropna()
    c1h = c5.resample("1h").agg({"open": "first", "high": "max", "low": "min",
                                 "close": "last", "volume": "sum"}).dropna()
    c1m = None
    if need_1m:
        try:
            c1m = loader.load_data(symbol, "1m", start, end)
            if c1m is not None and c1m.empty:
                c1m = None
        except Exception:
            c1m = None
    return c5, c15, c1h, c1d, c1m


def metrics_block(positions, initial=10000.0):
    return PerformanceMetrics.calculate(positions, initial)


def run_setup(loader, brain, symbol, strategy, start, end, mechanical_only=False):
    print(f"\n{'='*64}\n  {symbol} | {strategy.upper()} | {start} -> {end}\n{'='*64}")
    need_1m = strategy in ("ict_topdown",)
    data = load_candles(loader, symbol, start, end, need_1m=need_1m)
    if data is None:
        print(f"[SKIP] sem dados para {symbol}")
        return None
    c5, c15, c1h, c1d, c1m = data
    if need_1m and c1m is None:
        print(f"[SKIP] {strategy} precisa de 1m e não há dados 1m para {symbol}")
        return None

    corr = "BTC/USDT:USDT" if symbol == "ETH/USDT:USDT" else "ETH/USDT:USDT"
    try:
        c5_corr = loader.load_data(corr, "5m", start, end)
    except Exception:
        c5_corr = None

    strat = build_strategy(symbol, strategy)
    tick = 0.1 if symbol == "BTC/USDT:USDT" else 0.01
    engine = BacktestEngine(BacktestConfig(
        initial_balance=10000.0, slippage_ticks=1, spread_ticks=1,
        commission_usd=1.0, tick_size=tick, point_value=1.0,
        enable_partials=True, partial_rr=2.0, partial_pct=0.5,
        enable_break_even=True, break_even_trigger_rr=2.0,
        enable_trailing=True, trail_trigger_rr=4.0, trail_distance_rr=1.5))

    result = engine.run(strategy=strat, candles_5m=c5, candles_15m=c15, candles_1h=c1h,
                        candles_1d=c1d, candles_1m=c1m, use_filters=False,
                        candles_5m_corr=c5_corr)
    positions = result["positions"]
    raw_m = metrics_block(positions)

    if mechanical_only:
        print(f"[MECÂNICO] {len(positions)} sinais | win={raw_m['win_rate']:.1f}% "
              f"PF={raw_m['profit_factor']:.2f} PnL={raw_m['total_pnl_usd']:+.0f} "
              f"maxDD={raw_m['max_drawdown_percent']:.1f}%")
        return {"symbol": symbol, "strategy": strategy, "start": start, "end": end,
                "raw": raw_m, "brain": metrics_block([]), "approved": 0, "rejected": len(positions)}

    print(f"[MECÂNICO] {len(positions)} sinais gerados. Filtrando pelo segundo cérebro...")
    frames = (c5, c15, c1h, c1d)
    approved, rejected = [], []
    for i, pos in enumerate(positions, 1):
        ctx = brain.compute_context(pos, frames)
        dec = brain.evaluate(pos, symbol, strategy, context=ctx)
        if dec["approved"]:
            approved.append(pos)
        else:
            rejected.append(pos)
        if i % 20 == 0 or i == len(positions):
            print(f"  ...{i}/{len(positions)} avaliados | aprovados={len(approved)} rejeitados={len(rejected)}")

    brn_m = metrics_block(approved)

    print(f"\n  {'MÉTRICA':<22}{'RAW':>16}{'BRAIN':>16}")
    print(f"  {'-'*54}")
    print(f"  {'Trades':<22}{raw_m['total_trades']:>16}{brn_m['total_trades']:>16}")
    print(f"  {'Win rate %':<22}{raw_m['win_rate']:>16.1f}{brn_m['win_rate']:>16.1f}")
    print(f"  {'Profit factor':<22}{raw_m['profit_factor']:>16.2f}{brn_m['profit_factor']:>16.2f}")
    print(f"  {'PnL líquido USD':<22}{raw_m['total_pnl_usd']:>16.2f}{brn_m['total_pnl_usd']:>16.2f}")
    print(f"  {'Max drawdown %':<22}{raw_m['max_drawdown_percent']:>16.1f}{brn_m['max_drawdown_percent']:>16.1f}")
    print(f"  {'Expectancy USD':<22}{raw_m['expectancy_usd']:>16.2f}{brn_m['expectancy_usd']:>16.2f}")

    return {
        "symbol": symbol, "strategy": strategy, "start": start, "end": end,
        "raw": raw_m, "brain": brn_m,
        "approved": len(approved), "rejected": len(rejected),
    }


def save_report(results, start, end):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = REPORTS_DIR / f"brain_backtest_{ts}.json"
    md_path = REPORTS_DIR / f"brain_backtest_{ts}.md"

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    lines = [f"# Backtest Cripto com Segundo Cérebro", f"> Período: {start} → {end} | Gerado: {ts}", "",
             "Comparação: **RAW** (sinais mecânicos) vs **BRAIN** (aprovados pelo segundo cérebro ICT via Ollama local).", "",
             "| Setup | Trades RAW→BRAIN | Win% RAW→BRAIN | PF RAW→BRAIN | PnL RAW→BRAIN |",
             "|---|---|---|---|---|"]
    for r in results:
        if not r:
            continue
        rm, bm = r["raw"], r["brain"]
        lines.append(
            f"| {r['symbol'].split('/')[0]} {r['strategy']} "
            f"| {rm['total_trades']}→{bm['total_trades']} "
            f"| {rm['win_rate']:.1f}→{bm['win_rate']:.1f} "
            f"| {rm['profit_factor']:.2f}→{bm['profit_factor']:.2f} "
            f"| {rm['total_pnl_usd']:+.0f}→{bm['total_pnl_usd']:+.0f} |")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[RELATÓRIO] {md_path}\n[RELATÓRIO] {json_path}")
    return md_path


def main():
    ap = argparse.ArgumentParser(description="Backtest cripto longo com segundo cérebro (Ollama).")
    ap.add_argument("--symbols", type=str, default="BTC/USDT:USDT,ETH/USDT:USDT")
    ap.add_argument("--strategies", type=str, default=",".join(ALL_STRATEGIES))
    ap.add_argument("--start", type=str, default="2022-01-01")
    ap.add_argument("--end", type=str, default="2024-12-31")
    ap.add_argument("--mechanical-only", action="store_true",
                    help="Só métricas mecânicas (rápido, sem LLM) — para validar/poder estratégias.")
    args = ap.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    strategies = [s.strip() for s in args.strategies.split(",") if s.strip()]

    print("="*64)
    print("  BACKTEST CRIPTO LONGO — SEGUNDO CÉREBRO (Ollama local)")
    print(f"  Símbolos: {symbols}")
    print(f"  Estratégias: {strategies}")
    print(f"  Período: {args.start} -> {args.end}")
    print("="*64)

    brain = None
    if not args.mechanical_only:
        brain = BrainFilter()
        if not brain.available():
            print("[ERRO] Ollama offline. Inicie o servidor (ollama serve) e tente de novo.")
            sys.exit(1)

    loader = DataLoader()
    results = []
    for symbol in symbols:
        for strategy in strategies:
            try:
                results.append(run_setup(loader, brain, symbol, strategy, args.start, args.end,
                                         mechanical_only=args.mechanical_only))
            except Exception as e:
                import traceback
                print(f"[ERRO] {symbol}/{strategy}: {e}")
                traceback.print_exc()

    save_report(results, args.start, args.end)
    print("\n[OK] Backtest com segundo cérebro concluído.")


if __name__ == "__main__":
    main()
