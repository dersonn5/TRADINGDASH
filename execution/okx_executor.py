"""
Executor de ordens OKX via CCXT.
Converte Signal (USD risk) → contratos OKX e coloca ordem limit.
"""
import ccxt
from execution.okx_client import OKXConfig, make_okx
from strategies.base import Signal

# face value em crypto por contrato OKX swap:
CONTRACT_FACE = {
    "BTC/USDT:USDT": 0.01,   # 1 ct = 0.01 BTC
    "ETH/USDT:USDT": 0.1,    # 1 ct = 0.1 ETH
    "SOL/USDT:USDT": 1.0,    # 1 ct = 1 SOL
}


class OKXExecutor:
    def __init__(self, config: OKXConfig, balance_usd: float, risk_pct: float = 0.01):
        self.exchange = make_okx(config, pro=False)
        self.balance = balance_usd
        self.risk_pct = risk_pct

    def _contracts(self, symbol: str, entry: float, sl: float) -> int:
        risk_usd = self.balance * self.risk_pct
        sl_dist = abs(entry - sl)
        if sl_dist == 0:
            return 1
        face = CONTRACT_FACE.get(symbol, 0.01)
        risk_per_contract = face * sl_dist
        return max(1, int(risk_usd / risk_per_contract))

    def execute(self, signal: Signal, symbol: str) -> dict:
        """Coloca ordem limit síncrona (REST). Retorna resposta CCXT."""
        side = "sell" if signal.action == "SELL" else "buy"
        amount = self._contracts(symbol, signal.entry_price, signal.stop_loss)
        params = {'tdMode': 'cross'}  # margem cruzada para swaps
        result = self.exchange.create_order(
            symbol=symbol,
            type="limit",
            side=side,
            amount=amount,
            price=signal.entry_price,
            params=params,
        )
        return result
