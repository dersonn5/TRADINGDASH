"""Robustez temporal do NQ (walk-forward por blocos, com SMT vs S&P)."""
import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try: sys.stdout.reconfigure(encoding="utf-8")
    except Exception: pass
from research.backtest_nq import run  # reusa o runner NQ (SMT vs S&P)

BLOCKS = [("2022-01-01","2022-06-30"),("2022-07-01","2022-12-31"),
          ("2023-01-01","2023-06-30"),("2023-07-01","2023-12-31"),
          ("2024-01-01","2024-06-30"),("2024-07-01","2024-12-31")]

def main():
    print("="*60); print("  ROBUSTEZ NQ (walk-forward, SMT vs S&P, maker fee)"); print("="*60)
    print(f"  {'BLOCO':<20}{'trades':>7}{'win%':>7}{'PF':>7}{'PnL':>9}{'DD%':>7}")
    pos=0; tot=0
    for s,e in BLOCKS:
        try: m=run(s,e)
        except Exception as ex: print(f"  [ERRO] {s}: {str(ex)[:50]}"); continue
        print(f"  {s[:7]+'..'+e[5:7]:<20}{m['total_trades']:>7}{m['win_rate']:>7.1f}{m['profit_factor']:>7.2f}{m['total_pnl_usd']:>+9.0f}{m['max_drawdown_percent']:>7.1f}")
        tot+=1; pos+= 1 if (m['profit_factor']>1 and m['total_pnl_usd']>0) else 0
    print(f"\n  Blocos positivos: {pos}/{tot} ({100*pos/max(1,tot):.0f}%)")
    print("  " + ("ROBUSTO" if pos/max(1,tot)>=0.7 else "PARCIAL" if pos/max(1,tot)>=0.5 else "FRAGIL"))

if __name__=="__main__": main()
