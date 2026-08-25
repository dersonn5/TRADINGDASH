"""
ComplianceGuard — regras da prop firm (Bulenox 25k) que BLINDAM a conta
========================================================================
Antes de QUALQUER ordem, o guard decide se pode operar. Objetivo #1: nunca
violar o trailing drawdown (é o que mata a conta). Modela Bulenox Option 1:

  - Trailing DD: floor = pico_de_equity - trailing_amount ($1500 no 25k).
    Real-time (intraday). Se equity <= floor → conta QUEBRADA.
  - Sem daily loss limit (Option 1).
  - Alvo da eval: +profit_target ($1500). Bateu → aprovado.
  - Consistência 40% (só na Master/funded): nenhum dia > 40% do lucro total.
    Não bloqueia trade — pausa payout. Guard só AVISA.
  - Cutoff: fecha tudo até flat_by (15:59 CST). Sem overnight.
  - KILL-SWITCH: para de operar no dia se equity chega a buffer do floor
    (não encosta no DD — margem de segurança).

Tudo em USD sobre o saldo da conta. O guard não sabe de estratégia — só de risco.
"""
from dataclasses import dataclass, field
from datetime import time
from typing import Optional


@dataclass
class FirmRules:
    account_size: float = 25000.0
    trailing_dd: float = 1500.0        # Bulenox 25k
    profit_target: float = 1500.0
    daily_loss_limit: Optional[float] = None   # Option 1 = None
    consistency_pct: float = 0.40      # 40% (Master apenas)
    flat_by: time = time(15, 59)       # CST — fecha tudo
    safety_buffer: float = 300.0       # kill-switch: para se faltar < isso p/ o floor


@dataclass
class ComplianceGuard:
    rules: FirmRules = field(default_factory=FirmRules)
    phase: str = "eval"                # "eval" | "funded"
    start_balance: float = 25000.0
    peak_equity: float = 25000.0       # pico p/ trailing (real-time)
    day_start_equity: float = 25000.0
    day_profit_max: float = 0.0        # maior lucro isolado de um dia (consistência)
    day_pnls: list = field(default_factory=list)
    blown: bool = False
    passed: bool = False
    halted_today: bool = False

    def floor(self) -> float:
        """Nível de morte: pico - trailing. Nunca deixar equity encostar."""
        return self.peak_equity - self.rules.trailing_dd

    def on_equity(self, equity: float):
        """Chamar a cada tick/vela com a equity atual (realized + unrealized)."""
        self.peak_equity = max(self.peak_equity, equity)
        if equity <= self.floor():
            self.blown = True
        if self.phase == "eval" and equity - self.start_balance >= self.rules.profit_target:
            self.passed = True

    def can_trade(self, equity: float, now_t: time) -> tuple[bool, str]:
        """Decisão dura antes de abrir posição."""
        if self.blown:
            return False, "CONTA QUEBRADA (trailing DD violado)"
        if self.passed and self.phase == "eval":
            return False, "EVAL JÁ APROVADA — parar de arriscar"
        if self.halted_today:
            return False, "kill-switch: halted no dia"
        if now_t >= self.rules.flat_by:
            return False, "após cutoff (flat_by)"
        # kill-switch: margem até o floor
        room = equity - self.floor()
        if room <= self.rules.safety_buffer:
            self.halted_today = True
            return False, f"kill-switch: só ${room:.0f} até o floor (buffer ${self.rules.safety_buffer:.0f})"
        return True, "ok"

    def room_to_floor(self, equity: float) -> float:
        return equity - self.floor()

    def max_risk_usd(self, equity: float, frac_of_room: float = 0.5) -> float:
        """Risco máx sugerido p/ o trade: fração do espaço até o floor (nunca all-in)."""
        return max(0.0, self.room_to_floor(equity) * frac_of_room)

    def register_trade(self, pnl: float):
        """Registra trade fechado (p/ consistência e reset diário)."""
        self.day_pnls.append(pnl)

    def close_day(self):
        """Fim do dia: agrega p/ consistência, reseta flags diárias."""
        day_total = sum(self.day_pnls)
        if day_total > 0:
            self.day_profit_max = max(self.day_profit_max, day_total)
        self.day_pnls = []
        self.halted_today = False

    def consistency_ok(self, total_profit: float) -> bool:
        """40%: nenhum dia isolado > 40% do lucro total (só Master)."""
        if self.phase != "funded" or total_profit <= 0:
            return True
        return self.day_profit_max <= self.rules.consistency_pct * total_profit

    def status(self, equity: float) -> str:
        prog = equity - self.start_balance
        tgt = self.rules.profit_target
        return (f"[{self.phase}] equity=${equity:.0f} pico=${self.peak_equity:.0f} "
                f"floor=${self.floor():.0f} room=${self.room_to_floor(equity):.0f} "
                f"| progresso ${prog:+.0f}/{tgt:.0f} "
                f"{'✅PASS' if self.passed else ''}{'💀BLOWN' if self.blown else ''}")
