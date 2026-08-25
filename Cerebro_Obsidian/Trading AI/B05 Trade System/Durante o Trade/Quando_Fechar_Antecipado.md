---
tags: [durante-trade, fechar-antecipado, gestao-risco, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# ⛔ Quando Fechar Antecipado (Saída Manual)

> **Regras rígidas para intervir no trade antes de atingir o Stop Loss ou Alvo principal.**
> A saída manual não é um recurso de "achismo" — ela possui regras estritas baseadas em invalidação estrutural.

---

## 1. Regra de Fechamento por Invalidação Estrutural
Se ocorrer qualquer uma das condições abaixo, a IA/Trader deve fechar a posição imediatamente sem esperar o Stop Loss:
- **Fechamento de Vela no M5 além do CE (50%) da FVG**: Indica que o fluxo de ordens institucional não defendeu o ponto médio de equilíbrio do FVG.
- **MSS na direção oposta com deslocamento**: Se o preço quebrar a estrutura local contra o trade, demonstrando força agressiva oposta (velas de corpo grande).

---

## 2. Invalidação Temporal (Janela de Tempo Expirada)
- Se a operação foi aberta na Killzone do Silver Bullet NY AM (10:00-11:00 ET) e o preço **não se moveu** decisivamente até as 11:30 ET.
- **Ação**: Fechar a mercado no preço atual. O volume tende a secar na transição para o almoço de NY, e o setup perde a vantagem estatística temporal.

---

## 3. Notícias de Alto Impacto Imprevistas (Red Folder)
- Se o robô identificar o surgimento repentino de uma notícia ou discurso macro (ex: pronunciamento de emergência de membros do FED).
- **Ação**: Fechar 100% da posição imediatamente a mercado, independente do P&L flutuante. A preservação do capital prevalece.

---

## 🔗 Conexões Neurais
- [[MOC_DuranteTrade|👁️ MOC Durante o Trade]]
- [[Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]
- [[Regras_Nao_Intervir|🚦 Regras de Não Intervir]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Gestão de Stop Loss]]
- [[../MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar|🚫 Filtros - Não Operar]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]