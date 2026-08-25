"""
Executor de ordens Binance Futures via CCXT.
Converte Signal (USD risk) → contratos Binance e coloca ordem limit com Stop Loss e Take Profit.
"""
import asyncio
import ccxt
from execution.binance_client import BinanceConfig, make_binance
from strategies.base import Signal


class BinanceExecutor:
    def __init__(self, config: BinanceConfig, balance_usd: float, risk_pct: float = 0.01):
        self.exchange = make_binance(config, pro=False)
        self.balance = balance_usd
        self.risk_pct = risk_pct
        self.configured_symbols = set()

    async def _execute_with_retry(self, fn, *args, **kwargs):
        """Executa uma chamada CCXT com até 3 tentativas e backoff exponencial."""
        last_err = None
        delay = 1.0
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(fn, *args, **kwargs)
                return result
            except ccxt.RateLimitExceeded as e:
                print(f"[BinanceExecutor Retry] Rate limit excedido na tentativa {attempt+1}: {e}. Aguardando {delay * 2}s...")
                await asyncio.sleep(delay * 2)
                delay *= 2.0
                last_err = e
            except (ccxt.NetworkError, ccxt.ExchangeError) as e:
                err_msg = str(e).lower()
                # Se for erro que já está configurado, ignorar
                if "no need to change margin type" in err_msg or "leverage has not changed" in err_msg:
                    return {"ignored": True, "message": str(e)}
                
                # Se for erro fatal, propagar imediatamente
                if "insufficient balance" in err_msg or "balance is not enough" in err_msg or "reduceonly" in err_msg:
                    raise e
                    
                print(f"[BinanceExecutor Retry] Erro na tentativa {attempt+1}: {e}. Retentando em {delay}s...")
                await asyncio.sleep(delay)
                delay *= 2.0
                last_err = e
        raise last_err

    async def _configure_symbol_leverage_margin(self, symbol: str):
        """Configura a alavancagem e o modo de margem se ainda não feito nesta sessão."""
        if symbol in self.configured_symbols:
            return
            
        if not self.exchange.markets:
            await asyncio.to_thread(self.exchange.load_markets)
            
        # 1. Configurar alavancagem
        import config as app_config
        leverage = getattr(app_config, "BINANCE_LEVERAGE", 5)
        try:
            print(f"[BinanceExecutor] Configurando alavancagem de {leverage}x para {symbol}...")
            await self._execute_with_retry(self.exchange.set_leverage, leverage, symbol)
        except Exception as e:
            if "leverage has not changed" not in str(e).lower():
                print(f"[BinanceExecutor WARNING] Falha ao definir alavancagem para {symbol}: {e}")
                
        # 2. Configurar modo de margem
        margin_mode = getattr(app_config, "BINANCE_MARGIN_MODE", "cross").lower()
        try:
            print(f"[BinanceExecutor] Configurando modo de margem {margin_mode.upper()} para {symbol}...")
            await self._execute_with_retry(self.exchange.set_margin_mode, margin_mode, symbol)
        except Exception as e:
            if "no need to change margin type" not in str(e).lower():
                print(f"[BinanceExecutor WARNING] Falha ao definir modo de margem para {symbol}: {e}")
                
        self.configured_symbols.add(symbol)

    def _calculate_amount(self, symbol: str, entry: float, sl: float) -> float:
        """Calcula a quantidade em criptoativos base com base no risco USD."""
        risk_usd = self.balance * self.risk_pct
        sl_dist = abs(entry - sl)
        
        # Carrega mercados se ainda não carregou
        if not self.exchange.markets:
            self.exchange.load_markets()
            
        market = self.exchange.market(symbol)
        min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.001)
        
        if sl_dist == 0:
            return min_amount
            
        raw_amount = risk_usd / sl_dist
        
        # Formata a quantidade para a precisão exata aceita pela Binance
        formatted_amount = self.exchange.amount_to_precision(symbol, raw_amount)
        amount = float(formatted_amount)
        
        return max(amount, min_amount)

    async def execute(self, signal: Signal, symbol: str) -> dict:
        """
        Executa ordem bracket completa: entrada (Limit) + SL (Stop Market) + TP (Take Profit Market)
        com retry logic e fallback a mercado.
        """
        await self._configure_symbol_leverage_margin(symbol)
        
        side = "sell" if signal.action == "SELL" else "buy"
        opposite_side = "buy" if side == "sell" else "sell"
        
        # Calcular tamanho do lote
        amount = self._calculate_amount(symbol, signal.entry_price, signal.stop_loss)
        
        # Formatar precisões
        formatted_amount = float(self.exchange.amount_to_precision(symbol, amount))
        formatted_price = float(self.exchange.price_to_precision(symbol, signal.entry_price))
        
        # Parâmetros de posição padrão para One-way Mode da Binance Futures
        params = {
            'positionSide': 'BOTH',
        }
        
        print(f"[BinanceExecutor] Enviando ordem limit: {side.upper()} {formatted_amount} {symbol} @ {formatted_price}")
        
        try:
            # 1. Enviar ordem limite
            entry_order = await self._execute_with_retry(
                self.exchange.create_order,
                symbol=symbol,
                type="limit",
                side=side,
                amount=formatted_amount,
                price=formatted_price,
                params=params
            )
            order_id = entry_order['id']
            print(f"[BinanceExecutor] Ordem limite posicionada. ID: {order_id}. Aguardando preenchimento (limite 60s)...")
        except Exception as e:
            print(f"[BinanceExecutor ERROR] Falha ao colocar ordem de entrada: {e}")
            return {"status": "FAILED", "reason": f"Entry order failed: {e}"}
            
        # 2. Monitoramento de fill (60 segundos) com fallback para mercado
        filled = False
        fill_price = signal.entry_price
        filled_qty = 0.0
        
        for sec in range(12):  # 12 iterações * 5s = 60s
            await asyncio.sleep(5)
            try:
                order_status = await self._execute_with_retry(
                    self.exchange.fetch_order,
                    id=order_id,
                    symbol=symbol
                )
                status = order_status['status']
                filled_qty = order_status.get('filled', 0.0)
                print(f"[BinanceExecutor Monitor] Ordem {order_id} status: {status} | Preenchido: {filled_qty}/{formatted_amount}")
                
                if status == 'closed':
                    filled = True
                    fill_price = order_status.get('price') or order_status.get('average') or signal.entry_price
                    break
                elif status == 'canceled' or status == 'rejected':
                    print(f"[BinanceExecutor] Ordem cancelada ou rejeitada externamente.")
                    if filled_qty > 0:
                        formatted_amount = filled_qty
                        filled = True
                        break
                    return {"status": "FAILED", "reason": f"Order was {status}"}
            except Exception as e:
                print(f"[BinanceExecutor WARNING] Falha ao consultar status da ordem: {e}")
                
        # 3. Se não preencheu em 60 segundos, fazer o fallback
        if not filled:
            print(f"[BinanceExecutor] Limite de 60s atingido. Cancelando ordem limite e executando fallback a mercado...")
            try:
                # Cancelar ordem limite
                await self._execute_with_retry(self.exchange.cancel_order, id=order_id, symbol=symbol)
                # Consultar último status para verificar se houve preenchimento parcial no exato momento
                canceled_order = await self._execute_with_retry(self.exchange.fetch_order, id=order_id, symbol=symbol)
                filled_qty = canceled_order.get('filled', 0.0)
                remaining_qty = formatted_amount - filled_qty
                
                if filled_qty > 0:
                    print(f"[BinanceExecutor] Ordem parcialmente preenchida com {filled_qty} contratos.")
                    fill_price = canceled_order.get('price') or canceled_order.get('average') or signal.entry_price
                    
                market = self.exchange.market(symbol)
                min_amount = market.get('limits', {}).get('amount', {}).get('min', 0.001)
                
                if remaining_qty >= min_amount:
                    print(f"[BinanceExecutor Fallback] Executando restante de {remaining_qty:.4f} a mercado...")
                    market_order = await self._execute_with_retry(
                        self.exchange.create_order,
                        symbol=symbol,
                        type="market",
                        side=side,
                        amount=float(self.exchange.amount_to_precision(symbol, remaining_qty)),
                        params=params
                    )
                    fill_price = market_order.get('price') or market_order.get('average') or fill_price
                    filled = True
                    formatted_amount = formatted_amount  # Total pretendido foi completado
                    print(f"[BinanceExecutor Fallback] Ordem a mercado preenchida. ID: {market_order['id']}")
                else:
                    if filled_qty > 0:
                        formatted_amount = filled_qty
                        filled = True
                    else:
                        print("[BinanceExecutor] Nenhuma quantidade preenchida. Encerrando execução.")
                        return {"status": "CANCELED", "reason": "Timeout without fill"}
            except Exception as e:
                print(f"[BinanceExecutor ERROR] Falha na execução do fallback: {e}")
                if filled_qty > 0:
                    formatted_amount = filled_qty
                    filled = True
                else:
                    return {"status": "ERROR", "reason": f"Fallback error: {e}"}

        # 4. Colocar ordens de Stop Loss e Take Profit
        if filled:
            formatted_sl = float(self.exchange.price_to_precision(symbol, signal.stop_loss))
            formatted_tp = float(self.exchange.price_to_precision(symbol, signal.take_profit))
            
            # Parâmetros de parada
            sl_params = {
                'positionSide': 'BOTH',
                'stopPrice': formatted_sl,
                'reduceOnly': True,
            }
            tp_params = {
                'positionSide': 'BOTH',
                'stopPrice': formatted_tp,
                'reduceOnly': True,
            }
            
            print(f"[BinanceExecutor Bracket] Posicionando Stop Loss @ {formatted_sl} e Take Profit @ {formatted_tp} (Lote: {formatted_amount})...")
            
            sl_order_id = None
            tp_order_id = None
            
            # Enviar Stop Loss
            try:
                sl_order = await self._execute_with_retry(
                    self.exchange.create_order,
                    symbol=symbol,
                    type="STOP_MARKET",
                    side=opposite_side,
                    amount=formatted_amount,
                    price=None,
                    params=sl_params
                )
                sl_order_id = sl_order['id']
                print(f"[BinanceExecutor Bracket] Stop Loss ativo! ID: {sl_order_id}")
            except Exception as e:
                print(f"[BinanceExecutor CRITICAL] Falha ao enviar ordem de STOP LOSS: {e}")
                
            # Enviar Take Profit
            try:
                tp_order = await self._execute_with_retry(
                    self.exchange.create_order,
                    symbol=symbol,
                    type="TAKE_PROFIT_MARKET",
                    side=opposite_side,
                    amount=formatted_amount,
                    price=None,
                    params=tp_params
                )
                tp_order_id = tp_order['id']
                print(f"[BinanceExecutor Bracket] Take Profit ativo! ID: {tp_order_id}")
            except Exception as e:
                print(f"[BinanceExecutor CRITICAL] Falha ao enviar ordem de TAKE PROFIT: {e}")
                
            return {
                "status": "FILLED",
                "fill_price": fill_price,
                "amount": formatted_amount,
                "entry_order_id": order_id,
                "sl_order_id": sl_order_id,
                "tp_order_id": tp_order_id
            }
            
        return {"status": "FAILED", "reason": "Unknown state"}
