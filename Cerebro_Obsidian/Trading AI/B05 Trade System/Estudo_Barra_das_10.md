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

**2. Com o gatilho do operador, 1 min — RESULTADO ERRADO, ver item 6** (108 pregões, abr–set/2026): varrida + MSS + FVG na
reversão até 45 min depois, gestão BSL/SSL + trailing:
**64 trades, +0,39R/trade (t = 2,5)**, contra +0,08R dos outros gatilhos da janela. Positivo
nas duas metades e em todos os 6 meses. Com 3 contratos: +R$ 3.888, pior queda −R$ 834.
Entrar no fechamento do 15 min (sem o gatilho de 1 min) NÃO paga: stop mediano ~500 pts.

**3. Filtro de regime (lateral × tendência) testado e NÃO adotado:** cortava as varridas contra
a tendência, que deram +0,55R. A versão simples (as duas direções) é a mais estável.

**4. C2 por rompimento — DEFINIÇÃO ERRADA, substituída no item 5** (`profit/backtest_setup_c.py`)
C2 = a barra das 10 varre o topo/fundo de uma barra de 15 min anterior (intacto) e depois
uma barra fecha além do outro lado dela (10:15–11:14). Controle = o mesmo rompimento sem
a varrida antes.

| | 5 anos, 15 min: chega a 2R (stop na barra que rompeu) | 5 meses, 1 min, gatilho do operador |
|---|---|---|
| C1 | — | 67 trades, **+0,35R** (t 2,3), metades +0,17 / +0,58 |
| **C2** | **13%** (716 casos) | 51 trades, +0,31R (t 2,0), metades +0,24 / +0,39 |
| Controle (rompe sem varrer) | **19%** (539 casos) | 36 trades, +0,35R (t 1,7), metades −0,06 / +0,73 |

- A varrida feita pela barra das 10 **não acrescenta** ao rompimento: nos 5 anos, o
  rompimento depois dela anda **menos** (13% × 19% de chegar a 2R; pior em 4 dos 6 anos).
- A condição do C2 é muito comum (53% dos dias): quase sempre a barra das 10 passa de
  alguma barra anterior.
- No 1 min, C2 ≈ controle: o que rende é o **gatilho de 1 min depois do rompimento da
  barra das 10**, não a manipulação antes dele. E isso só tem 5 meses de base.
- **C1 segue sendo o modo com base** (estrutura especial em 5 anos + gatilho positivo).

**5. C2 corrigido pelo operador (25/09/2026)** (`profit/backtest_c2.py`)
A definição acima estava errada: *"não tem rompimento da barra das 10, é a próxima barra
depois do sweep da barra das 10 fechar pra dentro dela"*. C2 = a barra das 10 varre o
topo/fundo de uma barra de 15 min anterior (intacto até 10:00) e a **barra das 10:15 fecha
contra ela, dentro do range**. Controle = a mesma 10:15 sem a varrida antes. Varreu os
dois lados = controle.

5 anos de 15 min (entrada no fechamento das 10:15, stop no extremo da varrida, até 12:00):

| Versão de "fechar pra dentro" | C2: 1R / 2R / 3R | Controle: 1R / 2R / 3R | C2 melhor (2R) |
|---|---|---|---|
| **V1: 10:15 de baixa (alta), dentro de B** | **45% / 22% / 10%** (n=423) | 38% / 15% / 6% (n=922) | **5 de 6 anos** |
| V2: fecha além do meio de B | 44% / 20% / 8% (n=374) | 37% / 14% / 5% (n=976) | 5 de 6 anos |
| V3: fecha além da abertura de B | 43% / 19% / 8% (n=260) | 37% / 16% / 7% (n=1083) | 5 de 6 anos |

5 meses de 1 min (MSS + FVG no sentido, MSS 10:15–11:14, gestão BSL/SSL + trailing, 3 ct):

| | C2 | Controle |
|---|---|---|
| V1 | 32 trades, **+0,30R** (t 1,7), metades +0,41 / +0,17, +R$ 939 | 66, +0,11R, metades −0,28 / +0,49, +R$ 681 |
| V2 | 31, +0,15R (t 0,8), −R$ 9 | 68, +0,14R, +R$ 507 |
| V3 | 17, +0,36R (t 1,4), +R$ 210 | 78, +0,11R, +R$ 129 |

- Com a definição certa, a varrida feita pela barra das 10 **acrescenta**: a 10:15 que fecha
  de volta anda mais que a mesma 10:15 sem varrida, nas 3 versões e em 5 de 6 anos.
- **V1 adotada** (é a leitura literal do operador e a melhor no 1 min). Foram testadas 3
  versões: parte da vantagem da V1 no 1 min pode ser escolha. 32 trades é pouco.
- Parar aqui: nenhuma versão nova do C2 antes do teste prospectivo.

**6. CORREÇÃO — erro de olhar o futuro no 1 min (25/09/2026)** (`profit/backtest_c2b.py`)

Os testes de 1 min do Setup C (item 2: 64 trades +0,39R; item 4: C1 +0,35R; item 5: C2
V1 +0,30R; também `regime_vista.py`) aceitavam MSS e **entrada dentro da barra de 15 min
da varrida, antes de ela fechar**. Ao vivo, ninguém sabe nesse momento se a barra vai
fechar de volta. Refeito com a entrada só depois do fechamento que confirma:

| | Antes (com erro) | Entrada só após a confirmação |
|---|---|---|
| C1 | 67 trades, +0,35R | **56 trades, −0,03R** (metades −0,25 / +0,29) |
| C2 V1 | 32 trades, +0,30R | **28 trades, −0,02R** |

Os testes de 15 min (entrada no fechamento da barra) **não** tinham esse erro: a estrutura
do C1 (52% × 44%) continua valendo, e operar no fechamento do 15 min continua negativo.

**Os dois cenários do C2, como o operador descreveu** (confirmação: b2 = a própria barra
das 10 fecha contra o sweep; b1 = ela não reverteu e a 10:15 fecha contra ela, para dentro;
tendência da 1ª hora = 3 das 4 barras na mesma cor ou movimento ≥ 475 pts):

| 5 anos, 15 min, chega a 2R / 3R | C2 | Controle (sem varrida) |
|---|---|---|
| b2 — varre e reverte na mesma barra | 27% / 19% (n=186) | 26% / 14% (n=1.162) |
| b1 — a 10:15 fecha de volta | 23% / 11% (n=339) | 20% / 11% (n=326) |
| Continuação (a favor da 1ª hora) | 28% / 15% (n=138) | 26% / 15% (n=564) |
| **Reversão contra a 1ª hora** | **27% / 16%** (n=227), 1R 50% | 22% / 10% (n=471), 1R 39% |
| Lateral | 18% / 9% (n=160) | 25% / 14% (n=453) |
| Todos | 24% / 14% (n=525), melhor em 2 de 6 anos | 25% / 13% (n=1.488) |

No 1 min (5 meses, entrada após a confirmação): C2 37 trades +0,13R contra +0,15R do
controle; nenhum recorte do C2 separa do controle (continuação +0,34R × +0,37R; contra
−0,04R; lateral +0,12R, n=7).

- **No cenário de continuação, a varrida não acrescenta nada**: a 10:15 confirmando a favor
  da tendência anda igual com ou sem sweep antes.
- **No cenário de reversão contra a tendência da 1ª hora, a varrida acrescenta** na estrutura
  de 15 min (1R 50% × 39%, 3R 16% × 10%). No lateral, piora. Recorte visto depois dos dados.
- Com a confirmação no fechamento de 15 min, o gatilho de 1 min não tem vantagem. **Mas o
  operador não opera assim** — ver item 7.

**7. Setup C como o operador opera (25/09/2026)** (`profit/backtest_c_ao_vivo.py`)

Regra do operador: *"a vista sweepou um topo ou fundo dos 15? já procura entrada no 1m, a
regra é sempre ir contra ele, nem precisa esperar fechar. A mesma coisa vale pra ela ser
sweepada: capturou a máxima ou a mínima dela, entrar no 1m."*

Teste: sweep (o preço passa do nível, sem olhar fechamento) → primeiro MSS + FVG de reversão
em até 30 min, MSS antes de 11:15, entrada antes de 11:30. 5 meses de 1 min, 3 contratos:

| | Trades | Média | Metades | R$ |
|---|---|---|---|---|
| Base: todo gatilho MSS + FVG de 10:00–11:14 | 484 | +0,11R (t 2,0) | +0,03 / +0,19 | +5.691 |
| **C1** — capturou a máx/mín da barra das 10 | 86 | **+0,21R** (t 1,8) | +0,23 / +0,20 | +2.583 |
| **C2** — a barra das 10 sweepou topo/fundo de 15 min | 95 | **+0,20R** (t 1,8) | +0,36 / +0,05 | +1.695 |

Por contexto da 1ª hora (a operação contra o sweep fica a favor, contra ou sem tendência):

| | A favor da tendência | Contra a tendência | Lateral |
|---|---|---|---|
| C1 | 33, +0,08R | **36, +0,43R (t 2,2), metades +0,48 / +0,40** | 17, +0,01R |
| C2 | 36, +0,17R | 43, +0,21R | 16, +0,22R |

- Operado como o operador opera, o Setup C rende **o dobro da base** nos dois modos. A
  diferença para a base ainda não é significativa (5 meses).
- Se a barra de 15 min fechou de volta ou não **não muda o C1** (+0,21 × +0,22R): o sweep
  sozinho basta, como o operador disse. Quando não volta, o MSS não aparece ou o stop pega.
- Melhor recorte: **C1 contra a tendência da 1ª hora** (+0,43R, estável nas metades) — bate com
  a estrutura de 5 anos (item 6: reversão contra a 1ª hora é onde a varrida acrescenta).
  Achado depois de olhar os dados: confirmar ao vivo. **Não confirmou nos 5 anos — item 8.**

**8. Reversão × continuação nos 5 anos (25/09/2026)** (`profit/backtest_c_5anos.py`)

O 1 min só tem 5 meses, então nos 5 anos a entrada é o fechamento da primeira barra de 15 min
que volta para dentro depois do sweep (stop no extremo do sweep). Mede a direção, não o trade
de 1 min.

| Chega a 2R (1R / 3R) | Reversão (contra a 1ª hora) | Continuação (a favor) | Lateral |
|---|---|---|---|
| C1 — a barra das 10 é sweepada | 18% (38% / 10%), 678 sweeps | 21% (42% / 12%), 657 sweeps | 21% (39% / 9%), 580 sweeps |
| C1 — chega ao outro lado de B | 65% | 70% | 66% |
| C2 — a barra das 10 sweepa | 21% (40% / 12%), 682 sweeps | 22% (38% / 14%), 520 sweeps | 20% (38% / 14%), 504 sweeps |

Por ano, nenhum cenário ganha sempre: no C1 a reversão ganha só em 2021; no C2 cada cenário
ganha em anos diferentes.

- **Nos 5 anos, reversão e continuação andam igual.** O +0,43R do C1 contra a tendência (item 7)
  é de 5 meses e não se repete na estrutura: provavelmente sorte do período.
- O índice faz os dois cenários na mesma proporção. O contexto da 1ª hora não diz qual vai vir.
- Entrar no fechamento do 15 min continua abaixo do empate (2R pede 33%): o que pode ter
  vantagem é o gatilho de 1 min, e ele só tem 5 meses de base.

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


**9. Bloco de ordem × FVG na entrada de 1 min (25/09/2026)** (`profit/backtest_ob.py`)

Mesmo gatilho do item 7 (sweep → MSS de reversão em até 30 min), mudando só onde se entra.
OB = último candle contrário antes da pernada; entrada na abertura dele; stop no extremo da
pernada (igual). 5 meses de 1 min, 3 contratos:

| Entrada | C1 | C2 | Base (todo gatilho 10:00–11:14) | Stop mediano |
|---|---|---|---|---|
| FVG (atual) | 86, **+0,21R**, 5R 12%, +R$ 2.583 | 95, **+0,20R**, +R$ 1.695 | 484, +0,11R | ~400 pts |
| Bloco de ordem | 58, **+0,23R**, 5R 21%, +R$ 1.881 | 78, +0,01R, −R$ 750 | 351, +0,05R | ~205 pts |
| FVG, ou OB quando não há FVG | 89, +0,22R, +R$ 3.195 | 102, +0,11R, +R$ 990 | 551, +0,11R | ~400 pts |

- OB entra mais perto do stop: **metade do stop**, mais trades que chegam a 5R, mas **menos
  entradas** (o preço nem sempre volta até lá).
- No **C1**, OB e FVG dão o mesmo por trade. No **C2**, OB é pior. Aceitar OB quando não há
  FVG acrescenta poucos trades e não melhora.
- Adotado como o operador pediu (FVG ou OB), com a nota: no C2, preferir o FVG.

**Ver também:** [[Estudo_Reversao_Abertura_Vista]] · [[Trade_System_Anderson]] · [[Controle_e_Processo]]
