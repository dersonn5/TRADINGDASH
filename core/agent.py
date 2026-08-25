import json
import time
import traceback
from datetime import datetime
from google import genai
from google.genai import types
import config
from core.rag import ObsidianRAG
from core.risk_manager import RiskManager

class ICTAgent:
    """
    Agente de IA Cognitivo ICT.
    Utiliza o SDK moderno do Google GenAI para processar sinais com raciocínio Chain-of-Thought (CoT)
    e validação baseada no cérebro do Obsidian.
    """
    
    def __init__(self):
        # Inicializa o cliente oficial do Gemini com a chave de API
        api_key = config.GEMINI_API_KEY
        if not api_key:
            print("[AGENT][AVISO] GEMINI_API_KEY não configurada no ambiente. Usando chave vazia (pode falhar).")
        self.client = genai.Client(api_key=api_key)
        # Usamos o modelo gemini-2.5-flash devido à excelente latência, precisão e limite de cota mais alto no plano gratuito
        self.model_name = "gemini-2.5-flash"

    def evaluate_trade_setup(self, setup_data: dict, account_balance: float, is_backtest: bool = False) -> dict:
        """
        Recebe o sinal do TradingView, puxa o RAG do Obsidian, roda os filtros matemáticos
        de risco e consulta a IA Gemini para uma avaliação de trading cognitiva.
        """
        print(f"\n[AGENT] Iniciando avaliação cognitiva de setup para {setup_data.get('symbol', 'UNKNOWN')}...")
        
        symbol = setup_data.get("symbol", "")
        action = setup_data.get("action", "BUY").upper()
        price = float(setup_data.get("price", 0.0))
        timeframe = setup_data.get("timeframe", "15m")
        signal = setup_data.get("ict_signal", "Desconhecido")
        
        # 1. Obter cotações aproximadas ou fornecidas para SL e TP
        # Se o alerta do TradingView não enviar SL/TP exatos, a IA os definirá,
        # mas faremos estimativas iniciais com base na FVG para o RiskManager.
        fvg_high = float(setup_data.get("fvg_high", 0.0))
        fvg_low = float(setup_data.get("fvg_low", 0.0))
        
        # Estimativa de Stop Loss seguro para o cálculo matemático inicial
        if action == "BUY":
            # SL no fundo da FVG ou um pouco abaixo
            estimated_sl = fvg_low - (abs(price - fvg_low) * 0.1) if fvg_low > 0 else price * 0.995
            # TP buscando no mínimo 1:3 R:R
            estimated_tp = price + (abs(price - estimated_sl) * 3.0)
        else:
            # SL no topo da FVG ou um pouco acima
            estimated_sl = fvg_high + (abs(fvg_high - price) * 0.1) if fvg_high > 0 else price * 1.005
            # TP buscando no mínimo 1:3 R:R
            estimated_tp = price - (abs(estimated_sl - price) * 3.0)
            
        # 2. Rodar os filtros rígidos matemáticos e de drawdown primeiro!
        risk_check = RiskManager.validate_pre_trade_filters(
            symbol=symbol,
            entry_price=price,
            stop_loss=estimated_sl,
            take_profit=estimated_tp,
            account_balance=account_balance,
            bypass_daily_limits=is_backtest
        )
        
        if not risk_check["approved"]:
            print(f"[AGENT][BLOQUEADO] Filtros de risco quantitativo rejeitaram a operação: {risk_check['reason']}")
            # Criar um registro no diário informando que o gerenciamento de risco vetou o trade
            journal_data = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "action": action,
                "entry_price": price,
                "stop_loss": estimated_sl,
                "take_profit": estimated_tp,
                "risk_reward_ratio": round(abs(estimated_tp - price) / abs(price - estimated_sl), 2) if abs(price - estimated_sl) > 0 else 0.0,
                "size_units": 0.0,
                "result": "BLOCKED_BY_RISK",
                "reasoning": f"### OPERAÇÃO BLOQUEADA PELO GESTOR DE RISCO QUANTITATIVO\n\n**Motivo**: {risk_check['reason']}\n\nO cérebro de risco impediu a entrada para proteger o capital e evitar overtrading/drawdown excessivo.",
                "checklist_killzone": "PENDENTE",
                "checklist_sweep": "PENDENTE",
                "checklist_mss": "PENDENTE",
                "checklist_payout": "REJEITADO"
            }
            filepath = ObsidianRAG.write_trade_to_journal(journal_data, is_backtest=is_backtest)
            return {
                "approved": False,
                "action": "PASS",
                "reason": f"Gestor de Risco: {risk_check['reason']}",
                "size_units": 0.0,
                "journal_filepath": filepath.name if filepath else None,
                "applied_rules": ["Gestao_de_Trade_e_Parciais"]
            }

        # 3. Se aprovado pelo risco básico, compilar o contexto do Obsidian via RAG
        obsidian_context = ObsidianRAG.compile_brain_context(setup_data)
        
        # 4. Formular o prompt de análise para a IA
        system_instruction = """
Você é a MENTE COGNITIVA ICT, um super agente quantitativo de trading de elite. Seu único objetivo é analisar os setups de mercado, confrontá-los com o conhecimento do Obsidian (RAG) e determinar se a operação possui expectativa matemática altamente positiva e consistência estrutural.

Você DEVE realizar um raciocínio em múltiplos passos (Chain-of-Thought):
1. Avaliar se o horário da operação coincide com uma das Killzones válidas de ICT (Londres, Nova York ou Fechamento de Londres).
2. Verificar se houve varredura de liquidez (Sweep) de topos/fundos prévios importantes (BSL/SSL).
3. Analisar se a quebra de estrutura (MSS) ocorreu com deslocamento forte e corpo de vela fechando acima do nível chave.
4. Validar se o stop loss técnico está bem posicionado e se o alvo de take profit atende à relação risco:retorno mínima.
5. Confrontar o cenário atual com a lista de "Lições Aprendidas & Erros a Evitar". Se houver risco de CPI/Notícias fortes ou qualquer padrão de erro passado aplicável, aborte.

Regra Crítica para Sinapses no Obsidian:
No campo "applied_rules" do JSON de resposta, você DEVE retornar uma lista (array) contendo APENAS as regras técnicas (nomes das Notas Mestras enumerados) que foram determinantes principais para a sua aprovação ou rejeição do trade.
- Se o trade foi rejeitado pelo bias, inclua APENAS "Daily_Bias_e_Order_Flow".
- Se foi rejeitado por fechamento abaixo de 50% da FVG, inclua APENAS "Consequent_Encroachment_FVG".
- Se foi rejeitado por horário fora da Killzone, inclua APENAS "Silver_Bullet_Algoritmica".
- Se entrou num setup de compra clássico de Silver Bullet com FVG e alvos parciais, inclua "Silver_Bullet_Algoritmica", "Modelo_Mentoria_2022" e "Gestao_de_Trade_e_Parciais".
Mantenha a lista o mais curta e seletiva possível para desenharmos um grafo perfeito e limpo!

Você deve retornar estritamente um payload no formato JSON.
"""

        user_prompt = f"""
Dados em tempo real do setup (Olhar Clínico Multi-Timeframe):

--- CONTEXTO DIÁRIO & MACRO (HTF) ---
- Viés Diário (Daily Bias): {setup_data.get('daily_bias', 'N/A')}
- Fluxo de Ordens HTF (Order Flow H4): {setup_data.get('htf_order_flow', 'N/A')}
- Ímã de Liquidez Macro (Draw on Liquidity): {setup_data.get('draw_on_liquidity', 'N/A')}

--- GATILHO INTRADAY LOCAL ---
- Ativo: {symbol}
- Timeframe Operacional: {timeframe}
- Sinal Técnico Disparado: {signal}
- Preço Atual de Entrada: {price}
- Varredura de Liquidez Local: {setup_data.get('liquidity_swept', 'N/A')}
- Limites da FVG Intraday: Máxima {fvg_high} | Mínima {fvg_low}
- Consequent Encroachment (50% FVG): {setup_data.get('fvg_ce', (fvg_high + fvg_low)/2 if (fvg_high > 0 and fvg_low > 0) else 'N/A')}
- Observações de Ação do Preço (Price Action): {setup_data.get('price_action_notes', setup_data.get('commentary', 'N/A'))}
- Horário do Sinal (EST/Nova York): {setup_data.get('time_of_day_est', datetime.utcnow().strftime('%H:%M EST'))}

Instrução de Execução:
Avalie o setup realizando um diagnóstico clínico multi-timeframe contra o nosso cérebro do Obsidian e retorne a sua decisão estruturada em formato JSON.
Se sua decisão for de PASS (ignorar), explique minuciosamente o motivo técnico no campo reasoning.
Se sua decisão for BUY ou SELL, forneça os alvos refinados de stop_loss e take_profit baseados na confluência e congele o payout mínimo (R:R 1:2.5+).
"""

        # Configurar formato estruturado de resposta JSON
        schema = {
            "type": "OBJECT",
            "properties": {
                "approved": {"type": "BOOLEAN"},
                "action": {"type": "STRING", "enum": ["BUY", "SELL", "PASS"]},
                "entry_price": {"type": "NUMBER"},
                "stop_loss": {"type": "NUMBER"},
                "take_profit": {"type": "NUMBER"},
                "risk_reward_ratio": {"type": "NUMBER"},
                "confidence_score": {"type": "NUMBER"},
                "reasoning": {"type": "STRING"},
                "checklist_killzone": {"type": "STRING"},
                "checklist_sweep": {"type": "STRING"},
                "checklist_mss": {"type": "STRING"},
                "checklist_payout": {"type": "STRING"},
                "applied_rules": {
                    "type": "ARRAY",
                    "items": {
                        "type": "STRING",
                        "enum": [
                            "Modelo_Mentoria_2022",
                            "Silver_Bullet_Algoritmica",
                            "Optimal_Trade_Entry_OTE",
                            "Daily_Bias_e_Order_Flow",
                            "Consequent_Encroachment_FVG",
                            "Gestao_de_Trade_e_Parciais"
                        ]
                    }
                }
            },
            "required": [
                "approved", "action", "entry_price", "stop_loss", "take_profit",
                "risk_reward_ratio", "confidence_score", "reasoning",
                "checklist_killzone", "checklist_sweep", "checklist_mss", "checklist_payout",
                "applied_rules"
            ]
        }

        try:
            # Chamar a API do Gemini utilizando o SDK oficial com retentativas automáticas e backoff exponencial
            response = None
            max_retries = 6
            retry_delay = 5.0
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[obsidian_context, user_prompt],
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            response_mime_type="application/json",
                            response_schema=schema,
                            temperature=0.2 # Baixa temperatura para manter a IA estritamente lógica e focada nas regras
                        )
                    )
                    break
                except Exception as e:
                    err_msg = str(e)
                    is_quota_error = "429" in err_msg or "resource_exhausted" in err_msg.lower() or "quota" in err_msg.lower()
                    
                    if attempt < max_retries - 1:
                        if is_quota_error:
                            sleep_time = 65.0
                            print(f"[AGENT][RATE-LIMIT] Cota excedida (429 / RESOURCE_EXHAUSTED). Aguardando {sleep_time} segundos para liberar a cota (Tentativa {attempt+1}/{max_retries})...")
                            time.sleep(sleep_time)
                        else:
                            print(f"[AGENT][AVISO] Falha na API do Gemini (Tentativa {attempt+1}/{max_retries}): {err_msg}. Retentando em {retry_delay} segundos...")
                            time.sleep(retry_delay)
                            retry_delay *= 2.0
                    else:
                        print(f"[AGENT][ERRO] Esgotadas as {max_retries} tentativas na API do Gemini.")
                        raise e
            
            ai_decision = json.loads(response.text)
            print(f"[AGENT] IA concluiu avaliação! Decisão: {ai_decision.get('action')} | Confiança: {ai_decision.get('confidence_score')}")
            
            # 5. Se a IA decidir operar, calcular o tamanho do lote exato pelo RiskManager
            size_units = 0.0
            if ai_decision.get("approved") and ai_decision.get("action") in ["BUY", "SELL"]:
                size_units = RiskManager.calculate_position_size(
                    symbol=symbol,
                    entry_price=ai_decision.get("entry_price"),
                    stop_loss=ai_decision.get("stop_loss"),
                    account_balance=account_balance
                )
                
            # Adicionar lote e gravar no diário do Obsidian
            ai_decision["size_units"] = size_units
            ai_decision["timestamp"] = datetime.now().isoformat()
            ai_decision["symbol"] = symbol
            ai_decision["timeframe"] = timeframe
            ai_decision["result"] = "PENDING" if ai_decision.get("approved") else "PASS"
            
            # Gravar o relatório em markdown no Obsidian
            filepath = ObsidianRAG.write_trade_to_journal(ai_decision, is_backtest=is_backtest)
            ai_decision["journal_filepath"] = filepath.name if filepath else None
            
            return ai_decision

        except Exception as e:
            print(f"[AGENT][ERRO CRÍTICO] Falha na avaliação do agente de IA: {str(e)}")
            traceback.print_exc()
            return {
                "approved": False,
                "action": "PASS",
                "reason": f"Erro interno na IA: {str(e)}",
                "size_units": 0.0
            }
