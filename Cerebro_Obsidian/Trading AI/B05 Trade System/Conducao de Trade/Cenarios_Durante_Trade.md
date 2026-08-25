---
tags: [conducao, cenarios, gestao, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🔀 Cenários Durante o Trade (Gestão Operacional)

> **Camada 4 — Protocolo de Condução**
> Como ajustar ordens, gerenciar trailing e lidar com a execução física do trade à medida que o preço se move.

---

## 1. O Preço Atinge Parcial 1 (1.5R)
- **Cenário**: O preço expande a nosso favor e alcança a linha de 1.5R.
- **Ação Obrigatória**:
  1. Executar **ordem de venda de 50%** da posição (Market ou Limit pré-posicionada).
  2. Mover o stop loss da metade restante para o **Breakeven (preço de entrada exato)**.
  3. Desativar quaisquer alertas de stop inicial.

---

## 2. O Preço Consolida Perto da Entrada (Sem volume)
- **Cenário**: O trade é ativado, mas o preço lateraliza na região de entrada por mais de 20 minutos.
- **Ação**:
  - **Não intervir**. A consolidação é comum antes de um breakout institucional.
  - Se a janela da Killzone acabar e o preço continuar travado no zero a zero, fechar 100% da posição manualmente para evitar taxas overnight de futuros.

---

## 3. Re-teste Violento da Zona FVG (Deep Retest)
- **Cenário**: O preço ativa a entrada no CE (50%) e cai rapidamente até a base do FVG (muito perto do Stop Loss).
- **Ação**:
  - **Manter a posição**. O stop foi calculado especificamente abaixo da base do FVG.
  - Pavios cruzando a zona de desconto são normais antes da rejeição real do preço.
  - Se o corpo da vela fechar fora, ver [[../DURANTE_O_TRADE/Alertas_de_Invalidacao|🚨 Alertas de Invalidação]].

---

## 4. O Preço Expande Rápido e Chega Próximo ao Alvo de 2R
- **Cenário**: O preço alcança 1.9R mas mostra sinais de exaustão no book de ofertas (tape reading).
- **Ação**:
  - Se faltar menos de 0.1% para o Alvo Final e o volume cair bruscamente, fechar a posição manualmente a mercado.
  - Não arriscar a reversão completa de 1.9R para ganhar os últimos ticks.

---

## 🔗 Conexões Neurais
- [[MOC_Conducao|🎮 MOC Condução]]
- [[Gestao_de_Stop_Loss|🔴 Gestão de Stop Loss]]
- [[Gestao_de_Alvos|🏁 Gestão de Alvos]]
- [[../GERENCIAMENTO_VALIDADO/Parciais_e_Breakeven|🎯 Parciais e Break-Even]]
- [[../DURANTE_O_TRADE/Cenarios_Possiveis|🔀 Cenários Possíveis]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]