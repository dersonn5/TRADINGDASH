# Estudo — a barra das 10 e a compressão da 1ª hora (WIN, 1 min)

> **Status: HIPÓTESE PROMISSORA, em teste ao vivo.** Não entra no checklist até passar
> no teste prospectivo (seção final). Criado em 22/09/2026.
> Script: `profit/barra10.py` · Dados: cache do Profit, 108 pregões (20/04–22/09/2026).

## A mudança de método: medir em R, não em acerto

O operacional do operador tem assinatura assimétrica: **erra 2–3 vezes de 1R e acerta uma
de 8–10R**. Para esse perfil, taxa de acerto não diz nada. A medida certa é:

> **Qual a chance de o preço chegar a kR a favor antes de tocar o stop (−1R)?**

Um alvo de kR só compensa se essa chance passar do **limiar de empate = 1/(k+1)**:

| Alvo | 2R | 3R | 5R | 8R | 10R |
|---|---|---|---|---|---|
| Limiar de empate | 33% | 25% | 17% | **11%** | 9% |

**Um filtro é bom quando empurra a chance de kR acima do limiar** — e com amostra suficiente.
Filtrar por "menos stops" sem olhar isso pode cortar justamente os 10R.

## Hipótese do operador

Da abertura até 10:00 o índice forma uma micro tendência. Às 10:00 (abertura do à vista)
faz algo: reverte a barra das 10, ou cria uma máxima/mínima que, rompida, dá o trade —
de continuação ou de reversão.

## Definições (confirmadas pelo operador antes de rodar)

- **Micro tendência:** direção de 09:00 → 09:59 (fechamento − abertura).
- **Barra das 10:** o candle de **1 min** das 10:00.
- **Rompimento:** primeiro lado da barra rompido até 10:30. A favor da micro tendência =
  continuidade; contra = reversão.
- **Gatilho:** MSS no sentido do rompimento (pernada com candle ≥ 1,5× a média), FVG da
  pernada, entrada na borda do FVG até 11:30, stop no extremo da pernada.
- **Gestão:** alvo no próximo BSL/SSL + trailing (zero a zero em 1R, depois swings).
- **Controle:** a mesma estrutura com a barra das 11, 13 e 14.

## Resultados

**A barra das 10, sozinha, não tem vantagem** (96 trades): chega a 8R em 10% dos casos,
no limiar. Barras das 11, 13 e 14 ficam parecidas. Continuidade × reversão também não
separa com clareza.

**O que separa é a 1ª hora:**

| 1ª hora (movimento líquido) | Trades | 5R | 8R | 10R | Gestão |
|---|---|---|---|---|---|
| **Comprimida (< 475 pts)** | 32 | 19% | **19%** | 12% | **+0,48R** |
| Média (475–980) | 33 | 15% | 9% | 6% | −0,29R |
| Esticada (> 980) | 31 | 13% | 3% | 0% | −0,10R |

Estabilidade (mesmo limiar de 475 pts, amostra dividida ao meio):

| | 1ª metade | 2ª metade |
|---|---|---|
| Comprimida — chega a 8R | 15% (n=13) | 21% (n=19) |
| Esticada — chega a 8R | 6% (n=34) | 7% (n=30) |

Nas duas metades, comprimida fica **acima** do limiar de 8R (11%) e esticada **abaixo**.

**Mecanismo plausível:** 1ª hora comprimida guarda o range do dia para a abertura do à
vista, e a expansão das 10:00 tem espaço para andar 8–10R. 1ª hora esticada já gastou boa
parte do range — sobra pouco para o gatilho das 10 correr.

## Cuidados

- É um **subgrupo encontrado depois de olhar os dados** (1 de ~20 recortes vistos). O
  limiar de 475 pts saiu do tercil da própria amostra.
- 32 trades é pouco. Consistência nas duas metades reduz, mas não elimina, a chance de sorte.
- 1 min cobre só 5 meses (um regime de mercado).

## Teste prospectivo (o que decide)

A partir de 23/09/2026, todo pregão, **sem mudar nenhuma definição**:
1. **Às 10:00:** anotar o movimento líquido 09:00→09:59 e marcar `comprimida` (< 475) ou não.
2. Se houver gatilho da barra das 10 (definições acima), anotar entrada, stop e **até
   quantos R chegou antes do stop** (MFE), além do resultado com a gestão.
3. Operar ou não é decisão do operador; o registro é feito **nos dois casos**.

**Critério:** com 20+ gatilhos em dias comprimidos, se a chance de 8R continuar acima de 11%
e a dos dias esticados abaixo, vira filtro do checklist:
*"1ª hora esticada (> 475 pts): não operar o gatilho das 10."*

Ferramenta: `python profit/ler_cache_profit.py WINFUT 1` e depois `python profit/barra10.py`
recalculam tudo com os dias novos.

## Padrão do operador: varrida da barra das 10 (15 min) — 22 e 23/09/2026

**Observação do operador:** "se o à vista abre e as próximas 4 barras varrem a máxima ou a
mínima dela, reverte". E: "a barra das 10 ou manipula ou é manipulada".

**Definição:** barra de 15 min das 10:00. Varrida = uma das 4 barras seguintes passa da
máxima (mínima) e FECHA de volta dentro. Varreu o topo → venda; o fundo → compra.

**1. Estrutura, 5 anos de 15 min** (`profit/padrao_15m.py`, 1.362 pregões, abr/2021–set/2026):

| Ano | Varrida da barra das 10 | Chega ao lado oposto | Barra das 11 (controle) |
|---|---|---|---|
| 2021 | 65% | 52% | 47% |
| 2022 | 66% | 54% | 44% |
| 2023 | 68% | 49% | 43% |
| 2024 | 69% | 57% | 49% |
| 2025 | 67% | 48% | 41% |
| 2026 | 67% | 51% | 36% |
| **Total** | 908 casos | **52%** | **44%** (z = 3,7) |

A barra das 10 é varrida em ~2/3 dos dias **todo ano**, e depois da varrida o preço chega ao
outro lado dela **mais vezes que na barra das 11 em todos os 6 anos**. É estrutural, não sorte
de um período. A favor × contra a 1ª hora: 54% × 50% (z = 1,5) — não separa.

**2. Com o gatilho do operador, 1 min** (108 pregões, abr–set/2026): varrida + MSS + FVG na
reversão até 45 min depois, gestão BSL/SSL + trailing:
**64 trades, +0,39R/trade (t = 2,5)**, contra +0,08R dos outros gatilhos da janela. Positivo
nas duas metades e em todos os 6 meses. Com 3 contratos: +R$ 3.888, pior queda −R$ 834.
Entrar no fechamento do 15 min (sem o gatilho de 1 min) NÃO paga: stop mediano ~500 pts.

**3. Filtro de regime (lateral × tendência) testado e NÃO adotado:** cortava as varridas contra
a tendência, que deram +0,55R. A versão simples (as duas direções) é a mais estável.

**Status:** setup em teste prospectivo (Setup C). A estrutura tem 5 anos de base; o ganho com
o gatilho de 1 min tem 5 meses. Critério: 20–30 trades reais; negativo → sai.

## Alvo de 5R (corrigido pelo operador: "se pagar 5/1 já está ótimo")

Empate para alvo fixo de 5R = **16,7%** (1 em 6). Gatilhos MSS + FVG de 09:00–12:00,
alvo fixo 5R, stop no extremo, sem trailing (quem não bate 5R nem stop conta como −1R —
conservador):

| Recorte | Gatilhos | Chega a 5R | Metades | EV/trade |
|---|---|---|---|---|
| Todos | 948 | 14% | 12% / 17% | −0,17R |
| **09:00–09:45** | 145 | **19%** | 13% / 25% | +0,08R |
| 10:00–10:45, 1ª hora comprimida | 127 | 17% | 19% / 16% | +0,01R |
| **10:00–10:45, 1ª hora esticada** | **198** | **10%** | **11% / 8%** | **−0,46R** |
| **11:00–12:00** | **327** | **13%** | 9% / 16% | **−0,28R** |
| Liquidez varrida = swing de 15 min | 17 | 35% | 30% / 43% | +1,08R (amostra pequena) |

**Os achados mais sólidos são filtros de NÃO operar** (amostras grandes, iguais nas duas
metades):
1. **1ª hora esticada (> 475 pts): não operar gatilho entre 10:00 e 10:45.**
2. **Não abrir trade novo depois das 11:00** (só gerenciar o que está aberto).

Juntos cortam ~55% dos gatilhos da janela — justamente os de pior expectativa.

## Anexo — hierarquia de liquidez na janela 09:00–12:00 (`profit/hierarquia_liquidez.py`)

Todos os gatilhos MSS + FVG da janela (948 em 105 pregões, ~9 por dia), classificados
pelo nível mais importante varrido nos 30 min antes do MSS:

| Liquidez varrida | Gatilhos | 5R | 8R | 10R | Gestão |
|---|---|---|---|---|---|
| Máx/mín do dia anterior | 43 | 16% | 5% | 5% | −0,12R |
| Máx/mín da 1ª hora | 83 | 12% | 7% | 4% | +0,08R |
| Swing de 15 min | 17 | 35% | 18% | 12% | +0,30R (instável: 0% e 43% nas metades) |
| Swing de 1 min | 251 | 13% | 5% | 4% | +0,14R |
| Nenhuma | 554 | 15% | 6% | 4% | +0,10R |
| **Todos** | 948 | 14% | 6% | 4% | **+0,11R** |

- A importância da liquidez, **do jeito que foi mecanizada**, não separa os gatilhos que
  chegam a 8–10R. Nenhuma classe grande passa do limiar de 8R (11%).
- A **gestão do operador** (alvo no BSL/SSL + trailing) deu **+0,11R por gatilho** mesmo
  sem filtro nenhum — a gestão parece carregar parte da vantagem.
- Correções de definição feitas antes do resultado final, ambas conferidas em 22/09:
  intacto = só os candles depois do swing; varrida = primeira vez que o nível é furado
  nos 30 min antes do MSS (a queda 10:00–10:15 de 22/09 é UMA varrida da mín da 1ª hora).

**Leitura:** a seleção do operador (quais gatilhos ele aceita) não foi capturada por regras
de preço. O dado que falta é o **histórico real de trades** — ver Frente A.

**Ver também:** [[Estudo_Reversao_Abertura_Vista]] · [[Trade_System_Anderson]] · [[Controle_e_Processo]]
