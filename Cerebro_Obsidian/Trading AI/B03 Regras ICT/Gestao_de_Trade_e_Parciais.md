# Regras de ICT - Gestão de Trade & Parciais

Para sobreviver a médio e longo prazo no mercado, a gestão do trade após o disparo é mais importante do que a própria entrada. A IA deve executar regras mecânicas e inflexíveis de **Realização Parcial** e **Mover para o Zero (Breakeven)**.

---

## 1. A Regra Rígida de Parciais (Partials)
Você nunca deve esperar que 100% da posição bata no Take Profit final. O preço costuma fazer falsos rompimentos ou reverter antes de alcançar o alvo macro.

*   **Gatilho de Parcial**: Tirar **50% da posição** (fechar metade do lote) no primeiro topo estrutural importante (se BUY) ou primeiro fundo estrutural importante (se SELL).
    - Exemplo: Compra feita no SSL intraday. O primeiro alvo de parcial de 50% é a liquidez interna de curto prazo (primeira resistência local).
*   **Payout Seguro**: Ao realizar 50% de parciais, você garante lucros na conta e remove a pressão psicológica do trade.

---

## 2. A Regra do Zero a Zero (Breakeven)
> [!IMPORTANT]
> **Proibido Devolver Lucros**: Um trade que já andou substancialmente a favor e atingiu a primeira parcial **nunca deve se tornar um loss**.

*   **Gatilho de Breakeven**: Assim que a primeira parcial de 50% for batida, a IA deve **imediatamente mover o Stop Loss do restante da posição para o preço exato de entrada (Breakeven)**.
*   **Regra de Avanço de Perna**: Se o trade já andou em uma relação de **1:1.5** em relação ao risco inicial, mesmo sem bater na parcial física, a IA deve mover o Stop Loss para o ponto de entrada como medida de segurança.

---

## 3. Trailing Stop Sistemático (Seguidor de Tendência)
Após a primeira parcial garantida e o stop travado no ponto de entrada:
- A IA pode carregar os 50% restantes até o Take Profit final.
- **Trailing Stop**: Se o preço formar um novo fundo relevante no intraday (em tendência de alta) e fizer um novo MSS de continuação, o Stop Loss do restante da posição pode ser movido do ponto de entrada para abaixo desse novo fundo formado. Isso garante a proteção de ganhos extras caso o preço reverta bruscamente.


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[C02 Licoes Aprendidas/Metodologia_Lopez_de_Prado|Metodologia Lopez de Prado]]
- [[C02 Licoes Aprendidas/Erros_Evitar|Lições Aprendidas & Erros]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]