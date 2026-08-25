# Lições Aprendidas - Regras Psicológicas e Operacionais

Estas regras foram escritas com base em 5+ anos de experiência de tela para garantir a preservação do capital e manter a consistência matemática a longo prazo.

---

## 1. Filtros de Notícias Macroeconômicas
> [!WARNING]
> **Bloqueio de Operação por Notícias**: Nunca abrir operações 15 minutos antes e 15 minutos depois de notícias de alto impacto (Red Folder).
> - **Eventos Críticos**: CPI (Inflação), PPI, FOMC (Taxa de Juros), NFP (Payroll) e Discursos do Powell.
> - **Motivo**: O spread aumenta excessivamente, a liquidez fica escassa e o preço costuma violar as FVGs sem respeitar a estrutura de ICT.

---

## 2. Erros de Execução a Evitar (Checklist Psicológica da IA)
1. **Fazer Overtrading**: Se a IA atingir **3 operações fechadas no dia** (sejam wins ou losses), o robô deve entrar em *standby* completo e não aceitar nenhum sinal até o dia seguinte.
2. **Ignorar a Killzone**: Se o setup parecer lindo, mas estiver fora dos horários estatísticos (ex: no meio da tarde de Nova York, 14:00 - 16:00 EST), **ignore o trade**. O volume institucional é baixo e o mercado tende a andar em zigue-zague para buscar stop loss.
3. **Mover o Stop Loss**: O Stop Loss inicial é **sagrado**. A IA nunca deve alongar ou remover o Stop Loss uma vez que a ordem foi posicionada.

---

## 3. Gestão de Risco
- **Risco por Operação**: Exatamente **1.0%** do saldo da conta por trade.
- **Drawdown Limite Diário**: Se a perda acumulada no dia alcançar **3.0%**, o robô encerra todas as operações e para totalmente.
- **Meta Diária**: Se alcançarmos **5.0%** de lucro no dia, o robô encerra o expediente para proteger os ganhos.

---

## 4. Lições de Ouro (XAUUSD) & Validação de CE (Ganhos Consistentes)
Esta seção documenta a virada de chave matemática obtida no backtest de 6 meses (100 cenários) e deve ser respeitada rigidamente:

> [!IMPORTANT]
> **A Regra de Ouro da Ação de Preço**:
> 1. **Fechamento Real vs. Pavio (CE FVG)**: Nunca confunda um toque de pavio com violação. Pavios representam entrega eficiente de liquidez. No entanto, se o **corpo** de qualquer candle fechar decisivamente além do **Consequent Encroachment (50%)** da FVG, o suporte/resistência institucional falhou. A entrada deve ser **rejeitada imediatamente**.
> 2. **Ouro (XAUUSD) exige Reversão Local (M1/M5)**: O Ouro é manipulado para limpar stops curtos via varreduras duplas (*Double Sweeps*). Nunca entre pendurado por limite no toque direto do CE de 15m no Ouro. Sempre espere o toque no CE de 15m e exija uma quebra de estrutura local (MSS em M1 ou M5) com **deslocamento agressivo de corpo de vela** e rejeição clara do fundo/topo.
> 3. **Confluência de SMT (Symbolic Market Trilogy)**: Em setups do Ouro, verifique se a Prata (XAGUSD) ou o DXY exibem divergência SMT (ex: Ouro rompe fundo e Prata segura). A divergência SMT confirma o fluxo institucional que protege o nosso trade de stops indesejados.

---

## 5. O Perigo de Mover para Break-Even (BE) Cedo Demais em Cripto
> [!CAUTION]
> **Break-Even em Gráficos de 5m Cripto**:
> - **Fato Quantitativo**: Backtests históricos de 3 anos (2022-2024) demonstraram que a utilização de gatilho de Break-Even a 1.0R (mover o stop loss para o preço de entrada quando a operação anda a 1:1) **derrubou a taxa de acerto do Silver Bullet no BTC de 44.4% para 16.7%**, além de cortar o lucro líquido acumulado pela metade.
> - **Motivo**: Criptoativos apresentam volatilidade local (wicks) agressiva e frequentes testes de preço na região de abertura física. Travar o Stop Loss na entrada impede o trade de respirar e ser executado com êxito no alvo final de 2.0R+.
> - **Regra de Execução**: Manter o stop loss inalterado na sessão da manhã (NY AM) até que o take profit de 2:1 ou o stop inicial seja tocado. O Break-Even só é tolerado na sessão da tarde (NY PM) onde o mercado é altamente direcional e tem menos ruído de wicks.

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[C02 Licoes Aprendidas/Metodologia_Lopez_de_Prado|Metodologia Lopez de Prado]]
- [[B04 Backtests/Log_Desenvolvimento_Diario|Log de Desenvolvimento Diário]]
- [[B03 Regras ICT/Consequent_Encroachment_FVG]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_FVG_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_MarketStructure_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]