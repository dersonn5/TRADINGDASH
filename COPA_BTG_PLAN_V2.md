# PLANO V2 — Dar fundamento ao Cockpit Copa BTG

**Data:** 2026-08-26
**Estado atual:** sistema construído e funcional (commit `fb2d612`), verificado nesta sessão.
**Problema que este plano resolve:** o software funciona, mas seus números não têm origem medida.

---

## Diagnóstico

O que foi verificado funcionando: backend completo (7 módulos), gate com circuit
breakers, módulo de torneio com descarte do pior dia, `tsc` limpo, conformidade
com o regulamento intacta.

O que **não** tem fundamento:

1. **Os pesos do checklist são chute.** 15/15/15/10/10/10/10/10/5 e
   `score_minimo = 65` vieram de `core/entry_quality.py`, que era estimativa. Nunca
   foram medidos no WIN.
2. **A tela `por_item` não vai produzir significância a tempo.** Precisa de N ≥ 20
   por item. A 3 trades/dia, com 4 dias por fase, a Copa termina antes.
3. **Não existe histórico de WIN no projeto.** Nenhum backtest do playbook no
   ativo que vai ser operado.

Consequência: o operador vai confiar num score calibrado por palpite, e a tela
que deveria provar o que funciona vai mostrar `amostra_baixa` do começo ao fim.

**O backtest não é escopo novo. É o que faz a feature de probabilidade existir.**

---

## Regra de honestidade — vale para todo o plano

Nem todo item do checklist é mensurável por algoritmo. "Indução", "displacement
forte", "alvo é liquidez clara" são julgamentos visuais.

Portanto cada peso passa a carregar sua origem:

- `MEDIDO` — peso derivado de backtest, com N e período
- `ESTIMADO` — peso de julgamento, não medido

A interface **mostra a diferença**. Um peso estimado nunca aparece como se fosse
medido. Isso impede que o software repita o erro do gerador de gráficos: parecer
fundamentado sem ser.

---

## Fronteira de conformidade

O regulamento da Copa proíbe ferramentas externas na **operação**. Este plano
mantém a separação:

- **App da Copa** (`copa/`, `cockpit/app/copa`) — continua sem feed, sem dado de
  mercado, sem integração. Inalterado nas restrições do PRD §13.
- **Ferramenta de backtest** (`research/`, `data/`) — programa separado, offline,
  só histórico, roda fora do horário de competição. Nunca importado pelo app da
  Copa em runtime.

Os pesos medidos entram no app como **números num arquivo de config**, não como
conexão viva. Nenhum processo do backtest roda durante o pregão.

---

# Fase 1 — Histórico do WIN

**Goal:** dado de WINFUT em disco, com integridade provada e profundidade conhecida.

**Fonte escolhida: exportação manual do Profit Pro.** O Anderson já tem a
licença, não exige instalar nada, e é **o mesmo feed em que ele vai competir** —
backtest na série exata que será operada vale mais que backtest no feed de outra
corretora.

Limites do Profit Pro: **2 anos** de histórico, **50.000 candles por exportação**.
Para o WIN (pregão 09:00–18:00 ≈ 540 barras M1/dia, ~250 pregões/ano): D1 e H1
cabem numa exportação; M5 precisa de 2; M1 precisa de ~6 fatias por período.

## Fronteira de conformidade nesta fase

**Permitido:** exportação manual pelo menu `Exportar Dados Históricos`. É o
operador clicando e salvando um CSV — não é ferramenta externa operando.

**Proibido, sem exceção:**
- **ProfitDLL** — API programática da Nelogica
- **RTD/DDE** — link ao vivo com Excel
- ler por código os arquivos de dados/log/tela do Profit

Qualquer um dos três é software externo conectado à plataforma da competição, e
viola tanto o regulamento quanto a regra 1 do PRD §13.

- [ ] **T1.0 — Amostra de formato (Anderson + Claude)**
  - **Notes:** antes de qualquer parser, exportar **um** arquivo pequeno e
    inspecionar as 20 primeiras linhas: nome das colunas, separador, separador
    decimal (vírgula ou ponto), formato de data e hora, fuso, se há cabeçalho, se
    volume vem em contratos ou financeiro.
    **Não escrever loader contra formato suposto.** Foi exatamente assim que o
    gerador de gráficos inventou níveis que não existiam.
  - **Verify:** as 20 linhas coladas aqui.

- [ ] **T1.1 — Exportação (tarefa manual do Anderson)**
  - **Notes:** símbolo `WINFUT`. Timeframes, nesta ordem de prioridade:
    **D1, H1 (60min), M5**, e depois **M1** fatiado por janelas de ~4 meses para
    respeitar o teto de 50.000 candles.
    Salvar em `data/raw/profit/` com nome `winfut_<tf>_<inicio>_<fim>.csv`.
    Anotar em que data a exportação foi feita — o WINFUT é contínuo e muda.
  - **Verify:** listar os arquivos com tamanho e contagem de linhas.

- [ ] **T1.1b — Sonda MT5 (opcional, só se precisar de mais profundidade)**
  - **Files:** `data/mt5_probe.py`
  - **Notes:** só executar se 2 anos se mostrarem insuficientes na Fase 3, ou se
    a exportação manual do M1 for inviável. Requer instalar MT5 de corretora com
    B3 (conta demo serve). Reporta corretora, símbolos `WIN*`/`WDO*`,
    `symbol_info` completo (`trade_tick_size`, `trade_tick_value`, `point`,
    `digits`, `trade_contract_size`) e a primeira/última barra real por timeframe.
    **Proibido hardcodar valor de ponto** — sai daqui ou do manifest da T1.2.
  - **Verify:** saída colada. Sem ela, nada que dependa do MT5 começa.

- [ ] **T1.2 — Loader do CSV do Profit + tratamento de rolagem**
  - **Files:** `data/win_loader.py`
  - **Notes:**
    - Lê os CSVs de `data/raw/profit/` no formato **confirmado na T1.0**, nunca
      no suposto. Normaliza para OHLCV com índice datetime tz-aware
      (America/Sao_Paulo).
    - Usa o **contínuo WINFUT**, não contrato individual. Contrato específico
      (`WINV26`) vence e é purgado — não existe histórico de 2024 num contrato
      encerrado. Só o contínuo tem profundidade.
    - **Determinar empiricamente se a série é ajustada.** Exportar também o
      contrato vigente (esse ainda existe) e comparar com o WINFUT no período de
      sobreposição:
      - preços idênticos → contínuo **não-ajustado** (emenda crua)
      - diferença constante → **ajustado por diferença**
      - razão constante → **ajustado por razão**
      Registrar o veredito no manifest. Nunca supor.
    - **Por que importa:** o modelo usa nível recente (PDH/PDL de ontem, EQH/EQL
      de ~10 dias). Série ajustada por diferença mantém esses níveis coerentes.
      Série **não-ajustada** salta de base no dia da rolagem e o PDL da véspera
      vira nível fantasma — o backtest enxerga sweep que nunca aconteceu.
    - **Ajuste tem que ser por diferença (panamá), nunca por razão.** WIN tem
      valor de ponto fixo (R$ 0,20); ajuste por razão distorce distância em
      pontos, e stop e alvo são medidos em pontos. Se a corretora só oferecer
      não-ajustado, construir o ajuste por diferença localmente a partir do
      degrau medido em cada rolagem.
    - **Marcar as datas de rolagem.** WIN vence em meses pares — G(fev), J(abr),
      M(jun), Q(ago), V(out), Z(dez) — na quarta-feira mais próxima do dia 15.
      Tratar essa tabela como hipótese e confirmar contra o degrau observado nos
      dados e contra `symbol_info`.
    - **Excluir os dias de rolagem do backtest**, mesmo com série ajustada: a
      liquidez migra entre contratos e o comportamento do dia é atípico. São
      poucos dias por ano; é seguro barato.
    - **Nenhum nível calculado antes de uma rolagem pode ser usado depois dela.**
      Assert no carregador, não confiança.
    - Salva Parquet em `data/cached/win/winfut_<tf>.parquet`.
    - `manifest.json`: símbolo, timeframe, primeira e última barra, n_barras,
      veredito de ajuste, degraus medidos por rolagem, datas de rolagem
      detectadas, specs do símbolo, data do download.
  - **Verify:** carregar M5 e H1, imprimir n_barras, intervalo de datas, o
    veredito de ajuste com a evidência numérica, e a lista de rolagens detectadas
    com o degrau de cada uma.

- [ ] **T1.3 — Validação de integridade**
  - **Files:** `data/win_validate.py`
  - **Notes:** um backtest em dado furado mente com cara de verdade. Checar:
    - buracos dentro do pregão (barras faltando em 09:00–18:00 de dia útil)
    - barras com `high < low`, `open`/`close` fora do range, volume zero
    - duplicatas de timestamp
    - saltos de preço maiores que N desvios entre barras consecutivas
    - dias com contagem de barras muito abaixo da mediana (pregão parcial, feriado)
  - **Verify:** rodar em todos os contratos baixados e imprimir o relatório.
    Contrato reprovado é **excluído** do backtest, não remendado.

---

# Fase 2 — Backtest do Playbook no WIN

**Goal:** saber se o modelo das 5 lições tem edge no WIN, antes de operá-lo.

- [ ] **T2.1 — Adaptar o playbook para a B3**
  - **Files:** `strategies/playbook_anderson_win.py`
  - **Notes:**
    - `strategies/playbook_anderson.py` é read-only. Criar variante, não editar.
    - Killzones são de **B3**, não London/NY: abertura 09:00–10:30 e a janela
      09:00–12:00 que o Anderson opera. Remover qualquer referência a horário de
      Nova York.
    - Pregão do WIN: 09:00–18:00, sem 24h. Toda lógica de "sessão anterior" e
      PDH/PDL passa a ser por **dia de pregão**, não por janela de 24h.
    - Day trade obrigatório (regra da Copa): posição **tem** que fechar no mesmo
      pregão. Fechamento forçado no fim da janela.
    - Valor do ponto e tick vêm do manifest da T1.2.
  - **Verify:** rodar em 1 contrato e imprimir o funil de diagnóstico
    (`self.funnel`) — em qual etapa cada dia morre.

- [ ] **T2.2 — Rodar e medir**
  - **Files:** `research/backtest_win.py`
  - **Notes:**
    - Split honesto: in-sample / validação / holdout por período, **sem
      reotimizar no holdout**.
    - Custos reais: corretagem, emolumentos B3, slippage de pelo menos 1 tick na
      entrada e 1 no stop. Backtest sem custo em day trade de mini índice é
      ficção.
    - Métricas: PF, winrate, expectância em R$, drawdown, trades/dia,
      distribuição de RR realizado.
    - **Métrica específica da Copa:** resultado por dia, e o placar com descarte
      do pior dia aplicado em janelas de 4 dias. É assim que se estima o
      desempenho no formato real do torneio.
  - **Verify:** relatório impresso com as métricas e o número de trades. Se o
    modelo não tiver edge, **relatar isso** — não ajustar parâmetro até ficar
    bonito.

---

# Fase 3 — Calibrar o checklist com dado medido

**Goal:** substituir os pesos chutados por pesos medidos, e marcar honestamente
os que não deram para medir.

- [ ] **T3.1 — Instrumentar as confluências**
  - **Files:** `strategies/playbook_anderson_win.py` (extensão do meta)
  - **Notes:**
    - Em cada trade do backtest, gravar quais itens PONTO estavam presentes,
      usando o **mesmo id** do checklist do app (`p1`…`p9`).
    - Itens algoritmicamente decidíveis: `p1` (PD array), `p2` (premium/discount),
      `p3` (qualidade da liquidez), `p4` (displacement), `p5` (indução),
      `p6` (killzone), `p9` (WIN×WDO).
    - Itens **não** decidíveis por código: `p7` (alvo é liquidez clara) e `p8`
      (notícia) dependem de julgamento e de calendário externo. Ficam `ESTIMADO`.
    - Cada confluência gravada com **índice da vela** que a originou. Sem índice,
      não entra — é a mesma regra que faltou no gerador de gráficos.
  - **Verify:** imprimir, para 5 trades, o dict de confluências com os índices.

- [ ] **T3.2 — Medir o peso de cada item**
  - **Files:** `research/calibrar_checklist.py`
  - **Notes:**
    - Para cada item: winrate e expectância **com** o item presente vs **sem**,
      com N de cada lado.
    - Peso proposto proporcional ao ganho de expectância, normalizado para somar
      100 entre os itens medidos.
    - Reportar `delta_expectancia` e N. **Item com N < 30 de qualquer lado
      permanece `ESTIMADO`** — não promove peso com amostra fraca.
    - Propor `score_minimo` a partir da curva: qual corte de score maximiza
      expectância mantendo trades/dia viável para a Copa.
  - **Verify:** tabela impressa item a item, com N, delta e peso proposto.

- [ ] **T3.3 — Origem do peso na interface**
  - **Files:** `copa/strategies/playbook_anderson.json`, `copa/strategies_config.py`,
    `cockpit/components/copa/checklist-form.tsx`, `cockpit/app/copa/estrategias/page.tsx`
  - **Notes:**
    - Cada item do checklist ganha: `origem` (`MEDIDO` | `ESTIMADO`), `n_amostra`,
      `periodo_medicao`, `delta_expectancia`.
    - `strategies_config.py` valida que a soma dos PONTO continua 100.
    - Na tela, item `MEDIDO` mostra o N e o delta ao lado do peso. Item
      `ESTIMADO` mostra rótulo explícito de que é julgamento, não medição.
    - A ficha da estratégia declara o período e o contrato usados na calibração.
  - **Verify:** `npx tsc --noEmit`, abrir a tela e conferir que item estimado e
    item medido são visualmente distintos.

---

# Fase 4 — Buracos do app

**Goal:** fechar o que ficou faltando da v1. Tudo pequeno.

- [ ] **T4.1 — Print do trade no journal**
  - **Files:** `copa/api.py`, `cockpit/components/copa/fechar-trade-dialog.tsx`,
    `cockpit/app/copa/trades/page.tsx`
  - **Notes:** a coluna `screenshot_path` existe no banco e **não tem UI nenhuma**.
    Sem print, a revisão do trade é memória — e memória é o que falha. Colar da
    área de transferência ou selecionar arquivo; salvar em `copa/data/prints/`;
    miniatura na linha do histórico. Arquivo local, sem upload para lugar nenhum.
  - **Verify:** anexar print num trade, fechar o app, reabrir e o print continua lá.

- [ ] **T4.2 — Estratégias 2 e 3**
  - **Files:** `copa/strategies/abertura_b3.json`, `copa/strategies/reversao_pdh_pdl.json`
  - **Notes:** só depois que a Fase 3 fechar para o Playbook — senão nascem com
    pesos chutados de novo, que é o erro que este plano existe para corrigir.
    Nascem com todos os itens `ESTIMADO` e declaram isso.
  - **Verify:** `GET /api/copa/strategies` devolve 3, cada uma somando 100 pontos.

- [ ] **T4.3 — Limite de exposição e prêmio diário**
  - **Files:** `copa/risk.py`, `cockpit/app/copa/page.tsx`
  - **Notes:** `exposicao_maxima_contratos` está na config e ninguém usa. O BTG
    informa esse número antes de cada fase; se `contratos` do trade exceder,
    bloquear no gate. Painel do prêmio diário (melhor performance do dia,
    R$ 1.000, 12 dias) como objetivo secundário, separado do placar da fase.
  - **Verify:** tentar registrar trade acima do limite e receber HTTP 409.

---

# Fase 5 — Representação gráfica (pós-Copa)

**Goal:** pagar a dívida técnica do gerador de gráficos, e com isso **validar
visualmente o backtest**.

Contrato de anotação: toda marca carrega `bar_origin` e a regra que a produziu.
Renderer burro — desenha só o payload, proibido `min()`/`max()`. Validadores que
levantam exceção antes de virar imagem:

- `SWEEP` exige vela que negociou além do nível **e fechou de volta**
- `MSS` exige índice do swing rompido e vela **fechada** além dele
- `FVG` exige o gap aritmético de 3 velas, âncora na vela do meio
- `IFVG` exige a vela de fechamento que inverteu
- `DEALING_RANGE` exige dois extremos ancorados

Vocabulário visual: o do Scalping_Lab, que é finito — FVG âmbar, iFVG azul,
Breakaway roxo, Mitigation lilás, MSS 💡, Draw on Liquidity 👁, BSL/SSL em linha,
caixa verde para alvo e rosa para risco, sessão no eixo X, prefixo `+`/`−` para
array bullish/bearish.

**Por que isto valida a Fase 2:** o gráfico anotado é como se confere, vela por
vela, se o detector enxergou a estrutura certa. Backtest sem revisão visual é
número sem auditoria.

- [ ] **T5.1** — `Annotation` dataclass + validadores
- [ ] **T5.2** — detector emite anotações ancoradas
- [ ] **T5.3** — renderer burro com o vocabulário
- [ ] **T5.4** — revisão visual de 20 trades do backtest

**Escopo primeiro:** `LIQUIDITY_POOL`, `SWEEP`, `MSS`, `FVG`, `IFVG`, `CE`,
sessão, entrada/stop/alvo. É o núcleo das 5 lições.

**Prova de trabalho antes de escalar:** um gráfico, um trade real, toda marca
ancorada. Anderson confere vela por vela. Só depois vem o resto do vocabulário.

---

## Sequência e prazo

Faltam 20 dias para 14/09 (Etapa 1).

| Fase | Cabe antes da Copa? |
|---|---|
| 1 — Histórico do WIN | sim, é curta — depende do MT5 instalado |
| 2 — Backtest | sim |
| 3 — Calibração | sim, e é a que mais muda o resultado |
| 4 — Buracos do app | sim, é pequena |
| 5 — Gráfico | **não.** Fica para depois da Copa |

Bloqueio único do caminho crítico: **a exportação do WINFUT no Profit Pro**. Sem
o CSV a Fase 1 não começa e as Fases 2 e 3 não existem. Não exige instalar nada —
o Anderson já tem a licença.

## Anti-escopo deste plano

- Não mexer em `strategies/playbook_anderson.py` — criar variante WIN
- Não conectar o app da Copa a nenhum feed
- Não rodar nada do backtest durante o pregão
- Não ajustar parâmetro até o backtest ficar bonito
- Não promover peso para `MEDIDO` com N < 30
- Não criar estratégia nova antes de calibrar a primeira
