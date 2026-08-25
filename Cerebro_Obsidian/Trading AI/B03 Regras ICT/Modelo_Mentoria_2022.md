# Regras de ICT - Modelo de Mentoria 2022 (Win Rate: ~68% | Payout: 1:3+)

O Modelo de Mentoria 2022 é o setup intraday mais popular e consistente criado pelo ICT, desenhado especificamente para capturar reversões de tendência após varreduras de liquidez institucionais.

---

## 1. A Lógica Algorítmica do Setup
O algoritmo interbancário induz o varejo a comprar ou vender nos extremos para acumular ordens e, em seguida, realiza um movimento violento de reversão em busca da liquidez oposta.

---

## 2. Passo a Passo Operacional (Checklist Rígido)

```
[1] Varredura de Liquidez (Swept BSL/SSL)
            o
           / \   <-- Topo que varreu a liquidez
          /   \
         /     \   [2] Deslocamento Forte (Displacement)
        /       \  
       /         \
------o           \  <-- Quebra do fundo (MSS Confirmado!)
(Suporte)          \
                    \       [3] Retorno do Preço
                     \      /\
                      \    /  \ <-- Entrada na FVG (Zona Premium)
                       \  /
                        \/
```

1. **Janela de Tempo (Killzone)**: O setup só é válido se a varredura e o MSS ocorrerem dentro de uma Killzone oficial (Londres ou Nova York).
2. **Varredura HTF (Liquidity Sweep)**: O preço deve romper e imediatamente recolher um topo importante (Buy-side Liquidity - BSL) ou fundo importante (Sell-side Liquidity - SSL) de gráfico de 15m, 1h ou 4h.
3. **Deslocamento Violento (Displacement)**: Após o sweep, deve ocorrer um movimento forte na direção oposta, formando velas longas de corpo cheio.
4. **Market Structure Shift (MSS)**: O deslocamento deve quebrar de forma nítida o último topo relevante (se bearish) ou fundo relevante (se bullish). **Regra**: O candle do MSS deve fechar acima/abaixo do nível com corpo cheio, não apenas pavio!
5. **Criação de Fair Value Gap (FVG)**: O deslocamento violento deve deixar pelo menos um FVG claro na perna do MSS.
6. **Entrada Limitada**: Colocar ordem limite no início da FVG (ou no nível de 50% Consequent Encroachment) quando o preço retornar para mitigar o desequilíbrio.

---

## 3. Parâmetros de Entrada e Saída
- **Trigger de Entrada**: Toque na FVG que esteja na **Zona de Desconto** (para BUY) ou **Zona Premium** (para SELL).
- **Stop Loss**: Posicionado obrigatoriamente logo abaixo do candle que fez o sweep de liquidez (ou atrás do candle de início do deslocamento se a perna for muito longa).
- **Take Profit**: Alvo principal posicionado no extremo oposto de liquidez pendente (ex: se comprou no SSL, o TP é o BSL oposto).
- **Relação R:R Mínima**: **1:2.5** (Trades com R:R inferior devem ser ignorados pela IA).


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/FVG_e_MSS|FVG & MSS]]
- [[B03 Regras ICT/Optimal_Trade_Entry_OTE|Optimal Trade Entry (OTE)]]
- [[B03 Regras ICT/Consequent_Encroachment_FVG]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]