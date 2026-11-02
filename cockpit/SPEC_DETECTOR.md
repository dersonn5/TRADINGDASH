# PRD — Detector de estrutura validado pelo operador

Status: **rascunho para o Anderson revisar** · 02/11/2026 · Claude

## 1. Problema

Os backtests antigos (`profit/setup_bpr_sweep.py`, `setup_v_sweep.py`, `backtest_c_ao_vivo.py`)
detectam MSS, FVG, BPR etc. com definições escolhidas pelo código. Quando o resultado foi
desenhado no gráfico, o operador viu estruturas que ele **não** chamaria de MSS ou FVG, e
estruturas dele que o código não achou. O backtest media outro operacional — o número não
vale para decidir nada no Trade System.

Não é falta de modelo de previsão (o Kronos foi avaliado em 02/11 e descartado: prevê
candles, não reconhece estrutura). É falta de **definição exata + validação pelo olho do
operador**.

## 2. Objetivo

Um detector em que o operador confia: as estruturas que ele marca no gráfico de 1 min são
as que o código marca, no mesmo candle. Medido por:

- **Precisão ≥ 85%**: das detecções que o código mostra, o operador aprova 85%+.
- **Cobertura ≥ 85% nos trades reais**: em 85%+ dos trades registrados no cockpit com
  gatilho, o detector acha aquele gatilho no minuto da entrada (±2 candles).

Só com os dois números batidos o detector alimenta backtest.

## 3. Escopo

**Entra:**
- Definição escrita e parametrizada de: swing, MSS, CISD, FVG, iFVG, BPR, OB, sweep.
- Detector em Python sobre o cache de 1 min do Profit (`profit/WINZ26_1min.csv`, 5 meses).
- Tela de revisão local no cockpit: gráfico de 1 min com a estrutura desenhada, botões
  ✓ / ✗ / "quase" + comentário curto.
- Relatório de precisão e cobertura por conceito.
- Depois de validado: backtest dos setups exatos (MAV, CSI, RPP, RHT) com o detector novo.

**Não entra (anti-escopo):**
- Modelo de previsão/IA caixa-preta (Kronos e afins).
- Execução automática de ordens ou robô.
- Mudar regra do Trade System durante a validação (anotar, decidir no fim com números).
- Publicar a tela de revisão na Vercel: ela roda só no dev local (dados do Profit ficam na
  máquina).

## 4. Definições a fechar com o operador (o coração do projeto)

O que o código antigo usa ao lado da pergunta. Cada resposta vira um parâmetro.

| Conceito | Código antigo | Perguntas para o Anderson |
|---|---|---|
| **Swing** | fractal de 2 (2 candles de cada lado) | Quantos candles de cada lado? Swing "relevante" exige tamanho mínimo em pts? |
| **MSS** | fechamento além do último swing contrário antes do extremo | Rompe no fechamento ou basta o pavio? Precisa de candle de deslocamento (corpo grande)? Qual swing: o último ou o que originou a perna? |
| **CISD** | não existe | O fechamento passa da **abertura** de qual sequência (a série de candles da perna contrária)? Quantos candles mínimo na série? |
| **FVG** | máxima do candle i−2 < mínima do candle i (alta), sem tamanho mínimo | Tamanho mínimo em pts? Só conta FVG da perna de deslocamento? Em qual tempo gráfico (1 min / 5 min)? |
| **iFVG** | não existe | FVG invalidado por **fechamento** através dele ou por pavio? Vale por quanto tempo depois? |
| **BPR** | FVG a favor que sobrepõe FVG contrário da pernada do sweep | Sobreposição mínima (pts ou %)? Os dois FVGs precisam estar a quantos candles um do outro? |
| **OB** | último candle contrário antes da pernada; entrada na abertura dele | Usa o corpo ou o candle inteiro? Precisa ter causado MSS/deslocamento? |
| **Sweep** | pavio além do nível e fechamento de volta | Fechar de volta é obrigatório na mesma barra? Tolerância em pts? |

Método: o Claude propõe a definição mais provável, o operador corrige com exemplos do
gráfico (prints de 2–3 casos que **são** e 2–3 que **não são**).

## 5. Entidades

- `deteccao`: `{id, conceito, direcao, i_inicio, i_fim, preco_topo, preco_fundo, params_versao}`
- `rotulo`: `{deteccao_id, veredito: OK | ERRADO | QUASE, comentario, data}`
- `params`: versão das definições (JSON), para saber qual definição cada rótulo julgou.

Arquivos em `cockpit/.local/detector/` (no `.gitignore`): `velas.json`, `deteccoes.json`,
`rotulos.json`. Os parâmetros (`profit/detector_params.json`) vão para o git — são o
Trade System em forma de código.

## 6. Requisitos funcionais

- **FR-001** `profit/detector.py`: lê o cache, aplica `detector_params.json`, grava
  `deteccoes.json` e um recorte de velas ao redor de cada detecção.
- **FR-002** Amostragem: por conceito, sorteia 40 detecções espalhadas pelos 5 meses e
  pelos horários 09:00–12:00 (não pegar só um dia).
- **FR-003** Tela `/laboratorio` (só `NODE_ENV=development`): uma detecção por vez, gráfico
  de 1 min com ~60 candles, a estrutura desenhada (caixa no FVG/OB, linha no nível do
  MSS/sweep, seta no candle que confirma), atalhos de teclado ✓ (1) / ✗ (2) / quase (3).
- **FR-004** Comentário opcional por rótulo ("o swing certo era o anterior").
- **FR-005** Modo "trades reais": para cada trade do cockpit com gatilho, mostra o
  minuto da entrada e o que o detector achou ali (ou "nada").
- **FR-006** `profit/detector_relatorio.py`: precisão por conceito, cobertura nos trades
  reais, e os 10 erros mais comuns agrupados pelo comentário.
- **FR-007** Toda mudança de parâmetro gera nova `params_versao`; rótulos antigos continuam
  ligados à versão que julgaram.

## 7. UI

Gráfico com `lightweight-charts` (biblioteca de gráficos da TradingView, Apache 2.0 — a
mesma que o OpenTerminal usa; manter a atribuição exigida pela licença). Tema do cockpit
(ciano/branco, Sora). Painel lateral: conceito, horário, parâmetros usados, botões.
Contador "12 de 40 · precisão até aqui 75%".

## 8. Critério de sucesso

1. Tabela de definições do §4 fechada e assinada pelo operador.
2. Precisão ≥ 85% e cobertura ≥ 85% em todos os conceitos usados pelos setups.
3. Backtest do MAV e do CSI rodado com o detector validado, comparado ao resultado real
   dos trades do cockpit no mesmo período.

## 9. Roadmap (rascunho — vira build-spec depois do PRD aprovado)

- **Fase 0 — Definições** (operador + Claude): fechar o §4 com prints de exemplo.
- **Fase 1 — Detector** (Claude): `detector.py` + params + saída JSON. Verify: roda nos 5
  meses, contagem por conceito plausível (ex.: FVG por dia).
- **Fase 2 — Tela de revisão** (pode ir para o Gemini): `/laboratorio` com
  lightweight-charts. Verify: 40 detecções navegáveis, rótulo gravado no JSON.
- **Fase 3 — Rodada de rótulos** (operador, ~20 min por conceito) + ajuste de parâmetros
  até 85%.
- **Fase 4 — Cobertura nos trades reais** (FR-005).
- **Fase 5 — Backtest** dos setups com o detector validado.

## 10. Riscos

- **Sem dado de 1 min antes de 05/2026** no cache: o backtest fica em ~5 meses (amostra
  curta); 5 anos só em 15 min.
- **Definição que depende de contexto** ("esse FVG conta porque veio do sweep") pode não
  caber num parâmetro simples: nesses casos o detector marca o candidato e o setup decide.
- **Fadiga de rótulo**: 40 por conceito × 8 conceitos = 320 julgamentos. Fazer em rodadas
  curtas, conceito por conceito, começando pelos do MAV (sweep, MSS, FVG, BPR).
