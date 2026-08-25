# TASK — Path A: Implementar Setups ICT Públicos Validados

> **Self-contained. Executável por qualquer IDE/agente AI.**
> **SUPERSEDE:** [TASK_ICT_VAULT_BUILD.md](TASK_ICT_VAULT_BUILD.md) (caminho antigo, mais ambicioso, descartado em favor deste).

---

## Decisão estratégica

Após análise extensa, escolhido **Path A**: usar setups ICT publicamente documentados e validados pela comunidade, codificá-los exatamente como ensinados, validar com backtest rigoroso próprio, executar com disciplina via bot.

**Não inventar estratégia.** Reusar trabalho público + adicionar execução superior + filtros macro.

---

## Contexto do projeto

- **Localização:** `e:\AUTOMAÇÃO IA\TRADING AI\`
- **Stack existente:** FastAPI + Gemini + Obsidian RAG + MT5/Tradovate/Simulator + MCP TradingView client
- **Estado atual:** pipeline funciona end-to-end no simulador, backtester existente é defeituoso (ver `backtest_audit.md`)
- **Mercados alvo:** Nasdaq Futures (NQ/MNQ) + Gold (XAUUSD CFD)
- **Saldo conta teste:** $10.000 USD simulado

## Perfil do usuário

- 5 anos estudo mercado, foi quase lucrativo em B3
- Vinha de SMC adaptado + Al Brooks price action + estilo Ogro de Wall Street (André Machado) breakouts
- Sem pressão financeira (tem renda estável em IA)
- Pivot pra NQ/XAU agora
- Disciplina é o gargalo, não conhecimento

## Filosofia desta task

| Princípio | Tradução |
|---|---|
| Don't reinvent | Usa libs públicas existentes |
| Validate yourself | Backtest próprio é juiz final, não YouTube |
| Simple > clever | 2 setups bem feitos > 5 mal feitos |
| Mechanical entry | Bot decide entry sem AI no loop crítico |
| AI para contexto | Gemini só pré-sessão + journal + weekly review |
| Plan B sempre | Se backtest falhar, pivot pra ORB/trend following |

---

# FASES

## FASE 0 — Setup do ambiente (1-2h)

### 0.1 Dependências
Adicionar ao `requirements.txt`:
```
smartmoneyconcepts>=0.0.27   # joshyattridge, 1.7k stars, ativo
polygon-api-client>=1.14.0   # OFICIAL Polygon.io
plotly>=5.20.0               # gráficos backtest
pandas-ta>=0.3.14b           # indicadores TA (projeto incerto mas funciona)
yfinance>=0.2.40             # fallback se Polygon free tier limitar
```

**Backtrader NÃO incluído** — último release abr/2023, suporta só Python 3.2-3.7. Engine custom será implementada em `backtesting/engine.py` (Fase 3).

**Verificação de saúde das libs (executada antes desta task):**
- `smartmoneyconcepts`: ✅ 1.7k⭐, MIT, mantido por joshyattridge
- `polygon-api-client`: ✅ oficial Polygon.io, v1.16.3 out/2025
- `pandas-ta`: 🟡 projeto original parou 2024, comunidade fragmentada, mas funciona
- `yfinance`: 🟡 dados Yahoo têm gaps/ajustes — só fallback

### 0.2 Lib externa principal
Clonar/instalar `smart-money-concepts` (joshyattridge):
```bash
pip install smart-money-concepts
# Ou direto do source:
# git clone https://github.com/joshyattridge/smart-money-concepts
# cd smart-money-concepts && pip install -e .
```

**Funções principais da lib que vamos usar:**
- `smc.fvg(df)` — detecta Fair Value Gaps
- `smc.swing_highs_lows(df)` — swings
- `smc.bos_choch(df)` — Break of Structure / Change of Character (= MSS)
- `smc.ob(df)` — Order Blocks
- `smc.liquidity(df)` — pools de liquidez (Equal H/L)
- `smc.sessions(df)` — sessions Asian/London/NY
- `smc.previous_high_low(df)` — PDH/PDL

### 0.3 Dados históricos
Fontes (priorizadas):
1. **Polygon.io** — free tier 5 calls/min, 2 anos histórico. Suficiente pra protótipo.
2. **Databento** — pago mas barato (~$10 pra dataset histórico). Dados premium.
3. **yfinance** — free, dados degradados (gaps, ajustes). Apenas fallback.
4. **TradingView export** — manual, free, qualquer ativo.

**Para esta task, usar Polygon.io.** Configurar `POLYGON_API_KEY` no `.env`.

Símbolos:
- NQ: `X:NDQH26` (front month) ou `I:NDX` (Nasdaq 100 index proxy)
- XAU: `C:XAUUSD` (Polygon Forex/Metals)

Timeframes: M1, M5, M15, H1 (todos necessários).

### 0.4 Estrutura de arquivos a criar

```
e:\AUTOMAÇÃO IA\TRADING AI\
├── strategies/
│   ├── __init__.py
│   ├── base.py                    # Classe base Strategy + Trade
│   ├── silver_bullet_nq.py        # Setup #1
│   └── london_sweep_xau.py        # Setup #2
├── data/
│   ├── __init__.py
│   ├── polygon_client.py          # Wrapper Polygon.io
│   ├── data_loader.py             # Cache local + normalização
│   └── cached/                    # Parquet files locais
├── backtesting/
│   ├── __init__.py
│   ├── engine.py                  # Backtest loop com candle simulation
│   ├── metrics.py                 # Sharpe, Sortino, MDD, expectancy
│   ├── walk_forward.py            # Walk-forward orchestrator
│   └── reports/                   # Outputs HTML/MD
├── filters/
│   ├── __init__.py
│   ├── macro_filter.py            # DXY/ES/VIX cross-asset
│   ├── news_filter.py             # Economic calendar
│   ├── regime_filter.py           # ATR percentile
│   └── time_filter.py             # Killzones EST
├── execution/
│   ├── __init__.py
│   ├── live_runner.py             # Loop principal pra demo/live
│   └── order_manager.py           # Gestão entry/SL/TP/partials
└── TASK_PATH_A_EXECUTION.md       # Este arquivo
```

### 0.5 Validação Fase 0
```bash
python -c "from smartmoneyconcepts import smc; import pandas as pd; print('SMC lib OK')"
python -c "from polygon import RESTClient; print('Polygon OK')"
ls strategies/ data/ backtesting/ filters/ execution/
```

---

## FASE 1 — Setup #1: Silver Bullet NY AM (NQ) (3-5 dias)

### 1.1 Especificação canônica

Fonte: ICT 2022 Mentorship + documentação pública (YouTube/GitHub múltiplas implementações concordantes).

**Regras canônicas (NÃO modificar nesta fase):**

```
ATIVO: NQ (Nasdaq 100 Futures) ou MNQ (micro)
TIMEFRAME PRINCIPAL: M5 (entrada) + M15 (estrutura) + H1 (bias)

JANELA DE OPERAÇÃO: 10:00 AM - 11:00 AM EST (60 min strict)

PRÉ-REQUISITOS (avaliar 9:30 EST antes da janela):
  - Daily Bias definido via PO3 (Power of 3) do D1
  - HTF estrutura clara (H1 em trend ou estrutura definida)
  - Sweep prévio confirmado em sessão (Asian range OU PDH/PDL)

GATILHO (durante 10:00-11:00):
  1. Identificar FVG formado no movimento de deslocamento
  2. FVG deve estar alinhado com daily bias (FVG bullish se bias up, vice-versa)
  3. FVG deve estar em premium array (se short) ou discount array (se long)
     - Premium = acima do 50% do range do dia
     - Discount = abaixo do 50% do range do dia

ENTRADA:
  - Limit order no Consequent Encroachment (CE) = 50% do FVG
  - TIF: válido apenas até 11:00 EST (cancela se não preenche)

STOP LOSS:
  - Acima/abaixo do extremo do candle que criou o FVG
  - Buffer: +/- 2-3 ticks

TAKE PROFIT:
  - Próximo pool de liquidez (PDH/PDL/PWH/PWL ou swing recente)
  - Mínimo RR 1:2, ideal 1:3

INVALIDAÇÃO:
  - 11:00 EST: cancelar tudo, fechar tudo (zero overnight)
  - Preço fecha M5 oposto ao FVG antes da entrada: cancela
  - 2 entradas no dia: stop, não opera mais
```

### 1.2 Implementação `strategies/silver_bullet_nq.py`

Esqueleto:

```python
from dataclasses import dataclass
from datetime import time
from typing import Optional
import pandas as pd
from smartmoneyconcepts import smc
from strategies.base import Strategy, Trade, Signal

@dataclass
class SilverBulletConfig:
    killzone_start: time = time(10, 0)  # EST
    killzone_end: time = time(11, 0)
    max_trades_per_day: int = 2
    min_rr: float = 2.0
    sl_buffer_ticks: int = 3
    tick_size: float = 0.25  # NQ tick
    require_daily_bias: bool = True
    require_premium_discount: bool = True

class SilverBulletNQ(Strategy):
    name = "silver_bullet_nq"
    symbol = "NQ"
    timeframe_entry = "5m"
    timeframe_structure = "15m"
    timeframe_bias = "1h"

    def __init__(self, config: SilverBulletConfig = None):
        self.config = config or SilverBulletConfig()

    def evaluate(
        self,
        candles_5m: pd.DataFrame,
        candles_15m: pd.DataFrame,
        candles_1h: pd.DataFrame,
        candles_1d: pd.DataFrame,
    ) -> Optional[Signal]:
        # 1. Verificar killzone
        # 2. Calcular daily bias (PO3)
        # 3. Detectar FVGs no M5 da janela
        # 4. Filtrar FVGs alinhados com bias + premium/discount
        # 5. Retornar Signal se setup válido
        pass
```

**Métodos a implementar:**
- `_get_daily_bias(candles_1d) -> str` — bullish/bearish/neutral via PO3
- `_get_session_range(candles_5m, session)` — Asian/London range
- `_detect_fvgs_in_window(candles_5m, start, end)` — FVGs no killzone
- `_filter_aligned_fvgs(fvgs, bias, premium_discount)` — filtra alinhados
- `_calculate_ce(fvg)` — Consequent Encroachment
- `_find_nearest_liquidity_target(candles_15m, direction)` — TP target

### 1.3 Validação Fase 1
```bash
python -m strategies.silver_bullet_nq --test-on-date 2025-04-15
# Espera: log de evaluation step-by-step + decisão (signal ou no-signal)
```

---

## FASE 2 — Setup #2: London Sweep + FVG (XAU) (3-5 dias)

### 2.1 Especificação canônica

**Regras:**

```
ATIVO: XAUUSD (Gold CFD)
TIMEFRAME: M5 + M15 estrutura + H1 bias

JANELA DE OPERAÇÃO: 02:00 AM - 05:00 AM EST (London Open Killzone)

PRÉ-REQUISITOS (avaliar 02:00 EST):
  - Asian range identificado (00:00 - 02:00 EST)
  - Asian range high e low marcados
  - Daily bias definido (PO3 D1)

GATILHO (durante 02:00-05:00):
  1. Sweep do Asian High OU Asian Low (vela perfura + fecha do outro lado)
  2. Movimento de retorno cria FVG (gap 3 candles)
  3. FVG alinhado com daily bias
  4. Confirmação: MSS no M1/M5 após FVG

ENTRADA:
  - Limit order no CE do FVG
  - TIF: até 05:00 EST

STOP LOSS:
  - Além do pavio do sweep
  - Buffer: 5-10 ticks (XAU)

TAKE PROFIT:
  - Asian extremo oposto OU PDH/PDL OU swing high/low recente
  - Mínimo RR 1:2

INVALIDAÇÃO:
  - 05:00 EST: cancela e zera
  - Sweep do outro lado após entrada: cancela
  - 1 trade por sessão London (mais conservador que NQ)
```

### 2.2 Implementação `strategies/london_sweep_xau.py`

Mesma estrutura do Silver Bullet, adaptada. Reusar `strategies/base.py`.

### 2.3 Validação Fase 2
Similar à 1.3.

---

## FASE 3 — Backtest Engine válido (5-7 dias)

### 3.1 Requisitos (corrigir críticos do `backtest_audit.md`)

**Obrigatório:**
- ✅ Candle-by-candle simulation (não atalho `if outcome == WIN`)
- ✅ Slippage realista por ativo (NQ 0.25-0.50 pts, XAU 0.20-0.50)
- ✅ Comissão por trade (NQ ~$2 round trip, XAU ~$5)
- ✅ Spread incluído (XAU ~30 cents, NQ ~0.25)
- ✅ Latência de execução simulada (200-500ms)
- ✅ Stop hunt simulado (wick que toca SL mesmo se fecha além)
- ✅ Walk-forward (4-6 janelas temporais distintas)
- ✅ Out-of-sample 30% dos dados intocado até final
- ✅ Sem look-ahead (verificar manualmente em cada estratégia)
- ✅ Sample mínimo: 100 trades por setup

### 3.2 Implementação `backtesting/engine.py`

```python
@dataclass
class BacktestConfig:
    start_date: str
    end_date: str
    initial_balance: float = 10000.0
    slippage_ticks: dict = ...
    commission_per_trade: dict = ...
    spread: dict = ...
    latency_ms: int = 300

@dataclass
class BacktestResult:
    trades: list[Trade]
    equity_curve: pd.Series
    stats: dict  # PF, Sharpe, Sortino, MDD, expectancy, win_rate
    
class BacktestEngine:
    def run(self, strategy, candles_dict: dict, config: BacktestConfig) -> BacktestResult:
        # Iterate candle-by-candle (M5)
        # Em cada candle:
        #   1. Atualiza posições abertas (verifica SL/TP touch)
        #   2. Chama strategy.evaluate() com janela histórica até candle atual
        #   3. Se signal: cria pending order (limit)
        #   4. Próximo candle: verifica fill
        # Compute final stats
        pass
```

### 3.3 Walk-forward

```python
class WalkForwardEngine:
    def run(self, strategy, candles_dict, n_splits=6, embargo_days=2):
        # Divide dados em N splits
        # Para cada split: treina (opcional, neste caso só backtesta) + valida
        # Embargo: 2 dias entre train/test pra evitar autocorrelação
        # Retorna stats por janela + agregado
        pass
```

### 3.4 Critérios go/no-go por setup

**Setup só avança pra Fase 5 (forward test) se:**

| Métrica | Mínimo |
|---|---|
| Total trades | ≥ 100 |
| Profit Factor | ≥ 1.5 |
| Sharpe Ratio | ≥ 1.0 |
| Max Drawdown | ≤ 15% |
| Win Rate | ≥ 40% |
| Avg RR realized | ≥ 1.5 |
| Consistência walk-forward | ≥ 4/6 janelas positivas |

**Se NÃO passa:** documentar, tentar Plan B (ORB ou trend following), não force.

### 3.5 Validação Fase 3
```bash
python -m backtesting.engine --strategy silver_bullet_nq --start 2023-01-01 --end 2025-04-30
python -m backtesting.walk_forward --strategy silver_bullet_nq --splits 6
# Output: HTML report em backtesting/reports/silver_bullet_nq_walkforward.html
```

---

## FASE 4 — Filtros macro (3-5 dias)

### 4.1 Filtros a implementar

**`filters/time_filter.py`** — killzones rigorosas EST com handling de DST

**`filters/regime_filter.py`** — ATR percentile 20d
- ATR atual / ATR média 20d
- Pula dia se >2.0 (volatilidade extrema) ou <0.5 (mercado morto)

**`filters/macro_filter.py`** — cross-asset
- DXY momentum diário → afeta XAU (inverso)
- ES gap → afeta NQ (positivo)
- VIX nível → afeta tudo (alto = não opera ICT swing)

**`filters/news_filter.py`** — economic calendar
- API: `tradingeconomics` ou scraping `investing.com`
- Bloqueia entrada ±30 min de high-impact news
- Lista de eventos: FOMC, CPI, NFP, PPI, GDP, payroll, jobless claims, retail sales
- Específico XAU: NFP, CPI, FOMC, Powell speeches
- Específico NQ: FOMC, CPI, big tech earnings (AAPL, MSFT, NVDA, GOOGL, META, AMZN)

### 4.2 Integração no backtest

Filtros aplicados ANTES do `strategy.evaluate()`. Se qualquer filtro falha, signal ignorado.

### 4.3 A/B test: com vs sem filtros

```bash
python -m backtesting.engine --strategy silver_bullet_nq --filters none
python -m backtesting.engine --strategy silver_bullet_nq --filters all
# Comparar: deve melhorar Sharpe + reduzir DD, possivelmente reduzir n trades
```

**Critério aceite filtros:** Sharpe aumenta OU MDD reduz ≥20% sem cortar >40% dos trades.

---

## FASE 5 — Forward test demo (3 meses)

### 5.1 Setup MT5 demo (XAU)
- Conta demo broker compatível (XM, IC Markets, etc)
- Configurar `.env`:
  ```
  EXECUTION_MODE=MT5
  MT5_LOGIN=...
  MT5_PASSWORD=...
  MT5_SERVER=...
  ```
- Símbolo: `XAUUSD` ou `GOLD`

### 5.2 Setup Tradovate demo (MNQ)
- Conta demo Tradovate
- Configurar:
  ```
  TRADOVATE_USER=...
  TRADOVATE_PASSWORD=...
  TRADOVATE_DEMO=true
  ```
- Símbolo: `MNQH26` (front month micro)

### 5.3 Live runner `execution/live_runner.py`

```python
async def main():
    # Loop infinito:
    # 1. Aguarda próxima killzone
    # 2. Pre-session: chama Gemini pra análise macro + define go/no-go do dia
    # 3. Durante killzone: poll M5 candles via MCP a cada 30s
    # 4. Avalia estratégia
    # 5. Se signal: aplica filtros macro
    # 6. Se passa filtros: posiciona ordem via MT5/Tradovate
    # 7. Monitora até TP/SL ou fim killzone
    # 8. Log trade no Obsidian + journal
    # 9. Próxima killzone
```

### 5.4 Regras de disciplina

**HARDCODED no código (você não consegue mudar sem editar):**
- Bot roda autonomamente
- Você NÃO toca por 3 meses
- Review apenas sábados, escreve notas em arquivo
- Mudanças no bot apenas no domingo seguinte ao review
- Se modificar mid-week: reseta contador 3 meses

### 5.5 Métricas a coletar

- Trade-by-trade log
- Daily PnL
- Slippage real vs simulado
- Latência real de execução
- Drift entre signals esperados vs executados
- Comparativo: bot vs backtest projeção

### 5.6 Critérios go/no-go pra Fase 6

**Avança pra live se:**
- 3 meses completos rodando
- PnL positivo OU breakeven (~+/- 5%)
- Drift backtest vs forward < 30%
- Você não interveio nenhuma vez
- Max DD < 15%
- Latência aceitável (<2s p99)

---

## FASE 6 — Micro live (3-6 meses)

### 6.1 Capital inicial
- $500-1000 USD
- Conta separada do patrimônio pessoal
- Considera capital "queimável" (não dói se perder)

### 6.2 Sizing conservador
- Risco 0.5% por trade (não 1% do plano original)
- Max 2 trades/dia
- Max DD diário 2%
- Max DD mensal 8% → pausa investigação

### 6.3 Instrumentos
- XAU: 0.01 lote (mini) MT5
- MNQ: 1 contrato micro

### 6.4 Kill switch
- Botão físico/comando que para bot imediatamente
- Senha randômica de 20 chars pra reiniciar (não decorar)
- Após 5 stops consecutivos: bot pausa 24h obrigatório

### 6.5 Validação live (6 meses)
- Mantém forward test critérios
- PnL projeção anualizada: 15-30% (Sharpe ≥1)
- Sem violação de DD limits
- Sem necessidade de intervenção manual

---

## FASE 7 — Escalonamento (futuro)

Só considera se Fase 6 completa com sucesso:
- Aumentar capital gradualmente (×2 cada 3 meses lucrativos)
- Adicionar 1 estratégia adicional (testada via mesmo processo)
- Considerar conta funded (Topstep, etc) pra alavancagem

---

# PLAN B — Se Fase 3 ou 4 falhar

Se Silver Bullet OU London Sweep não atingirem critérios go/no-go, **não force ICT**.

Alternativas a testar (mesma infra de backtest):

### Plan B1 — Opening Range Breakout (ORB)
- Primeiros 5-30 min do NY Open (9:30-10:00 EST)
- Break do range + retest = entry
- Documentado academicamente (Hooke 2024, ORB studies)
- Bem mecânico, menos discrição

### Plan B2 — Trend Following clássico
- EMA 50/200 crossover
- ATR-based stop
- Trail stop 2× ATR
- 40+ anos de validação histórica
- Funciona em qualquer ativo trendable

### Plan B3 — Mean Reversion em extremos
- RSI <20 ou >80 em M15
- Bollinger Band touch + retest
- Funciona bem em XAU em consolidação
- Stop apertado, target curto

---

# Integração com sistema existente

### Manter/reusar
- `core/agent.py` (Gemini) → usar apenas pré-sessão + journal
- `core/rag.py` → manter pra context
- `core/risk_manager.py` → reusar como base (corrigir crítico C4)
- `core/mcp_client.py` → usar pra polling de dados em forward test
- `core/common_execution.py` → manter como roteador
- `main.py` → manter endpoints atuais + adicionar `/start_session` e `/stop_session`

### Reescrever
- `core/backtester.py` → SUBSTITUIR por `backtesting/engine.py` (atual está quebrado)
- Cenários sintéticos em `backtest_scenarios/` → DEPRECAR, usar dados reais

### Corrigir antes de qualquer coisa
- `core/agent.py` → adicionar `bypass_daily_limits=True` quando `is_backtest=True` (crítico C4 do audit)
- `core/risk_manager.py` → suportar flag de bypass

---

# Cronograma realista

| Fase | Tempo | Cumulativo |
|---|---|---|
| 0. Setup ambiente | 1-2h | 2h |
| 1. Silver Bullet NQ | 3-5 dias | 1 semana |
| 2. London Sweep XAU | 3-5 dias | 2 semanas |
| 3. Backtest engine + walk-forward | 5-7 dias | 3 semanas |
| 4. Filtros macro | 3-5 dias | 4 semanas |
| 5. Forward test demo | 3 meses | 4 meses |
| 6. Micro live | 3-6 meses | 7-10 meses |

**Total realista até live profitable validado: 7-12 meses.**

---

# Critérios de aceite final desta task

- [x] Estrutura de pastas criada (`strategies/`, `data/`, `backtesting/`, `filters/`, `execution/`)
- [x] `smart-money-concepts` instalado e funcionando
- [x] Polygon.io configurado (com yfinance de fallback e cache robusto parquet funcionando)
- [x] Setup #1 (Silver Bullet) implementado + testado em 1 dia
- [x] Setup #2 (London Sweep) implementado + testado em 1 dia
- [x] Backtest engine com candle simulation rodando
- [x] Walk-forward funcional com splits dinâmicos
- [x] Filtros macro implementados + A/B test feito
- [x] Reports HTML gerados em `backtesting/reports/`
- [x] Decisão documentada: setups avaliados
- [x] Se passam: forward test infraestrutura pronta (live_runner robusto e modular)
- [x] `core/agent.py` corrigido (bypass daily limits no backtest)

---

# Notas finais para o agente executor

1. **Use a lib `smart-money-concepts`** quando possível. Não reimplementar FVG/MSS detection do zero — eles têm bugs sutis.
2. **Cada setup vai ter ~10% diferença de implementação por interpretação.** Documente decisões feitas, valide com usuário.
3. **Backtest sem look-ahead é CRÍTICO.** Em cada iteração da engine, só passa pra `strategy.evaluate()` dados ATÉ o candle atual. Use slicing explícito `candles.iloc[:current_idx]`.
4. **Dados Polygon free tier:** rate-limit. Cache em parquet local. Não re-fetch.
5. **Timezones:** Polygon retorna UTC. Killzones são EST. Converta SEMPRE. Cuidado com DST (mar-nov vs nov-mar nos EUA).
6. **Não pular Fase 3 (backtest válido).** Tentação enorme de ir direto pro forward. Backtest é o juiz. 1 mês investido aqui economiza 6 meses de forward inútil.
7. **Manter Plan B sempre carregado.** Se ICT setups falharem, ORB e trend following já têm specs prontos.

---

# Estado do projeto referenciado

- `backtest_audit.md` — auditoria do backtester antigo
- `TASK_ICT_VAULT_BUILD.md` — task anterior, SUPERSEDED por este documento
- `core/mcp_client.py` — cliente MCP TradingView, usável em forward test
- `main.py` — endpoints atuais (`/webhook`, `/analyze`, `/market/snapshot`)
- `config.py` — configurações, adicionar `POLYGON_API_KEY` no `.env`
- `requirements.txt` — adicionar deps da Fase 0
