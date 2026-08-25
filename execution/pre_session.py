import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from google import genai
from google.genai import types

# Garantir que o diretório raiz está no path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from data.data_loader import DataLoader
from filters.news_filter import NewsFilter

class PreSessionBriefing:
    """
    Orquestrador do Pre-Session Briefing (Playbook Diário).
    Executa a análise macro antes das Killzones, detecta a tendência HTF (D1/H1),
    identifica notícias de alto impacto do dia e utiliza a IA Gemini para gravar
    o roteiro operacional estratégico no Obsidian Vault.
    """
    
    def __init__(self):
        self.data_loader = DataLoader()
        api_key = config.GEMINI_API_KEY
        if not api_key:
            print("[PRE-SESSION][AVISO] GEMINI_API_KEY não configurada no ambiente.")
        self.client = genai.Client(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        self.news_filter = NewsFilter()

    def get_simulated_news_for_today(self) -> list:
        """
        Retorna notícias de alto impacto simuladas/reais para o dia atual.
        Em produção real, isso consome uma API de calendário econômico.
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Mapeamento dinâmico de notícias comuns para dar dinamismo aos playbooks diários
        day_of_week = datetime.now().weekday()
        
        news_events = []
        if day_of_week == 1:  # Terça-feira (ex: PPI / Retail Sales)
            news_events.append({
                "timestamp": f"{today_str} 08:30:00",
                "headline": "Core PPI MoM",
                "impact": "HIGH"
            })
        elif day_of_week == 2:  # Quarta-feira (ex: CPI / Estoques de Petróleo)
            news_events.append({
                "timestamp": f"{today_str} 08:30:00",
                "headline": "Core CPI YoY (Inflacao EUA)",
                "impact": "HIGH"
            })
        elif day_of_week == 3:  # Quinta-feira (ex: Pedidos de Seguro Desemprego / Claims)
            news_events.append({
                "timestamp": f"{today_str} 08:30:00",
                "headline": "Initial Jobless Claims",
                "impact": "HIGH"
            })
        elif day_of_week == 4:  # Sexta-feira (ex: NFP)
            news_events.append({
                "timestamp": f"{today_str} 08:30:00",
                "headline": "Non-Farm Payroll (NFP) & Unemployment Rate",
                "impact": "HIGH"
            })
            
        # Sempre incluir decisões do FOMC se for uma quarta-feira de decisão teórica
        if day_of_week == 2 and datetime.now().day in [10, 11, 17, 18, 24, 25]:
            news_events.append({
                "timestamp": f"{today_str} 14:00:00",
                "headline": "FOMC Interest Rate Decision",
                "impact": "HIGH"
            })
            news_events.append({
                "timestamp": f"{today_str} 14:30:00",
                "headline": "FOMC Press Conference (Powell)",
                "impact": "HIGH"
            })
            
        return news_events

    def run_briefing(self):
        """
        Coleta dados, dispara a IA e grava o Playbook no Obsidian.
        """
        print("="*60)
        print("   INICIANDO PRE-SESSION BRIEFING DIÁRIO (PLAYBOOK IA)   ")
        print("="*60)
        
        today_str = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
        
        # 1. Carregar Dados de Mercado (Nasdaq e Gold)
        print("[1/4] Coletando dados históricos do Ouro e Nasdaq...")
        
        # Nasdaq proxy
        candles_nq_1d = self.data_loader.load_data("I:NDX", "1d", start_date, today_str)
        candles_nq_1h = self.data_loader.load_data("I:NDX", "1h", start_date, today_str)
        
        # Ouro
        candles_xau_1d = self.data_loader.load_data("C:XAUUSD", "1d", start_date, today_str)
        candles_xau_1h = self.data_loader.load_data("C:XAUUSD", "1h", start_date, today_str)
        
        # 2. Obter Calendário Econômico do Dia
        print("[2/4] Consolidando calendário de notícias do dia...")
        news = self.get_simulated_news_for_today()
        self.news_filter.load_simulated_news(news)
        
        news_summary = ""
        if news:
            for event in news:
                news_summary += f"- **{event['timestamp'][11:16]} EST**: {event['headline']} (Impacto: {event['impact']})\n"
        else:
            news_summary = "- Sem notícias macroeconômicas de alto impacto agendadas para hoje.\n"
            
        # 3. Computar estatísticas rápidas para passar à IA
        nq_stats = "N/A"
        if not candles_nq_1d.empty:
            last_nq = candles_nq_1d.iloc[-1]
            nq_stats = f"Fechamento Anterior: {last_nq['close']:.2f} | Máxima: {last_nq['high']:.2f} | Mínima: {last_nq['low']:.2f}"
            
        xau_stats = "N/A"
        if not candles_xau_1d.empty:
            last_xau = candles_xau_1d.iloc[-1]
            xau_stats = f"Fechamento Anterior: {last_xau['close']:.2f} | Máxima: {last_xau['high']:.2f} | Mínima: {last_xau['low']:.2f}"

        # 4. Chamar Inteligência Artificial Gemini
        print("[3/4] Consultando a Mente Cognitiva ICT para gerar o Playbook...")
        
        system_instruction = """
        Você é a MENTE COGNITIVA ICT, um super agente analista e trader quantitativo. Seu objetivo é redigir um Roteiro de Preparação Diária (Playbook do Dia) clínico, prático e extremamente visual para o Obsidian, direcionado ao trader.
        Você deve analisar os preços recentes, o calendário de notícias e desenhar a estratégia estrita de execução das Killzones.
        Evite previsões vagas. Seja clínico, defina níveis exatos (de suporte, resistência e equilíbrio) e determine as faixas horárias proibidas para operar devido a notícias ou faltas de liquidez.
        Use formatação rica em Markdown compatível com o Obsidian (incluindo boxes de dica/alerta do GitHub como > [!IMPORTANT] ou > [!WARNING]).
        """
        
        user_prompt = f"""
        Olá, Mente Cognitiva. Aqui estão os dados diagnósticos de mercado para hoje ({datetime.now().strftime('%d de %M de %Y')}):
        
        --- CALENDÁRIO ECONÔMICO (NOTÍCIAS DO DIA) ---
        {news_summary}
        
        --- NASDAQ (NQ / I:NDX) ---
        - {nq_stats}
        - Últimas 3 velas H1 (fechamentos recentes): {[round(c, 2) for c in candles_nq_1h['close'].tail(3).tolist()] if not candles_nq_1h.empty else 'N/A'}
        
        --- GOLD (XAUUSD / C:XAUUSD) ---
        - {xau_stats}
        - Últimas 3 velas H1 (fechamentos recentes): {[round(c, 2) for c in candles_xau_1h['close'].tail(3).tolist()] if not candles_xau_1h.empty else 'N/A'}
        
        Instrução:
        Crie o Playbook do Dia estruturado no seguinte padrão:
        1. # 🧠 PLAYBOOK OPERACIONAL DIÁRIO - [Data de Hoje]
        2. ## 📅 Calendário de Risco Macro (Eventos que podem causar slippage ou stop hunt, definindo os buffers de +/- 30 minutos em que o bot não deve abrir posições).
        3. ## 🗽 Nasdaq (NQ) - Análise Técnica de Elite (Diretriz do Viés / Bias do PO3, Suporte/Resistência em H1, Alvos de Liquidez e Instruções para a Killzone Silver Bullet 10h EST).
        4. ## 🥇 Ouro (XAUUSD) - Análise Técnica de Elite (Diretriz do Viés, Asian Range de referência, Alvos de Liquidez e Instruções para a Killzone London Sweep 2h EST).
        5. ## 🛡️ Regras de Ouro e Compliance (Risco de 1%, Drawdown limite e lembrete de manter a disciplina).
        
        Retorne apenas o texto puro em Markdown para ser gravado diretamente no arquivo.
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3
                )
            )
            
            playbook_content = response.text
            
            # Gravar no Obsidian
            print("[4/4] Gravando relatório no Obsidian Vault...")
            target_path = config.OBSIDIAN_VAULT_PATH / "Diario_Trades" / "Playbook_Dia.md"
            
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(playbook_content)
                
            print(f"\n[SUCESSO] Playbook do Dia gerado e salvo em:")
            print(f"  - '{target_path}'")
            print("="*60)
            
            return playbook_content
            
        except Exception as e:
            print(f"[PRE-SESSION][ERRO] Falha ao gerar o briefing: {e}")
            return None

if __name__ == "__main__":
    briefing = PreSessionBriefing()
    briefing.run_briefing()
