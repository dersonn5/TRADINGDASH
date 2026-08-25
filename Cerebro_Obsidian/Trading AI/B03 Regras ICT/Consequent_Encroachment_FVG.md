# Regras de ICT - Consequent Encroachment (FVG 50%)

O *Consequent Encroachment* (CE) é o ponto de equilíbrio exato (50%) de um Fair Value Gap (FVG). É um dos filtros mais poderosos e refinados de ICT, servindo como uma "linha na areia" para validar ou invalidar setups e obter entradas com risco extremamente reduzido.

---

## 1. A Lógica do Consequent Encroachment
O preço não precisa preencher 100% de uma FVG para continuar o movimento. Na verdade, em desequilíbrios institucionais muito fortes, o algoritmo interbancário costuma rebalancear o preço **exatamente até a metade (50%)** da FVG e imediatamente retomar a direção.

```
Vela 1: [ ] (Máxima) ─────────── Início da FVG
         |
         |  - - - - - - - - - -  CONSEQUENT ENCROACHMENT (50% do Gap)
         |
Vela 3: [ ] (Mínima) ─────────── Fim da FVG
```

---

## 2. Como Mapear e Utilizar o CE
1. **Identificar o FVG**: Encontrar um FVG de 3 velas válido no gráfico de M15 ou M1.
2. **Medição**: Traçar uma retração de Fibonacci do topo do FVG ao fundo do FVG. O nível de **0.50 (50%)** é o seu Consequent Encroachment (CE).
3. **Ordem Limite (Risco Otimizado)**:
   - Em vez de entrar no início do FVG (que deixa o Stop Loss mais longo), colocar a ordem limite de entrada posicionada **exatamente no preço do CE (50%)**.
   - Isso reduz drasticamente a distância para o Stop Loss, aumentando substancialmente a relação Risco:Retorno (payout).

---

## 3. A Regra de Invalidação de Vela (Olhar Clínico)
A IA deve monitorar ativamente como os corpos dos candles reagem ao Consequent Encroachment:

> [!WARNING]
> **Corpo de Vela Cruzando o CE**: Pavios podem passar do CE de 50% (isso é apenas uma busca de liquidez interna). No entanto, se o **corpo** de qualquer candle de M15 ou M5 fechar decisively **além do nível de 50% (CE)** da FVG, o setup de trading é **desqualificado e cancelado**!
> - **Motivo**: O fechamento do corpo de vela além do CE demonstra fraqueza na estrutura do FVG, indicando alta probabilidade de o gap ser totalmente violado e bater no Stop Loss.


---

## 4. Cláusula de Execução Específica para Commodities (XAUUSD)
O Ouro (XAUUSD) é uma commodity altamente volátil de alta liquidez e famosa por **Varreduras Duplas (Double Sweeps)** e falsos rompimentos de varejo. Para alcançar consistência institucional no Ouro, a IA DEVE aplicar as seguintes regras restritivas antes de aprovar qualquer operação:

> [!IMPORTANT]
> **As Três Leis de Blindagem do Ouro (XAUUSD)**:
> 1. **Proibição de Mitigação Direta**: É estritamente proibido entrar em ordens limites diretas no CE da FVG de 15m no XAUUSD sem confirmação. O preço no Ouro costuma romper o CE para limpar liquidez antes de reverter.
> 2. **Exigência de MSS em Baixo Timeframe (M1/M5)**: O robô deve aguardar o preço mitigar o CE de 15m e, em seguida, fazer uma reversão estrutural (MSS) no gráfico de 1m ou 5m com **deslocamento de corpo de vela forte** na direção desejada antes de acionar a entrada.
> 3. **Filtro SMT (Symbolic Market Trilogy)**: Compare o comportamento do XAUUSD com a Prata (XAGUSD). Se o Ouro varrer a liquidez de um fundo mas a Prata falhar em varrer (Divergência SMT), a reversão é patrocinada institucionalmente. Se não houver divergência, reduza a confiança da operação e aborte caso o bias diário esteja fraco.

---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/FVG_e_MSS|FVG & MSS]]
- [[B03 Regras ICT/Balanced_Price_Range_BPR|Balanced Price Range (BPR)]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]