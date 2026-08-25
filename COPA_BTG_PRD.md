# PRD — Cockpit Copa BTG

**Status:** aguardando revisão do Anderson
**Data:** 2026-08-25
**Pipeline:** PRD (este doc) → BUILD-SPEC (`COPA_BTG_BUILD_SPEC.md`) → execução (Gemini) → verify (Claude)

---

## 1. Problema

Anderson volta ao mercado na Copa BTG operando WIN/WDO manualmente. O que custa
dinheiro não é falta de leitura — é **entrar sem a sequência completa** e **mexer
no trade depois de aberto**. As 5 lições já formalizam o modelo:

> Liquidez → Tendência → CHoCH → Nova liquidez → Execução

Modelo na cabeça não impede o clique no impulso. Falta um **gate físico** entre a
vontade de entrar e a ordem enviada, e falta **prova estatística** de quais
confluências realmente pagam.

O projeto já tem o cérebro: `strategies/playbook_anderson.py` codifica a sequência
inteira e `core/entry_quality.py` pontua confluência 0-100 → A+/A/B/C/D. O que não
existe é a camada de operação humana.

## 2. Para quem

Um operador: Anderson. Solo, discricionário, WIN/WDO, durante a Copa BTG.
Não é produto multi-usuário. Sem login, sem onboarding, sem deploy em nuvem.

## 3. Objetivo mensurável

Ao fim da Copa:

- **0 trades sem checklist completo.** Ordem só sai depois do gate liberar.
- **0 trades fora dos circuit breakers** (perda máx. diária, máx. trades, sequência
  de perdas, horário).
- Existe resposta numérica para: *"quais itens do meu checklist aumentam meu
  winrate e quais são decorativos?"*
- Existe o número do **custo da indisciplina**: quanto R$ foi perdido em trades onde
  o plano não foi respeitado (stop antecipado, parcial emocional, alvo mudado no meio).
- **Nenhuma fase é perdida por dois dias negativos.** O descarte do pior dia cobre
  um; o software garante que não exista um segundo.

## 4. Escopo

### ENTRA
- Pré-sessão diária obrigatória (ambiente qualitativo do dia).
- Ranking de quais estratégias estão favoráveis hoje, derivado da pré-sessão.
- Checklist interativo por estratégia, com itens **KILL** (bloqueiam) e **PONTO**
  (somam score).
- Score 0-100 ao vivo + grade A+/A/B/C/D, reusando os pesos de `core/entry_quality.py`.
- Gate: botão de liberar entrada só ativa com todos os KILL marcados, score ≥
  threshold e nenhum circuit breaker ativo.
- Registro do trade (entrada, stop, alvo, contratos, RR planejado).
- Fechamento do trade + auditoria de disciplina obrigatória.
- Estatística: por estratégia, por grade, **por item de checklist**, por horário,
  por dia da semana.
- Circuit breakers de risco da Copa, configuráveis.
- Estratégias definidas como **arquivo de configuração**, não código — adicionar ou
  ajustar checklist não exige programar.

### NÃO ENTRA (anti-escopo — é lei)
- Feed de preço em tempo real. O software não sabe onde o preço está.
- Detecção automática de sweep / CHoCH / FVG. Quem enxerga é o operador.
- Envio de ordem para corretora. O software libera; você digita no Profit/MT5.
- Backtest, ML, robô. Já existe no projeto e continua separado.
- Multi-usuário, login, nuvem. Roda local, no PC do pregão.
- Mobile app. Uso é no desktop, ao lado do gráfico.

## 5. Modelo de dados

```
SessionDay (1 por dia de pregão)
  data (PK), bias_d1, bias_h1, contexto (TENDENCIA|RANGE|INDEFINIDO)
  niveis[]        : lista livre { label, preco }  — PDH, PDL, máx/mín semanal, EQH/EQL, gaps
  agenda[]        : { evento, horario, impacto: ALTO|MEDIO|BAIXO }
  estado_operador : { sono 0-5, tilt 0-5, pressao 0-5 }
  meta_dia, limite_perda_dia, max_trades_dia
  modo            : NORMAL | DEFENSIVO   (defensivo auto-sugerido por red flags)
  notas

Strategy (config versionada em arquivo, não banco)
  id, nome, descricao, mercado
  ambiente_favoravel[]      : condições onde funciona
  ambiente_desfavoravel[]   : onde falha
  horarios_validos[]        : janelas HH:MM-HH:MM
  checklist[]               : { id, tipo: KILL|PONTO, peso, label, ajuda }
  score_minimo

Trade
  id, session_day (FK), strategy_id, direcao (COMPRA|VENDA)
  checklist_marcado : { item_id: bool }
  score, grade
  entrada, stop, alvo, contratos, rr_planejado
  status            : ABERTO | FECHADO
  saida, motivo_saida : ALVO | STOP | MANUAL
  pnl_real, pnl_plano
  disciplina        : { respeitou_plano, antecipou_stop, parcial_emocional, mudou_alvo }
  notas, screenshot_path
  criado_em, fechado_em
```

`pnl_plano` = resultado que o trade teria se tivesse ido até alvo ou stop. É o que
permite calcular custo da indisciplina **sem feed de preço**: numa saída manual, você
informa no fechamento o que aconteceu depois.

## 6. Requisitos funcionais

| ID | Requisito |
|---|---|
| FR-001 | Sem pré-sessão preenchida no dia, todo o resto fica bloqueado. |
| FR-002 | A pré-sessão gera ranking de estratégias: FAVORAVEL / NEUTRA / DESFAVORAVEL hoje, com motivo escrito. |
| FR-003 | Checklist por estratégia com itens KILL e PONTO, renderizado a partir da config. |
| FR-004 | Score e grade recalculam a cada clique, em tempo real, no cliente. |
| FR-005 | Gate de entrada bloqueado enquanto faltar KILL, score < mínimo, ou breaker ativo. Motivo do bloqueio sempre visível. |
| FR-006 | Circuit breakers: perda máx. do dia, máx. trades, N perdas seguidas → cooldown, fora do horário, meta batida. |
| FR-007 | Registro do trade com stop e alvo obrigatórios antes de liberar; RR calculado e exibido ao vivo. |
| FR-008 | Fechamento com auditoria de disciplina (4 flags) obrigatória. |
| FR-009 | Estatística por item de checklist: winrate e expectância com o item marcado vs. não marcado, com N. |
| FR-010 | Estatística por grade: prova se A+ realmente performa acima de B. |
| FR-011 | Painel "custo da indisciplina": soma de (pnl_plano − pnl_real) nos trades com flag de desvio. |
| FR-012 | Curva de capital da Copa + distância para a meta. |
| FR-013 | Estratégias em arquivo de config editável, sem recompilar nem programar. |
| FR-014 | Export/backup do banco em um clique. |
| FR-015 | Modelo de fase: cada dia de trade pertence a uma fase da Copa. Placar da fase exibido **com e sem** o descarte do pior dia. |
| FR-016 | Estado do mulligan: sistema informa se o descarte do pior dia ainda está disponível ou já foi consumido por um dia negativo. |
| FR-017 | Aperto automático: com o mulligan consumido, os dias restantes da fase entram em modo DEFENSIVO forçado e o limite de perda diária cai por um fator configurável. |
| FR-018 | Eficiência de contratos: contratos acumulados na fase e R$ por contrato, exibidos como métrica de primeira classe (é o critério oficial de desempate). |
| FR-019 | Painel do prêmio diário: melhor performance do dia é objetivo secundário rastreado separadamente do placar da fase. |

## 7. Estratégias no MVP

### 1. Playbook Anderson — as 5 lições. Estratégia principal.

**KILL** (sem isso, não entra):
1. Bias H1 definido e a direção da operação bate com ele
2. Liquidez relevante foi varrida — sweep confirmado, preço rejeitou e fechou de volta
3. CHoCH confirmado em vela **fechada**, rompendo a estrutura anterior
4. Nova liquidez formou depois do CHoCH e o preço voltou para buscá-la
5. Stop e alvo definidos antes da ordem, RR ≥ 2
6. Dentro do horário permitido e nenhum breaker ativo

**PONTO** (confluência, peso — total 100):
| Peso | Item |
|---|---|
| 15 | Entrada dentro de PD array — FVG, OB ou breaker |
| 15 | Premium/discount correto |
| 15 | Liquidez varrida é de qualidade: PDH/PDL, EQH/EQL, máx/mín semanal |
| 10 | Displacement forte no CHoCH, deixou FVG |
| 10 | Indução: o pullback varreu micro-topo/fundo antes da entrada |
| 10 | Killzone nobre — dentro de 09:00-12:00, com preferência para 09:00-10:30 |
| 10 | Alvo é liquidez clara, não número arbitrário |
| 10 | Sem notícia de alto impacto nos próximos 30 min |
| 5 | Confluência WIN×WDO |

`score_minimo` default: 65 (grade A).

### 2. Abertura B3 — falso rompimento do range de abertura, reversão.
### 3. Reversão em PDH/PDL — sweep do dia anterior com rejeição.

2 e 3 entram depois que o motor genérico rodar com a 1 — custo de adicionar é
editar config, não programar.

## 8. UI / telas

| Rota | Conteúdo |
|---|---|
| `/copa` | Status do dia (LIBERADO / BLOQUEADO + motivo), KPIs da Copa, pré-sessão, botão Novo Trade |
| `/copa/pre-sessao` | Formulário do ambiente qualitativo do dia |
| `/copa/novo` | Escolha da estratégia → checklist com score ao vivo → gate → registro |
| `/copa/trades` | Journal: abertos (fechar) e histórico |
| `/copa/fase` | Placar da fase: dia a dia, com e sem descarte, estado do mulligan, contratos usados, R$/contrato |
| `/copa/stats` | Probabilidade: por estratégia, grade, item, horário; custo da indisciplina |
| `/copa/estrategias` | Ficha de cada estratégia: quando funciona, quando não, estatística própria |

Reusa o layout que já existe em `cockpit/` (Next 16, shadcn, sidebar pronta). O
cockpit atual (métricas do robô) continua intocado — a Copa é uma seção nova.

## 9. Stack

- **Front:** `cockpit/` existente — Next 16 + React 19 + shadcn + Tailwind 4.
- **Back:** `cockpit_api.py` (FastAPI, porta 8010) + SQLite.
- **Motivo de manter Python no back:** reusa `core/entry_quality.py` e a estatística
  usa pandas. Um `.bat` sobe os dois processos antes do pregão.

## 10. Critério de sucesso

Pronto quando, num pregão real:
1. Você abre, preenche a pré-sessão, e ele diz quais estratégias estão favoráveis.
2. Aparece um setup, você abre o checklist, marca, e o gate libera ou recusa — e você
   aceita a recusa.
3. Você registra, opera, fecha e responde a auditoria de disciplina.
4. No fim da semana, a tela de stats responde qual item do checklist está pagando e
   quanto custou cada desvio de plano.

## 11. Riscos

| Risco | Mitigação |
|---|---|
| Checklist vira burocracia e você pula no calor do pregão | Máx. 6 KILL. Marcação em 1 clique. Meta: < 30s para preencher. |
| Amostra pequena na Copa não dá significância por item | Stats mostram N junto do winrate e sinalizam quando N < 20. |
| Software cai no meio do pregão | SQLite local, sem rede. Export em 1 clique. Subir antes do pregão abrir. |
| Escopo cresce para robô/feed no meio | Anti-escopo do §4 é lei. Feed vira v2, depois da Copa. |

## 12. Regras oficiais da Copa BTG Trader 2026

Fonte: `regulamento-copa-btg-trader.pdf` (Certificado SPA/ME 03.051033/2026),
lido em 2026-08-25. **Estes números são os defaults da config.**

### Calendário
| Fase | Datas | Dias |
|---|---|---|
| Inscrições | 20/07 – **06/09/2026** | — |
| Classificatória Etapa 1 | 14/09 – 17/09 | 4 |
| Classificatória Etapa 2 | 21/09 – 24/09 | 4 |
| Repescagem | 28/09 – 30/09 | 3 |
| Semifinal | 13/10 – 16/10 | 4 |
| Final presencial (SP) | 29/10 | 2 baterias de 45 min |

**Prazo de entrega do software: 14/09/2026.**

### Mecânica de apuração
- Ranking = **melhor performance financeira acumulada em R$ absoluto**, não
  percentual. "Ainda que essa performance represente resultado negativo."
- Saldo **zera a cada fase**. Exceção: Etapas 1 e 2 somam entre si.
- **Descarte do pior dia** em cada fase.
- Apenas **Day Trade** — aberta e encerrada no mesmo pregão. A plataforma zera
  posições e fecha para novas operações **a partir das 17h**.
- Corte: 30% melhores das Etapas 1+2 → Semifinal. Repescagem passa mais 5%.
- Semifinal define 6º–100º lugar e os 5 finalistas.
- **Desempate: vence quem operar o MENOR número de contratos.** Persistindo,
  vence a inscrição mais antiga.
- Prêmio diário de R$ 1.000 para a melhor performance de cada dia, nas Etapas 1,
  2 e Semifinal (12 dias no total).
- Ativos elegíveis: WIN, WDO, BIT, ETR, SOL, EUP, GLD.
- **Exposição máxima** é parametrizada pelo BTG e comunicada antes de cada fase —
  não consta no regulamento. Vira campo de config editável.
- **Não existe regra de perda máxima nem desclassificação por drawdown.** Os
  limites diários são exclusivamente autoimpostos.

### Horário de operação escolhido
**09:00 – 12:00** (definido pelo Anderson). É a janela do checklist e do breaker
de horário. A plataforma permite até as 17h, mas fora dessa janela o sistema
bloqueia.

## 13. Conformidade com o regulamento — restrição de projeto

O item 10 do regulamento prevê desclassificação por "automações não autorizadas,
robôs, scripts, **ferramentas externas** ou qualquer mecanismo não previsto ou
não autorizado pela Promotora", e exige que só o Participante opere, "sem ajuda
ou orientação de terceiros".

Para manter esta ferramenta na categoria de **diário de bordo pessoal** — e não
de ferramenta externa de operação — as restrições abaixo são **invioláveis**,
acima de qualquer requisito funcional deste PRD:

1. **Zero integração** com Profit Pro / Profit Ultra / Scalper Pro / Nelogica /
   BTG. Nenhuma leitura de tela, arquivo, DLL, API ou clipboard dessas
   plataformas.
2. **Zero dado de mercado.** O software nunca sabe onde o preço está.
3. **Zero geração de sinal.** Ele não diz o que operar, nem quando. Só registra
   o que **você** afirma ter visto e trava se você não afirmou tudo.
4. **Zero envio de ordem.** Nenhum caminho de código toca em execução.
5. **Roda offline, local, sem rede externa.** Sem nuvem, sem terceiro.

Estas 5 restrições devem ser reafirmadas em qualquer alteração futura de escopo.

**Ação pendente do Anderson:** enviar ao suporte oficial da Copa a descrição da
ferramenta (checklist pessoal de disciplina, offline, sem integração, sem dados
de mercado, sem sinal) e **guardar a resposta por escrito** antes do início da
Etapa 1. Não bloqueia o desenvolvimento; bloqueia o uso em competição.
