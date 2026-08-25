import json
import random
from pathlib import Path
from datetime import datetime, timedelta

def generate_scenarios():
    base_dir = Path(__file__).resolve().parent
    
    # -------------------------------------------------------------
    # 🥇 GOLD (XAUUSD) GENERATOR - 50 SCENARIOS
    # -------------------------------------------------------------
    xauusd_scenarios = []
    
    # Lista de setups básicos para diversificação
    setups_xau = [
        {"signal": "NY AM Silver Bullet FVG Touch", "killzone": "10:15 EST", "timeframe": "15m"},
        {"signal": "London Open Bullish OTE", "killzone": "03:30 EST", "timeframe": "15m"},
        {"signal": "NY PM Silver Bullet Bearish FVG", "killzone": "14:15 EST", "timeframe": "15m"},
        {"signal": "London Close Bearish Sweep & FVG", "killzone": "11:30 EST", "timeframe": "15m"},
        {"signal": "NY AM Silver Bullet OTE Discount", "killzone": "09:45 EST", "timeframe": "15m"}
    ]
    
    # Datarange: Últimos 6 meses (Novembro 2025 a Maio 2026)
    start_date = datetime(2025, 11, 1)
    
    for i in range(1, 51):
        # Gerar datas espaçadas uniformemente pelos 6 meses
        current_date = start_date + timedelta(days=(i * 3.5))
        # Evitar finais de semana
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            
        date_str = current_date.strftime("%Y-%m-%d")
        setup = random.choice(setups_xau)
        
        # Tipagem de cenários para testar regras cognitivas específicas da IA
        scenario_type = i % 5  # 0: Golden Win, 1: Counter-Bias Trap, 2: Out-of-Killzone Trap, 3: FVG CE Violation, 4: Consolidation Trap
        
        sc_id = f"SCENARIO-{i:03d}"
        symbol = "XAUUSD"
        
        if scenario_type == 0:
            # 🟢 Golden Win: Alinhamento perfeito
            bias = "BULLISH"
            action = "BUY"
            price = round(2200.0 + i * 4.5, 2)
            ict_signal = setup["signal"]
            time_of_day = setup["killzone"]
            outcome = "WIN"
            max_runup = 400.0
            max_drawdown = -60.0
            tp = price + 4.0
            sl = price - 1.5
            commentary = "Preco mitigou perfeitamente o CE da FVG de M15 apos varrer o SSL da abertura de Londres, com forte rejeicao (pavio longo) e formacao de MSS com deslocamento agressivo no grafico de 1m."
            narrative = "Alinhamento de elite! SSL capturado na Killzone, preco respeitou o CE da FVG e atingiu o TP de forma explosiva."
            htf = "Estrutura HTF fortemente bullish, tendencia diaria fazendo topos e fundos ascendentes."
            liquidity = "Sell-side Liquidity (SSL) capturada na abertura da sessao fisica."
            draw_liq = "BSL pendente na maxima diaria anterior."
            applied = ["Modelo_Mentoria_2022", "Silver_Bullet_Algoritmica", "Consequent_Encroachment_FVG"]
            
        elif scenario_type == 1:
            # 🔴 Counter-Bias Trap (IA deve REJEITAR!)
            bias = "BULLISH"
            action = "SELL"
            price = round(2210.0 + i * 4.5, 2)
            ict_signal = "London Open Bearish OTE"
            time_of_day = "03:45 EST"
            outcome = "LOSS"
            max_runup = 80.0
            max_drawdown = -300.0
            tp = price - 6.0
            sl = price + 2.0
            commentary = "O preco tocou a zona Premium OTE de 79%, porem o Daily Bias diario macro e extremamente de alta (BULLISH) e o order flow H4 nao apresenta nenhuma quebra de estrutura de baixa. Operar contra a tendencia principal e de alto risco."
            narrative = "Setup contra a tendencia diaria forte de alta. IA rejeitou corretamente salvando stop."
            htf = "Daily Bias fortemente bullish. Ordem de fluxo HTF de alta dominando o mercado."
            liquidity = "Pequena varredura local de BSL, mas insignificante perante o fluxo macro."
            draw_liq = "BSL pendente em niveis muito mais altos."
            applied = ["Optimal_Trade_Entry_OTE"]
            
        elif scenario_type == 2:
            # 🔴 Out of Killzone Trap (IA deve REJEITAR!)
            bias = "BEARISH"
            action = "SELL"
            price = round(2205.0 + i * 4.5, 2)
            ict_signal = "Late NY Bearish FVG Touch"
            time_of_day = "12:15 EST"  # Horario de almoco / fora de Killzone!
            outcome = "LOSS"
            max_runup = 50.0
            max_drawdown = -350.0
            tp = price - 4.5
            sl = price + 2.0
            commentary = "O sinal de FVG foi mitigado as 12:15 EST, que esta completamente fora de qualquer Killzone institucional valida de ICT. Baixo volume de mercado devido ao horario de almoco dos bancos americanos, alta chance de consolidaçoes manipulativas."
            narrative = "Operacao executada no horario de almoco de NY, sem liquidez institucional. Preco consolidou e violou o SL."
            htf = "HTF bearish, porem sem momentum na sessao da tarde."
            liquidity = "Nenhuma varredura de liquidez de HTF antes do setup."
            draw_liq = "Suporte local fraco."
            applied = ["Daily_Bias_e_Order_Flow"]

        elif scenario_type == 3:
            # 🔴 FVG CE Violation (IA deve REJEITAR!)
            bias = "BULLISH"
            action = "BUY"
            price = round(2202.0 + i * 4.5, 2)
            ict_signal = "NY AM Silver Bullet FVG entry"
            time_of_day = "10:10 EST"
            outcome = "LOSS"
            max_runup = 70.0
            max_drawdown = -400.0
            tp = price + 5.0
            sl = price - 2.0
            commentary = "ATENÇAO CRITICA: O corpo de vela do grafico de M5 fechou de forma nitida e decisiva ABAIXO do Consequent Encroachment (50%) do Fair Value Gap em andamento, violando o suporte institucional."
            narrative = "O preco fechou com corpo de vela M5 abaixo de 50% (CE) da FVG, invalidando o setup. IA recusou."
            htf = "HTF bullish, mas fraqueza local invalidou a FVG."
            liquidity = "Varrido SSL local de forma apressada."
            draw_liq = "Resistencia local."
            applied = ["Silver_Bullet_Algoritmica", "Consequent_Encroachment_FVG"]

        else:
            # 🔴 Consolidation Trap (IA deve REJEITAR!)
            bias = "NEUTRAL"
            action = "BUY"
            price = round(2208.0 + i * 4.5, 2)
            ict_signal = "NY AM FVG entry in Consolidation"
            time_of_day = "10:05 EST"
            outcome = "LOSS"
            max_runup = 50.0
            max_drawdown = -300.0
            tp = price + 5.0
            sl = price - 2.5
            commentary = "O preco de H4 esta preso em um range lateral extremamente apertado (consolidaçao) ha 3 dias consecutivos. Ausencia completa de expansao institucional e falta de direcionamento claro de mercado, alto risco de violinaçoes."
            narrative = "Preco travado em range lateral ha 3 dias. Mercado sem expansao macro. IA rejeitou."
            htf = "Estrutura HTF em consolidaçao estreita de H4."
            liquidity = "Sem varredura relevante."
            draw_liq = "Indefinido devido a lateralidade."
            applied = ["Silver_Bullet_Algoritmica"]

        xauusd_scenarios.append({
            "id": sc_id,
            "date": date_str,
            "time_of_day_est": time_of_day,
            "symbol": symbol,
            "action": action,
            "price": price,
            "timeframe": setup["timeframe"],
            "ict_signal": ict_signal,
            "daily_bias": bias,
            "htf_order_flow": htf,
            "draw_on_liquidity": draw_liq,
            "liquidity_swept": liquidity,
            "fvg_high": round(price + 0.8, 2),
            "fvg_low": round(price - 0.8, 2),
            "fvg_ce": price,
            "commentary": commentary,
            "applied_rules": applied,
            "historical_outcome": {
                "result": outcome,
                "max_runup_usd": max_runup,
                "max_drawdown_usd": max_drawdown,
                "real_tp": tp,
                "real_sl": sl,
                "narrative": narrative
            }
        })

    # -------------------------------------------------------------
    # 🗽 NASDAQ (NQ) GENERATOR - 50 SCENARIOS
    # -------------------------------------------------------------
    nq_scenarios = []
    
    setups_nq = [
        {"signal": "NY AM Silver Bullet FVG Touch", "killzone": "10:15 EST", "timeframe": "15m"},
        {"signal": "London Open Bearish OTE", "killzone": "03:30 EST", "timeframe": "15m"},
        {"signal": "NY PM Silver Bullet FVG entry", "killzone": "14:20 EST", "timeframe": "15m"},
        {"signal": "NY AM Silver Bullet Bullish MSS", "killzone": "09:45 EST", "timeframe": "15m"},
        {"signal": "London Close Sweep & FVG", "killzone": "11:15 EST", "timeframe": "15m"}
    ]
    
    for i in range(1, 51):
        current_date = start_date + timedelta(days=(i * 3.5))
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
            
        date_str = current_date.strftime("%Y-%m-%d")
        setup = random.choice(setups_nq)
        
        scenario_type = i % 5  # 0: Golden Win, 1: Counter-Bias Trap, 2: Out-of-Killzone Trap, 3: FVG CE Violation, 4: Consolidation Trap
        
        sc_id = f"SCENARIO-{i:03d}"
        symbol = "NQ"
        
        if scenario_type == 0:
            bias = "BEARISH"
            action = "SELL"
            price = round(17000.0 - i * 15.0, 2)
            ict_signal = setup["signal"]
            time_of_day = setup["killzone"]
            outcome = "WIN"
            max_runup = 350.0
            max_drawdown = -50.0
            tp = price - 25.0
            sl = price + 8.0
            commentary = "O indice mitigou de forma precisa a FVG na Killzone de NY logo apos a captura de BSL acima do topo asiatico, confirmando MSS com deslocamento agressivo e corpo de vela fechando na direçao de baixa."
            narrative = "Excelente! Mitigacao perfeita no premio da OTE, o preco expandiu e bateu o TP com agressividade."
            htf = "HTF fortemente de baixa, estrutura fazendo topos e fundos descendentes no D1."
            liquidity = "BSL capturada acima da maxima da sessao asiatica."
            draw_liq = "SSL do fundo da semana posicionado em niveis mais baixos."
            applied = ["Modelo_Mentoria_2022", "Silver_Bullet_Algoritmica", "Optimal_Trade_Entry_OTE"]
            
        elif scenario_type == 1:
            bias = "BEARISH"
            action = "BUY"
            price = round(17050.0 - i * 15.0, 2)
            ict_signal = "NY AM Silver Bullet OTE Discount"
            time_of_day = "09:50 EST"
            outcome = "LOSS"
            max_runup = 60.0
            max_drawdown = -250.0
            tp = price + 30.0
            sl = price - 10.0
            commentary = "O sinal de compra (BUY) foi acionado em uma FVG intraday, porem a estrutura diaria de HTF e fortemente de baixa (Daily Bias Bearish) sem nenhum sinal macro de reversao institucional, o que anula a compra por ser contra a tendencia."
            narrative = "Setup contra a tendencia forte de baixa (Daily Bias Bearish). IA barrou a operacao."
            htf = "Daily Bias fortemente de baixa. Order flow HTF dominado por vendedores."
            liquidity = "Micro varredura local insignificante."
            draw_liq = "SSL pendente em niveis muito mais baixos."
            applied = ["Optimal_Trade_Entry_OTE"]
            
        elif scenario_type == 2:
            bias = "BULLISH"
            action = "BUY"
            price = round(17020.0 - i * 15.0, 2)
            ict_signal = "NY PM Market Close Bullish Sweep"
            time_of_day = "16:20 EST"  # Fora de todas as Killzones!
            outcome = "LOSS"
            max_runup = 40.0
            max_drawdown = -300.0
            tp = price + 25.0
            sl = price - 10.0
            commentary = "O sinal tecnico ocorreu as 16:20 EST, que esta localizado no encerramento e apos o fechamento oficial do mercado regular de Nova York. Sem volume e fora das Killzones de execuçao institucional."
            narrative = "Operacao fora de Killzone (final de pregao de NY).IA recusou."
            htf = "HTF bullish, mas sem volatilidade relevante de volume institucional."
            liquidity = "Nenhuma varredura importante."
            draw_liq = "Resistencia de topo fraca."
            applied = ["Daily_Bias_e_Order_Flow"]

        elif scenario_type == 3:
            bias = "BEARISH"
            action = "SELL"
            price = round(17010.0 - i * 15.0, 2)
            ict_signal = "NY AM Silver Bullet FVG entry"
            time_of_day = "10:15 EST"
            outcome = "LOSS"
            max_runup = 80.0
            max_drawdown = -400.0
            tp = price - 20.0
            sl = price + 8.0
            commentary = "ATENÇAO CRITICA: O corpo da vela de M5 fechou de forma decisiva e expressiva ACIMA do Consequent Encroachment (50%) do FVG de baixa, invalidando a resistencia dos vendedores."
            narrative = "Candle de M5 fechou acima do CE de 50% da FVG de baixa, invalidando o setup. IA barrou."
            htf = "HTF de baixa, mas momentum local violou o CE."
            liquidity = "SSL sweep local fraco."
            draw_liq = "Fundo local."
            applied = ["Silver_Bullet_Algoritmica", "Consequent_Encroachment_FVG"]

        else:
            bias = "NEUTRAL"
            action = "SELL"
            price = round(17030.0 - i * 15.0, 2)
            ict_signal = "NY AM FVG entry in Consolidation"
            time_of_day = "10:10 EST"
            outcome = "LOSS"
            max_runup = 40.0
            max_drawdown = -350.0
            tp = price - 25.0
            sl = price + 10.0
            commentary = "O indice esta travado dentro de uma lateralidade estreita no grafico de H1, sem qualquer sinal de expansao de bias ou deslocamento de ordens institucionais. Alto risco de violinaçao lateral."
            narrative = "Indice preso em lateralidade estreita no grafico de 1 hora. Risco alto de violinada. IA barrou."
            htf = "Estrutura HTF acumulando lateralmente sem tendencia definida."
            liquidity = "Sem sweep relevante."
            draw_liq = "Indefinido."
            applied = ["Silver_Bullet_Algoritmica"]

        nq_scenarios.append({
            "id": sc_id,
            "date": date_str,
            "time_of_day_est": time_of_day,
            "symbol": symbol,
            "action": action,
            "price": price,
            "timeframe": setup["timeframe"],
            "ict_signal": ict_signal,
            "daily_bias": bias,
            "htf_order_flow": htf,
            "draw_on_liquidity": draw_liq,
            "liquidity_swept": liquidity,
            "fvg_high": round(price + 4.0, 2),
            "fvg_low": round(price - 4.0, 2),
            "fvg_ce": price,
            "commentary": commentary,
            "applied_rules": applied,
            "historical_outcome": {
                "result": outcome,
                "max_runup_usd": max_runup,
                "max_drawdown_usd": max_drawdown,
                "real_tp": tp,
                "real_sl": sl,
                "narrative": narrative
            }
        })

    # Gravar arquivos JSON consolidados de 50 cenários
    with open(base_dir / "scenarios_xauusd.json", "w", encoding="utf-8") as f:
        json.dump(xauusd_scenarios, f, indent=4, ensure_ascii=False)
        
    with open(base_dir / "scenarios_nq.json", "w", encoding="utf-8") as f:
        json.dump(nq_scenarios, f, indent=4, ensure_ascii=False)

    print("SUCESSO: Gerados 50 cenarios para XAUUSD e 50 cenarios para NQ (Total: 100 cenarios de 6 meses)!")

if __name__ == "__main__":
    generate_scenarios()
