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
