# Trade System — Anderson

> **Fonte canônica.** Tudo o que existe no cockpit deriva deste documento:
> os checklists, o gate, a pré-sessão, a calibração.
> Se algo no sistema não está aqui, sai do sistema.

**Definido pelo operador em:** 2026-09-15
**Mercado:** **só WIN** (mini índice) — desde 22/09/2026
**Plataforma:** Profit Chart

---

## 1. Janela

> **Atualizado em 22/09/2026 — teste de 2 semanas (até ~06/10).** Fonte: trades
> reais exportados do Profit, 22/08–22/09 (conta real e conta da Copa). Script:
> `profit/analise_trades.py`.

| Horário | O que fazer |
|---|---|
| **09:00 – 10:00** | **Só observar e marcar**: micro tendência, lado manipulado, liquidez. **Sem entrada.** |
| 10:00 | Ler o rótulo do indicador: 1ª hora COMPRIMIDA ou ESTICADA |
| **10:00 – 11:00** | **Janela nobre de entrada**: abertura do à vista (10:00) e de NY (10:30) |
| **11:00 – 11:30** | Entrada ainda válida (score maior) |
| **11:30 – 12:00** | **Sem entrada nova.** Só gerenciar o que está aberto |
| **12:00** | **FIM.** Fecha o Profit |

**O norte, em três linhas** (definido pelo operador em 22/09/2026):
1. Tela só de **09:00 a 12:00**, sempre.
2. Abrir posição só de **10:00 a 11:30**.
3. Só **WIN**.

**Por quê** (só WIN, entradas por horário):

| | 09:00–09:59 | 10:00–10:59 | 11:00–11:59 | 14:00+ |
|---|---|---|---|---|
| Conta real | −R$ 800 (19% acerto) | +R$ 526 | +R$ 1.916 | −R$ 1.669 |
| Copa | +R$ 2.970 (4 trades) | +R$ 11.755 | +R$ 6.375 | −R$ 2.009 |

- 09:00–10:00 é quando o índice faz a **manipulação da abertura**, antes de o volume
  do à vista e de NY definir um lado. Entrar ali muitas vezes é ser a liquidez.
- WDO e Bitcoin: na Copa, WIN fez +R$ 20.576; WDO + BIT tiraram R$ 7.137.

O cockpit trava: entrada só de 10:00 a 11:29, e só WIN. O Profit não trava o horário
nem o ativo — tirar WDO/BIT do layout e fechar o Profit às 12:00.

**Decisão ao fim do teste:** comparar os trades das 2 semanas (registrados no cockpit)
com o período anterior. Se 10:00–12:00 mantiver o resultado com menos operações, fica.

## 2. Gerenciamento de risco

Configurado no próprio Profit, e ele trava:

| Limite | Valor |
|---|---|
| Perdas no dia | **3** |
| Operações no dia | **5** |

Esses são os números da plataforma. O sistema respeita exatamente eles — regra
que contradiz a plataforma vira regra ignorada.

## 3. Timeframes

| Papel | Timeframe |
|---|---|
| **HTF** — liquidez, sweep, PD array | **60m e 15m** |
| **LTF** — reação, confirmação, gatilho | **1m** |

> No índice, o HTF é 60m/15m. **Não é o diário.** Derivar para o diário é sair do
> sistema.

O LTF existe para uma coisa só: ver **como é a briga dentro da região** marcada
no HTF. Mesma lógica de leitura que o campeão do Robbins World Cup descreve —
ele olha absorção e troca de dominância; aqui se olha estrutura, indução e MSS.

---

# Setup A — REVERSÃO

Opera contra o movimento que acabou de acontecer, depois que ele varreu
liquidez.

## Sequência

```
1. Liquidez HTF mapeada (60m / 15m)
2. PD array HTF marcado como destino (FVG / OB / BPR, 60m ou 15m)
3. SWEEP dessa liquidez HTF
4. Desce para o 1m e lê a reação DENTRO da região
5. Encontra um dos três sinais de reversão (abaixo)
6. MSS no 1m
7. Reteste de FVG ou BPR → entrada
```

## O que se procura no 1 minuto

Três coisas. Qualquer uma delas serve; juntas valem mais.

**1. Estrutura de rompimento induzindo players**
Rompimento que convida o player a comprar ou vender o rompimento, **dentro da
região de sweep**. O rompimento existe para capturar quem entrou nele.

**2. AMD na região**
Acumulação, manipulação e distribuição revertendo o movimento depois do sweep na
liquidez HTF. A sequência completa visível dentro da região.

**3. Swing + reversão forte**
O mercado deixa um swing low (ou high) depois do sweep e reverte **forte, com
barras grandes e consecutivas**, realiza o MSS, e volta a retestar um FVG ou BPR.

> "Barras grandes e consecutivas" é o critério. Reversão arrastada não conta.

## Entrada

No **reteste** do FVG ou BPR deixado pela perna do MSS. Nunca perseguindo.

## Stop

Além do extremo do swing que originou o MSS. **Não** na barra do FVG.

---

# Setup B — CONTINUIDADE DE TENDÊNCIA

Opera a favor do movimento, entrando na correção.

## Compra — tendência de alta clara

```
1. Tendência de alta clara no HTF
2. Mercado cria um SWING HIGH
3. Mercado CAPTURA O FUNDO desse swing high
4. Entrada em FVG ou bloco de ordem
   (ou em FVG na retomada da próxima perna)
```

## Venda — tendência de baixa clara

```
1. Tendência de baixa clara no HTF
2. Mercado cria um SWING LOW
3. Mercado CAPTURA O ÚLTIMO TOPO
4. Entrada em bloco de ordem ou FVG
```

## A lógica

A captura do extremo oposto do swing é o mesmo mecanismo do sweep, em escala
menor: pega a liquidez de quem entrou na correção, e devolve o preço para a
direção da tendência. O array (FVG ou OB) é onde se entra depois disso.

## Diferença essencial para o Setup A

| | Setup A — Reversão | Setup B — Continuidade |
|---|---|---|
| Direção | **contra** a perna que varreu | **a favor** da tendência |
| Gatilho | sweep de liquidez HTF | captura do extremo do swing |
| Contexto exigido | PD array HTF como destino | tendência clara no HTF |
| Confirmação | MSS no 1m | array na região da captura |

**Não se mistura os dois.** Ou o dia é de reversão em array HTF, ou é de
continuidade em tendência. Escolher na pré-sessão, não no calor.

---

# Setup C — VARRIDA DA BARRA DAS 10 *(em teste desde 23/09/2026)*

Observado pelo operador no gráfico de 15 min: *"a barra das 10 ou manipula ou é
manipulada, deixando máxima e mínima"*. A abertura do à vista é o momento da
manipulação — em dois modos.

## Os dois modos

| Modo | O que acontece | Direção | Evidência |
|---|---|---|---|
| **C1 — é manipulada** | entre 10:15 e 11:14, o preço passa da máxima/mínima **da barra das 10** (sweep) | contra o lado varrido | 1 min: +0,21R, 2× a base; 5 anos: reversão e continuação iguais |
| **C2 — manipula** | **a própria barra das 10** varre o topo/fundo de uma **barra de 15 min anterior** e devolve (na mesma barra ou nas seguintes; não precisa romper) | contra o lado varrido | 1 min: +0,20R, 2× a base, menos estável |

Os dois cenários do C2 (descritos pelo operador):

- **Continuação:** 1ª hora em tendência (3 das 4 barras de 15 min na mesma direção,
  ou domínio claro de um lado). O índice deixa uma máxima (ou mínima) contra a tendência;
  o à vista abre, varre essa liquidez e o preço segue a tendência.
  Exemplo (25/09): 1ª hora de baixa; a barra das 10 subiu e varreu o topo da barra das
  09:15; a barra das 10:15 fechou de baixa, para dentro → venda.
  É o cenário principal do C2 para o operador: a barra das 10 vem papar os stops do
  último topo (tendência de baixa) ou do último fundo (tendência de alta) e o preço
  segue. Medido (5 meses de 1 min): 36 trades, +0,17R (t 1,0), metades +0,44 / 0,00;
  base +0,11R. Em 5 anos de 15 min, anda igual à mesma confirmação sem o sweep.
- **Reversão:** o à vista abre perto de um BSL/SSL, varre na barra das 10 e devolve —
  com barras contrárias depois, ou já na própria barra das 10 (sweep e início da
  reversão na mesma barra).

## Regras

```
1. NÍVEL      às 10:15, máxima e mínima da barra de 15 min das 10:00
              (linhas douradas do indicador Barra10H)
2. SWEEP
   C1         entre 10:15 e 11:14, o preço PASSA da linha da barra das 10
   C2         dentro da barra das 10, o preço PASSA do topo/fundo de uma
              barra de 15 min anterior
   Direção    topo varrido -> VENDA   |   fundo varrido -> COMPRA
   NÃO esperar a barra de 15 min fechar: o sweep já libera olhar o 1 min.
   Se o preço seguir e romper, não aparece o MSS (ou o stop pega).
3. GATILHO    no 1 min: sinal de atuação institucional e MSS de reversão
              em até 30 min depois do sweep, e antes de 11:15
4. ENTRADA    reteste do FVG ou do BLOCO DE ORDEM da pernada do MSS
              OB = último candle contrário antes da pernada; entrada na
              abertura dele. No C2, preferir o FVG (OB pior no teste)
5. STOP       no extremo da pernada do MSS
              (no C2, NUNCA no extremo da barra das 10: fica largo demais)
6. ALVO       próximo BSL/SSL; trailing: zero a zero em 1R, depois
              atrás dos swings de 1 min
```

**Registrar C1 ou C2 em cada trade.** Os dois são medidos separados.

| | Estrutura (5 anos, 15 min) | Gatilho de 1 min (5 meses) |
|---|---|---|
| C1 | volta ao outro lado 52% × 44% da barra das 11 (z = 3,7) | 86 trades, **+0,21R** (t 1,8), metades +0,23 / +0,20 |
| C2 | só se destaca na **reversão contra a tendência da 1ª hora** (3R 16% × 10%) | 95 trades, **+0,20R** (t 1,8), metades +0,36 / +0,05 |
| Base: todo gatilho 10:00–11:14 | — | 484 trades, +0,11R |

Gatilho de 1 min testado **como se opera ao vivo**: sweep → MSS + FVG de reversão, sem
esperar o 15 min fechar (`profit/backtest_c_ao_vivo.py`). Recorte mais forte: **C1 contra a
tendência da 1ª hora, 36 trades, +0,43R (t 2,2), metades +0,48 / +0,40** — achado depois
de olhar os dados, precisa confirmar ao vivo.

> **Correção de 25/09/2026.** Os números de 1 min publicados antes (C1 +0,35R, C2
> +0,30R, 64 trades +0,39R) estavam errados: o backtest exigia que a barra de 15 min
> fechasse de volta, mas deixava a entrada acontecer antes desse fechamento. Detalhes:
> [[Estudo_Barra_das_10]] itens 6 e 7.

- **Um trade do Setup C por dia.** Dentro da janela de entrada 10:00–11:30, só WIN,
  limites do dia valendo.
- **As duas direções valem**, e os dois cenários também. Em 5 meses de 1 min, a reversão
  contra a 1ª hora foi o melhor recorte do C1 (+0,43R), mas **nos 5 anos de 15 min
  reversão e continuação andam igual** (C1 2R 18% × 21%; C2 21% × 22%). Anotar o cenário
  em cada trade, sem dar prioridade a nenhum.
- **Tamanho calculado para o stop** (mediana do backtest: ~420 pts).

## Evidência

| Parte | Função | Base |
|---|---|---|
| Barra das 10 varrida | onde e quando | 5 anos de 15 min: varrida em ~2/3 dos dias todo ano; volta ao outro lado 52% × 44% da barra das 11, em todos os 6 anos (z = 3,7) |
| MSS + FVG no 1 min | entrada com stop curto | 5 meses de 1 min, sweep → gatilho sem esperar o 15 min: C1 +0,21R, C2 +0,20R, o dobro da base (+0,11R); 3 contratos: C1 +R$ 2.583, C2 +R$ 1.695 |
| Alvo BSL/SSL + trailing | o ganho | a gestão do operador |

**Operar a varrida no fechamento do 15 min NÃO funciona** (5 anos: 41% de acerto, payoff
1,12, −0,08R/trade). O ganho vem do **gatilho de 1 min logo depois do sweep**. Ainda não é
prova (t 1,8, 5 meses; a diferença para a base não é significativa): os trades reais do
cockpit decidem.

Detalhes: [[Estudo_Barra_das_10]].

## Critério de manutenção (definido antes do teste)

- Registrar cada trade no cockpit com o **R final** e o tipo do dia (lateral/tendência).
- **20–30 trades:** média acima de zero → fica; perto do backtest (+0,3R ou mais) →
  setup principal.
- **Negativo depois de 30 trades → sai.** Sem ajustar regra para salvar o setup.
- Cenário novo durante o teste (ex.: rompimento seguido de continuidade, 23/09): anotar,
  **não mudar a regra**. Mudança só no fim, com os números.

---

## 4. O que NÃO faz parte deste sistema

Registrado explicitamente para não voltar por acidente:

- **Diário como HTF** — o HTF aqui é 60m/15m
- **CE / 50% do array como regra** — a região é que vale, não a linha
- **SMT WIN × WDO** — não é usado
- **Quarterly Theory / Quarter Sequence** — material de estudo, não operacional
- **GEX, order flow, volume profile** — outro operacional, do campeão, não deste
- **BPR como ponto de entrada isolado** — BPR entra como array de reteste no
  Setup A, não como gatilho próprio fora da sequência
- **Qualquer entrada fora de 10:00–11:30** (09:00–10:00 é leitura; 11:30–12:00 é gestão)
- **WDO, Bitcoin e outros ativos** — só WIN
- **Operar depois das 12:00** — nas duas contas, a tarde deu prejuízo

---

## 5. Rotina — pré-mercado

Antes das 09:00, com a cabeça fria. Nada disso se faz com o preço andando.

**1. Liquidez HTF** — marcar no 60m e no 15m:
- PDH e PDL
- topos e fundos relevantes
- EQH / EQL

**2. PD arrays HTF** — marcar os não mitigados, 60m e 15m:
- FVG
- order blocks
- BPR

**3. Contexto** — decidir e escrever:
- tendência clara? qual direção?
- ou preço chegando em array HTF com liquidez varrida?
- **qual setup está disponível hoje: A, B, ou nenhum**

**4. Agenda** — eventos do dia e horário. Notícia dentro da janela muda o
tamanho, não a leitura.

**5. Estado próprio** — sono, tilt, pressão. Honesto, não otimista.

**6. Limites do dia** — confirmar: 3 perdas, 5 operações.

> Se ao fim da pré-sessão a resposta do item 3 for "nenhum", o dia é de não
> operar. Isso é uma decisão válida e é a mais barata que existe.

---

## 6. Rotina — durante

- 09:00–10:00: só leitura — marcar o lado manipulado e a liquidez
- Entradas só de 10:00 a 11:29, só WIN; de 11:30 a 12:00 só gestão
- 12:00: fecha o Profit
- Um setup por vez, o escolhido na pré-sessão
- Checklist preenchido **antes** da ordem, sempre
- Fechou o trade, registra e sai do gráfico — não fica caçando o próximo

## 7. Rotina — pós

Ao fechar cada trade, classificar a **execução**, separado do resultado:

| | |
|---|---|
| **A** | fiz exatamente o que devia. Sem hesitar, sem perseguir, sem antecipar |
| **B** | executei, mas com ruído. Hesitei, entrei torto, saí cedo |
| **C** | forcei. Entortei a regra, antecipei sem confirmação, quis recuperar |

Trade vencedor pode ser C. Vitória com processo C é o resultado mais perigoso
que existe, porque reforça o comportamento errado.

A métrica que importa não é winrate. É **frequência de C**.

---

## 8. Princípio

> Consistência não vem de mais sessões A. Vem de **eliminar as C**.
> Você não controla quantos setups bons o mercado oferece.
> Controla as perdas burras.

---

**Ver também:** [[CRT_e_Quarterly_Theory]] (estudo, fora do operacional) ·
[[FVG_e_MSS]] · [[Draw_on_Liquidity]]
