---
tags: [cenarios, durante-trade, nuances, camada-4]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🔀 Cenários Possíveis Durante o Trade

> **Camada 4 — Sistema Operacional**
> Todo cenário que pode acontecer após a entrada está mapeado aqui.
> Para cada cenário, existe uma resposta definida — sem improvisação.

---

## Contexto: Por Que Mapear Cenários?

O mercado é probabilístico. Não há certeza. Mas há **respostas corretas** para cada situação.
Quando o operador sabe antecipadamente o que pode acontecer e como reagir,
a emoção é eliminada da equação.

---

## GRUPO 1 — Cenários Favoráveis

### C1 — Trade Indo Direto ao Alvo ✅
**O que acontece**: Após a entrada, o preço se move diretamente na direção do trade sem retestes.
**Resposta**: Não fazer nada. Deixar o trade correr. Honrar o alvo definido.
**Risco psicológico**: Ganância de mover o alvo para cima → **não fazer isso**.

### C2 — Trade Atinge Alvo 1 (2R) ✅
**O que acontece**: Preço atinge o primeiro alvo de 2R.
**Resposta**:
- Fechar 50% da posição
- Mover stop para breakeven na posição restante
- Alvo 2 = próximo nível de liquidez HTF
Ver: [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos]]

### C3 — Trade Com Boa Expansão Além do Alvo 1 ✅
**O que acontece**: Preço passou pelo alvo 1 e continua forte.
**Resposta**: Com 50% já realizado e stop em BE, a posição restante corre com trailing stop.
**Risco psicológico**: Querer adicionar posição → **violação da regra NI-3**.

---

## GRUPO 2 — Cenários Neutros / De Espera

### C4 — Consolidação Após Entrada ⚠️
**O que acontece**: Preço entrou, moveu um pouco, agora está lateral por vários candles.
**Resposta**: Aguardar. Stop e alvo permanecem. O setup pode estar em fase de acumulação antes da distribuição.
**Limite**: Se passar das próximas 2 killzones sem movimento → avaliar [[Alertas_de_Invalidacao]]

### C5 — Reteste do Ponto de Entrada ⚠️
**O que acontece**: Após entrar, o preço volta exatamente para a região de entrada (sem atingir o stop).
**Resposta**: Aguardar. Retestes são normais em ICT. O stop foi posicionado além deste nível.
**Risco psicológico**: Pânico de que o stop vai ser atingido → normal, manter posição.

### C6 — Aproximação do Stop Sem Atingi-lo ⚠️
**O que acontece**: Preço chega a 30–50% do caminho até o stop e para.
**Resposta**: Nada. O stop foi calculado para permitir esse movimento. Aguardar.
**Se atingir o stop**: Aceitar a perda de 1R. Isso é parte do plano.

---

## GRUPO 3 — Cenários Adversos

### C7 — Stop Loss Atingido ❌
**O que acontece**: Stop foi tocado. Trade fechado com perda de 1R.
**Resposta**:
1. Aceitar — isso foi orçado no risco de 1%
2. Não reabrir o trade imediatamente (viés de recuperação)
3. Registrar no protocolo de review: [[Protocolo_de_Review]]
4. Verificar se há mais trades disponíveis no dia (limite de 3)

### C8 — Dupla Varredura (Stop Hunt no Stop Hunt) ❌⚠️
**O que acontece**: O preço varre SSL, forma FVG, depois varre mais fundo antes de subir.
Se o stop estava na primeira varredura → stop atingido (C7).
Se o stop estava além → aguardar formação de nova estrutura.
**Resposta**: Avaliar se um novo setup se formou na segunda varredura → novo protocolo de entrada.

### C9 — Invalidação Técnica da FVG ❌
**O que acontece**: Corpo de vela fecha decisivamente além do CE da FVG usada na entrada.
**Resposta**: Fechar manualmente **antes** do stop se possível (saída de emergência).
Ver: [[Alertas_de_Invalidacao]]

### C10 — Notícia de Alto Impacto Surgiu Após Entrada ⚠️❌
**O que acontece**: Uma notícia não prevista é publicada enquanto o trade está aberto.
**Resposta**:
- Se o trade está em lucro: fechar posição imediatamente
- Se o trade está em perda: aguardar o stop (não ampliar)
- Ver: [[../MENTALIDADE_PRE_TRADE/Filtros_Nao_Operar#f4-noticia-de-alto-impacto]]

---

## GRUPO 4 — Cenários Técnicos / Operacionais

### C11 — Problema de Conexão com a Exchange ⚠️
**O que acontece**: Perda de conexão enquanto há posição aberta.
**Resposta**:
1. Stop Loss já está na exchange (proteção automática)
2. Tentar reconectar em até 60 segundos
3. Se não reconectar: acessar pelo celular e verificar status da ordem

### C12 — Ordem de Entrada Não Executada ⚠️
**O que acontece**: O preço chegou ao CE do FVG mas a ordem limit não foi preenchida.
**Resposta**:
- Se o preço está voltando do CE → o setup pode continuar válido, reposicionar a ordem
- Se o preço passou pelo CE com força → o setup foi perdido. Não perseguir.

---

## 🔗 Conexões Neurais
- [[MOC_DuranteTrade|👁️ MOC Durante o Trade]]
- [[Regras_Nao_Intervir|🚦 Não Intervir]]
- [[Quando_Fechar_Antecipado|⛔ Fechar Antecipado]]
- [[Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos|🏁 Alvos]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Stop Loss]]
- [[../POS_TRADE/Protocolo_de_Review|🔍 Review]]
- [[../01_Regras_ICT/ICT_FVG_YouTube_Distilled|📐 FVG]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]