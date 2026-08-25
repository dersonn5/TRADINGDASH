---
tags: [durante-trade, regras, nao-intervir, camada-4, psicologia]
camada: 4
categoria: TRADE_SYSTEM
status: validado
ultima_revisao: 2026-06-27
---

# 🚦 Regras de Não Intervir

> **Camada 4 — Sistema Operacional**
> Após a entrada, o maior perigo não é o mercado — é a vontade de "fazer algo".
> Estas regras existem para proteger o trade de si mesmo.

---

## O Princípio Central

> [!IMPORTANT]
> **O trade foi planejado ANTES da entrada. Tudo o que acontece DEPOIS é ruído emocional.**
> Confiar no plano = confiar nos 3 anos de backtest que o validaram.
> Interferir = invalidar o edge estatístico.

---

## Regras de Não Intervenção

### NI-1 — Não Fechar Antes do Alvo ou Stop
```
O trade fecha quando:
  A) Stop Loss é atingido → perda de 1R (planejada)
  B) Alvo 1 é atingido → ganho de 2R (planejado)
  C) Condição de invalidação técnica é ativada → ver Alertas_de_Invalidacao
```
Fechar manualmente por ansiedade = destruir o PF estatístico

### NI-2 — Não Ampliar o Stop Loss
```
O stop foi calculado com precisão cirúrgica.
Aumentar o stop = aumentar o risco sem aumentar o reward.
= Destruir o R:R validado pelo backtest.
```
Se o preço está chegando no stop, o stop foi bem posicionado — o setup falhou. Aceitar.

### NI-3 — Não Adicionar Posição (Piramidação)
```
A posição é 100% definida na entrada.
Adicionar mais contratos após a entrada = risco não calculado.
= Violação direta da regra R1 (1% por trade).
```

### NI-4 — Não Monitorar o P&L em Tempo Real
```
Olhar o P&L flutuante durante o trade ativa o viés emocional.
A IA não exibe P&L em tempo real durante a gestão do trade.
Somente Stop e Alvo são monitorados.
```

### NI-5 — Não Mudar o Alvo por Ganância
```
Se o preço está indo bem e o alvo se aproxima:
→ Não remover o alvo esperando "mais"
→ O alvo foi definido em contexto frio, pré-trade
→ Honrar o plano
```
Exceção: trailing stop **após** alvo 1 atingido — ver [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos]]

---

## Quando a Intervenção É Permitida

Intervenção manual é permitida **somente** nas seguintes condições (ver [[Quando_Fechar_Antecipado]]):

1. **Notícia de alto impacto** surgiu inesperadamente após a entrada
2. **Alerta de invalidação técnica** confirmado — ver [[Alertas_de_Invalidacao]]
3. **Problema técnico** da exchange (conexão, ordem não executada)
4. **Breakeven programado** atingiu condição — ver [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss]]

---

## A Psicologia do Não Intervir

### Por que é difícil?
O cérebro humano interpreta perda iminente como ameaça física → resposta de luta ou fuga → impulso de "fazer algo".

### O que a IA faz diferente?
Não tem sistema límbico. Executa o plano porque o plano é tudo o que existe.

### O que o operador humano deve lembrar?
```
"Eu já tomei a decisão correta quando abri o trade.
 O trade em andamento é o plano sendo executado.
 Minha tarefa agora é não destruir o plano."
```

---

## 🔗 Conexões Neurais
- [[MOC_DuranteTrade|👁️ MOC Durante o Trade]]
- [[Cenarios_Possiveis|🔀 Cenários Possíveis]]
- [[Quando_Fechar_Antecipado|⛔ Fechar Antecipado]]
- [[Alertas_de_Invalidacao|🚨 Alertas de Invalidação]]
- [[MOC_TradeSystem|🧠 TRADE SYSTEM]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Stop_Loss|🔴 Gestão do Stop]]
- [[../CONDUCAO_DE_TRADE/Gestao_de_Alvos|🏁 Gestão de Alvos]]
- [[../MENTALIDADE_PRE_TRADE/Estado_Mental_Ideal|🧘 Estado Mental]]
- [[../02_Licoes_Aprendidas/Erros_Evitar|⚠️ Erros a Evitar]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]