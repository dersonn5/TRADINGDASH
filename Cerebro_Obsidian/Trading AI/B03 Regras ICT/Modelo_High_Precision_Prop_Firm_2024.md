# 📐 Nota Mestra: Modelo High-Precision Prop Firm (ICT 2024)

Este documento codifica o modelo de trading de curto prazo de alta precisão e agressividade, baseado nas mentorias do ICT de **2023 e 2024**. Este é o setup predileto de traders de mesas proprietárias (Prop Firms) para alavancagem de contas e consistência rápida de saques.

---

## ⚡ 1. A Filosofia do Modelo 2024: O Tempo Domina o Preço

No modelo ICT de 2024, **o Tempo (Time) é a variável primária e o Preço (Price) é a secundária**. Se o setup gráfico ocorrer no preço correto, mas fora da janela do algoritmo temporal (Macro), a probabilidade cai drasticamente e o trade deve ser evitado.

### A Hierarquia Temporal de Execução:
*   **Timeframe de Direção (15m)**: Usado para mapear a estrutura intradiária e definir o **Draw on Liquidity (DOL)** (para onde o mercado está sendo atraído).
*   **Timeframe de Contexto (5m)**: Usado para mapear Order Blocks, Breakers de maior relevância e a tendência imediata.
*   **Timeframe de Gatilho (1m)**: É onde a mágica acontece. A entrada é refinada no gráfico de 1 minuto para obter **Stop Loss curtíssimos**, maximizando a relação Risco-Retorno (R:R de 1:3 a 1:5+).

---

## 🦄 2. Setup Central: O Modelo "Unicorn" (Unicórnio)

O **Unicorn Setup** é um dos modelos mais assertivos e agressivos do ICT moderno, pois une dois dos mais fortes "PD Arrays" de fluxo institucional em uma única zona de confluência:

```
        Vela 1: [Impulso Forte]
        Vela 2: [Rompimento de Estrutura (Breaker Block)]  <-- ZONA DE
        Vela 3: [Imbalanço de Preço (Fair Value Gap)]     <-- SOBREPOSIÇÃO (UNICORN)
```

### Regras de Entrada do Unicorn:
1.  **Varredura (Sweep)**: O preço varre a liquidez de um topo ou fundo local (Asian Range ou 24h High/Low).
2.  **Deslocamento Agressivo (MSS)**: O preço faz uma reversão forte que rompe um swing point estrutural anterior, caracterizando o **Breaker Block**.
3.  **A Sobreposição do FVG**: O rompimento agressivo deve deixar um **Fair Value Gap (FVG)**. A entrada é programada exatamente onde o **FVG se sobrepõe ao Breaker Block** (a zona Unicórnio).
4.  **Stop Loss Curto**: Posicionado logo acima/abaixo do Breaker Block (e não da máxima do sweep), reduzindo o risco pela metade.
5.  **Alvo Agressivo**: Mira o DOL macro de 15m, gerando R:R excelentes de forma rápida.

---

## 🔄 3. O Gatilho de Continuidade: Inversion FVG (IFVG)

A **Inversion FVG (IFVG)** é o conceito de FVG invertido, introduzido na Mentoria de 2023, perfeito para trades agressivos de continuidade de tendência quando o preço não retorna à zona de desconto:

*   **Bullish IFVG**: Ocorre quando o preço está em tendência forte de alta e ignora/fecha com corpo de vela acima de um **FVG bearish** (SIBI) anterior. Esse FVG agora se inverte e funciona como uma zona de suporte de alta confiabilidade para compra imediata.
*   **Bearish IFVG**: Ocorre quando o preço está em tendência de baixa e fecha com corpo abaixo de um **FVG bullish** (BISI) anterior. A zona inverte e passa a agir como resistência para venda.

```
                  [Corpo fecha acima da FVG Bearish]
                       |
        ======== FVG BEARISH ORIGINAL ======== (Inverte para Suporte de Alta)
                       |
               [Reteste e Entrada de COMPRA]
```

---

## ⏰ 4. As Macros Algorítmicas (Janelas de Entrega de Preço)

As **Macros** são micro-janelas de tempo de 20 a 30 minutos programadas no algoritmo interbancário para distribuir preço e caçar liquidez. Operar estritamente dentro destas janelas elimina o ruído lateral:

### Principais Macros da Sessão de Nova York (EST / Horário de NY):
*   **Macro 1: 08:50 AM – 09:10 AM**: Caçada de liquidez pré-abertura de NY. Seta o viés da manhã.
*   **Macro 2: 09:50 AM – 10:10 AM**: Montagem do setup clássico de Silver Bullet e reversão/continuação pós-abertura do mercado de ações (09:30 AM).
*   **Macro 3: 10:50 AM – 11:10 AM**: Pico de distribuição e expansão do dia em direção ao DOL da manhã.
*   **Macro 4: 11:50 AM – 12:10 PM**: Macro do almoço de NY, geralmente caça a liquidez final antes da calmaria.

---

## 📋 Checklist de Execução Prop Firm (Mesa Proprietária)

Para executar este modelo de forma mecânica e sem hesitação:

*   [ ] **1. Identificar o DOL (15m)**: O preço tem um alvo magnético claro não mitigado (máxima/mínima recente, FVG HTF)?
*   [ ] **2. Alinhamento de Tendência**: O sinal de 1m está a favor da tendência da EMA 200 intradiária?
*   [ ] **3. Janela de Macro Ativa**: O horário atual está dentro de uma das Macros Algorítmicas (ex: 08:50-09:10, 09:50-10:10, 10:50-11:10)?
*   [ ] **4. Unicorn ou IFVG em 1m**:
    *   *Unicorn*: Entrada pendurada no reteste do FVG dentro do Breaker Block de 1m.
    *   *IFVG*: Entrada no fechamento de vela que inverteu o FVG anterior em 1m.
*   [ ] **5. Risco Controlado**: Risco estrito de 0.5% a 1.0% por operação. Stop Loss técnico logo atrás do Breaker/IFVG.

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Power_of_3_e_AMD|Power of 3 & AMD]]
- [[B03 Regras ICT/Modelo_Mentoria_2023_e_MMXM|Mentoria 2023 & MMXM]]
- [[B03 Regras ICT/Algoritmo_IPDA_e_Ciclos_Tempo|Algoritmo IPDA & Ciclos]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]