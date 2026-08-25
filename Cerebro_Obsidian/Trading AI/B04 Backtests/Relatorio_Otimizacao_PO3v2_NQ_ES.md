---
tags: [camada-4, backtest, otimizacao, po3v2, nq, es]
camada: 4
categoria: BACKTEST
status: em_teste
ultima_revisao: 2026-07-04
---

# 📊 Relatório de Otimização Massiva e Validação da Estratégia PO3v2 (NQ & ES)

Este relatório consolida os resultados da busca massiva de hiperparâmetros realizada nos mercados de Nasdaq-100 (NQ) e S&P 500 (ES), utilizando uma amostragem aleatória de **300 combinações de parâmetros** por mercado em paralelo. O objetivo foi testar a robustez temporal da estratégia [[B03 Regras ICT/Power_of_3_e_AMD|Power of Three (PO3v2)]] contra o viés de sobreajuste estatístico (*overfitting*).

---

## 🔬 Metodologia de Validação Cruzada (Staged Validation)

Seguindo os princípios de rigor matemático descritos na [[C02 Licoes Aprendidas/Metodologia_Lopez_de_Prado|Metodologia de Lopez de Prado]]:
1. **Estágio 1 (Validação - Out-Of-Sample 2024)**: Teste rápido de 300 amostras. Filtro de corte rígido: `total_trades >= 25` e `profit_factor >= 1.10`.
2. **Estágio 2 (In-Sample 2022-2023)**: As candidatas aprovadas no Estágio 1 são testadas nos 2 anos anteriores. Critério para edge estatístico real: `profit_factor >= 1.05` no período completo de 2 anos.

---

## 📈 Resultados do Nasdaq (NQ)

O Estágio 1 processou as 300 amostras e selecionou **5 finalistas** com excelente desempenho em 2024. Contudo, todas falharam no Estágio 2:

### Tabela de Desempenho dos Finalistas (NQ)

| Amostra | Parâmetros Chave | PF 2024 (Val) | Trades 2024 | DD 2024 | PF 2022-23 (IS) | Trades IS | Veredito |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **208** | both / rr / entry_precision="ce" | **1.36** | 28 | 7.99% | **0.74** | 62 | ❌ Rejeitada (Overfit) |
| **294** | asia / rr / entry_precision="ce" | **1.29** | 37 | 7.21% | **0.84** | 58 | ❌ Rejeitada (Overfit) |
| **236** | asia / liquidity / entry_precision="edge" | **1.21** | 35 | 4.23% | **0.73** | 91 | ❌ Rejeitada (Overfit) |
| **246** | asia / liquidity / entry_precision="edge" | **1.19** | 46 | 6.00% | **0.72** | 98 | ❌ Rejeitada (Overfit) |
| **59** | both / liquidity / entry_precision="edge" | **1.13** | 27 | 5.50% | **0.69** | 69 | ❌ Rejeitada (Overfit) |

* **Veredito NQ**: **NENHUMA configuração passou**. A melhor candidata em 2024 (Amostra 208 com PF=1.36) colapsou para um PF de 0.74 no período anterior, confirmando viés de seleção no ano de 2024.

---

## 📉 Resultados do S&P 500 (ES)

O Estágio 1 processou as 300 amostras e selecionou **3 finalistas** com métricas aparentemente excepcionais em 2024. O Estágio 2 revelou um colapso ainda mais drástico:

### Tabela de Desempenho dos Finalistas (ES)

| Amostra | Parâmetros Chave | PF 2024 (Val) | Trades 2024 | DD 2024 | PF 2022-23 (IS) | Trades IS | Veredito |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **78** | both / liquidity / entry_precision="edge" | **1.72** | 37 | 4.00% | **0.49** | 69 | ❌ Rejeitada (Overfit) |
| **59** | both / liquidity / entry_precision="edge" | **1.51** | 32 | 4.00% | **0.58** | 65 | ❌ Rejeitada (Overfit) |
| **279** | asia / rr / entry_precision="edge" | **1.14** | 27 | 4.00% | **0.58** | 39 | ❌ Rejeitada (Overfit) |

* **Veredito ES**: **NENHUMA configuração passou**. A Amostra 78, que obteve um PF brilhante de 1.72 e apenas 4% de drawdown em 2024, despencou para um PF perdedor de 0.49 em 2022-2023.

---

## 🧠 Diagnóstico Técnico e Lições Aprendidas

### 1. Ausência de Direcionamento Macroscópico (Daily Bias)
A estratégia PO3v2 reage puramente a varreduras de liquidez interna/externa de curto prazo e quebra de estrutura (MSS/CISD). Sem um filtro de [[B03 Regras ICT/Daily_Bias_e_Order_Flow|Daily Bias ou fluxo de ordens HTF]], a estratégia executa vendas contra tendências de alta massivas (como o ano de 2023 inteiro) ou compras contra fortes tendências de baixa (como o mercado de queda livre em 2022).

### 2. Mudança no Regime de Volatilidade
Os anos de 2022 (alta volatilidade e mercado urso) e 2023 (recuperação) possuem assinaturas de mercado radicalmente diferentes de 2024. Multiplicadores de ATR estáticos para stop loss e buffers de reclaim, e limites de [[B03 Regras ICT/Consequent_Encroachment_FVG|Consequent Encroachment]] fixos geram degradação rápida quando o ATR médio do ativo se expande ou contrai drasticamente.

### 3. Confirmação do Filtro de Estágio Duplo
Este teste provou a eficácia absoluta do funil de validação. Se operássemos apenas com base no backtest otimizado de 2024, teríamos ativado uma estratégia perdedora no mercado real. A validação cruzada evitou a destruição de capital.

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B04 Backtests/Log_Desenvolvimento_Diario|Log de Desenvolvimento Diário]]
- [[C02 Licoes Aprendidas/Metodologia_Lopez_de_Prado|Metodologia Lopez de Prado]]
- [[B03 Regras ICT/Power_of_3_e_AMD|Conceito: Power of Three]]
- [[B03 Regras ICT/Optimal_Trade_Entry_OTE|Optimal Trade Entry]]
- [[B03 Regras ICT/SMT_Divergence|SMT Divergence]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow|Daily Bias e fluxo de ordens]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]