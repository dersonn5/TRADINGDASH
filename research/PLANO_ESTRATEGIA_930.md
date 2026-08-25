# PLANO — Estratégia "9:30-11am IFVG Reversal" (teste honesto)

## Origem
Post de redes sociais (carro vermelho + "trust me"). Alega sucesso em Ouro/Nasdaq.
Regras dele:
- Janela 9:30-11:00am (horário NY)
- Liquidity sweep no gráfico de 1 hora
- Reversão via IFVG (Inversion Fair Value Gap) no gráfico de 1 minuto
- Take profit RR 1:2 (testar também 1:3)

## ⚠️ Postura (ler antes de codar)
Isto é a MESMA família (IFVG reversal) que já falhou em 100+ testes. O "trust me" +
foto de carro é sinal clássico de vendedor. NÃO assumir que funciona. O objetivo é
MEDIR honestamente — não confirmar. Régua travada ANTES do resultado:
**PF >= 1.3 e DD <= 15% no HOLDOUT. Abaixo disso = descartar, sem "quase deu".**

## Base já existente no projeto (NÃO recomeçar do zero)
- `strategies/playbook_anderson.py` — já faz IFVG reversal + sweep + indução. É o esqueleto.
- `strategies/ict_topdown_crypto.py` — detectores base (_detect_fvg_list, _detect_mss_and_swing,
  _atr5, _in_window, _convert_to_est). Playbook herda daqui.
- `backtesting/engine.py` — engine SEM look-ahead (corrigido: HTF só vela fechada,
  `allow_overnight_hold` flag). Cuidado: engine força flat até ~11h ET p/ não-cripto
  (killzone_end fallback) — pra ESTA estratégia (janela 9:30-11h) isso É desejável.
- `research/lab_market.py` — MARKETS (NQ, ES, XAU), _load_full, _slice (dados 2022-2024).
- `data/cached_holdout/` — dados 2025-01 a 2026-06 (holdout travado). Só NQ/ES baixados;
  XAU precisa baixar (usar research/holdout_2025.py como molde, adicionar XAU).
- Dados: Dukascopy. NAS/USD=NQ, SPX/USD=ES, XAU/USD=Ouro. Cache em data/cached/.

## Especificação da estratégia nova (arquivo: strategies/strat_930_ifvg.py)

Máquina de estados (vendedor; comprador = espelho):
1. GATE HORÁRIO: só avalia entre 9:30 e 11:00 ET (usar _in_window com time(9,30), time(11,0))
2. LIQUIDITY SWEEP no 1h: preço varreu um swing high/low do gráfico de 1 HORA
   (não diário). Usar candles_1h, detectar swing fractal e checar sweep+reclaim.
   - SELL: varreu swing high do 1h e voltou abaixo
   - BUY: varreu swing low do 1h e voltou acima
3. IFVG 1m: no candles_1m, achar FVG contrário que foi INVERTIDO por fechamento
   (reutilizar lógica de ict_po3_v2 / playbook_anderson: _detect_fvg_list + inversão)
4. ENTRADA: no reteste do IFVG (troca de polaridade)
5. STOP: além do swing extremo / IFVG + buffer ATR
6. ALVO: RR fixo (parâmetro target_rr = 2.0; testar também 3.0)

Config sugerida (dataclass Strat930Config(ICTTopDownConfig)):
- kz_start = time(9,30), kz_end = time(11,0)
- swing_lookback_1h = 20
- reclaim_buffer_atr = 0.1
- ifvg_lookback_1m = 30
- sl_buffer_atr = 0.25
- target_rr = 2.0  (rodar 2.0 E 3.0)
- min_rr = 1.5
- cooldown_minutes = 60

## Script de teste (arquivo: research/test_930.py)
Copiar estrutura de research/test_playbook.py:
- Rodar NQ, ES, XAU em paralelo (ProcessPoolExecutor, max_workers=6)
- Janelas: IS 2022-01-01..2023-12-31 / VAL 2024-01-01..2024-12-31
- Config: BacktestConfig com commission_pct=0.0002 (custo real), partials 2.0/0.5,
  BE 2.0, trailing off (RR fixo, deixa bater alvo/stop)
- Testar target_rr = 2.0 e 3.0 (2 rodadas)
- Imprimir: trades, PF, win%, DD por mercado/janela
- Régua: só vai pro holdout se IS E VAL >= 1.05

## Diagnóstico se der ~0 trades (provável — janela restrita)
Adicionar FUNIL (copiar de playbook_anderson.py: self.funnel + self._fn) contando
quantos dias passam cada etapa: horário → sweep 1h → IFVG → reteste → entrada.
Assim se sabe qual gate mata tudo, sem chutar.

## Comandos (rodar na outra IDE, na raiz do projeto)
```bash
cd "e:/AUTOMAÇÃO IA/TRADING AI"

# 1. syntax check
python -c "import ast; ast.parse(open('strategies/strat_930_ifvg.py',encoding='utf-8').read()); print('OK')"

# 2. smoke test rápido (1 mercado, 1 ano) antes de rodar tudo
python -u -c "import sys;sys.path.insert(0,'.'); from research.test_930 import run; print(run('NQ','2024-01-01','2024-12-31'))"

# 3. teste completo IS+VAL (RR 2:1)
python -u -m research.test_930 > research/strat930_rr2.log 2>&1

# 4. teste RR 3:1 (editar target_rr=3.0 ou passar via arg)
python -u -m research.test_930 --rr 3.0 > research/strat930_rr3.log 2>&1

# 5. SÓ SE passar IS+VAL: holdout (1x, travado)
python -u -m research.test_930 --holdout > research/strat930_holdout.log 2>&1
```

## Filtro de log (Dukascopy polui com HTML/yfinance)
```bash
grep -aE "trades=|PF=|ERRO|MELHOR|NENHUMA" research/strat930_rr2.log | grep -avE "yahoo|<|CACHE|BACKTEST|delisted|ticker|Failed|CARREGADOR|INFO"
```

## Histórico honesto (contexto pra outra IDE / outro agente)
Já testado e FALHOU (engine honesto, sem look-ahead):
- ICT top-down + PO3 + variações: ~29 configs, 0 sobreviveu robusto
- Momentum diário: 24 configs, 0 passou
- Playbook Anderson (IFVG reversal, 7 versões): raro demais ou PF < 1
- Cripto BTC/ETH revalidado: PF 0.81/0.85 (era inflado por leak)
Padrão consistente: win rate ~25-40% = aleatório com o RR usado; custo derruba PF < 1.
Esta estratégia 9:30 é variação da MESMA família IFVG. Expectativa baixa. Testar mesmo
assim, com rigor, e ACEITAR o veredito (a barra PF>=1.3 holdout foi combinada com o usuário).

## Se passar (improvável mas possível)
1. Rodar holdout 2025-26 (1x). PF>=1.3 e DD<=15% → candidato real.
2. Plotar trades (research/plot_trades.py adaptado) p/ auditoria visual do usuário.
3. Só então: forward test em conta paper/demo antes de qualquer capital.
