# Regras de ICT - Optimal Trade Entry (OTE)

O OTE (Entrada Ótima de Trade) é uma ferramenta matemática baseada em Fibonacci desenhada para identificar com precisão cirúrgica a zona de desconto profundo (para compras) ou premium (para vendas) onde as instituições costumam reprecificar os ativos.

---

## 1. Configurações Estritas da Fibonacci de ICT
A Fibonacci tradicional do varejo foca nos níveis de 50.0% e 61.8%. O ICT utiliza configurações proprietárias específicas:

*   **0.00** - Início do Swing (Start)
*   **0.50** - Equilibrium (Equilíbrio do Range)
*   **0.62** - Limite Inferior da OTE
*   **0.705** - **Nível de Precisão da OTE (Sweet Spot)** (Nível de entrada prioritário!)
*   **0.79** - Limite Superior da OTE
*   **1.00** - Fim do Swing (Stop Original)

---

## 2. A Lógica de Desconto vs Premium (Equilibrium)
Para operar de forma lucrativa a longo prazo, você deve pensar como uma instituição interbancária:
- **Premium (Acima de 50%)**: Onde o preço está "caro". **Apenas setups de VENDA (Sell) são permitidos!**
- **Desconto (Abaixo de 50%)**: Onde o preço está "barato". **Apenas setups de COMPRA (Buy) são permitidos!**

```
[1.00] ═════════════════════════════════ Topo do Swing
       |
       |  ZONA PREMIUM (Apenas SELL)
       |
[0.50] --------------------------------- EQUILIBRIUM (Equilíbrio)
       |
       |  ZONA DE DESCONTO (Apenas BUY)
       |  [0.62 - 0.705 - 0.79] <--- OTE (Área de Compra Institucional)
       |
[0.00] ═════════════════════════════════ Fundo do Swing
```

---

## 3. Confluência e Checklist de Entrada OTE
O OTE não deve ser utilizado de forma cega. A IA deve validar a confluência utilizando o seguinte checklist:
1. **Perna com Deslocamento**: Traçar a Fibonacci apenas em pernas que realizaram uma quebra de estrutura clara (MSS).
2. **Confluência de Bloco (PD Array)**: A zona de OTE (0.62 - 0.79) deve coincidir com uma FVG ou com um Order Block / Breaker Block existente.
3. **Trigger**: Colocar a ordem limite posicionada exatamente em **0.705** (ou no início da FVG se esta estiver dentro da área de OTE).
4. **Stop Loss**: Posicionado além do nível de **1.00** (fundo/topo original do swing).
5. **Take Profit**:
   - Alvo 1: Extremo do Swing (0.00)
   - Alvo 2: Extensão de Fibonacci `-0.27`
   - Alvo 3: Extensão de Fibonacci `-0.62`


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Modelo_Mentoria_2022|Modelo Mentoria 2022]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow|Daily Bias & Order Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]