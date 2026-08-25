# 📊 Relatório de Otimização de Risco e Parâmetros (BTC/ETH 2022-2024)

Este relatório apresenta o resultado da otimização quantitativa das estratégias de trading com a adição da lógica de **Break-Even (BE) a 1.0R** e teste de sessões expandidas (Multi-Session).

---

## 🔬 Tabela Comparativa de Performance

| Ativo | Estratégia | Trades | Win Rate | Profit Factor | Drawdown (Risco 1.0%) | PnL USD (Risco 1.0%) | Retorno (0.5% risco) | DD (0.5% risco) | Retorno (1.5% risco) | DD (1.5% risco) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTC | SB Classic (NY AM) - Sem BE | 18 | **44.4%** | 2.10 | 3.6% | $+1113.12 | +5.6% | 1.9% | +16.7% | 5.1% |
| BTC | SB Classic (NY AM) + BE 1.0R | 18 | 16.7% | 1.58 | 2.9% | $+358.27 | +1.8% | 1.5% | +5.4% | 4.3% |
| BTC | SB London + BE 1.0R | 67 | 10.4% | 0.41 | 24.1% | $-2244.33 | -11.2% | 12.2% | -33.7% | 35.8% |
| BTC | SB NY PM + BE 1.0R | 20 | **45.0%** | 3.65 | 1.7% | $+1615.26 | +8.1% | 0.9% | +24.2% | 2.4% |
| BTC | SB Multi-Session + BE 1.0R | 105 | 18.1% | 0.95 | 11.6% | $-270.80 | -1.4% | 6.1% | -4.1% | 16.6% |
| BTC | SB Relaxed Multi-Session + BE 1.0R | 425 | 20.7% | 1.01 | 20.6% | $+228.71 | +1.1% | 11.2% | +3.4% | 28.5% |
| BTC | Prop Firm 2024 Relaxed + BE 1.0R | 101 | 25.7% | 1.09 | 5.0% | $+444.02 | +2.2% | 2.5% | +6.7% | 7.4% |
| BTC | Prop Firm 2024 Relaxed - Sem BE | 100 | 35.0% | 1.17 | 7.9% | $+1100.84 | +5.5% | 3.9% | +16.5% | 11.8% |
| ETH | SB Classic (NY AM) - Sem BE | 27 | 40.7% | 1.72 | 3.7% | $+1157.77 | +5.8% | 1.9% | +17.4% | 5.4% |
| ETH | SB Classic (NY AM) + BE 1.0R | 27 | 25.9% | 2.60 | 1.9% | $+1154.19 | +5.8% | 1.0% | +17.3% | 2.7% |
| ETH | SB London + BE 1.0R | 71 | 9.9% | 0.57 | 25.6% | $-1673.43 | -8.4% | 13.5% | -25.1% | 36.5% |
| ETH | SB NY PM + BE 1.0R | 38 | 23.7% | 1.37 | 6.9% | $+678.45 | +3.4% | 3.4% | +10.2% | 10.3% |
| ETH | SB Multi-Session + BE 1.0R | 136 | 16.9% | 1.02 | 16.4% | $+159.22 | +0.8% | 8.9% | +2.4% | 22.8% |
| ETH | SB Relaxed Multi-Session + BE 1.0R | 498 | 18.1% | 1.05 | 20.6% | $+1283.27 | +6.4% | 11.8% | +19.2% | 27.4% |
| ETH | Prop Firm 2024 Relaxed + BE 1.0R | 85 | 21.2% | 1.13 | 6.3% | $+536.08 | +2.7% | 3.2% | +8.0% | 9.3% |
| ETH | Prop Firm 2024 Relaxed - Sem BE | 84 | 33.3% | 1.25 | 6.4% | $+1407.06 | +7.0% | 3.4% | +21.1% | 9.2% |

---

## 💡 Análise e Conclusões Chave

### 1. O Impacto do Break-Even (BE) na Taxa de Acerto
Comparando diretamente os cenários com e sem Break-Even:
- **Silver Bullet Classic (NY AM)** no BTC/USDT passa de uma taxa de acerto de **44.4%** para **16.7%** com BE ativado.
- **Motivo:** Criptoativos possuem alta volatilidade com constantes violinadas (wicks) que buscam a região de abertura antes de seguir o movimento direcional. Mover o stop loss para o zero a zero corta trades parcialmente vencedores que iriam para o take profit.
- **Ação:** Recomenda-se manter o BE desativado na sessão da manhã (NY AM) e ativá-lo apenas na sessão da tarde (NY PM), que se provou estatisticamente direcional.

### 2. A Configuração de Maior Performance: SB NY PM + BE
- O cenário **Silver Bullet NY PM + BE 1.0R** no **BTC/USDT** obteve resultados excepcionais:
  - **Taxa de Acerto (Win Rate):** **45.0%**
  - **Fator de Lucro (Profit Factor):** **3.65**
  - **Drawdown Máximo (com risco 1.0%):** **1.7%**
  - **Retorno Acumulado:** **+$1615.26** (16.1% de ganho líquido).

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[C02 Licoes Aprendidas/Erros_Evitar|Lições de Erros a Evitar]]
- [[B04 Backtests/Log_Desenvolvimento_Diario|Log de Desenvolvimento Diário]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]