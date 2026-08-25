# Backlog de melhorias — aplicar tudo junto após as buscas atuais fecharem

## ✅ Já implementado (pronto, aguardando ativação em busca)
- **CISD** (`ict_po3_v2.py`, `confirm_type: "mss"|"cisd"|"either"`) — confirmação por corpo
  fechando além do corpo da vela oposta anterior, sem exigir quebra de swing. Gatilho mais
  cedo que MSS. Fonte: aula CISD do HSM Trading.
- **Trailing estrutural** (`backtesting/engine.py`, `trail_mode: "structure"`) — stop segue
  último swing 5m confirmado a favor (fractal N-bars) em vez de distância fixa em R.

## 🔜 Próximo a implementar (fila, por prioridade)
1. **Duas fases de acumulação** — exigir 2 pernadas de range/consolidação antes de aceitar
   o judas sweep como válido (não só 1 sweep único). Fonte: aula Market Maker Model.
   Reduz falso-sinal (MSS falso que induz e não distribui).
2. **Calendário macro** (CPI/NFP/FOMC) como filtro de dia.
3. **Weekly/monthly bias** como camada extra de contexto (perene, filtra dias contra a maré).
4. **Filtro de seleção de dia** (range/volume mínimo esperado) — aproxima o que trader
   discricionário faz manualmente ("hoje não vou operar").
5. **Escada de timeframe fractal HTF→LTF** (semanal→12h, diário→4h/1h, 4h→15m, 1h→5m) —
   substituir nosso 1h/4h/D→5m→1m fixo. Prioridade menor, mais complexo.

## 🔜 Extraído da aula "PO3 diário + Killzones" (HSM Trading) — adicionar à fila
6. **Gate de alinhamento direcional por sessão** (mais forte desta aula) — antes de esperar
   continuação numa killzone, checar se a sessão anterior (Ásia) moveu A FAVOR ou CONTRA
   o bias HTF. A favor → espera continuação (AMD clássico). Contra → espera REVERSÃO na
   killzone seguinte, não continuação. Filtro condicional que não existe hoje (tratamos
   toda sessão igual).
7. **NY-reversal específico p/ índices americanos** — observação do autor: NQ/ES têm mais
   reversão em NY do que o AMD clássico prevê (Ásia acumula/London manipula/NY reverte
   AMBOS os lados, em vez de distribuir na direção iniciada). Relevante pro NOSSO mercado
   exato. Pode explicar por que `require_open_side`/continuação luta contra regime real.
   REFINAMENTO (aula Killzones): tabela de decisão mais precisa p/ o gate #6 —
   (a) Ásia+London AMBAS expandiram forte mesma direção → espera exaustão/reversão/lateral
       em NY, NÃO continuação;
   (b) Ásia+London AMBAS fracas/acumuladas → espera NY Reversal (captura os 2 lados);
   (c) Ásia expandiu, London fraca → NY continua o movimento da Ásia;
   (d) Ásia acumula, London manipula → NY distribui (caso clássico já coberto).
8. **OTE (Fibonacci 62-79%) como entrada alternativa** — não temos nenhuma entrada por
   retração de Fib, só FVG. Setup: sweep → expansão → retração 62-79% → entrada. Testar
   como "either" (FVG ou OTE), igual fizemos com CISD/MSS.
9. **Abertura 17h NY como referência adicional** ao midnight open (alguns ativos/sessões
   respondem melhor a 17h que meia-noite). Barato de testar.
10. **Filtro de volatilidade dos primeiros 30min de sessão** — Ásia "parada" no início tende
    a ficar lateral (pular setup); início volátil = setup mais provável. Pré-filtro barato.

## 🔜 Extraído da aula "Turtle Soup ICT" (HSM Trading)
11. **Entrada no FVG SEGUINTE à indução, não no primeiro FVG** — a única regra genuinamente
    nova desta aula. Depois da indução (sweep local), não entrar no 1º desbalanço — localizar
    o PRÓXIMO FVG além desse ponto e entrar ali (ordem limite). Stop mais apertado/referência
    mais próxima = payoff melhor. Testar `entry_fvg: "first" | "next"`.
12. **Confluência explícita sweep-local + PD-array-HTF** — turtle soup DENTRO de um array HTF
    tem probabilidade maior (ele reforça). Já temos os dois gates separados (`liquidity_quality`
    + `in_htf_array`); testar como bônus de score quando ocorrem NO MESMO PONTO, não só
    separadamente.
    (Nota: "nunca confie no 1º topo/fundo" desta aula = mesma regra do item #6 (duas fases),
    de fonte independente — reforça prioridade do item #6, não é item novo.)

## 🔜 Extraído da aula "Order Block ICT" (HSM Trading)
13. **🔥 Precisão de entrada = 50% do CORPO do bloco/FVG, não a borda.** O achado mais forte
    até agora. Entrar na borda (pavio) paga ~1:1 no 1º pivô; entrar no meio do corpo (ele
    chama "mitigation") paga ~3:1 no MESMO pivô. Ataca direto o problema de payoff pequeno.
    Testar: exigir retorno ao 50%-corpo do bloco antes de disparar entrada, não só tocar
    a borda do array/FVG.
14. **Condução do stop por blocos VALIDADOS** — refina o `trail_mode=structure` que já
    implementamos: só mover o stop pra um swing que foi CONFIRMADO (vela fechou além do
    pavio dele), não qualquer swing fractal raw. Filtro mais rígido, reduz ruído.
15. **Validação de bloco = quebra do PAVIO inteiro** (vs CISD que só exige corpo) — dois
    limiares distintos, propósitos diferentes. CISD = gatilho rápido pra reversão; validação
    de bloco = mais rígido, define ponto de precisão de entrada.
16. **"Bread and butter" — variante mais leve/agressiva**: entrar direto no 50%-corpo de um
    bloco alinhado ao HTF, sem esperar MSS/FVG completo, alvo no 1º pivô. Testar como
    estratégia SEPARADA (mais trades, lógica mais simples) — não misturar com PO3v2.
    (Reforça item #6 duas fases — 3ª fonte independente agora: MMM + Turtle Soup + este.)

## 🔜 Extraído da aula "Standard Deviations ICT" (HSM Trading)
17. **🔥 BE/parcial por projeção de desvio-padrão da perna de manipulação** — em vez de
    gatilho por múltiplo de R (arbitrário), medir o tamanho do sweep JÁ detectado
    (`sweep_window_5m`) e projetar múltiplos inteiros dele. BE quando preço atinge -2
    dessas projeções, parcial no -3. Gatilho baseado em estrutura, não risco arbitrário.
    Direto implementável — usa dado que já calculamos, sem nova detecção. ALTA prioridade,
    ataca diretamente o tema "condução"/payoff.
18. **CBDR (Central Bank Dealing Range)** 14h-20h ou 16h-20h NY como referência adicional
    pro judas (além de Ásia/PDH-PDL). Prioridade menor — mais um "onde", incremento pequeno.
19. **Filtro "só usar range de referência se for LATERAL"** — pré-condição objetiva: medir
    se o range ficou contido (não trending) antes de confiar nele pra qualquer projeção/CBDR/
    Ásia. Se CBDR trending → tenta Ásia → se também trending → Flout (combinação).
20. **Confluência entre múltiplas referências de desvio-padrão** (ex: CBDR -4 ≈ Ásia -3) como
    bônus de score quando coincidem — reforça ponto de precisão.

## 🔜 Extraído da aula "Liquidez / Dealing Range" (HSM Trading)
21. **Janela de gatilho 9h30 NY específica p/ índices** (abertura oficial NQ/ES) — mais
    precisa que nossa "prime" genérica (02-05h+10-11h). Testar 9h30 como janela prioritária
    de manipulação pro NOSSO mercado exato (ele separa Forex de índices explicitamente).
    REFINAMENTO (aula FVG): o PRIMEIRO desbalanço criado logo após 9h30 carrega peso extra —
    candidato preferencial a INVERTER (não continuar), pois combina precisão preço+tempo.
    Priorizar esse FVG específico como sinal de reversão, não FVG genérico da killzone.
    (FVG reclamado — 3º estágio pós-inversão que segura como suporte/resistência na nova
    direção — nuance menor, baixa prioridade de implementação.)
22. **Consolidação NÃO varrida vira PD array de referência futura** — hoje só tratamos FVG
    como array HTF; expandir pra rastrear zonas de acumulação intocadas como referência
    válida mais tarde (order block de timeframe maior).
    NUANCE (confirmado com chart real DXY diário): existem 2 tipos de "order block" no ICT —
    (a) ESTREITO: 1 vela só antes da virada (já codado, item #13, precisão 50%-corpo);
    (b) LARGO: o RANGE inteiro de consolidação antes do rompimento (várias velas, não FVG de
    3 velas) — é o que este item #22 descreve e ainda não está implementado. Detecção: range
    de N velas com variação contida (baixa volatilidade relativa) antes de um breakout, tratado
    como zona/caixa de referência, não ponto único.
    FRACTAL (confirmado pelo usuário, mesmo chart em múltiplos TFs): a marcação é feita em
    CADA timeframe (D/4h/1h/15m/5m/1m), não só no diário. Implementação deve rodar a detecção
    de range-largo em CADA nível da cascata HTF→LTF, não uma vez só — conecta direto com o
    item #5 (escada de timeframe fractal).
    (Validação, não novo: razão timeframe execução↔contexto que ele usa bate com nosso
    1h como contexto atual; premium/discount como soft-filter já é assim no nosso scorer.)

## 🔜 Extraído da aula "Mapeamento HTF-LTF" (HSM Trading)
23. **New Week Opening Gap (NWOG)** — gap sexta-fechamento → domingo/segunda-abertura no
    SEMANAL, tratado como nível de referência forte. Não temos hoje (só gaps intradiários).
    Adicionar como referência extra pro bias semanal.
24. **🔥 Liquidez multi-dia (EQH/EQL de verdade)** — topos/fundos relativamente iguais ENTRE
    DIAS DIFERENTES (não só intra-sessão) = ímã de preço mais forte. Completa o gap de EQH/EQL
    identificado há muito tempo atrás (nunca implementado) — precisão: procurar no diário/4h
    across múltiplos dias, não só na sessão atual.
    (CE = 50% de qualquer ineficiência generaliza item #13 pra FVG/void/NWOG, não só bloco —
    extensão, não item novo. Disciplina "nunca LTF contra HTF" já é nossa regra atual —
    validação, não novidade.)

## Candidatos a avaliar (ainda não assistido, avaliar se parecer forte)
(nenhum pendente da lista original — aguardando novas sugestões)

## Regra de execução
Não implementar/rodar isoladamente — acumular aqui, aplicar em lote numa única rodada de
busca nova quando os processos atuais (PO3v2 NQ/ES geral + struct) fecharem. Cada teste
sempre: IS 2022-23 (busca) / VAL 2024 (seleção) / HOLDOUT 2025-26 (travado, só no final).
