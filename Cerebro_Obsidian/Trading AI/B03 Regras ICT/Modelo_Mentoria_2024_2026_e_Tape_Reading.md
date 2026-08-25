# 📊 Nota Mestra: Mentoria ICT 2024/2026 & Tape Reading Avançado

Este documento codifica as atualizações de ponta da **Mentoria ICT 2024**, os refinamentos aplicados em **2025/2026** e as mecânicas de **Tape Reading (Leitura de Fluxo de Fita)** em baixíssimos timeframes (M1/15s).

---

## 1. Tape Reading (Leitura de Fluxo de Alta Resolução)
O **Tape Reading** na metodologia ICT não utiliza indicadores tradicionais, mas rastreia a entrega de preço interbancária em velas de **1 minuto (M1)** e **15 segundos (15s)**.

### Regras de Leitura do Fluxo:
*   **Velocidade e Deslocamento (Displacement)**: A IA deve monitorar a velocidade com que o preço passa por um nível chave. Velas longas com pouco pavio indicam que o IPDA está entregando preço com urgência institucional.
*   **Rebalanceamento Imediato (Immediate Rebalance)**: Se o preço forma um gap (FVG) e a vela seguinte o fecha e reverte instantaneamente, isso é um sinal de força institucional extrema (a ordem foi preenchida sem necessidade de acumulação).
*   **Rastreamento de Open Float**: Observar os topos e fundos locais em tempo real para identificar a formação de liquidez oculta de varejo.

---

## 2. Refinamento de Order Blocks (OB) de Alta Probabilidade (2025/2026)
Nas atualizações recentes de 2025 e 2026, o ICT refinou as regras de validação de um bloco de ordens institucional para eliminar "falsos OBs":

### Filtros Rigorosos de Validação:
1.  **Filtro do Pavio (Wick Validation)**: O corpo do candle do Order Block deve ser maior do que 50% de sua amplitude total (máxima-mínima). Se o pavio for muito longo, o bloco é desclassificado (pois indica indecisão, não acumulação institucional).
2.  **Volume Imbalance Confluente**: Um OB é considerado de alta probabilidade apenas se a expansão que o originou deixar um **Volume Imbalance** ou uma FVG ativa logo acima/abaixo dele.
3.  **Invalidação de Fechamento**: O OB é instantaneamente invalidado se o corpo de qualquer vela fechar além da mínima (para OB Bullish) ou máxima (para OB Bearish) do bloco de ordens. Pavios são aceitos, mas o corpo fechar fora invalida o fluxo de ordens.

---

## 3. As Macros Algorítmicas de Tempo (Precisão ao Segundo)
Uma das grandes revelações da mentoria recente são os ciclos de **Macros de Tempo**. O IPDA opera em janelas específicas de minutos dentro da hora, onde executa varreduras automáticas de liquidez:

### Janelas de Macros Principais (EST/Nova York):
*   **09:50 - 10:10 AM EST**: A Macro de Abertura da Nasdaq/Ouro. Executa sweeps rápidos de liquidez local para capturar stop-loss antes da expansão das 10:00 AM (Silver Bullet).
*   **10:50 - 11:10 AM EST**: A Macro de Fechamento de Ciclo. O algoritmo costuma buscar retrações até o equilíbrio (50%) ou consolidar posições antes do almoço dos bancos.
*   **11:50 - 12:10 PM EST**: A Macro do Fechamento de Londres. Foco em reversões de contra-tendência de curto prazo.

### Regra de Ouro das Macros para a IA:
A IA deve priorizar entradas que ocorram **dentro** de uma dessas janelas de macro, pois a probabilidade de o preço explodir na direção do DOL sem acumulação lateral é 85% maior.

---

## 4. Checklist Clínico de Fluxo (Tape Reading)
*   [ ] **Macro Horária Ativa**: O setup disparou dentro de uma das janelas de macro (ex: 09:50-10:10)?
*   [ ] **Velocidade de Deslocamento**: A expansão em M1 ocorreu com corpos de vela limpos e volume institucional?
*   [ ] **OB Refinado**: O Order Block respeita o limite de corpo > 50% e não possui fechamento de corpo contra a estrutura?
*   [ ] **Immediate Rebalance**: Ocorreu rebalanceamento instantâneo de FVG em M1/15s?

---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Modelo_Mentoria_2023_e_MMXM|Mentoria 2023 & MMXM]]
- [[B03 Regras ICT/Gestao_de_Trade_e_Parciais|Gestão de Trade & Parciais]]
- [[B03 Regras ICT/Algoritmo_IPDA_e_Ciclos_Tempo]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]