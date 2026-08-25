"""
AccountRunner — 1 conta = motor + broker + compliance + fase
=============================================================
Encapsula o ciclo por vela 5m FECHADA:
  1. atualiza equity (realized + unrealized) e alimenta o compliance
  2. gerencia posição aberta (broker.on_price)
  3. se flat E pode operar (compliance) → roda o motor → Signal → ordem LIMIT
  4. sizing = risco_alvo / distância_do_stop (respeita o teto do kill-switch)

Multi-conta = várias instâncias, cada uma com seu motor/mercado (streams distintos,
compliant Bulenox — nada de copy). Mesmo código roda replay (forward/paper) e live.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from executor.broker import PaperBroker, MgmtParams
from executor.compliance import ComplianceGuard, FirmRules


@dataclass
class AccountConfig:
    name: str
    symbol: str                 # NAS/USD, SPX/USD...
    point_value: float          # valor do ponto (real da corretora)
    risk_usd: float             # risco alvo por trade ($200 eval / $150 funded)
    phase: str = "eval"         # eval | funded
    corr_symbol: Optional[str] = None
    tick_size: float = 0.25


class AccountRunner:
    def __init__(self, cfg: AccountConfig, strategy, mgmt: MgmtParams = None,
                 rules: FirmRules = None, on_event=None):
        self.cfg = cfg
        self.strategy = strategy
        self.guard = ComplianceGuard(rules=rules or FirmRules(), phase=cfg.phase,
                                     start_balance=(rules or FirmRules()).account_size,
                                     peak_equity=(rules or FirmRules()).account_size,
                                     day_start_equity=(rules or FirmRules()).account_size)
        self.broker = PaperBroker(mgmt=mgmt, on_event=self._ev, tick_size=cfg.tick_size,
                                  fill_through_ticks=1.0, stop_slippage_ticks=1.0)
        self.start_balance = self.guard.start_balance
        self._cb = on_event or (lambda name, e: None)
        self.trades = 0
        self.last_day = None

    def _ev(self, e):
        self._cb(self.cfg.name, e)
        if e.get("type") in ("exit", "flat"):
            self.trades += 1
            self.guard.register_trade(e.get("pnl", 0.0))

    def equity(self, price) -> float:
        return self.start_balance + self.broker.realized_pnl() + self.broker.unrealized(price)

    def on_bar(self, ohlc_5m, now: datetime, feeds: dict):
        """ohlc_5m=(o,h,l,c) da vela fechada. feeds=dfs até agora p/ o motor."""
        o, h, l, c = ohlc_5m
        # reset diário
        d = now.date()
        if self.last_day is not None and d != self.last_day:
            self.guard.close_day()
        self.last_day = d

        # INTRABAR (trailing DD é real-time): pico pelo lado FAVORÁVEL, floor pelo ADVERSO.
        # Se há posição aberta, o pior preço da vela pode violar o floor mesmo fechando ok.
        if self.broker.has_position() and self.broker.pos is not None:
            adverse = l if self.broker.pos.action == "BUY" else h
            favor = h if self.broker.pos.action == "BUY" else l
            self.guard.on_equity(self.equity(favor))    # pico primeiro (sobe o trailing)
            self.guard.on_equity(self.equity(adverse))  # depois o pior (testa o floor)
        else:
            self.guard.on_equity(self.equity(c))

        # gerencia posição / fills
        self.broker.on_price(h, l, c, now)
        eq = self.equity(c)
        self.guard.on_equity(eq)

        if self.guard.blown or (self.guard.passed and self.cfg.phase == "eval"):
            return

        # cutoff: fecha tudo
        if now.time() >= self.guard.rules.flat_by:
            if self.broker.has_position():
                self.broker.flat(c, now)
            return

        # só busca setup se flat
        if self.broker.has_position():
            return
        ok, why = self.guard.can_trade(eq, now.time())
        if not ok:
            return

        sig = self._eval_strategy(feeds)
        if sig is None or sig.action not in ("BUY", "SELL"):
            return

        stop_dist = abs(sig.entry_price - sig.stop_loss)
        if stop_dist <= 0:
            return
        # sizing: risco alvo, mas nunca acima do teto do kill-switch (metade do room)
        risk_cap = self.guard.max_risk_usd(eq, frac_of_room=0.5)
        risk = min(self.cfg.risk_usd, risk_cap)
        if risk <= 0:
            return
        # Futuros = contratos INTEIROS. floor (nunca arredonda p/ cima o risco).
        raw_size = risk / (stop_dist * self.cfg.point_value)
        size = float(int(raw_size))
        if size < 1:
            self._cb(self.cfg.name, {"type": "skip", "reason":
                     f"stop largo demais p/ 1 contrato (precisaria {raw_size:.2f})"})
            return
        actual_risk = size * stop_dist * self.cfg.point_value
        self.broker.submit(sig, size, actual_risk, self.cfg.point_value)

    def _eval_strategy(self, feeds: dict):
        try:
            if feeds.get("5m_corr") is not None:
                self.strategy.correlated_data = feeds["5m_corr"]
            return self.strategy.evaluate(
                candles_5m=feeds["5m"], candles_15m=feeds.get("15m", feeds["5m"]),
                candles_1h=feeds["1h"], candles_1d=feeds["1d"], candles_1m=feeds.get("1m"))
        except Exception as ex:
            self._cb(self.cfg.name, {"type": "error", "msg": str(ex)[:120]})
            return None

    def summary(self, price) -> dict:
        eq = self.equity(price)
        return {"name": self.cfg.name, "phase": self.cfg.phase, "equity": round(eq, 2),
                "pnl": round(eq - self.start_balance, 2), "trades": self.trades,
                "passed": self.guard.passed, "blown": self.guard.blown,
                "peak": round(self.guard.peak_equity, 2), "floor": round(self.guard.floor(), 2)}
