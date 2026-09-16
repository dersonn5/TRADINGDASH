# Trade System — Anderson

> **Fonte canônica.** Tudo o que existe no cockpit deriva deste documento:
> os checklists, o gate, a pré-sessão, a calibração.
> Se algo no sistema não está aqui, sai do sistema.

**Definido pelo operador em:** 2026-09-15
**Mercado:** WIN (mini índice) · WDO
**Plataforma:** Profit Chart

---

## 1. Janela

| | |
|---|---|
| Abertura do pregão B3 | 09:00 |
| **Janela de operação** | **09:00 – 12:00** |
| Depois das 12:00 | o Profit trava sozinho |

Não existe operação fora dessa janela. O trava do Profit é o limite externo; o
checklist é o limite interno e chega antes.

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

## 4. O que NÃO faz parte deste sistema

Registrado explicitamente para não voltar por acidente:

- **Diário como HTF** — o HTF aqui é 60m/15m
- **CE / 50% do array como regra** — a região é que vale, não a linha
- **SMT WIN × WDO** — não é usado
- **Quarterly Theory / Quarter Sequence** — material de estudo, não operacional
- **GEX, order flow, volume profile** — outro operacional, do campeão, não deste
- **BPR como ponto de entrada isolado** — BPR entra como array de reteste no
  Setup A, não como gatilho próprio fora da sequência
- **Qualquer setup fora de 09:00–12:00**

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

- Só a janela 09:00–12:00
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
