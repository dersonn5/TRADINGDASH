---
tags: [moc, trade-system, camada-4, sistema-operacional]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🧠 TRADE SYSTEM — Hub Central do Sistema Operacional

> Este é o **núcleo executivo** do Segundo Cérebro de Trading.
> Toda decisão de trade passa por aqui — antes, durante e depois da operação.
> A IA consulta este hub para navegar para o módulo correto em cada fase.

---

## 🏗️ Arquitetura em Camadas

```
CAMADA 1 — CONCEITOS    → [[Cerebro_ICT]] / 01_Regras_ICT/
CAMADA 2 — REGRAS       → 01_Regras_ICT/ (avançado)
CAMADA 3 — MODELOS      → B05 Trade System/Estrategias Validadas/
CAMADA 4 — SISTEMA      → TRADE_SYSTEM/ (você está aqui)
CAMADA 5 — SABEDORIA    → 02_Licoes_Aprendidas/ + 03_Diario_Trades/
```

---

## ⚡ Fluxo de Consulta da IA (Ordem Obrigatória)

```
SINAL DETECTADO
      │
      ▼
① [[MENTALIDADE_PRE_TRADE/Checklist_Pre_Sessao]]
  → Condições OK? Se NÃO → ENCERRAR
      │
      ▼
② [[MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar]]
  → Algum filtro ativado? Se SIM → ENCERRAR
      │
      ▼
③ [[ESTRATEGIAS_VALIDADAS/MOC_Estrategias_Validadas]]
  → Qual estratégia? → Consultar nota específica
      │
      ▼
④ [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias]]
  → Calcular sizing + verificar limites
      │
      ▼
⑤ [[CONDUCAO_DE_TRADE/Execucao_de_Entrada]]
  → Executar ordem
      │
      ▼
⑥ [[DURANTE_O_TRADE/Regras_Nao_Intervir]]
  → Aguardar resultado (sem interferência)
      │
      ▼
⑦ [[POS_TRADE/Protocolo_de_Review]]
  → Registrar, aprender, atualizar
```

---

## 📂 Módulos do Sistema

### ① PRÉ-TRADE — Preparação Mental e Técnica
> *Antes de abrir o terminal, antes de olhar o gráfico*
- [[MENTALIDADE_PRE_TRADE/MOC_PreTrade|📋 MOC Pré-Trade]]
- [[MENTALIDADE_PRE_TRADE/Checklist_Pre_Sessao|✅ Checklist da Sessão]]
- [[MENTALIDADE_PRE_TRADE/Estado_Mental_Ideal|🧘 Estado Mental Ideal]]
- [[MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar|🚫 Filtros — Quando NÃO Operar]]
- [[MENTALIDADE_PRE_TRADE/Mapeamento_de_Liquidez|🗺️ Mapeamento de Liquidez]]

### ② ESTRATÉGIAS — O Que a IA Executa
> *Protocolos validados por backtest — Camada 3*
- [[ESTRATEGIAS_VALIDADAS/MOC_Estrategias_Validadas|📈 MOC Estratégias Validadas]]
- [[ESTRATEGIAS_VALIDADAS/Silver_Bullet_BTC_USDT|⚡ Silver Bullet BTC/USDT]]
- [[ESTRATEGIAS_VALIDADAS/Silver_Bullet_ETH_USDT|⚡ Silver Bullet ETH/USDT]]
- [[ESTRATEGIAS_VALIDADAS/Breaker_Block_BTC_USDT|🧱 Breaker Block BTC/USDT]]
- [[ESTRATEGIAS_VALIDADAS/Breaker_Block_ETH_USDT|🧱 Breaker Block ETH/USDT]]
- [[ESTRATEGIAS_VALIDADAS/Prop_Firm_2024_BTC|🏆 Prop Firm 2024 BTC]]

### ③ GERENCIAMENTO — Regras de Risco Não-Negociáveis
> *A matemática que protege o capital*
- [[GERENCIAMENTO_VALIDADO/MOC_Gerenciamento|💰 MOC Gerenciamento]]
- [[GERENCIAMENTO_VALIDADO/Regras_Risco_Obrigatorias|⚖️ Regras de Risco Obrigatórias]]
- [[GERENCIAMENTO_VALIDADO/Sizing_e_Alavancagem|📐 Sizing e Alavancagem]]
- [[GERENCIAMENTO_VALIDADO/Drawdown_e_Limites_Diarios|🛡️ Drawdown e Limites Diários]]
- [[GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais e Break-Even]]

### ④ CONDUÇÃO — Gestão da Vida do Trade
> *Do momento da entrada até o fechamento*
- [[CONDUCAO_DE_TRADE/MOC_Conducao|🎮 MOC Condução]]
- [[CONDUCAO_DE_TRADE/Execucao_de_Entrada|🟢 Execução de Entrada]]
- [[CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Gestão do Stop Loss]]
- [[CONDUCAO_DE_TRADE/Gestao_de_Alvos|🏁 Gestão de Alvos]]
- [[CONDUCAO_DE_TRADE/Cenarios_Durante_Trade|🔀 Cenários Durante o Trade]]

### ⑤ DURANTE — Estado Mental e Vigilância
> *Enquanto o trade está aberto*
- [[DURANTE_O_TRADE/MOC_DuranteTrade|👁️ MOC Durante o Trade]]
- [[DURANTE_O_TRADE/Regras_Nao_Intervir|🚦 Regras de Não Intervir]]
- [[DURANTE_O_TRADE/Cenarios_Possiveis|🔀 Todos os Cenários Possíveis]]
- [[DURANTE_O_TRADE/Quando_Fechar_Antecipado|⛔ Quando Fechar Antecipado]]
- [[DURANTE_O_TRADE/Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]

### ⑥ PÓS-TRADE — Aprendizado e Registro Sináptico
> *Como o sistema evolui após cada trade*
- [[POS_TRADE/MOC_PosTrade|📊 MOC Pós-Trade]]
- [[POS_TRADE/Protocolo_de_Review|🔍 Protocolo de Review]]
- [[POS_TRADE/Licoes_e_Ajustes|💡 Lições e Ajustes]]
- [[POS_TRADE/Gravacao_Sinapse_Obsidian|🧬 Gravação Sináptica]]
- [[POS_TRADE/Cenarios_Finalizacao|🏁 Cenários de Finalização]]

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT|🧠 Hub Central — Cérebro ICT]]
- [[A00 Mapas de Conteudo/MOC_Estrategias|📈 MOC de Estratégias]]
- [[C02 Licoes Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[B04 Backtests/Log_Desenvolvimento_Diario|📋 Log de Desenvolvimento]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]