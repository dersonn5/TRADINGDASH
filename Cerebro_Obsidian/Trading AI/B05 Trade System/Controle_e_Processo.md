# Controle e Processo

> O que o sistema controla, com que gatilho, e o que ele faz quando o gatilho
> dispara. Sem filosofia e sem opinião de terceiro — só mecanismo.
>
> Companion do [[Trade_System_Anderson]], que define **o que** operar.
> Este define **como o processo é forçado**.

---

## A regra de admissão

Uma regra só entra neste sistema se responder as três:

| | |
|---|---|
| **1. Qual o número?** | Se não tem número, é conselho. Conselho não entra. |
| **2. O que o sistema FAZ quando o número bate?** | Se ele só avisa, não é controle. É enfeite. |
| **3. Dá pra verificar depois?** | Se não fica registrado, não dá pra saber se funcionou. |

"Não operar demais" falha nas três. "Máximo 5 operações, o botão trava na 5ª,
e fica gravado quantas foram" passa nas três.

---

## Os controles ativos

### C1 · Janela de operação

| | |
|---|---|
| **Controla** | quando pode operar |
| **Número** | 09:00 – 12:00 · janela nobre 10:00 – 11:00 |
| **Ação** | fora da janela, o gate não libera. Fora da nobre, score mínimo sobe de 65 para 80 |
| **Registro** | coluna `janela` em cada trade: PRIME, VALIDA ou FORA |
| **Reforço externo** | o Profit trava sozinho depois das 12:00 |

### C2 · Limite de operações

| | |
|---|---|
| **Controla** | quantidade de trades no dia |
| **Número** | 5 operações |
| **Ação** | na 5ª, o gate bloqueia |
| **Registro** | `operacoes_hoje` contado da sessão do dia |
| **Reforço externo** | o Profit trava no mesmo número |

### C3 · Limite de perdas

| | |
|---|---|
| **Controla** | quando o dia acaba |
| **Número** | 3 perdas |
| **Ação** | na 3ª, pregão encerrado |
| **Registro** | `perdas_hoje` |
| **Reforço externo** | o Profit trava no mesmo número |

### C4 · Cooldown após perda

| | |
|---|---|
| **Controla** | operar no calor logo depois de perder |
| **Número** | 30 minutos, a partir de **qualquer** perda |
| **Ação** | gate bloqueado até o tempo passar, com os minutos restantes na tela |
| **Registro** | `ultimo_loss_em` |
| **Por que na primeira** | a cascata começa na primeira, não na terceira. Cooldown que só arma depois chega atrasado |

### C5 · Sequência do setup

| | |
|---|---|
| **Controla** | entrar sem a sequência completa |
| **Número** | 7 passos obrigatórios (reversão) · 6 (continuidade) |
| **Ação** | só o próximo passo é clicável. Voltar a um passo limpa todos os seguintes |
| **Registro** | snapshot de todos os itens, marcados e não marcados, por trade |

### C6 · Score mínimo

| | |
|---|---|
| **Controla** | entrar em setup fraco |
| **Número** | 65 na janela nobre · 80 fora dela |
| **Ação** | abaixo do mínimo, o botão não libera |
| **Registro** | `score` e `score_minimo` gravados no trade |
| **Status** | **pesos são ESTIMADO.** Nenhum medido ainda. Ver C11 |

### C7 · Coerência de preço

| | |
|---|---|
| **Controla** | registrar stop ou alvo do lado errado |
| **Número** | COMPRA exige `stop < entrada < alvo` · VENDA o inverso |
| **Ação** | validação na tela e `CHECK` no banco. O banco recusa |
| **Registro** | impossível gravar incoerente |

### C8 · RR mínimo

| | |
|---|---|
| **Controla** | risco desproporcional ao alvo |
| **Número** | RR ≥ 2 |
| **Ação** | é item obrigatório do checklist; sem ele a sequência não fecha |
| **Registro** | `rr_planejado` |

### C9 · Um trade por vez

| | |
|---|---|
| **Controla** | acumular posição |
| **Número** | 1 trade aberto |
| **Ação** | com trade aberto, não registra outro |
| **Registro** | `status` ABERTO/FECHADO |

### C10 · Auditoria de execução

| | |
|---|---|
| **Controla** | julgar o trade pelo resultado em vez do processo |
| **Número** | classificação A, B ou C, obrigatória no fechamento |
| **Ação** | o trade não fecha sem ela. É independente do P&L — **trade vencedor pode ser C** |
| **Registro** | prefixo `[EXEC:X]` nas notas + as 4 flags de disciplina |
| **Métrica derivada** | frequência de C. É ela que mede processo, não o winrate |

### C11 · Custo da indisciplina

| | |
|---|---|
| **Controla** | não perceber o preço de furar o plano |
| **Número** | soma de `pnl_plano − pnl_real` |
| **Ação** | número visível, em reais |
| **Registro** | `v_copa_disciplina` |
| **Detalhe** | ancorado no **fato** (saiu manual e o plano daria outro resultado), não no auto-relato. Auto-relato falha justamente sob emoção |

### C12 · Descarte do pior dia

| | |
|---|---|
| **Controla** | gastar o mulligan da fase sem perceber |
| **Número** | 1 dia negativo por fase sai de graça |
| **Ação** | com o mulligan gasto, o limite de perda diária é cortado pela metade e o modo defensivo é forçado |
| **Registro** | `v_copa_fase_placar` |

---

## O que ainda NÃO está controlado

Registrado para não ser esquecido.

| Lacuna | Por que importa | Correção |
|---|---|---|
| **Tamanho de posição** | `contratos` é digitado na hora, com o emocional quente. É o canal por onde a ganância entra sem passar por nenhuma trava | declarar o tamanho na pré-sessão, frio, e bloquear desvio |
| **Pré-sessão não é obrigatória** | dá para abrir e operar sem ter marcado liquidez, arrays e escolhido o setup do dia | gate exige sessão preenchida antes de liberar o primeiro trade |
| **Escolha do setup no calor** | a tela deixa trocar de estratégia durante o pregão | a escolha é da pré-sessão; trocar depois exige justificativa registrada |
| **Pesos não calibrados** | o score bloqueia com números que são estimativa minha, não medição sua | backtest no histórico de WINFUT, Fase 3 do plano |
| **O score prevê?** | se faixa alta não performar acima da baixa, o score é decorativo | `v_copa_score_buckets` responde assim que houver amostra |

---

## Regra de alteração

Mudar qualquer número acima exige duas coisas:

1. **Dado.** Qual observação nos seus trades justifica a mudança.
2. **Fora do pregão.** Número nunca muda com posição aberta nem no meio de uma
   fase da competição — senão os dias deixam de ser comparáveis entre si.

Afrouxar limite durante sequência de perda é a alteração mais cara que existe, e
é a que mais dá vontade de fazer.
