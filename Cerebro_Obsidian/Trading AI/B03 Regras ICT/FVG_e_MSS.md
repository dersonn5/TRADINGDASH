# Regras de ICT - Fair Value Gap (FVG) e Market Structure Shift (MSS)

Estas são as diretrizes estritas do Inner Circle Trader (ICT) para identificar quebras de estrutura estruturadas e entradas de alta probabilidade.

---

## 1. Market Structure Shift (MSS)
O MSS ocorre quando o preço faz uma quebra de estrutura clara com **deslocamento forte**, mudando o viés (bias) do mercado.
- **MSS de Alta (Bullish)**: Quebra do último topo relevante (Swing High) após uma varredura de liquidez de baixa (SSL).
- **MSS de Baixa (Bearish)**: Quebra do último fundo relevante (Swing Low) após uma varredura de liquidez de alta (BSL).

> [!IMPORTANT]
> **Filtro de Deslocamento**: A vela que quebra o topo/fundo deve fechar com corpo cheio (candle forte), indicando presença institucional. Pavios longos sem fechar acima não contam como MSS!

---

## 2. Fair Value Gap (FVG)
O FVG é um desequilíbrio (imbalance) de preço de 3 velas consecutivas.
- **FVG de Alta (Bullish)**: O espaço vazio deixado entre a máxima da Vela 1 e a mínima da Vela 3. O preço tende a retornar a essa zona de "Desconto" para mitigar a ineficiência.
- **FVG de Baixa (Bearish)**: O espaço vazio deixado entre a mínima da Vela 1 e a máxima da Vela 3.

```
Vela 1: [ ] (Máxima)
           <--- FVG (Espaço Vazio)
Vela 3: [ ] (Mínima)
```

---

## 3. Checklist de Entrada Perfeita
1. **Killzone Ativa**: Estamos nas janelas de Londres ou Nova York?
2. **Varredura de Liquidez (Liquidity Sweep)**: O preço rompeu e recolheu um topo/fundo importante antes do movimento?
3. **Deslocamento Clara**: Houve MSS com corpo de vela cheio?
4. **Retorno à FVG**: O gatilho de compra/venda é ativado somente no toque na FVG (na zona de Desconto/Premium).
5. **Relação R:R**: O alvo na próxima liquidez oposta dá no mínimo **1:2.5** de retorno em relação ao Stop Loss (colocado atrás do candle do MSS)?


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Modelo_Mentoria_2022|Modelo Mentoria 2022]]
- [[B03 Regras ICT/Consequent_Encroachment_FVG|Consequent Encroachment FVG]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]