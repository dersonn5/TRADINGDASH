# CRT + Quarterly Theory — o filtro de preço e o filtro de tempo

Destilado do canal **Chronos CRT** (vídeo sobre Quarter Sequence). A transcrição
de origem era tradução automática do espanhol e estava bastante corrompida — os
termos foram restaurados aqui.

> **Status: ESTUDO. Não está no checklist operacional.**
> Nada deste material foi medido nos dados do WIN. Ver a seção final.

---

## Linhagem — quem criou o quê

Importa porque os três se citam e o material circula sem crédito.

| Pessoa | Contribuição |
|---|---|
| **ICT** (Inner Circle Trader) | Base de todos. Liquidez, order blocks, dealing ranges. |
| **Romeo** (Romeo TPT / @raidorpurge) | Criou o **CRT** — Candle Range Theory. Aluno de ICT. |
| **TraderDaye** | Criou a **Quarterly Theory**. Aluno da mentoria privada do ICT. |
| **Lethality** | Aluno do TraderDaye. Foi quem tornou pública a **Quarter Sequence**. |

Erros comuns da tradução automática: `TIC` = ICT · `Teoria Crítica da Raça` = CRT
· `Quarly` / `teoria dos quartos` / `pedreiras` = Quarterly Theory ·
`Letalidade` = Lethality · `beijo da morte` = KOD (Kiss of Death).

---

## 1. CRT — o filtro de preço

Lê liquidez nas **máximas e mínimas de velas de timeframe maior**. Cada vela de
HTF é um range; o preço vai buscar a liquidez de um dos lados.

É AMD — acumulação, manipulação, distribuição — no lugar certo. A tese do CRT é
que não é padrão de vela: é a lógica por trás de Turtle Soup, modelo 1, breaker
block, MSS, OTE e KOD, todos casos particulares da mesma coisa.

## 2. Quarterly Theory — o filtro de tempo

Ciclos se dividem em **quartos**, fractalmente, sem fim:

```
Ano      → 4 trimestres
Mês      → 4 semanas
Semana   → seg, ter, qua, qui        (sexta tem papel independente)
Dia      → 4 blocos de 6 horas
Sessão   → 4 quartos
...      → até nano
```

Cada quarto recebe um papel do AMD: pode ser **A**cumulação, **M**anipulação,
**D**istribuição ou **X** (reversão / continuação). Daí `AMDX`, `XAMD`.

> [!IMPORTANT]
> **A âncora horária exata dos quartos precisa ser confirmada.** A transcrição
> está corrompida justamente nessa parte. A divisão fractal (dia = 4 × 6h) está
> clara; o horário de início de cada quarto, não. Confirmar na fonte antes de
> usar qualquer coisa ancorada em horário.

## 3. Quarter Sequence — a regra de alinhamento

Esta é a parte que raramente é divulgada, e é o núcleo prático.

**Regra: pelo menos 3 ciclos alinhados.**

Alinhamentos válidos:
- `Q2 · Q2 · Q2`
- `Q3 · Q3 · Q3`
- **Q1 e Q4 são os únicos que se combinam entre si** → `1-4`, `1-4-1`, `1-1-1`, `4-1`

Q2 e Q3 só alinham com iguais. Q1 e Q4 são intercambiáveis.

Quando a sequência alinha em 3+ ciclos, aquele é o ponto de maior probabilidade
do ciclo.

## 4. SSMT — Sequential SMT

Não basta ter SMT (divergência entre ativos correlacionados). O SSMT exige que a
divergência coincida com **duas** coisas:

1. a sequência de quartos alinhada
2. a máxima ou mínima que se forma **durante** essa sequência

SMT solto é ruído. SMT em cima da sequência é o sinal.

## 5. O checklist do Romeo

Publicado por ele em 2024 como "os elementos de um trade de alta probabilidade":

| # | Elemento | Importância |
|---|---|---|
| 2 | **O horário da manipulação** | **maior** |
| 1 | Nível-chave marcado em timeframe alto | média |
| 3 | Máxima/mínima antes da manipulação | menor |

Ordem declarada: **2 > 1 > 3**. O tempo acima do nível, e o nível acima do padrão.

Nas notas dele: *"ignore todos os padrões, ignore FVG, order blocks, breaker
blocks, e foque nos fatores acima."*

Alinha com o ICT: *"tempo é muito mais importante que preço, que qualquer padrão."*

## 6. A tese central

CRT e Quarterly Theory **não se contradizem** — olham a mesma coisa com filtros
diferentes. Um filtro para preço, outro para tempo.

A justificativa: toda vela tem em comum apenas **abertura e fechamento**. O que
acontece no meio — até onde sobe, até onde desce — é variável. O tempo é o que
permanece constante.

Mercados vão de **abertura → liquidez → fechamento**.

---

## Como isto se relaciona com o Playbook Anderson

O playbook atual tem **um** elemento de tempo: a janela 09:00–12:00, com
10:00–11:00 como nobre. A justificativa foi por evento de mercado — abertura do
à vista às 10:00 e abertura americana às 10:30.

**Conversão de fuso, que importa porque toda essa literatura é em horário de
Nova York:** o Brasil não tem horário de verão, os EUA têm. Entre março e
novembro, `NY = BRT − 1`.

| BRT | NY (com DST) |
|---|---|
| 09:00 | 08:00 |
| **10:00** | **09:00** |
| **11:00** | **10:00** |
| 12:00 | 11:00 |

Ou seja, a janela nobre **10:00–11:00 BRT é 09:00–10:00 NY**.

**A pergunta a testar, não a assumir:** a Quarterly Theory aponta para a mesma
janela? Se apontar, é confirmação independente de uma escolha feita por outro
critério. Se apontar para outra, é informação mais valiosa ainda.

Isso é respondível com dado: a coluna `janela` em `copa_trades` e a view
`v_copa_janela_performance` já medem o desempenho por janela. E o backtest do
WINFUT (Fase 3 do `COPA_BTG_PLAN_V2.md`) pode testar alinhamento de quartos
contra resultado.

---

## Por que isto NÃO entra no checklist agora

Dois motivos, ambos do próprio sistema:

**1. A Etapa 1 está em andamento.** Mudar o modelo no meio da fase é a lição 5
aplicada no nível do sistema em vez do trade. Item novo agora e os 4 dias deixam
de ser comparáveis entre si.

**2. Todos os pesos atuais já são `ESTIMADO`.** Acrescentar confluência não
medida não melhora o score — dilui. Item sem medição é ruído com aparência de
rigor.

**Caminho correto:** fica aqui como estudo, entra na Fase 3 do plano junto com a
calibração, e só vira item de checklist se o backtest mostrar que separa trade
bom de trade ruim nos dados do WIN.

---

**Fonte:** canal Chronos CRT, vídeo sobre Quarter Sequence (~34 min).
**Ver também:** [[Algoritmo_IPDA_e_Ciclos_Tempo]] · [[ICT_Killzones_YouTube_Distilled]] · [[ICT_PowerOfThree_YouTube_Distilled]] · [[FVG_e_MSS]]
