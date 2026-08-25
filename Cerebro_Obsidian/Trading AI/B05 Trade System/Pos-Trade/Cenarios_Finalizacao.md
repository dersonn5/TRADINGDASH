---
tags: [pos-trade, finalizacao, metricas, cenarios, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🏁 Cenários de Finalização (Desfecho Estatístico)

> **Camada 4 — Gestão de Resultados**
> Mapeamento de como o trade foi encerrado e a ação correspondente para atualizar a performance e a mente.

---

## 1. Take Profit Atingido (Cenário Ideal) ✅
- **Desfecho**: O preço atingiu a Limit Order de saída no Alvo 1 (2R) ou Alvo 2 (Trailing).
- **Ações**:
  1. Registrar como `WIN` de `+2.0R` (ou valor final do trailing).
  2. Celebrar silenciosamente a disciplina do plano.
  3. Evitar o sentimento de invencibilidade. **Manter o risco inalterado (1%) no próximo trade**.
  4. Executar [[Protocolo_de_Review]].

---

## 2. Stop Loss Atingido (Perda Planejada) ❌
- **Desfecho**: O preço tocou o Stop Loss inicial, fechando com `-1.0R`.
- **Ações**:
  1. Registrar como `LOSS` de `-1.0%` (ou valor orçado).
  2. Lembrar-se: **uma perda é apenas um custo operacional do negócio**.
  3. Não buscar retaliação ou abrir nova posição imediata (proibição de *Revenge Trading*).
  4. Analisar se a invalidação foi estrutural ou puro ruído.

---

## 3. Break-Even Atingido (Saída Neutra) 🟡
- **Desfecho**: O preço subiu, ativou a parcial/BE e retornou para stopar a posição restante no preço de entrada.
- **Ações**:
  1. Registrar como `BE` ou ganho parcial (+0.75R).
  2. Não lamentar que o trade "Poderia ter dado 2R". A proteção do capital é a prioridade.
  3. Analisar se o stop foi movido para o local correto de acordo com a regra da sessão.

---

## 4. Invalidação Manual Executada (Saída de Emergência) ⚠️
- **Desfecho**: O trade foi encerrado manualmente após a confirmação técnica de um dos [[../DURANTE_O_TRADE/Alertas_de_Invalidacao|Alertas de Invalidação]].
- **Ações**:
  1. Registrar como `MANUAL` de `-0.XXR` (perda reduzida).
  2. Verificar se a regra de invalidação estava realmente ativa ou se foi pânico emocional.
  3. Documentar detalhadamente o fechamento da vela de M5 que acionou a saída.

---

## 🔗 Conexões Neurais
- [[MOC_PosTrade|📊 MOC Pós-Trade]]
- [[Protocolo_de_Review|🔍 Protocolo de Review]]
- [[Licoes_e_Ajustes|💡 Lições e Ajustes]]
- [[../DURANTE_O_TRADE/Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]
- [[../DURANTE_O_TRADE/Cenarios_Possiveis|🔀 Cenários Possíveis]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]