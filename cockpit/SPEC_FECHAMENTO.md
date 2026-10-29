# SPEC — Fechar o dia (importar o Profit + completar com a agenda)

> **Executor:** Gemini. **Revisor:** Claude (lê o `git diff`, não o relatório). **Aprovação:** Anderson.
> Escrita em 28/10/2026.

Antes de abrir código, ler: `CHECKPOINT.md` (raiz), `cockpit/AGENTS.md` (Next 16: ler
`node_modules/next/dist/docs` antes de usar API do Next), `lib/copa-db.ts` (`registrarTrade`,
`fecharTrade`, `TradeHistorico`), `lib/gate.ts` (`REGRAS_DA_HORA`, `MAX_*`, `classificarJanela`),
`lib/metricas.ts` (`lerPreco`, `calcularRiscoTrade`, `calcularRTrade`, `temDesvio`,
`calcularCustoDesvio`), `app/calendario/page.tsx` (tela v2 mais recente, usar como modelo de
estilo) e `components/layout/shell.tsx`. Cada task tem **Verify**; sem o Verify rodado nesta
sessão, a task não está pronta.

---

## 1. PRD

### 1.1 Problema
O operador mudou a rotina: fecha a pré-sessão no cockpit e, durante o pregão, anota cada trade
**no papel** (agenda). Isso funcionou: em dois dias, quase tudo dentro do plano. Mas o checklist
ao vivo deixou de ser usado, e os trades chegam ao sistema dias depois, por SQL montado à mão a
partir do print do Profit. Nesse caminho:
- preço e horário são copiados de print (erro de digitação);
- stop e alvo foram **inventados** (200 pts e 2R "nominais") quando não estavam anotados, e isso
  contamina o R médio de cada setup;
- "dentro ou fora do plano" foi decidido por conversa, não pela regra.

### 1.2 Objetivo
Uma tela **"Fechar o dia"** em que, depois das 12:00, o operador:
1. sobe o relatório de operações do Profit (CSV) — horário, lado, contratos, preços e R$ entram
   **exatamente** como o Profit registrou;
2. completa cada trade com o que só a agenda sabe — setup, gatilho, stop, alvo, motivo da saída,
   execução, erro;
3. vê o sistema calcular sozinho quais trades ficaram fora do plano;
4. confere que o total bate com o Profit e salva.

**Regra de ouro: o que nenhuma fonte informa fica vazio.** Nada de valor nominal, presumido ou
"padrão". Vazio aparece como "—" e sai das médias que dependem dele.

### 1.3 Fontes de cada dado

| Dado | Fonte | Editável na tela? |
|---|---|---|
| Ativo, abertura, fechamento, lado, contratos, preço de entrada e saída, pontos, R$ | **CSV do Profit** | Não |
| Setup, gatilho, contexto da 1ª hora, modo da MAV, stop, alvo, motivo da saída, execução, erro, observação | **Agenda** (operador digita) | Sim |
| Janela, dentro/fora do plano e o motivo, R | **Calculado** pelo sistema | Não |

### 1.4 Escopo — entra
- **FR-001** Página nova `/fechamento`, no menu lateral no grupo **Registro**, primeira do grupo
  (antes de "Histórico"). Rótulo "Fechar o dia". Ícone no mesmo estilo (`svgProps`).
- **FR-002** Seletor de data (padrão: hoje em America/Sao_Paulo, via `getDataSaoPaulo`; não passa
  de hoje). Abrir uma data já carrega os trades que o sistema tem nela, para completar depois.
- **FR-003** Entrada do Profit de dois jeitos, mesmo parser:
  - botão "Subir CSV do Profit" (`.csv`, `.txt`);
  - área "ou cole aqui" (Ctrl+V da tabela do Profit, que vem separada por tab).
- **FR-004** Parser tolerante (ver §2.2). Cada linha lida vira um trade com: ativo, mercado,
  direção, contratos, entrada, saída, hora de entrada e de saída, pontos por contrato, R$.
  Linhas de outro dia que não o escolhido: aviso e não importa. Ativo que não é WIN
  (`mercadoPermitido`): aviso "fora do operacional, não importado" e entra no rodapé de
  conferência como diferença explicada.
- **FR-005** Casamento com o que já está no banco (ver §2.4). Cada linha mostra um selo:
  `novo` · `já no sistema` · `do checklist (vai ser corrigido pelo Profit)`.
- **FR-006** Cartão por trade, em ordem de horário. Topo: hora, lado, contratos, entrada → saída,
  pontos, R$ (só leitura). Abaixo, os campos da agenda:
  - **Setup** (obrigatório para salvar): chips RPP · MAV · CSI · RHT (`SIGLAS`).
  - **Gatilho**: chips de `NOMES_GATILHOS` + "não anotei".
  - **Contexto da 1ª hora**: chips `NOMES_CONTEXTOS` + "não anotei". Escondido na RPP.
  - **Modo da MAV**: C1 · C2 + "não anotei". Só na MAV.
  - **Stop**: em pontos **ou** em preço (o campo aceita os dois: até 4 dígitos = pontos;
    mais que isso = preço, lido com `lerPreco`). Vazio = "não anotei".
  - **Alvo**: idem.
  - **Escalonou a favor?** Só aparece quando o Profit mostra mais de 3 contratos: "Sim — entrei
    com até 3 e aumentei a favor, com o stop no zero ou no lucro" / "Não". Grava em
    `escalonado` (coluna de `migration_escalonamento.sql`). Decide o item 6 de §2.5.
    Com "Sim", pedir também **stop em pts e contratos da entrada** e gravar
    `risco_inicial_rs = pts × contratos × 0,2`. É dele que `rDoTrade` tira o R do trade
    escalonado (a entrada do Profit é o preço médio dos contratos, e dá R errado).
  - **Motivo da saída** (obrigatório): Alvo · Stop · Manual.
  - **Execução** (obrigatório): A · B · C.
  - **Erro**: lista fechada (§2.6) + "nenhum".
  - **Observação**: texto livre curto.
  - Linha calculada, só leitura: janela, `R` (ou "R —, sem stop"), e
    **"No plano"** ou **"Fora do plano: <motivos>"** (§2.5).
- **FR-007** Barra de conferência fixa no rodapé da tela:
  `Profit: R$ +845 · Sistema: R$ +845 ✓ · 5 trades · 3 no plano · stop anotado em 4 de 5`.
  Se o total do sistema ≠ soma das linhas do CSV, mostrar a diferença em destaque e não deixar
  salvar até ser explicada (linhas não importadas listadas).
- **FR-008** Botão "Salvar o dia": grava tudo numa ida (§2.7). Depois de salvo, a tela recarrega
  do banco e mostra "Salvo às HH:MM". Reabrir a data e salvar de novo não duplica nada.
- **FR-009** Trades com stop vazio continuam somando em R$, WR e PF, mas **não entram** em nenhuma
  conta de R (média, soma, expectativa, gráficos) em nenhuma tela. Onde o R aparece por trade,
  mostrar "—".
- **FR-010** Custo do desvio sem alvo (ou sem desfecho do plano) é **"não medido"**, nunca R$ 0.
- **FR-011** Trades antigos com valores nominais (lançados por SQL até 28/10) passam a ter stop
  e/ou alvo vazios (migração, §2.1, parte 3).
- **FR-012** Modo demonstração (`?demo=1`): a tela abre, o parser e o cálculo funcionam, mas
  "Salvar o dia" fica desabilitado com o texto "Demonstração: nada é gravado".

### 1.5 Anti-escopo — NÃO entra
- Ler o Profit direto (DLL, RTD, arquivo interno). Só CSV/colagem feitos pelo operador.
- Mudar o checklist ao vivo ou o fechamento de trade pelo checklist (continuam como estão).
- Override manual de "fora do plano". A regra é a regra; o motivo aparece escrito.
- Ler print/imagem do Profit (OCR). Proibido pelo princípio de conformidade do projeto.
- Mercado que não seja WIN.
- Commit ou push sem o Anderson pedir.
- Versionar CSV real de operações do operador (dado pessoal): amostra real fica em pasta
  ignorada pelo git; no repositório, só fixture sintética.

### 1.6 Critério de sucesso
- Os 5 trades de 28/10 importados do CSV real batem 1 a 1 com o print do Profit (horário, lado,
  contratos, preços, R$) e o total dá **R$ +845**.
- Um trade sem stop anotado aparece com "R —" e não muda a média de R do setup na tela
  Estratégias nem na Visão Geral.
- Importar o mesmo CSV duas vezes não cria trade novo.
- `tsc`, `verify.ts` e `npm run build` limpos.

---

## 2. Decisões técnicas

### 2.1 Migração — `supabase/migration_fechamento.sql` (o Anderson roda no SQL Editor)
Parte 1 — colunas:
```sql
ALTER TABLE copa_trades ALTER COLUMN stop DROP NOT NULL;
ALTER TABLE copa_trades ALTER COLUMN alvo DROP NOT NULL;
ALTER TABLE copa_trades ALTER COLUMN rr_planejado DROP NOT NULL;
ALTER TABLE copa_trades
  ADD COLUMN IF NOT EXISTS origem TEXT NOT NULL DEFAULT 'CHECKLIST'
      CHECK (origem IN ('CHECKLIST', 'PROFIT', 'SQL')),
  ADD COLUMN IF NOT EXISTS profit_chave TEXT,      -- §2.4
  ADD COLUMN IF NOT EXISTS erro_tipo TEXT
      CHECK (erro_tipo IN (<lista de §2.6>));
CREATE UNIQUE INDEX IF NOT EXISTS uq_trades_profit_chave
  ON copa_trades(user_id, profit_chave) WHERE profit_chave IS NOT NULL;
```
Parte 2 — a constraint de direção passa a aceitar vazio:
```sql
ALTER TABLE copa_trades DROP CONSTRAINT IF EXISTS chk_direcao_coerente;
ALTER TABLE copa_trades ADD CONSTRAINT chk_direcao_coerente CHECK (
  (stop IS NULL OR (direcao = 'COMPRA' AND stop < entrada) OR (direcao = 'VENDA' AND stop > entrada))
  AND
  (alvo IS NULL OR (direcao = 'COMPRA' AND alvo > entrada) OR (direcao = 'VENDA' AND alvo < entrada))
);
```
Parte 3 — limpar os nominais (com `SELECT` de prévia antes do `UPDATE`, mostrando quantas
linhas cada regra pega):
- `origem = 'SQL'` onde `notas LIKE '%[lançado depois]%'`;
- `stop = NULL, rr_planejado = NULL` onde `notas LIKE '%200 pts nominais%'`;
- `alvo = NULL, rr_planejado = NULL` onde `notas LIKE '%2R presumido%' OR notas LIKE '%2R nominais%'`;
- nas notas, trocar esses trechos por "stop não anotado" / "alvo não anotado".
Parte 4 — conferência: `SELECT` contando trades por `origem` e quantos têm stop/alvo nulos.

O app tem de funcionar **antes e depois** da migração rodar? Não: a tela nova só é usada depois.
Mas `tsc` e o build não podem depender do banco.

### 2.2 Parser do Profit — `lib/profit-csv.ts`, função pura
`lerOperacoesProfit(texto: string): { linhas: OperacaoProfit[]; avisos: string[] }`

- **Separador**: detectar pela linha de cabeçalho entre `;`, `\t` e `,`.
- **Preâmbulo**: o Profit pode pôr linhas antes do cabeçalho (conta, período). Pular até a
  primeira linha que contenha, sem acento e sem caixa, `ativo` **e** `abertura`.
- **Colunas por nome**, nunca por posição. Normalizar (minúsculas, sem acento, sem pontuação,
  espaços simples) e mapear por alias. Colunas vistas na tela de Operações do Profit (28/10):
  `Ativo`, `Abertura`, `Fechamento`, `Tempo Op`, `Qtd`, `Preço Compra`, `Preço Venda`, `TET`,
  `Médio`, `Res. Intervalo Bruto`, `Res. Intervalo (%)`, `Res. Total Intervalo`,
  `Res. Operação`, `Res. Operação (%)`. Atenção: na tela, as colunas "(%)" mostram **pontos**
  ("1.620,00 pts"). Usar `Res. Operação` (R$) e a de pontos da operação; as de "Intervalo" são
  acumuladas e não servem.
- **Qtd** vem como `2 V` / `2 C` (contratos + lado de abertura: V = venda, C = compra). Se o CSV
  trouxer lado em coluna separada (`Lado`, `C/V`, `Sentido`), aceitar também.
- **Preços**: `lerPreco` (`175.905` = 175905). Entrada/saída: compra → entrada = Preço Compra,
  saída = Preço Venda; venda → entrada = Preço Venda, saída = Preço Compra.
- **R$**: aceitar `R$ 648,00`, `-R$ 116,00`, `R$ -116,00`, `(116,00)`, `648,00`.
- **Pontos**: `1.620,00 pts`, `-71,67`. Se a coluna não existir, calcular
  `(saída − entrada) × sinal` (média por contrato).
- **Data/hora**: `Abertura`/`Fechamento` podem vir como `28/10/2026 10:01:17` ou só
  `10:01:17`. Só a hora → usar a data escolhida na tela (parâmetro `dataPadrao`). Gravar com
  offset explícito `-03:00` (B3, sem horário de verão).
- **Mercado**: prefixo do ativo (`WINZ26` → `WIN`, `WDOX26` → `WDO`).
- **Conferência por linha**: `|pts × contratos × 0,2 − R$| > 0,05` em WIN → aviso na linha
  (não bloqueia; o R$ do Profit vale).
- Linha que não parseia → aviso com o número da linha e o conteúdo, nunca exceção.

### 2.3 Amostra real e fixture
- O Anderson exporta o relatório de 28/10 e salva em `cockpit/.local/profit-2026-10-28.csv`.
  Adicionar `.local/` ao `.gitignore` do cockpit **antes** de tudo.
- Escrever o parser olhando a amostra real. No repositório, criar
  `scripts/fixtures/profit-operacoes.csv` **sintética**: mesmo cabeçalho, separador, preâmbulo
  e formatos da real, com preços e horários inventados e sem número de conta nem nome.

### 2.4 Casamento com o banco
- `profit_chave` = `${ativo}|${horaEntradaISO}|${lado}|${contratos}|${entrada}`. Trade com a
  mesma chave = **já no sistema**: a tela carrega os campos da agenda dele e o salvar faz UPDATE.
- Sem chave igual, procurar trade do mesmo dia, mesma direção, `origem` ≠ `PROFIT`, com
  `|hora_entrada − abertura| ≤ 120 s`. Achou → **do checklist / SQL**: o salvar atualiza esse
  trade com os dados do Profit (preços, horários, pontos, R$, `profit_chave`, `origem` mantida)
  em vez de criar outro. Mais de um candidato → o mais próximo no tempo.
- Trade do banco naquele dia que não casou com nenhuma linha do CSV: listar abaixo dos cartões
  como "No sistema, mas não no Profit" (não apagar nada).

### 2.5 Regra do plano — `lib/plano-do-dia.ts`, função pura
`avaliarPlanoDoDia(trades: TradeDoDia[]): Array<{ noPlano: boolean; motivos: string[] }>`,
trades em ordem de `hora_entrada`. Para cada trade, olhando só os anteriores:
1. hora fora de 09:00–11:59 (SP) → "fora da janela";
2. janela via a mesma regra de `classificarJanela`; setup não está em
   `REGRAS_DA_HORA[janela].setups` → "RPP não vale na 2ª hora" (sigla + nome da hora);
3. trades anteriores **na mesma hora** ≥ `maxTrades` → "cota da 1ª hora (1) já usada";
4. perdas **seguidas** imediatamente antes (`contarPerdasSeguidas` de `lib/gate.ts`, sobre os
   trades anteriores em ordem; um resultado ≥ 0 zera) ≥ `MAX_PERDAS_DIA` → "depois de 3 stops
   seguidos" (regra esclarecida em 29/10/2026: stops não seguidos não encerram o dia);
5. trades anteriores no dia ≥ `MAX_OPERACOES_DIA` → "6º trade do dia (máximo 5)";
6. Tamanho (regra de 29/10/2026, constantes em `lib/gate.ts`):
   - `contratos ≤ MAX_CONTRATOS` (3) → ok;
   - `MAX_CONTRATOS < contratos ≤ MAX_CONTRATOS_ESCALONADO` (6) → ok **só** com `escalonado = true`
     (o operador confirma que entrou com até 3 e aumentou a favor, com stop financeiro);
     sem isso → "4 contratos na entrada (máximo 3)";
   - `contratos > MAX_CONTRATOS_ESCALONADO` → "7 contratos (máximo 6 escalonando)".
7. Perda do trade (`pnl_real < 0`) maior que `MAX_RISCO_TRADE_RS` (R$ 160, todos os contratos) →
   "perda de R$ 180 passou do teto de R$ 160". Vale para todo trade, escalonado ou não.
   Com `risco_inicial_rs` anotado acima do teto → "risco de R$ 180 na entrada (teto R$ 160)".
   Teste: 29/10 RHT 11:26, 5 contratos, −R$ 159, risco R$ 159 → no plano.
   Teste obrigatório em `verify.ts`: 29/10, MAV 10:04 com 6 contratos e `escalonado` → no plano;
   RPP 09:45 com 4 contratos sem `escalonado` → fora.
Sem setup escolhido ainda, o item 2 e o 3 ficam pendentes ("escolha o setup").
O trade fora do plano conta na cota e nas perdas do mesmo jeito (o que foi feito, foi feito).
Resultado gravado em `respeitou_plano` e, nas notas, prefixo `[FORA DO PLANO: motivo; motivo]`.

### 2.6 Erros — lista fechada (`lib/erros.ts`, exportar `TIPOS_ERRO` com id e nome)
Os ids de `migration_notas_voz.sql` que fazem sentido por trade, mais dois novos:
`FORA_DO_SETUP`, `SEM_CONFIRMACAO`, `PERSEGUIU_PRECO`, `FORA_DO_TAMANHO`, `MELHOR_PRECO`,
`EXCESSO_TRADES`, `REVANCHE`, `ANTECIPOU_STOP`, `PARCIAL_EMOCIONAL`, `MUDOU_ALVO`,
`AUMENTOU_POSICAO`, `LEITURA_CONTRA_LIQUIDEZ` ("Operou a favor da liquidez já tomada", ex.: comprou rompimento logo
após a captura do PWH), `ERRO_BOLETA` ("Ordem errada: lado, quantidade ou preço").
`ANTECIPOU_STOP`, `PARCIAL_EMOCIONAL` e `MUDOU_ALVO` também ligam os booleanos de mesmo nome
(é deles que `temDesvio` lê).

### 2.7 Gravação — `lib/fechamento-db.ts`
`salvarFechamento(data: string, itens: ItemFechamento[]): Promise<void>`
- Sessão: usar a de `data`; se não existir, criar com `setup_do_dia = 'POR_HORA'` e sem
  `fechada_em` (o dia fica marcado como "sem pré-sessão", que é verdade).
- Por item: INSERT (`origem = 'PROFIT'`, `status = 'FECHADO'`) ou UPDATE (§2.4). Campos:
  `version_id` via `getVersaoVigente(setup)`, `janela`, `score = 0`, `score_minimo` via
  `scoreMinimoEfetivo`, `grade = 'D'` (não houve checklist; não inventar score), preços e
  horários do Profit, `stop`, `alvo` (ou null), `rr_planejado` = |alvo − entrada| ÷
  |entrada − stop| ou null, `pontos_real`, `pnl_real`, `pnl_plano` (§2.8), `motivo_saida`,
  `respeitou_plano` (§2.5), booleanos (§2.6), `erro_tipo`, `gatilho`, `contexto_1h`,
  `setup_c_modo`, `profit_chave`, `notas` = `[EXEC:X] [FORA DO PLANO: …] observação`.
- **Não** chamar `registrarTrade` nem `validarCamposNovosTrade`: eles exigem pré-sessão fechada,
  gatilho e máximo de 3 contratos — aqui o trade já aconteceu e tem de entrar como foi.
- Sem `copa_trade_items` (não houve checklist).
- Erro em um item → mensagem com o horário do trade; os já gravados ficam (o salvar de novo é
  idempotente pela `profit_chave`).

### 2.8 pnl_plano e custo do desvio
- `motivo_saida` ALVO ou STOP → `pnl_plano = pnl_real`.
- MANUAL com alvo e stop anotados → o operador escolhe "depois da saída, o preço foi ao alvo /
  ao stop / não sei" (mesmo `desfecho_plano` do checklist). Alvo → pontos até o alvo; stop →
  pontos até o stop; não sei → `pnl_plano = null`.
- MANUAL sem alvo ou sem stop → `pnl_plano = null`.
- `calcularCustoDesvio` passa a devolver `number | null` (null quando `pnl_plano` é null). Na
  Visão Geral (`lib/visao-geral.ts` linhas ~288–293 e `components/v2/visao-geral-conteudo.tsx`),
  custo null aparece como "não medido"; a frase do cartão conta só os medidos e diz quantos
  ficaram sem medir.

### 2.9 R sem stop — um helper só
Em `lib/metricas.ts`: `rDoTrade(t): number | null` = null se `stop` é null/undefined ou o
risco é 0; senão `calcularRTrade(pontos, risco)`. **Todo** cálculo de R passa a usar esse helper
e filtra os null antes de somar/média. Pontos conhecidos (conferir com `grep -n "calcularRiscoTrade\|\.stop"`):
`lib/metricas.ts` (~288–291, ~416, ~466, ~512), `lib/visao-geral.ts` (~41–44),
`lib/calendario-resultados.ts` (~130), `app/calendario/page.tsx` (~652),
`app/estrategias/page.tsx` (~31), `app/trades/page.tsx` (~75, ~343).
Armadilha: `Number(null)` é 0 e `calcularRiscoTrade(entrada, 0)` dá um "risco" de 175.000 pts —
R perto de zero, sem erro nenhum. Por isso o helper, e não `Number(t.stop ?? 0)`.
`TradeHistorico.stop`, `.alvo` e `.rr_planejado` viram `number | null`; o `tsc` aponta o resto.

---

## 3. Roadmap

### Fase 0 — Pré-requisito do Anderson
- [ ] **TASK-001** — Anderson exporta do Profit o relatório de operações de 28/10 (aba
  Operações, "Hoje" ou a data) em CSV e salva em `cockpit/.local/profit-2026-10-28.csv`.
  Se o Profit não exportar CSV, copiar a tabela (Ctrl+C) e colar num `.txt` no mesmo lugar.
  - Verify: o arquivo existe e abre num editor de texto. **Fase 2 não começa sem ele.**

### Fase 1 — Banco e métricas (não depende do CSV)
- [x] **TASK-101** — `supabase/migration_fechamento.sql` (§2.1) e `.local/` no `.gitignore`.
  - Files: `supabase/migration_fechamento.sql`, `.gitignore`
  - Verify: leitura do Claude; o Anderson roda e cola o resultado da Parte 4.
- [x] **TASK-102** — `rDoTrade` e troca em todos os pontos de §2.9; tipos `stop/alvo/rr_planejado`
  nulos; `calcularCustoDesvio` com null (§2.8) e "não medido" na Visão Geral.
  - Files: `lib/metricas.ts`, `lib/copa-db.ts`, `lib/visao-geral.ts`, `lib/calendario-resultados.ts`,
    `components/v2/visao-geral-conteudo.tsx`, `app/calendario/page.tsx`, `app/estrategias/page.tsx`,
    `app/trades/page.tsx`
  - Verify: `npx tsc --noEmit` limpo; testes novos em `scripts/verify.ts`: trade sem stop → `rDoTrade`
    null; média de R de [+2R, sem stop, −1R] = +0,5R; R$ total inclui os três; custo de desvio com
    `pnl_plano` null → null. `npx tsx scripts/verify.ts` termina com "✅ Todos os testes passaram com sucesso!".

### Fase 2 — Parser
- [ ] **TASK-201** — `lib/profit-csv.ts` (§2.2) e a fixture sintética (§2.3).
  - Files: `lib/profit-csv.ts`, `scripts/fixtures/profit-operacoes.csv`
  - Verify: testes em `verify.ts` com a fixture: número de linhas, lado (C/V), entrada/saída
    trocadas certo na venda, preço com ponto de milhar, R$ negativo nos 3 formatos, só-hora +
    `dataPadrao`, linha WDO com aviso, linha quebrada com aviso sem exceção. E, uma vez, à mão:
    `npx tsx -e` lendo `.local/profit-2026-10-28.csv` → 5 linhas, total R$ 845 (colar a saída no
    relatório; não vira teste porque o arquivo não está no git).

### Fase 3 — Regra do plano
- [ ] **TASK-301** — `lib/plano-do-dia.ts` (§2.5) e `lib/erros.ts` (§2.6).
  - Files: `lib/plano-do-dia.ts`, `lib/erros.ts`
  - Verify: testes em `verify.ts` reproduzindo 28/10: RPP 09:18 (−) no plano; RPP 09:25 (−)
    fora, "cota da 1ª hora"; MAV 10:01 (+) no plano; MAV 10:31 (−) no plano;
    CSI 10:32 (+) **no plano** (as 3 perdas do dia não foram seguidas: o +648 das 10:01 zerou). E 27/10: CSI 11:24 e CSI 11:42 os dois no plano
    (cota 2 na 3ª hora). E: RPP às 10:15 → fora, setup não vale na hora; trade com 4 contratos →
    fora; 6º trade → fora.

### Fase 4 — Tela
- [ ] **TASK-401** — `lib/fechamento-db.ts`: carregar trades de uma data, casamento (§2.4),
  `salvarFechamento` (§2.7).
  - Files: `lib/fechamento-db.ts`
  - Verify: `tsc` limpo; função pura do casamento (`casarComBanco(linhas, tradesDoBanco)`) testada
    em `verify.ts`: chave igual → já no sistema; checklist a 90 s → casa; a 200 s → novo.
- [ ] **TASK-402** — `app/fechamento/page.tsx` (FR-002 a FR-008, FR-012), estilo das telas v2
  (`components/v2/estilos.ts`, `CARD`, `chip`…).
  - Files: `app/fechamento/page.tsx` (pode separar o cartão em `components/v2/cartao-fechamento.tsx`)
  - Verify: `npm run dev`, abrir `/fechamento?demo=1`, colar a fixture → cartões aparecem, barra de
    conferência bate, plano calculado aparece por trade, "Salvar" desabilitado no demo.
- [ ] **TASK-403** — Item "Fechar o dia" no menu (FR-001).
  - Files: `components/layout/shell.tsx`
  - Verify: aparece primeiro no grupo Registro, ativo em `/fechamento`, funciona com a barra recolhida.

### Fase 5 — Fechamento
- [ ] **TASK-501** — `npx tsc --noEmit`, `npx tsx scripts/verify.ts` e `npm run build` limpos
  (parar o `npm run dev` antes do build). Conferência visual em 1440 px e ~900 px, temas claro e
  escuro, sem rolagem horizontal. Desvio temporário no `components/auth-gate.tsx` só para ver sem
  login, **removido antes de terminar** (o `git diff` desse arquivo vem vazio).
- [ ] **TASK-502** — Atualizar `CHECKPOINT.md` (Pronto e verificado + a armadilha do
  `Number(null)`). Não fazer commit nem push: o Anderson pede.
- [ ] **TASK-503** (Anderson + Claude) — Prova real: com a migração rodada, importar
  `.local/profit-2026-10-28.csv` em `/fechamento` para 28/10. Os 5 trades já lançados por SQL
  casam (nenhum duplicado), o total fica R$ +845, e a Visão Geral mostra R só dos trades com stop.

---

## 4. Rotina do operador (para a tela ensinar, em texto pequeno no topo)
1. **Antes de cada trade, na agenda:** hora · setup · gatilho · stop · alvo · contratos · cota da hora.
2. **Depois:** motivo da saída · erro (ou nenhum).
3. **12:00:** Profit → Operações → exportar CSV → "Fechar o dia" → completar com a agenda → conferir o total → salvar.
