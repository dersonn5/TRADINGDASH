# Estudo — a reversão da abertura do à vista (10:00)

> **Status: EM ANDAMENTO.** Escopo definido pelo operador: **só WIN, só gráfico de 1 min**
> (108 pregões no cache, abr–set/2026). As camadas de 30/60 min abaixo ficam fora.
> Criado em 22/09/2026, semana de testes antes da semifinal da Copa BTG.

## Resultados até aqui (WIN 1 min, 105 pregões)

**1. A 2ª hora não reverte a 1ª mais do que em outros horários** (`profit/reversao_vista.py`).
09h→10h rompe o extremo oposto da 1ª hora em 23% dos dias; os controles (11→12, 13→14,
14→15, 15→16) ficam entre 13% e 35%. Quanto maior a 1ª hora, menos reverte
(1ª hora > 1.060 pts: 12%).

**2. O que é especial é o PRIMEIRO IMPULSO do à vista** (`profit/abertura_reversao.py`).
Impulso = direção de 10:00–10:05. Rompe o extremo oposto dos primeiros 15 min até 11:00:

| Início do impulso | Reversão forte |
|---|---|
| 09:00 (futuro) | 21% — o impulso do futuro tende a valer |
| **10:00 (à vista)** | **71%** |
| 11:00 / 13:00 / 14:00 / 15:00 | 52–58% |

**3. Varrer o extremo da 1ª hora não aumenta a reversão às 10:00.**
Impulso das 10:00 que varre a máx/mín de 09:00–09:59: reverte forte 67% (n=45).
Que não varre: 75% (n=60). Nos outros horários, varrer *reduz* a reversão (42–55%) —
às 10:00 o sweep é menos confiável como rompimento do que no resto do dia.

**Foco a partir daqui:** o impulso inicial do à vista (10:00–10:15). Fase 3 (anatomia)
passa a ser sobre ele: quanto dura, quanto anda, onde vira, até onde vai.

**4. Anatomia do impulso das 10:00** (`profit/anatomia_vista.py`, 105 pregões, 75 revertidos)

| Medida (dias que reverteram) | p25 | mediana | p75 | p90 |
|---|---|---|---|---|
| Extremo do impulso (min após 10:00) | 3 | **7** | 14 | 26 |
| Rompimento do lado oposto (min) | 16 | **19** | 30 | 39 |
| Tamanho do impulso, 10:00 → extremo (pts) | 355 | **520** | 695 | 1020 |
| Quanto anda depois de 10:05 (pts) | 195 | **295** | 470 | 805 |
| Alcance da reversão a partir do extremo, até 11:29 (pts) | 1045 | **1370** | 1880 | 2430 |

Alvos atingidos depois do extremo (dias que reverteram): **50% da 1ª hora 83%**,
abertura 09:00 52%, extremo oposto da 1ª hora 56%.
Dias que NÃO reverteram: depois de 10:05 o impulso andou mediana 1.255 pts.

- Contexto (impulso a favor ou contra a 1ª hora) não muda a taxa: 68% × 74%.
- Tamanho dos 5 primeiros minutos não muda a taxa: 70–74%.
- **Impulso que fica DENTRO do range da 1ª hora reverte 87%; que varre o extremo, 59%.**
  (Esta definição mede o extremo até a reversão; a contagem do item 3 usava só
  10:00–10:14 — por isso os números diferem.)

**Referência bruta, NÃO é regra:** fade no fechamento de 10:04, stop e alvo fixos,
custo 10 pts. Resultado entre −18 e +50 pts por trade conforme stop/alvo — dentro do
ruído para 105 trades, e a melhor célula de uma grade é otimista por construção.
Leitura: a reversão existe, mas entrar cedo exige stop largo (o impulso ainda anda
300–800 pts). A vantagem, se houver, está em **esperar o extremo (≈10:07–10:14) e
entrar na confirmação**, com stop além dele — que é a Reversão do operador.

**5. Fase 4 — a regra do operador** (`profit/setup_vista.py`)

Regra: 1ª hora define a tendência; entre 10:00 e 10:30 o à vista varre o último swing
**contrário** (manipulação); MSS no 1 min; entrada no FVG; stop no extremo; alvo no
próximo swing não varrido; trailing (zero a zero em 1R, depois atrás dos swings).

| Amostra | Pregões | Trades | Acerto | Média | Total |
|---|---|---|---|---|---|
| Ajuste (20/04–10/08) | 78 | 37 | 70% | +113 pts | +R$ 835/contrato |
| **Validação (11/08–22/09)** | 30 | **15** | **47%** | **−2 pts** | **−R$ 7/contrato** |

**A vantagem do ajuste não se sustentou na validação.** Com 15 trades e erro padrão de
120 pts, nada se prova nem se descarta, mas não há evidência de vantagem.

Padrão visível nos 15 trades: **entradas tardias e risco grande** (entradas entre 10:22
e 11:11; risco de 255 a 1.440 pts). As perdas vieram dos trades de risco alto.

Correções de código feitas no caminho (não são mudanças de regra):
- busca de FVG passou a incluir o candle da manipulação como candle do meio (era o caso
  do 26/05, que a regra deixava passar);
- o cache do Profit guarda o WINFUT **sem ajuste** de vencimento; o gráfico mostra a série
  ajustada. Distâncias em pontos batem, níveis não.

**Conclusão parcial:** não entra no checklist. Reavaliar com mais histórico de 1 min
("Expandir base" no Profit) ou com a regra de risco máximo definida pelo operador —
sabendo que definir o limite depois de ver os resultados é ajuste, não descoberta.

**6. Que condição separa o V da continuação? (26/09/2026)** (`profit/condicoes_reversao.py`)

Pergunta do operador: "na abertura faz um movimento forte, é falso, reverte e entrega em V —
qual condição ele imprime que mais impacta em reverter?". Definições do item 4 (impulso =
10:00–10:04; reverteu = rompe o lado oposto de 10:00–10:14 até 10:59). **V** = reverteu e
anda além da abertura das 10:00 pelo menos o tamanho do impulso, até 11:29.
Só condições conhecidas **até 10:15**. 1 min: 107 pregões (abr–set/2026, reverteu 70%,
V 53%, estável mês a mês). Confirmação: 15 min, 1.347 pregões (2021–2026), com espelho
(impulso = corpo da barra de 15 min das 10:00), que concorda com o 1 min em 69% dos dias.

**O que decide é como a barra das 10:00 termina — nada antes das 10:00 importa.**

| Às 10:15 (1 min) | Reverteu | V | n |
|---|---|---|---|
| Extremo cedo (até 10:07) e 10:14 fecha na metade de volta | **92%** | **79%** | 39 |
| Extremo tarde (10:08+) e 10:14 fecha no lado do impulso | **46%** | **24%** | 41 |
| 10:14 fecha no lado do impulso **e impulso grande** (range > ~850 pts) | **33%** | **14%** | 21 |

5 anos, 15 min (barra das 10:00): fechou de volta (pavio contra o impulso) **79%**;
fechou no impulso com barra grande (> 25% do range médio de 10 dias) **38%**. As duas pontas
se repetem **em todos os anos** de 2021 a 2026.

- **O movimento forte que fecha forte NÃO é falso:** impulso grande que segue fechando no
  extremo às 10:14 continua em 2 de cada 3 dias. O V vem do impulso que **perde força cedo**
  (extremo nos primeiros ~7 min) e já devolve até 10:14.
- Não separam (1 min e 5 anos): gap, direção do dia anterior, direção da 1ª hora, 1ª hora ou
  impulso tomando máx/mín do dia anterior, varrer a máx/mín da 1ª hora, onde o à vista abre.
- Dia da semana: quarta 43% no 1 min, mas não se repete nos 5 anos — ruído.
- **Controle:** barra de 15 min que fecha de volta reverte mais em qualquer horário
  (11:00 68%, 14:00 69%). Às 10:00 é mais (79%), e a base das 10:00 é maior (56% contra
  45–50%). Parte do efeito é mecânica: quem já devolveu está mais perto do outro lado.
- Isto é descritivo, não é regra de entrada: falta medir entrada/stop/alvo depois das 10:15
  (Fase 4 do operador), com os últimos pregões guardados para validação.

**Os 92% não viram trade sozinhos** (`profit/referencia_v_1015.py`, referência bruta, não
é regra). Entrada no fechamento de 10:14 contra o impulso, stop além do extremo, custo 10 pts:

| | n | Acerto | Média | Risco med. | Alvo med. |
|---|---|---|---|---|---|
| Sinal, alvo = lado oposto (1 min) | 39 | 92% | **+0,19R** | 615 pts | 150 pts |
| Sinal, alvo = V completo (1 min) | 28 | 61% | +0,08R | 600 pts | 440 pts |
| Espelho 5 anos (15 min), alvo = lado oposto | 225 | 54% | **−0,17R** | 240 pts | 145 pts |

Motivo: quando o sinal aparece, o preço já devolveu metade — o stop no extremo fica 4× maior
que o que falta até o alvo. Acerta muito e ganha pouco. Para pagar, a entrada precisa de
stop curto (gatilho de 1 min depois das 10:15), a ser definido pelo operador.

**7. O V da abertura das 09:00 — definição do operador (26/09/2026)** (`profit/padrao_v_0900.py`)

"Vi diversos pregões que o índice começa indo pra baixo e reverte em V, e vice-versa."
Definição combinada antes de rodar:
- **Movimento:** o preço se afasta **800 pts** da abertura das 09:00; o lado que chega
  primeiro define a direção.
- **V:** depois do extremo, volta **pelo menos 75%** do caminho abertura → extremo.
- **Prazo:** até 12:00. Conservador: extremo e volta no mesmo candle não conta.

| Base | Dias com movimento 800+ | V (volta 75%) |
|---|---|---|
| 1 min, abr–set/2026 (108 pregões) | 106 (98%) | **80 (75%)** — baixa 74%, alta 78% |
| 15 min, 2026 | 176 | **74%** |
| 15 min, 2021–2025 | 842 | 23% a 42% por ano |

**O V é mais forte em 2026, mas não é novo.** 800 pts em 2021 (índice ~117 mil) é um
movimento maior que em 2026 (~181 mil). Com o mesmo tamanho em % (0,43% da abertura):

| Ano | V | Chegou ao tamanho até 09:29 | Chegou depois |
|---|---|---|---|
| 2021 | 60% | 69% | 55% |
| 2022 | 72% | 77% | 67% |
| 2023 | 61% | 71% | 56% |
| 2024 | 45% | 62% | 37% |
| 2025 | 57% | 61% | 53% |
| **2026** | **74%** | **75%** | **70%** |

**A condição que mais pesa: a velocidade.** Movimento que chega ao tamanho nos primeiros
30 min (até 09:29) reverte mais **em todos os anos** (+5 a +25 pontos percentuais). Em 2026
isso acontece em 73% dos dias — por isso o operador vê o V quase todo dia.

Não separam nos 5 anos (15 min): direção inicial (alta × baixa), gap, direção do dia
anterior, dia da semana. Ter tomado a máx/mín do dia anterior **reduz** um pouco (39% × 47%);
no 1 min parecia o contrário (81% × 71%) — ruído de amostra pequena.

Anatomia dos 80 V do 1 min: movimento até o extremo mediana **1.225 pts** (p25 935, p75 1.575);
extremo mediana **09:30** (p25 09:07, p75 10:07); V completo mediana **10:02** (p25 09:20,
p75 10:28) — a volta costuma terminar perto da abertura do à vista.

Datas para conferir no Profit: `profit/padrao_v_0900_dias.csv` (fora do git) ou a saída do
script. **Diferença para o item 2:** lá o "impulso das 09:00" eram os 5 primeiros minutos;
aqui é o movimento de 800 pts até o extremo — definição do operador, e por isso o resultado
muda (21% × 75%).

Próximo: é descritivo. Para virar trade falta a entrada do operador (quando entrar contra o
movimento, com qual stop) — o extremo pode sair das 09:07 às 10:07, e entrar antes dele
custa o resto do movimento.

**8. Setup V: V das 09:00 + sweep de liquidez + gatilhos (26/09/2026)** (`profit/setup_v_sweep.py`)

Hipótese do operador: o V (item 7) + sweep de PDH/PDL ou BSL/SSL + nossos gatilhos de entrada.
Definições confirmadas antes de rodar: liquidez = PDH/PDL + swings de 15 min do dia anterior
intactos; gatilho contra o movimento de 800 pts em até 30 min depois do sweep; gatilhos MSS+FVG,
MSS+OB, BPR e Risk (cada um separado); alvo na liquidez oposta + zero a zero em 1R + trailing;
saída até 12:00; custo 10 pts; janelas 09:00–11:29 e 10:00–11:29. 1 min, 109 pregões.

| Entrada 10:00–11:29 (regra atual) | n | Acerto | Média | t |
|---|---|---|---|---|
| **V + sweep**, primeiro gatilho do dia | 23 | 30% | +0,40R | 0,7 |
| V + sweep, MSS+FVG | 14 | 29% | **−0,42R** | −1,8 |
| **V sem exigir sweep**, primeiro gatilho | 100 | 46% | **+0,38R** | **2,2** |
| V sem exigir sweep, MSS+FVG | 96 | 51% | +0,24R | 1,8 |
| Base: todo MSS+FVG da janela | 490 | 48% | +0,13R | 2,3 |
| Base: todo BPR da janela | 177 | 51% | **+0,30R** | **2,9** |

Entrada 09:00–11:29: V + sweep, primeiro gatilho +0,98R (n=49, t=1,2) — puxado por poucos Risk
com stop de 10–35 pts (um de +38R); MSS+FVG +0,13R, igual à base.

- **O sweep de liquidez não melhorou o V** — na janela das 10:00 piorou. Os sweeps acontecem
  cedo (09:0x); 30 min depois ainda não é 10:00.
- O que ficou melhor que a base foi o **gatilho contra o movimento do V, sem sweep** (+0,38R).
  Mas: 5 meses, ~40 combinações olhadas — alguma sai boa por acaso. Não é prova.
- **BPR foi o melhor gatilho em geral** (+0,30R, positivo nas duas metades), sem relação com o V.
- MSS+OB: acerto 5–21%, resultado zero ou negativo em quase todo recorte.
- Risk entry com stop de 10–35 pts não é executável na prática (slippage do WIN).

**Não entra no checklist.** Para validar é preciso mais histórico de 1 min (meses anteriores a
abr/2026, "Expandir base" no Profit) e rodar as mesmas regras sem mudar nada.

## Por que este estudo

Observação do operador: "o índice abre às 09:00, vai para um lado e depois reverte".

Primeira medição (1 min, 108 pregões, abr–set/2026) contradisse a frase **para as 09:00**
e apontou outro horário:

| Início | Reversão leve | Reversão forte | Fechou contra em 60 min |
|---|---|---|---|
| 09:00 (futuro) | 42% | 21% | 15% |
| **10:00 (à vista)** | **89%** | **71%** | **44%** |
| 11:00 – 15:00 | 70–79% | 52–58% | 28–39% |

Hipótese: **a abertura das 09:00 define um movimento; a abertura do à vista, às 10:00,
é quem reverte**. No gráfico as duas aparecem juntas e parecem uma coisa só.

Objetivo: amostra sólida para decidir se vale operar **exatamente a janela da reversão
do à vista**, e com quais regras.

## Dados

Cache local do Profit, lido por `profit/ler_cache_profit.py` (sem exportação).

| Granularidade | Pregões | Período |
|---|---|---|
| 60 min | 1.040 | jul/2022 – set/2026 |
| 30 min | 529 | ago/2024 – set/2026 |
| 15 min | 275 | ago/2025 – set/2026 |
| 1 min | 108 | abr – set/2026 |

## Lições dos testes anteriores (22/09) — valem para este

1. **A regra de entrada é do operador, não minha.** Os backtests em que eu inventei
   entrada/stop/alvo não mediram o operacional real.
2. **Definição decide.** Um "sweep" visual foi, nos dados, fundo mais alto por 4 ticks.
3. **Sempre com controle em outros horários.** Sem isso, qualquer frequência parece alta.
4. **Uma redefinição no máximo por pergunta**, combinada antes de rodar.
5. **Toda contagem sai com lista de datas** para conferir no Profit (`DiasAtras`).

## Fases

### Fase 1 — A reversão existe e é especial das 10:00? (60 e 30 min, 1.040 / 529 pregões)
Contagem descritiva, sem entrada.
- Movimento da 1ª hora = direção 09:00 → 10:00.
- A 2ª hora (10:00–11:00) **rompe o extremo oposto da 1ª hora**? Fecha **contra**?
- Controle: o mesmo par de horas em 11→12, 13→14, 14→15, 15→16.
- Estabilidade: resultado **ano a ano** (2022, 2023, 2024, 2025, 2026). Se só um ano
  sustentar, não é característica do índice.

**Critério para seguir:** 10:00 reverte claramente mais que os controles, e isso se
mantém na maioria dos anos.

### Fase 2 — Quando a reversão funciona? (15 e 30 min)
Cruzar a taxa de reversão com condições conhecidas **antes das 10:00**:
- tamanho do movimento da 1ª hora (pequeno / médio / grande);
- gap de abertura (a favor / contra / sem gap);
- a 1ª hora já tomou máxima ou mínima do dia anterior?
- dia da semana, semana de vencimento.

**Critério:** alguma condição separa dias de reversão de dias de continuação.

### Fase 3 — Anatomia da reversão (1 min, 108 pregões)
Para montar stop e alvo com base em dado:
- **a que horas** o extremo da manhã se forma (distribuição entre 09:45 e 10:45);
- **quanto** o preço passa do extremo da 1ª hora antes de virar (tamanho do sweep);
- **até onde** vai depois: 50% da 1ª hora, abertura das 09:00, extremo oposto;
- quanto anda contra antes de andar a favor.

### Fase 4 — Regra do operador
O operador escreve a regra em palavras (gatilho, entrada, stop, alvo, horário limite).
Eu traduzo para código, mostro **trade a trade** em datas escolhidas por ele, e só
depois calculo o resultado.

**Critério para ir ao checklist:** expectativa positiva depois de custos, em amostra
fora do período usado para ajustar (os últimos 30 pregões guardados para validação).

## Riscos conhecidos
- 1 min só cobre 5 meses — a anatomia (Fase 3) vale para o regime recente.
- Horário do à vista pode ter mudado em algum período (B3 ajusta horários com o
  horário de verão americano). Conferir na Fase 1 se a 1ª barra das 10:00 é
  consistente em todos os anos.
- Semifinal próxima: se o estudo não fechar a tempo, nada entra no checklist por
  pressa.

**Ver também:** [[Trade_System_Anderson]] · [[Controle_e_Processo]] · [[CRT_e_Quarterly_Theory]]
