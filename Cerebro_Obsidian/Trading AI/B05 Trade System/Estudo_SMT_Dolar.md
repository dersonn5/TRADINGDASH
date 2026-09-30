# Estudo — SMT do WIN com o dólar (WDO)

> Script: `profit/smt_dolar.py` · 30/09/2026 · WIN e WDO de 1 min, 69 pregões (23/06–30/09/2026).
> O cache do Profit só tem WDO de 1 min desse período (contratos Q26, U26, V26, X26).

## Pergunta
No pregão de 30/09 houve SMT de baixa às 09:44–09:46: o dólar fez fundo novo (5.192,0 < 5.196,0)
e o WIN fez topo mais baixo (188.425 < 188.860); depois o índice caiu 2.600+ pts. A SMT melhora os
gatilhos de 1 min? Palpite do operador: "não vai ter relevância, o dólar anda descolado".

## Definição
- Gatilhos: todo MSS de 1 min (MSS+FVG, MSS+OB, BPR) com entrada 10:00–11:29, gestão do sistema.
- Extremo = fundo/topo que virou o stop. Referência = 30 a 5 min antes dele.
- **SMT**: o WIN passou do fundo/topo da referência e o dólar **não** fez o espelho (na compra, o
  topo do WDO no extremo ±2 min não passou do topo da referência; na venda, o inverso).
- **Confirmado**: o WIN varreu e o dólar acompanhou. **Sem varrida**: o WIN não passou da referência.

## Resultado

| No extremo do gatilho | n | Acerto | Média | Pts/trade |
|---|---|---|---|---|
| SMT | 108 | 39% | +0,14R | +6 |
| Confirmado (sem divergência) | 57 | 49% | +0,27R | +62 |
| Sem varrida | 496 | 38% | +0,25R | +41 |

Por gatilho, SMT nunca fica acima de "confirmado" (MSS+FVG +0,13 × +0,23R; MSS+OB +0,18 × +0,46R;
BPR +0,13 × +0,09R). Nenhuma diferença é estatisticamente clara.

Correlação dos retornos de 1 min WIN × WDO, 10:00–11:29: jun −0,52 · jul −0,47 · ago −0,39 · set −0,42.

## Leitura
- **A SMT com o dólar não melhora os gatilhos** — se algo, os trades sem divergência foram melhores.
  O palpite do operador se confirmou.
- Mas o motivo não é o dólar descolado: a correlação inversa minuto a minuto é forte e estável
  (−0,4 a −0,5). A divergência acontece, só não separa trade bom de ruim.
- Amostra de 3 meses. Não entra no checklist.
