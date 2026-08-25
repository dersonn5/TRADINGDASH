"""
Broker — camada de execução (abstrata) + PaperBroker (simulação fiel ao backtest)
=================================================================================
Interface única p/ o engine. Hoje: PaperBroker (fills + gestão local, p/ forward
test sem dinheiro). Depois: NinjaTraderATI (mesma interface, manda ordem real).

Gestão replicada do backtest validado: entrada LIMIT (maker), parcial em partial_rr,
break-even, trailing após trigger. O engine só chama on_price(); o broker cuida do
ciclo de vida da posição e devolve eventos (fill, partial, exit) + pnl.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Callable


@dataclass
class ManagedPosition:
    symbol: str
    action: str            # BUY | SELL
    entry: float
    stop: float
    target: float
    size: float
    risk_usd: float
    opened: datetime
    init_risk: float = 0.0     # distância de preço inicial (p/ R)
    mfe: float = 0.0
    partial_done: bool = False
    realized: float = 0.0
    point_value: float = 1.0

    def __post_init__(self):
        self.init_risk = abs(self.entry - self.stop)
        self.mfe = self.entry


@dataclass
class MgmtParams:
    partial_rr: float = 2.0
    partial_pct: float = 0.5
    be_trigger_rr: float = 2.0
    trail_trigger_rr: float = 4.0
    trail_distance_rr: float = 1.5


class Broker:
    """Interface. NinjaTraderATI implementará os mesmos métodos."""
    def submit(self, signal, size, risk_usd, point_value) -> bool: ...
    def on_price(self, high, low, close, now) -> list: ...   # devolve eventos
    def has_position(self) -> bool: ...
    def flat(self, price, now) -> Optional[float]: ...       # fecha tudo, devolve pnl
    def realized_pnl(self) -> float: ...


class PaperBroker(Broker):
    def __init__(self, mgmt: MgmtParams = None, on_event: Callable = None,
                 fill_through_ticks: float = 1.0, tick_size: float = 0.25,
                 stop_slippage_ticks: float = 1.0):
        self.mgmt = mgmt or MgmtParams()
        self.pos: Optional[ManagedPosition] = None
        self.pending = None       # (signal, size, risk, pv) esperando fill LIMIT
        self._realized = 0.0
        self.on_event = on_event or (lambda e: None)
        # Realismo pessimista: ordem LIMIT só preenche se o preço ATRAVESSA (não só toca)
        # por N ticks; stop sofre slippage (fila de execução real, não instantâneo).
        self.fill_buffer = fill_through_ticks * tick_size
        self.stop_slip = stop_slippage_ticks * tick_size

    def realized_pnl(self) -> float:
        return self._realized

    def has_position(self) -> bool:
        return self.pos is not None or self.pending is not None

    def submit(self, signal, size, risk_usd, point_value) -> bool:
        if self.has_position():
            return False
        self.pending = (signal, size, risk_usd, point_value)
        self.on_event({"type": "pending", "symbol": signal.symbol, "side": signal.action,
                       "entry": signal.entry_price, "stop": signal.stop_loss, "tp": signal.take_profit})
        return True

    def _pnl(self, exit_price, size, pos) -> float:
        d = (exit_price - pos.entry) if pos.action == "BUY" else (pos.entry - exit_price)
        return d * size * pos.point_value

    def on_price(self, high, low, close, now) -> list:
        ev = []
        # 1) fill da ordem LIMIT pendente (maker)
        if self.pending is not None and self.pos is None:
            sig, size, risk, pv = self.pending
            # pessimista: exige atravessar o preço por 1 tick (fila de execução real)
            filled = (sig.action == "BUY" and low <= sig.entry_price - self.fill_buffer) or \
                     (sig.action == "SELL" and high >= sig.entry_price + self.fill_buffer)
            if filled:
                self.pos = ManagedPosition(sig.symbol, sig.action, sig.entry_price, sig.stop_loss,
                                           sig.take_profit, size, risk, now, point_value=pv)
                self.pending = None
                ev.append({"type": "fill", "symbol": sig.symbol, "side": sig.action, "price": sig.entry_price})
                self.on_event(ev[-1])

        p = self.pos
        if p is None:
            return ev
        is_buy = p.action == "BUY"
        # MFE + R corrente
        p.mfe = max(p.mfe, high) if is_buy else min(p.mfe, low)
        r_now = ((p.mfe - p.entry) if is_buy else (p.entry - p.mfe)) / p.init_risk if p.init_risk > 0 else 0

        # parcial + move BE no resto
        if not p.partial_done and r_now >= self.mgmt.partial_rr:
            part_price = p.entry + p.init_risk * self.mgmt.partial_rr if is_buy \
                else p.entry - p.init_risk * self.mgmt.partial_rr
            part_size = p.size * self.mgmt.partial_pct
            pnl = self._pnl(part_price, part_size, p)
            p.realized += pnl; self._realized += pnl
            p.size -= part_size; p.partial_done = True
            if (is_buy and p.stop < p.entry) or (not is_buy and p.stop > p.entry):
                p.stop = p.entry
            ev.append({"type": "partial", "price": part_price, "pnl": pnl})
            self.on_event(ev[-1])

        # break-even
        if r_now >= self.mgmt.be_trigger_rr:
            if is_buy and p.stop < p.entry: p.stop = p.entry
            elif not is_buy and p.stop > p.entry: p.stop = p.entry

        # trailing após trigger
        if r_now >= self.mgmt.trail_trigger_rr:
            dist = p.init_risk * self.mgmt.trail_distance_rr
            if is_buy:
                p.stop = max(p.stop, p.mfe - dist)
            else:
                p.stop = min(p.stop, p.mfe + dist)

        # saídas: stop OU target (intrabar: stop primeiro = conservador)
        hit_stop = (is_buy and low <= p.stop) or (not is_buy and high >= p.stop)
        hit_tp = (is_buy and high >= p.target) or (not is_buy and low <= p.target)
        exit_price = None
        if hit_stop:
            # slippage pessimista: stop preenche PIOR que o nível (fila real de execução)
            exit_price = p.stop - self.stop_slip if is_buy else p.stop + self.stop_slip
        elif hit_tp:
            exit_price = p.target
        if exit_price is not None:
            pnl = self._pnl(exit_price, p.size, p)
            p.realized += pnl; self._realized += pnl
            ev.append({"type": "exit", "price": exit_price, "pnl": p.realized,
                       "reason": "stop" if hit_stop else "target"})
            self.on_event(ev[-1])
            self.pos = None
        return ev

    def unrealized(self, price) -> float:
        if self.pos is None:
            return 0.0
        return self._pnl(price, self.pos.size, self.pos)

    def flat(self, price, now) -> Optional[float]:
        if self.pos is None:
            self.pending = None
            return None
        pnl = self._pnl(price, self.pos.size, self.pos)
        self.pos.realized += pnl; self._realized += pnl
        r = self.pos.realized
        self.on_event({"type": "flat", "price": price, "pnl": r})
        self.pos = None
        return r
