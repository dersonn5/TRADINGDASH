# Regras de ICT - Daily Bias & Order Flow (Direção Macro)

O Daily Bias (Viés Diário) é o mapa direcional do Super Agente. Operar contra o Bias diário é a causa número um de perdas operacionais. A IA deve alinhar os gráficos intraday (M15/M5/M1) estritamente na direção do fluxo macro de ordens (D1/H4).

---

## 1. Como Determinar o Daily Bias (Olhar Clínico HTF)
O Bias diário não é determinado por médias móveis ou indicadores atrasados, mas sim pela estrutura pura do preço nos gráficos Diário (D1) e de 4 Horas (H4):

1. **Estrutura de Swing (Market Structure)**: Identificar se o preço está fazendo topos e fundos descendentes (Bullish) ou ascendentes (Bearish) no gráfico D1.
2. **Mitigação de Blocos (PD Arrays)**:
   - Se o preço está ativamente mitigando FVGs e Order Blocks de **Alta** e rompendo topos, o viés é **Bullish** (Alta).
   - Se o preço está ativamente mitigando FVGs e Order Blocks de **Baixa** e rompendo fundos, o viés é **Bearish** (Baixa).
3. **Draw on Liquidity (O Ímã do Preço)**: Identificar qual é a liquidez pendente mais próxima no gráfico de H4 ou D1. O preço se moverá como um ímã em direção aos stops de topos anteriores (BSL) ou stops de fundos anteriores (SSL).

---

## 2. Regra de Confluência Multi-Timeframe (M-T-F)
A IA deve cruzar a informação direcional dos diferentes tempos gráficos de forma rígida antes de acionar qualquer ordem:

```
[D1 / H4]   -----------------> Determina a DIREÇÃO (Daily Bias / Draw on Liquidity)
   |
[H1 / M15]  -----------------> Determina a ESTRUTURA LOCAL (MSS e Mitigação de FVGs)
   |
[M5 / M1]   -----------------> Determina o GATILHO (Entrada e cálculo de SL curto)
```

> [!WARNING]
> **Filtro de Contratendência**: Se o Daily Bias for **Bullish**, a IA está **terminantemente proibida** de aceitar sinais de SELL (Venda), mesmo que apareça um MSS de baixa no gráfico de 1 minuto! Ela deve apenas esperar o preço retornar às zonas de Desconto do D1/H4 para comprar.

---

## 3. Checklist de Identificação de Bias
- [ ] O preço está em tendência estrutural de alta no D1/H4?
- [ ] O preço mitigou recentemente um PD Array de desconto (suporte institucional)?
- [ ] A liquidez pendente mais atraente (Draw on Liquidity) está acima do preço atual?
- **Resultado**: Se todas forem SIM, o Bias é **BULLISH**. Focar apenas em compras!


---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Algoritmo_IPDA_e_Ciclos_Tempo|Algoritmo IPDA & Ciclos]]
- [[B03 Regras ICT/Silver_Bullet_Algoritmica|Silver Bullet Algorítmica]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OrderBlocks_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Liquidity_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]