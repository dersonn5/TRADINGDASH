from typing import Optional, Dict
from strategies.base import Signal, Position
from datetime import datetime

class OrderManager:
    """
    Gerenciador de Execução de Ordens (Order Manager).
    Controla o ciclo de vida completo de ordens limit, de stop loss, take profit,
    parciais de saída e encerramento de posições ativas.
    """
    def __init__(self):
        self.active_positions: Dict[str, Position] = {}
        self.pending_orders: Dict[str, Signal] = {}

    def place_pending_order(self, symbol: str, signal: Signal):
        """Registra uma ordem pendente (Limit Order) na killzone."""
        print(f"[ORDER MANAGER] Ordem pendente posicionada para {symbol}: {signal.action} @ {signal.entry_price:.2f}")
        self.pending_orders[symbol] = signal

    def cancel_pending_order(self, symbol: str):
        """Cancela uma ordem pendente não preenchida."""
        if symbol in self.pending_orders:
            order = self.pending_orders.pop(symbol)
            print(f"[ORDER MANAGER] Ordem pendente CANCELADA para {symbol}: {order.action} @ {order.entry_price:.2f}")

    def execute_fill(self, symbol: str, fill_price: float, size: float) -> Optional[Position]:
        """Transforma a ordem pendente em uma posição aberta (Fill)."""
        if symbol not in self.pending_orders:
            return None
            
        signal = self.pending_orders.pop(symbol)
        
        position = Position(
            symbol=symbol,
            action=signal.action,
            entry_price=fill_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            size_units=size,
            entry_time=datetime.now(),
            status="OPEN"
        )
        
        self.active_positions[symbol] = position
        print(f"[ORDER MANAGER] [FILL] Ordem preenchida! {symbol} {position.action} Lote {size:.2f} @ {fill_price:.2f}")
        return position

    def close_position(self, symbol: str, exit_price: float, reason: str) -> Optional[Position]:
        """Fecha uma posição ativa no mercado."""
        if symbol not in self.active_positions:
            return None
            
        position = self.active_positions.pop(symbol)
        position.status = "CLOSED"
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        
        # Calcular P&L final
        # 1. Ponto do Nasdaq = $20, Ponto do Ouro = $100, Cripto (par com '/' ou ':') = $1.0
        is_crypto = "/" in symbol or ":" in symbol
        if is_crypto:
            point_value = 1.0
        else:
            point_value = 20.0 if "NQ" in symbol.upper() else 100.0
        
        if position.action == "BUY":
            gross_pnl = (exit_price - position.entry_price) * position.size_units * point_value
        else:
            gross_pnl = (position.entry_price - exit_price) * position.size_units * point_value
            
        # Comissão: se for crypto, aplicar taxas reais da Binance Futures (ex: 0.04% taker por transação)
        if is_crypto:
            # 0.04% na entrada + 0.04% na saída = 0.08% do valor total nocional
            entry_value = position.entry_price * position.size_units
            exit_value = exit_price * position.size_units
            commission = (entry_value + exit_value) * 0.0004
        else:
            commission = 2.0  # Comissão simulada padrão para futuros tradicionais
            
        position.pnl_usd = gross_pnl - commission
        position.reason = reason
        
        print(f"[ORDER MANAGER] [CLOSE] Posição fechada para {symbol}! Motivo: {reason} | P&L Bruto: ${gross_pnl:.2f} | Taxa: ${commission:.2f} | P&L Líquido: ${position.pnl_usd:.2f}")
        return position

