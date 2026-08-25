import os
import uvicorn
import json
import hashlib
from zoneinfo import ZoneInfo
from fastapi import FastAPI, HTTPException, status, Body, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import config
from core.agent import ICTAgent
from core.common_execution import CommonExecution
from core.mcp_client import MCPTradingViewClient

app = FastAPI(
    title="Cérebro de Trading Cognitivo ICT",
    description="API para integrar alertas do TradingView com RAG no Obsidian, raciocínio Gemini CoT e execução nas corretoras.",
    version="1.0.0"
)

# Definir o modelo de dados para validação do sinal do TradingView
class TradingViewSignal(BaseModel):
    secret: str = Field(..., description="Chave secreta de autenticação do webhook")
    symbol: str = Field(..., description="Ativo operado (ex: XAUUSD, NQ, ES)")
    action: str = Field(..., description="Direção do trade (BUY ou SELL)")
    price: float = Field(..., description="Preço de fechamento da entrada")
    timeframe: str = Field("15m", description="Tempo gráfico do sinal")
    ict_signal: str = Field("Liquidity Sweep + MSS", description="Descrição do sinal de ICT acionado")
    liquidity_swept: Optional[str] = Field("SSL", description="Lado da liquidez varrido (BSL ou SSL)")
    fvg_high: Optional[float] = Field(0.0, description="Preço máximo da Fair Value Gap")
    fvg_low: Optional[float] = Field(0.0, description="Preço mínimo da Fair Value Gap")
    alert_id: Optional[str] = Field(None, description="Identificador único para deduplicação do alerta")
    timestamp: Optional[str] = Field(None, description="Timestamp do alerta (ex: ISO8601)")

def is_duplicate_alert(signal: TradingViewSignal) -> bool:
    """Implementa idempotência de webhook gravando alertas processados em data/processed_alerts.json"""
    registry_path = os.path.join("data", "processed_alerts.json")
    os.makedirs(os.path.dirname(registry_path), exist_ok=True)
    
    # Gerar chave única para o alerta
    if signal.alert_id:
        unique_key = signal.alert_id
    else:
        hasher = hashlib.sha256()
        payload_str = f"{signal.symbol}_{signal.action}_{signal.price}_{signal.timeframe}_{signal.ict_signal}_{signal.timestamp or ''}"
        hasher.update(payload_str.encode('utf-8'))
        unique_key = hasher.hexdigest()
        
    processed_alerts = []
    if os.path.exists(registry_path):
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                processed_alerts = json.load(f)
                if not isinstance(processed_alerts, list):
                    processed_alerts = []
        except Exception:
            processed_alerts = []
            
    if unique_key in processed_alerts:
        return True
        
    # Adiciona à lista de processados
    processed_alerts.append(unique_key)
    # Limita o tamanho do arquivo
    if len(processed_alerts) > 1000:
        processed_alerts = processed_alerts[-1000:]
        
    try:
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(processed_alerts, f, indent=4)
    except Exception as e:
        print(f"[SERVER][ERRO] Falha ao salvar processed_alerts.json: {e}")
        
    return False

@app.get("/api/backtests")
def get_backtest_data():
    """Retorna os dados brutos do backtest_database.json para o Dashboard."""
    db_path = "backtest_database.json"
    if not os.path.exists(db_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banco de dados de backtest não encontrado. Por favor, execute o backtester primeiro."
        )
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ler banco de dados de backtest: {str(e)}"
        )

@app.get("/api/live_trades")
def get_live_trades_data():
    """Retorna os dados dinâmicos do trades_database.json formatados para o Dashboard."""
    db_path = "trades_database.json"
    if not os.path.exists(db_path):
        return {
            "ideal": {"statistics": {"total_pnl_usd": 0.0, "trades_taken": 0, "wins": 0, "losses": 0, "prevented_losses": 0}, "trades": []},
            "stressed": {"statistics": {"total_pnl_usd": 0.0, "trades_taken": 0, "wins": 0, "losses": 0, "prevented_losses": 0}, "trades": []}
        }
    try:
        with open(db_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        trades = raw_data.get("trades", [])
        
        # Calcular estatísticas reais
        total_pnl = sum(t.get("profit_loss_usd", 0.0) for t in trades)
        wins = sum(1 for t in trades if t.get("result") == "WIN")
        losses = sum(1 for t in trades if t.get("result") == "LOSS")
        prevented_losses = sum(1 for t in trades if t.get("result") == "PREVENTED_LOSS")
        trades_taken = sum(1 for t in trades if t.get("action") in ["BUY", "SELL"])
        
        # Mapear os trades reais para a estrutura aceita pelo Javascript do Dashboard
        mapped_trades_ideal = []
        mapped_trades_stressed = []
        
        for idx, t in enumerate(trades):
            timestamp_str = t.get("timestamp")
            try:
                dt_obj = datetime.fromisoformat(timestamp_str)
                date_str = dt_obj.strftime("%Y-%m-%d")
                time_str = dt_obj.strftime("%H:%M EST")
            except Exception:
                date_str = "Hoje"
                time_str = "Agora"
            
            pnl = t.get("profit_loss_usd", 0.0)
            result = t.get("result", "PENDING")
            
            # Mapear resultado para avaliação
            evaluation = "WIN"
            if result == "LOSS":
                evaluation = "LOSS"
            elif result == "PREVENTED_LOSS":
                evaluation = "PREVENTED_LOSS"
            elif result == "PENDING":
                evaluation = "PENDING"
                
            trade_obj = {
                "scenario_id": f"LIVE-{(idx + 1):03d}",
                "date": date_str,
                "time_of_day_est": time_str,
                "symbol": t.get("symbol"),
                "signal_type": t.get("strategy", "ICT Setup"),
                "daily_bias": "BULLISH" if t.get("action") == "BUY" else ("BEARISH" if t.get("action") == "SELL" else "NEUTRAL"),
                "ai_decision": t.get("action"),
                "pnl_usd": pnl,
                "evaluation": evaluation,
                "reasoning": t.get("reasoning", "Execução ao vivo rastreada."),
                "checklist_killzone": t.get("checklist", {}).get("killzone", True),
                "checklist_sweep": t.get("checklist", {}).get("sweep", True),
                "checklist_mss": t.get("checklist", {}).get("mss", True),
                "checklist_payout": t.get("checklist", {}).get("payout", True),
            }
            
            mapped_trades_ideal.append(trade_obj)

            # Stressed trade: passthrough honesto (mesmo PnL).
            # Stress real só faz sentido com simulação de slippage no momento da execução,
            # não com multiplicação cosmética pós-fato. Mantemos a coluna pra compatibilidade
            # do dashboard mas SEM mentir estatisticamente.
            trade_stressed_obj = trade_obj.copy()
            mapped_trades_stressed.append(trade_stressed_obj)

        stressed_total_pnl = sum(t.get("pnl_usd", 0.0) for t in mapped_trades_stressed)
        
        return {
            "ideal": {
                "statistics": {
                    "total_pnl_usd": total_pnl,
                    "trades_taken": trades_taken,
                    "wins": wins,
                    "losses": losses,
                    "prevented_losses": prevented_losses
                },
                "trades": mapped_trades_ideal
            },
            "stressed": {
                "statistics": {
                    "total_pnl_usd": stressed_total_pnl,
                    "trades_taken": trades_taken,
                    "wins": wins,
                    "losses": losses,
                    "prevented_losses": prevented_losses
                },
                "trades": mapped_trades_stressed
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ler banco de dados de trades reais: {str(e)}"
        )

@app.get("/api/screenshots/{trade_id}")
def get_trade_screenshot(trade_id: str):
    """Retorna a imagem do screenshot do gráfico correspondente ao trade_id."""
    from fastapi.responses import FileResponse
    screenshot_dir = os.path.join(os.path.dirname(__file__), "screenshots")
    screenshot_path = os.path.join(screenshot_dir, f"{trade_id}.png")
    if os.path.exists(screenshot_path):
        return FileResponse(screenshot_path)
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Screenshot não encontrado para este trade."
    )

@app.get("/", response_class=HTMLResponse)
def get_dashboard():
    """Serve a página HTML interativa do Dashboard do Cérebro ICT."""
    template_path = os.path.join("templates", "dashboard.html")
    if not os.path.exists(template_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template do dashboard (dashboard.html) não encontrado sob a pasta templates/."
        )
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return html_content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao ler template do dashboard: {str(e)}"
        )

@app.post("/webhook", status_code=status.HTTP_200_OK)
def receive_signal(signal: TradingViewSignal = Body(...)):
    """
    Recebe os sinais enviados do TradingView.
    Valida a chave secreta, aciona o Agente de IA para raciocínio quantitativo-cognitivo
    e encaminha para a execução na corretora.
    """
    print(f"\n[SERVER] Sinal recebido de TradingView para {signal.symbol} ({signal.action})...")
    
    # 1. Verificação de Segurança Rígida
    if signal.secret != config.WEBHOOK_SECRET:
        print("[SERVER][AVISO] Tentativa de acesso não autorizada! Secret incorreto.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado: Chave secreta de webhook inválida."
        )

    # 1.5. Idempotência / Deduplicação de Webhook
    if is_duplicate_alert(signal):
        print(f"[SERVER][INFO] Alerta {signal.alert_id or 'hash'} ja processado. Ignorando por idempotencia.")
        return {
            "signal_received": True,
            "duplicate": True,
            "detail": "Sinal ignorado (ja processado por idempotencia)",
            "ai_decision": {"approved": False, "action": "PASS"}
        }

    # 2. Definir o saldo da conta dinâmico
    account_balance = config.ACCOUNT_BALANCE
    
    # 3. Chamar a inteligência artificial (Gemini) e filtros quânticos
    agent = ICTAgent()
    setup_data = signal.model_dump()
    
    ai_decision = agent.evaluate_trade_setup(setup_data, account_balance)
    
    # 4. Se a IA aprovou e gerou ordens, encaminhar para a execução
    execution_result = {"success": False, "detail": "Setup rejeitado ou ignorado pela IA/Risco"}
    
    if ai_decision.get("approved") and ai_decision.get("action") in ["BUY", "SELL"]:
        execution_result = CommonExecution.execute_trade(ai_decision)
        
        # Opcional: Se a execução falhar, você pode adicionar logs adicionais aqui
        if not execution_result.get("success"):
            print(f"[SERVER][ALERTA] Falha de execução física na corretora: {execution_result.get('error')}")
    else:
        # Registrar a rejeição como uma perda evitada no DB de trades
        from core.risk_manager import RiskManager
        RiskManager.log_trade(
            symbol=signal.symbol,
            action="PASS",
            entry_price=signal.price,
            stop_loss=signal.fvg_low or signal.price * 0.99,
            take_profit=signal.fvg_high or signal.price * 1.01,
            size_units=0.0,
            result="PREVENTED_LOSS",
            profit_loss_usd=0.0,
            reasoning=ai_decision.get("reasoning", ai_decision.get("reason", "Filtro de IA/Risco ativado.")),
            strategy=signal.ict_signal,
            checklist={
                "killzone": ai_decision.get("checklist_killzone", False),
                "sweep": ai_decision.get("checklist_sweep", False),
                "mss": ai_decision.get("checklist_mss", False),
                "payout": ai_decision.get("checklist_payout", False)
            }
        )
            
    # Retorna o relatório final compilado para o TradingView / Logs
    return {
        "signal_received": True,
        "ai_decision": {
            "approved": ai_decision.get("approved"),
            "action": ai_decision.get("action"),
            "entry_price": ai_decision.get("entry_price"),
            "stop_loss": ai_decision.get("stop_loss"),
            "take_profit": ai_decision.get("take_profit"),
            "size_units": ai_decision.get("size_units"),
            "rr_ratio": ai_decision.get("risk_reward_ratio"),
            "confidence": ai_decision.get("confidence_score"),
            "checklist": {
                "killzone": ai_decision.get("checklist_killzone"),
                "sweep": ai_decision.get("checklist_sweep"),
                "mss": ai_decision.get("checklist_mss"),
                "payout": ai_decision.get("checklist_payout")
            }
        },
        "execution": execution_result
    }

class AnalyzeRequest(BaseModel):
    secret: str = Field(..., description="Webhook secret de autenticação")
    symbol: str = Field(..., description="Ativo (ex: XAUUSD, NQ, BTCUSDT)")
    timeframe: str = Field("15m", description="Timeframe do snapshot")
    candles: int = Field(100, description="Quantidade de candles a puxar")
    exchange: Optional[str] = Field(None, description="Exchange override (OANDA, CME_MINI, BINANCE...)")
    execute: bool = Field(False, description="Se True, executa o trade caso IA aprove")


@app.get("/market/snapshot")
async def market_snapshot(
    symbol: str = Query(..., description="Símbolo (ex: XAUUSD)"),
    timeframe: str = Query("15m"),
    candles: int = Query(100, ge=10, le=500),
    exchange: Optional[str] = Query(None),
):
    """
    Puxa snapshot ao vivo do TradingView via MCP (candles + indicadores).
    Endpoint read-only para debug e validação da conexão MCP.
    """
    try:
        snapshot = await MCPTradingViewClient.market_snapshot(
            symbol=symbol, timeframe=timeframe, candles=candles, exchange=exchange,
        )
        return {"success": True, "snapshot": snapshot}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao consultar MCP TradingView: {str(e)}"
        )


@app.post("/analyze", status_code=status.HTTP_200_OK)
async def analyze_via_mcp(req: AnalyzeRequest = Body(...)):
    """
    Análise proativa: puxa estado atual do mercado via MCP, monta setup_data
    com snapshot ao vivo, e roda agente Gemini para decisão.
    Útil para scheduling em killzones (não-reativo a webhook).
    """
    if req.secret != config.WEBHOOK_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Secret inválido.")

    try:
        snapshot = await MCPTradingViewClient.market_snapshot(
            symbol=req.symbol, timeframe=req.timeframe, candles=req.candles, exchange=req.exchange,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"MCP falhou: {str(e)}")

    candles_data = snapshot.get("candles", {}).get("data", [])
    indicators_data = snapshot.get("indicators", {}).get("indicators", {})
    last_candle = candles_data[-1] if candles_data else {}
    current_price = float(last_candle.get("close", 0.0)) if last_candle else 0.0

    setup_data = {
        "symbol": req.symbol,
        "action": "PASS",  # Agente decidirá BUY/SELL/PASS
        "price": current_price,
        "timeframe": req.timeframe,
        "ict_signal": "Live Market Snapshot (MCP-driven)",
        "liquidity_swept": "N/A (auto-detection pendente)",
        "fvg_high": 0.0,
        "fvg_low": 0.0,
        "daily_bias": indicators_data.get("Recommend.All", "N/A"),
        "htf_order_flow": f"RSI={indicators_data.get('RSI', 'N/A')} | MACD={indicators_data.get('MACD.macd', 'N/A')}",
        "draw_on_liquidity": "N/A",
        "price_action_notes": f"Snapshot ao vivo MCP: ultimo close={current_price}, {len(candles_data)} candles recentes",
        "time_of_day_est": datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M EST"),
    }

    agent = ICTAgent()
    ai_decision = agent.evaluate_trade_setup(setup_data, account_balance=config.ACCOUNT_BALANCE)

    execution_result = {"success": False, "detail": "Execução desativada ou setup rejeitado"}
    if req.execute and ai_decision.get("approved") and ai_decision.get("action") in ["BUY", "SELL"]:
        execution_result = CommonExecution.execute_trade(ai_decision)

    return {
        "source": "mcp_analyze",
        "symbol": req.symbol,
        "timeframe": req.timeframe,
        "current_price": current_price,
        "candles_count": len(candles_data),
        "ai_decision": {
            "approved": ai_decision.get("approved"),
            "action": ai_decision.get("action"),
            "entry_price": ai_decision.get("entry_price"),
            "stop_loss": ai_decision.get("stop_loss"),
            "take_profit": ai_decision.get("take_profit"),
            "size_units": ai_decision.get("size_units"),
            "rr_ratio": ai_decision.get("risk_reward_ratio"),
            "confidence": ai_decision.get("confidence_score"),
            "reasoning": ai_decision.get("reasoning"),
        },
        "execution": execution_result,
    }


if __name__ == "__main__":
    # Inicia o servidor uvicorn na porta 8000
    print("\n===========================================================")
    print("  Inicializando Cerebro de Trading FastAPI...")
    print(f"  Diretorio do Obsidian: {config.OBSIDIAN_VAULT_PATH}")
    print(f"  Modo de Execucao:      {config.EXECUTION_MODE}")
    print("===========================================================\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
