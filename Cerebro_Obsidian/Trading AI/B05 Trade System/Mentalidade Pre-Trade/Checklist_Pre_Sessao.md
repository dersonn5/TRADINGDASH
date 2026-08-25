---
tags: [checklist, pre-trade, sessao, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# ✅ Checklist da Sessão — Pré-Trade

> **Execute este checklist ANTES de ativar qualquer estratégia.**
> Cada item deve ser ✅ para o sistema operar. Qualquer ❌ = sessão cancelada.

---

## BLOCO A — Filtros Automáticos (Sistema Verifica)

- [ ] **Drawdown diário < 3%** → se ≥ 3%, sistema em standby até amanhã
- [ ] **Trades no dia < 3** → se = 3 trades fechados, sistema para
- [ ] **Meta diária não atingida** → se lucro ≥ 5% no dia, sistema encerra
- [ ] **Sem notícias de alto impacto** nos próximos 15 min (CPI, FOMC, NFP, Powell)
- [ ] **Horário dentro de killzone** → se fora, sistema aguarda

> [!IMPORTANT]
> Os filtros do Bloco A são **não-negociáveis**. A IA não executa se qualquer um estiver violado.
> Ver: [[Filtros_Nao_Operar]]

---

## BLOCO B — Análise Técnica da Sessão (IA Executa)

- [ ] **Daily Bias mapeado** em H4/D1 → bullish, bearish ou neutro?
- [ ] **DOL identificado** → onde o preço está sendo atraído hoje?
- [ ] **Asian Range marcado** → high e low da sessão asiática registrados
- [ ] **Midnight Open plotado** → nível de 00:00 ET marcado no gráfico
- [ ] **FVGs de H1 identificados** → zonas de interesse acima e abaixo do preço
- [ ] **Níveis de liquidez mapeados** → BSL e SSL relevantes do dia anterior e semana

---

## BLOCO C — Contexto de Mercado (IA Verifica)

- [ ] **DXY alinhado** com o viés do trade (correlação inversa para cripto)
- [ ] **BTC e ETH em correlação** → SMT divergência visível ou ausente?
- [ ] **Fase do AMD identificada** → em qual fase do Power of 3 estamos?
- [ ] **Nenhuma posição aberta** de sessão anterior (sistema flat)

---

## BLOCO D — Estado do Sistema (Técnico)

- [ ] **Conexão com exchange estável** → Binance API respondendo
- [ ] **Saldo da conta verificado** → capital disponível calculado
- [ ] **Parâmetros de risco atualizados** → 1% do saldo atual calculado em USD
- [ ] **Logs do dia anterior revisados** → alguma anomalia a considerar?

---

## Resultado do Checklist

| Resultado | Ação |
|---|---|
| Todos os blocos ✅ | Sistema ativado — aguardar sinal |
| Bloco A com ❌ | Sessão **encerrada** — protocolo de filtro ativado |
| Bloco B/C com ❌ | Análise incompleta — concluir antes de ativar |
| Bloco D com ❌ | Problema técnico — resolver antes de ativar |

---

## 🔗 Conexões Neurais
- [[MOC_PreTrade|📋 MOC Pré-Trade]]
- [[Filtros_Nao_Operar|🚫 Filtros — Não Operar]]
- [[Mapeamento_de_Liquidez|🗺️ Mapeamento de Liquidez]]
- [[Estado_Mental_Ideal|🧘 Estado Mental]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco]]
- [[../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|⏰ Killzones]]
- [[../01_Regras_ICT/Power_of_3_e_AMD|📐 Power of 3 & AMD]]
- [[../01_Regras_ICT/Daily_Bias_e_Order_Flow|📊 Daily Bias]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]