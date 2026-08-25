---
tags: [pos-trade, licoes, ajustes, camada-5, sabedoria]
camada: 5
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 💡 Lições e Ajustes

> **Camada 5 — Repositório Dinâmico de Sabedoria**
> Onde registramos desvios das estratégias, novas descobertas empíricas e calibrações de regras baseadas na prática.

---

## 1. Ajustes Ativos (Compilado de Backtests e Operações)

### Ouro (XAUUSD) — Sem Entrada Direta
- **Ajuste**: Nunca entrar pendurado por limit order no CE de 15m no Ouro. O ouro exige varredura e quebra local em 1m/5m para evitar double sweeps.
- **Origem**: [[../../02_Licoes_Aprendidas/Erros_Evitar#lições-de-ouro-xauusd--validação-de-ce-ganhos-consistentes|Erros a Evitar (XAUUSD)]]

### Cripto (BTC/ETH) — Proibição de BE no NY AM
- **Ajuste**: Proibir o uso de Break-Even na sessão da manhã (NY AM) do Silver Bullet para BTC e ETH.
- **Origem**: Backtest histórico de 3 anos (2022-2024). O BE reduziu a lucratividade pela metade devido à volatilidade local de wicks do Bitcoin.

---

## 2. Registro de Novos Ajustes (Formato de Entrada)

Toda vez que uma nova lição for identificada no review semanal, adicionar aqui:

```markdown
### [Ativo] — [Assunto / Regra Nova]
- **Data**: YYYY-MM-DD
- **Descrição da Lição**: [O que foi aprendido?]
- **Ação Prática**: [O que o robô/trader deve fazer diferente de agora em diante?]
- **Impacto no Código**: [Requer alteração de código ou apenas consulta RAG?]
- **Vínculo**: [[Diário correspondente]] / [[Estratégia afetada]]
```

---

## 🔗 Conexões Neurais
- [[MOC_PosTrade|📊 MOC Pós-Trade]]
- [[Protocolo_de_Review|🔍 Protocolo de Review]]
- [[../../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[../../04_Backtests/Log_Desenvolvimento_Diario|📋 Log de Desenvolvimento]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]