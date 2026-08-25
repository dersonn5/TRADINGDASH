---
tags: [filtros, nao-operar, risco, camada-4, sistema-operacional]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🚫 Filtros — Quando NÃO Operar

> Esta é uma das notas mais importantes do sistema.
> **Saber quando NÃO operar é mais valioso do que saber quando operar.**
> O sistema só é lucrativo quando é seletivo.

---

## Filtros Absolutos (Circuit Breakers — Automáticos)

> [!CAUTION]
> Os filtros abaixo **desligam o sistema imediatamente**. Sem exceção. Sem julgamento humano.

### F1 — Drawdown Diário ≥ 3%
- Perda acumulada no dia atingiu 3% do capital
- **Ação**: Sistema vai para standby. Zero trades até o dia seguinte (00:00 ET)
- **Por quê**: Após 3% de perda, o estado emocional e o mercado estão contra você. Recuperar durante o mesmo dia piora o drawdown estatisticamente

### F2 — Limite de 3 Trades no Dia
- 3 trades fechados (vitórias ou perdas)
- **Ação**: Sistema para. Independente do resultado
- **Por quê**: Backtests provam que trades adicionais além de 3/dia reduzem o edge estatístico

### F3 — Meta Diária de 5% Atingida
- Lucro acumulado no dia chegou a 5% do capital
- **Ação**: Sistema encerra a sessão. Proteger o lucro
- **Por quê**: Continuar depois de 5% de lucro aumenta o risco de devolver o ganho

### F4 — Notícia de Alto Impacto
- Janela de ±15 minutos em torno de: **CPI, PPI, FOMC, NFP, Discurso do Powell, PIB**
- **Ação**: Sistema em pausa durante a janela completa
- **Por quê**: Spread aumenta, liquidez cai, o preço viola estruturas ICT sem respeitar zonas

### F5 — Fora da Killzone
- Horário fora de: London Open, NY AM, NY PM, Silver Bullet
- **Ação**: Sistema não procura setups. Aguarda próxima janela
- **Por quê**: Volume institucional é baixo fora das killzones. Zigue-zague destrói stops

---

## Filtros Condicionais (Analíticos)

> [!WARNING]
> Estes filtros exigem análise. Se a condição estiver presente, não operar.

### F6 — Daily Bias Neutro
- H4 sem direção clara: sem swing high/low definido, sem FVG HTF ativo
- **Ação**: Aguardar bias se estabelecer. Não forçar operação

### F7 — SMT Divergência Confirmando o Lado Oposto
- BTC fazendo novo high, ETH **não** confirma (bearish SMT) → não fazer long
- BTC fazendo novo low, ETH **não** confirma (bullish SMT) → não fazer short

### F8 — Preço Dentro de FVG de H1 ou H4
- Se o preço está no meio de um FVG HTF sem direção definida
- **Ação**: Aguardar o preço sair do FVG e mostrar direção

### F9 — Múltiplos Níveis de Liquidez Muito Próximos
- BSL e SSL estão a menos de 0.3% de distância do preço atual
- **Ação**: Aguardar uma das varreduras ocorrer primeiro

### F10 — Correlação DXY Rompida
- DXY e BTC se movendo na mesma direção (ambos subindo ou ambos caindo)
- **Ação**: Ambiente de risco anômalo. Não operar

---

## Log de Ativação de Filtros

Quando um filtro for ativado, registrar no diário:
```
Data: ____
Filtro: F__ — [nome]
Horário: __:__
Capital no momento: $____
Decisão: Sessão encerrada / Trade cancelado
```
Ver: [[../03_Diario_Trades/Diario_2026_06|📅 Diário de Junho]]

---

## 🔗 Conexões Neurais
- [[MOC_PreTrade|📋 MOC Pré-Trade]]
- [[Checklist_Pre_Sessao|✅ Checklist da Sessão]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[GERENCIAMENTO_VALIDADO/Drawdown_e_Limites_Diarios|🛡️ Drawdown e Limites]]
- [[DURANTE_O_TRADE/Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[../01_Regras_ICT/ICT_Killzones_YouTube_Distilled|⏰ Killzones]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]