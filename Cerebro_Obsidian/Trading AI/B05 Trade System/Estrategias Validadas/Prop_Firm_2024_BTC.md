---
tags: [estrategia, prop-firm, btc, camada-3, modelo, validado]
camada: 3
categoria: TRADE_SYSTEM
ativo: BTC/USDT
win_rate: 30.7%
profit_factor_ideal: 1.12
profit_factor_estressado: 1.03
total_trades_backtest: 231
periodo_backtest: 2022-2024
status: validado
ultima_revisao: 2026-06-27
---

# 🏆 Prop Firm 2024 — BTC/USDT

> **Camada 3 — Modelo Validado**
> Estratégia de scalping agressivo otimizada para regras de contas de mesas proprietárias (Prop Firms).
> **Foco: controle estrito de drawdown diário com setups de alta velocidade (Unicorn Setup & IFVG).**

---

## 1. O Conceito Prop Firm

Mesas proprietárias impõem regras rígidas de **Drawdown Diário (geralmente 5%)** e **Drawdown Total (geralmente 10%)**.
Este modelo foi desenhado para maximizar a taxa de recuperação após perdas e usar a volatilidade do BTC para atingir alvos rápidos com baixo tempo de exposição ao mercado.

---

## 2. O Unicorn Setup (Gatilho Principal)

O **Unicorn Setup** é a confluência de dois elementos principais no mesmo timeframe (M5 ou M1):
1. **Breaker Block** (OB rompido)
2. **Inversion FVG (IFVG)** (um FVG que foi rompido e agora atua na direção oposta)

```
        ▲ Alta Expansão
       /
      /   [MSS Bullish]
  ───/──────────────────── [Breaker Block]
    /  [IFVG] (Suporte)
   /
```

---

## 3. Condições de Entrada (Obrigatórias)

- [ ] **Horário**: Somente dentro das Macros de Alta Liquidez (08:50-09:10, 09:50-10:10, 10:50-11:10 ET)
- [ ] **Daily Bias**: Alinhado com o viés de H1
- [ ] **Gatilho**: Reteste simultâneo do Breaker Block + Inversion FVG (Unicorn Setup)
- [ ] **Alinhamento EMA 200**: Entrada a favor da tendência local de M5

---

## 4. Execução e Gestão de Risco Controlada

```
ENTRADA:  Limit Order no ponto de interseção do Breaker + IFVG
STOP:     1 tick atrás da estrutura de invalidação
ALVO:     1.5R fixo (para maximizar taxa de acerto nas regras de mesas)
RISCO:    0.5% a 1% por operação (dependendo do drawdown restante no dia)
```

> [!IMPORTANT]
> **Drawdown Limit**: Se o drawdown da conta atingir **-4%** no dia, este modelo é **desativado automaticamente** para evitar violação do limite de 5% da mesa.

---

## 🔗 Conexões Neurais
- [[MOC_Estrategias_Validadas|📈 MOC Estratégias]]
- [[Silver_Bullet_BTC_USDT|⚡ Silver Bullet BTC]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../01_Regras_ICT/ICT_OrderBlocks_YouTube_Distilled|📐 Order Blocks & Breakers]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 Inversion FVG]]
- [[../GERENCIAMENTO_VALIDADO/Drawdown_e_Limites_Diarios|🛡️ Drawdown e Limites]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]