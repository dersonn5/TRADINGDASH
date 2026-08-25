# Relatório de Auditoria Técnica — Breaker Block Strategy

Este documento apresenta a análise técnica detalhada sobre a estratégia de **Breaker Block** (`strategies/breaker_block_nq.py`, `strategies/breaker_block_xau.py` e a lógica base em `strategies/base.py`).

---

## 1. Verificação de Look-Ahead Bias (Dados Futuros)

**Veredito:** **SIM. Existe um look-ahead bias crítico na determinação do Daily Bias (PO3) que invalida a fidedignidade dos backtests.**

### Prova de Código do Viés:

No arquivo do backtester (`backtesting/engine.py:221-222`), a série temporal diária é cortada da seguinte forma a cada iteração intraday (M5):
```python
idx_1d = df_1d.index.searchsorted(current_time, side='right')
history_1d = df_1d.iloc[:idx_1d]
```

Se o backtester está avaliando o candle operacional M5 das **13:20 EST de 21/01/2022**:
1. O timestamp diário de hoje (`2022-01-21 00:00:00 EST`) é menor ou igual ao tempo operacional (`2022-01-21 13:20:00 EST`).
2. Com `side='right'`, o `idx_1d` retorna a primeira posição estritamente maior que `13:20 EST` (que seria a barra do dia seguinte, `2022-01-22`).
3. Logo, `history_1d.iloc[-1]` (o último candle diário disponível no fatiamento) é a barra diária do **dia de hoje**.

Nas estratégias (`breaker_block_nq.py`, `breaker_block_xau.py` e até mesmo nas versões de `silver_bullet_nq.py`), a função `_get_daily_bias` lê este candle diário:
```python
def _get_daily_bias(self, candles_1d: pd.DataFrame) -> str:
    if len(candles_1d) < 2:
        return "NEUTRAL"
    last = candles_1d.iloc[-1]  # <--- Lê a barra diária do dia de hoje (em andamento)
    close, open_val = last["close"], last["open"]
    high, low = last["high"], last["low"]
    
    body_size = abs(close - open_val)
    total_range = high - low if high > low else 1.0
    
    if close > open_val and (high - close) / total_range < 0.3:
        return "BULLISH"
    elif close < open_val and (close - low) / total_range < 0.3:
        return "BEARISH"
    return "NEUTRAL"
```

### O Impacto:
Como o DataFrame de entrada diária (`candles_1d`) vem do arquivo estático de dados históricos do backtest, **as colunas `close`, `high` e `low` já contêm os valores finais fechados daquele dia (definidos às 17:00 EST)**.
* Às 13:20 EST, a estratégia já sabe exatamente se o dia de hoje **irá fechar** como uma barra fortemente altista ou baixista.
* Isso significa que o robô só opera compras em dias que fecharão em alta e vendas em dias que fecharão em queda, filtrando quase todos os trades falsos utilizando informações do futuro!
* **Conclusão:** A taxa de acerto de ~56% e o P&L positivo do backtest estão artificialmente inflados e não refletirão a realidade em ambiente real.

---

## 2. O Breaker Block ICT real está implementado corretamente?

**Veredito:** **NÃO. A lógica em `strategies/base.py` está extremamente simplificada e diverge do conceito ICT canônico em vários pontos estruturais.**

### Comparação de Lógica:

1. **Order Block (OB) Violado:**
   * *Código:* Considera a vela exata que forma o pivô de alta/baixa como o OB (`ob_high = highs[i]`, `ob_low = lows[i]`).
   * *ICT Real:* O OB que vira Breaker é a última vela de alta/baixa antes do movimento de sweep, que pode não ser apenas a vela exata do pivô de reversão.
2. **Liquidity Sweep (Varrer Topo/Fundo):**
   * *Código:* Não há validação local de sweep na estrutura do Breaker. O código apenas busca qualquer pivô recente e checa se ele foi rompido.
   * *ICT Real:* Um Breaker Block **exige** que o preço limpe a liquidez acima de um swing high anterior (gerando um novo topo mais alto) antes de quebrar a estrutura. Sem essa validação, o algoritmo confunde **Breaker Blocks** (com sweep) com **Mitigation Blocks** (sem sweep).
3. **Displacement Forte (MSS):**
   * *Código:* Implementado na verificação de `body >= atr_multiplier * atr_val` (Displacement com base no ATR).
   * *ICT Real:* Rompimento violento e com corpo de candle significativo na direção oposta. **[CORRETO NO CÓDIGO]**
4. **Reteste da Zona Violada:**
   * *Código:* Checa se o preço atual está dentro da zona, mas não rastreia se a zona já foi violada e invalidada anteriormente por um fechamento além do extremo.
   * *ICT Real:* Entrada no retorno do preço à zona do antigo OB (ex: 50% Consequent Encroachment). **[PARCIALMENTE CORRETO, MAS FRÁGIL NO CÓDIGO]**
5. **Market Structure Shift (MSS):**
   * *Código:* Define o rompimento como o fechamento abaixo da *mínima do candle do pivô* (`closes[j] < ob_low`), e não abaixo do swing low estrutural do mercado.
   * *ICT Real:* Quebra do swing structure de mercado (swing low anterior).

---

## 3. Resultados de 2022 (Bear Market) Isolados & Impacto do Viés

Isolei os dados de performance apenas para o ano de **2022** (que representou um bear market severo de queda de ~65% no BTC e ~75% no ETH) sob o ambiente **Stressed** (com slippage físico, embargo temporal e comissões) e comparei o cenário **Com Viés** (original) vs. **Sem Viés** (real):

### 📈 BTC/USDT (2022 Isolado)
* **Cenário Com Viés (Oracle):** 44 trades | **52.3% WR** | **+$283.34 USD** PnL
* **Cenário Sem Viés (Real):** 43 trades | **30.2% WR** | **-$235.50 USD** PnL | **Fator de Lucro: 0.87**

### 📈 ETH/USDT (2022 Isolado)
* **Cenário Com Viés (Oracle):** 45 trades | **48.9% WR** | **+$166.65 USD** PnL
* **Cenário Sem Viés (Real):** 53 trades | **39.6% WR** | **+$54.61 USD** PnL | **Fator de Lucro: 1.03**

### 📊 Desempenho Histórico Geral Unbiased (3 Anos: 2022-2024)
Após a remoção completa do viés, o robô foi submetido ao backtest completo de 3 anos no ambiente **Stressed**:

#### BTC/USDT (Breaker Block)
* **2022:** 43 trades | 30.2% WR | PF: 0.87 | PnL: -$235.50 USD
* **2023:** 33 trades | 42.4% WR | PF: 1.25 | PnL: +$328.63 USD
* **2024:** 44 trades | 45.5% WR | PF: 1.26 | PnL: +$678.42 USD
* **Total Acumulado:** 120 trades | 37.3% WR | **PF: 1.04** | **PnL: +$254.44 USD**

#### ETH/USDT (Breaker Block)
* **2022:** 53 trades | 39.6% WR | PF: 1.03 | PnL: +$54.61 USD
* **2023:** 35 trades | 45.7% WR | PF: 1.26 | PnL: +$223.97 USD
* **2024:** 46 trades | 63.0% WR | PF: 1.95 | PnL: +$1142.62 USD
* **Total Acumulado:** 129 trades | 48.1% WR | **PF: 1.24** | **PnL: +$974.50 USD**

### Análise Crítica dos Resultados:
1. **O Efeito Oracle Exposto:** A remoção do look-ahead bias confirmou nossa hipótese. No BTC, o viés sustentava a estratégia no azul em 2022. Sem ele, a estratégia faliu (**PF 0.87** e PnL negativo), pois comprou wicks de topo e vendeu wicks de fundo em um mercado puramente em queda livre. No ETH, reduziu o desempenho a um mero breakeven (**PF 1.03**).
2. **Ciclos de Mercado e Edge Real:** Fica evidente que a estratégia Breaker Block atual sofre muito em mercados laterais ou de forte tendência unidirecional violenta (como o Bear Market de 2022). No entanto, em mercados em recuperação/bullish estável (como **ETH em 2024**), a estratégia performou incrivelmente bem (**PF 1.95** e **+$1.142,62** PnL), mostrando que o edge de volatilidade existe, mas é altamente condicional.
3. **Conclusão:** O robô está agora com métricas **reais**. O Breaker Block não está pronto para rodar live de forma irrestrita, precisando urgentemente da refatoração lógica do sweep e MSS.

---

## 🛠️ Recomendações Atualizadas de Próximos Passos

Agora que o look-ahead bias foi corrigido em todas as estratégias e as métricas reais foram consolidadas:

### 1. Colocar Silver Bullet (ETH/USDT) em Live Testnet
O **Silver Bullet** em **ETH/USDT** é o nosso maior vencedor real:
* **Fator de Lucro Real (Stressed):** **1.59** (acima da barreira de 1.5)
* **Taxa de Acerto Real:** **63.6%**
Este setup tem edge estatístico real comprovado e deve ser ativado imediatamente em ambiente de simulação live (Testnet).

### 2. Executar Fase 2: Refatorar o Breaker Block
Como a barreira do Silver Bullet de PF > 1.5 foi batida em ETH, vale a pena o esforço de refatorar o Breaker Block em `strategies/base.py` para:
1. Implementar o **Liquidity Sweep real** local (evitando confundir Breaker com Mitigation Block).
2. Corrigir o **MSS estrutural** (usando swing lows de estrutura em vez da mínima simples do candle do pivô).
3. Rastrear a invalidação da zona de reteste para evitar trades redundantes no mesmo bloco violado.
Re-testar após a refatoração para verificar se o PF do ETH Breaker Block sobe de **1.24** para **> 1.5**.
