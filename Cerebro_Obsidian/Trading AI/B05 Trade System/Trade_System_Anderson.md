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
manipulada, deixando máxima e mínima"*. A abertura do à vista cria liquidez nos dois
lados da barra das 10:00, e o mercado costuma voltar para buscar.

## Regras

```
1. NÍVEL      às 10:15, máxima e mínima da barra de 15 min das 10:00
              (linhas douradas do indicador Barra10H)
2. VARRIDA    entre 10:15 e 11:14, uma barra de 15 min PASSA da linha
              e FECHA DE VOLTA dentro da barra das 10
                topo varrido  -> procurar VENDA
                fundo varrido -> procurar COMPRA
              fechou fora e ficou fora = rompimento -> SEM TRADE
3. GATILHO    no 1 min: MSS no sentido da reversão, até 45 min depois
              do início da barra que varreu
4. ENTRADA    reteste do FVG da pernada do MSS
5. STOP       além do extremo da pernada (o topo/fundo da varrida)
6. ALVO       próximo BSL/SSL; trailing: zero a zero em 1R, depois
              atrás dos swings de 1 min
```

- **Um trade do Setup C por dia.** Dentro da janela de entrada 10:00–11:30, só WIN,
  limites do dia valendo.
- **As duas direções valem.** A direção da 1ª hora (a favor ou contra) não separou
  resultado nos testes — o lado varrido define a direção.
- **Tamanho calculado para o stop** (mediana do backtest: ~420 pts).

## Evidência

| Parte | Função | Base |
|---|---|---|
| Barra das 10 varrida | onde e quando | 5 anos de 15 min: varrida em ~2/3 dos dias todo ano; volta ao outro lado 52% × 44% da barra das 11, em todos os 6 anos (z = 3,7) |
| MSS + FVG no 1 min | entrada com stop curto | 5 meses de 1 min: 64 trades, **+0,39R/trade** (t = 2,5), positivo em todos os meses; 3 contratos: +R$ 3.888, pior queda −R$ 834 |
| Alvo BSL/SSL + trailing | o ganho | a gestão do operador |

**Operar a varrida no fechamento do 15 min NÃO funciona** (5 anos: 41% de acerto, payoff
1,12, −0,08R/trade). O resultado vem do gatilho de 1 min em cima da estrutura.

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
