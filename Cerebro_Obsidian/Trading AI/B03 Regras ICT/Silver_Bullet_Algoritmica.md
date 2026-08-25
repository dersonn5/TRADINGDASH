# Regras de ICT - Silver Bullet (Bala de Prata Algorítmica)

A Silver Bullet é uma estratégia puramente baseada em tempo e algoritmo interbancário, que se aproveita de janelas específicas de 60 minutos onde o algoritmo é programado para gerar liquidez e mitigar desequilíbrios do mercado.

---

## 1. As 3 Janelas Horárias Sagradas (Horário de Nova York - EST/EDT)
> [!IMPORTANT]
> **Filtro de Tempo Estrito**: A IA deve desqualificar qualquer setup que se forme fora dessas janelas exatas. O trigger de entrada deve ser acionado apenas dentro destes limites horários.

1. **London Open Silver Bullet (03:00 - 04:00 AM EST)**
   - Ativos Ideais: XAUUSD, EURUSD, GBPUSD.
   - Cenário: Ocorre a varredura do range da sessão asiática e mitigação inicial de FVGs macros.
2. **New York AM Session Silver Bullet (10:00 - 11:00 AM EST)**
   - Ativos Ideais: NQ Mini, ES Mini, XAUUSD.
   - Cenário: Sessão de altíssima volatilidade líquida. Ocorre após a abertura física do mercado de Nova York (09:30 AM EST). Excelente para reversões de tendência ou continuação estrutural.
3. **New York PM Session Silver Bullet (14:00 - 15:00 PM EST)**
   - Ativos Ideais: NQ Mini, ES Mini.
   - Cenário: Fim de tarde, focado na varredura dos topos/fundos criados na sessão da manhã de Nova York.

---

## 2. A Mecânica do Setup (Checklist de Execução)
*   **Timeframe de Entrada**: Gráfico de **1 minuto (1m) ou 5 minutos (5m)**.
*   **Meta Mínima**: 10 a 15 ticks em futuros (NQ/ES) ou 20 a 30 pips em Ouro (XAUUSD).
*   **Passo a Passo**:
    1. Aguardar o relógio bater o início exato da janela (ex: 10:00 AM EST).
    2. Identificar a liquidez mais próxima pendente (BSL ou SSL de sessões anteriores).
    3. Esperar o preço varrer essa liquidez.
    4. Identificar o primeiro **Fair Value Gap (FVG)** formado por um deslocamento violento.
    5. Posicionar ordem limite de entrada no FVG.
    6. Se o preço não retornar para tocar a FVG dentro da janela horária, a ordem é cancelada.

---

## 3. Gestão e Limites da Silver Bullet
- **Risco**: Risco fixo de **1%** por operação.
- **Relação R:R Mínima**: **1:2** para alvos curtos da Silver Bullet (focados em 15 ticks/pontos rápidos de Nasdaq), ou **1:2.5** para alvos estendidos.
- **Circuit Breaker**: Apenas **1 trade por janela**. Se a IA tomar loss ou win na janela, encerra a operação para essa janela específica.


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow|Daily Bias & Order Flow]]
- [[B03 Regras ICT/Modelo_Mentoria_2024_2026_e_Tape_Reading|Mentoria 2024/2026 & Tape Reading]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]