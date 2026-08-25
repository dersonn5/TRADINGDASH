# 🧬 Nota Mestra: Metodologia Quantitativa de Marcos López de Prado

Este documento codifica e eterniza os princípios de rigor quantitativo e combate ao **Overfitting** extraídos do livro *Advances in Financial Machine Learning (AFML)* de **Marcos López de Prado**, implementados em nosso motor de backtest (`core/backtester.py`).

---

## 1. O Filtro de Independência Estatística: Purging & Embargo (Capítulo 7)
Em finanças, a sobreposição temporal de operações cria **correlação serial de dados**. Se abrirmos ordens sequenciais sem um intervalo mínimo, os resultados serão artificialmente inflados, induzindo o robô ao erro de excesso de confiança.

### As Regras Implementadas:
*   **O Embargo Cronológico (Trade Cooldown)**: 
    *   Definido um intervalo mínimo de **2 horas** após o encerramento de qualquer operação.
    *   Durante esta janela de embargo, o algoritmo rejeita e descarta automaticamente qualquer sinal técnico, neutralizando a autocorrelação de ruído de mercado.
*   **O Purging Temporal**:
    *   Eliminação de quaisquer dados ou rótulos de testes que compartilhem informações da mesma janela de volatilidade macro.

---

## 2. O Estressor de Vizinhança & Degradação de Execução (Capítulo 11)
A expectativa matemática de um trading system em tela (ideal) nunca é idêntica à realidade da corretora. Para provar que uma estratégia é estatisticamente robusta para receber capital real, ela deve ser degradada de forma severa em uma "vizinhança desfavorável" de parâmetros.

### Os Algoritmos de Perturbação:
1.  **Neighborhood Slippage Check (Deslizamento Controlado)**:
    *   **Ativos de Commodities (Ouro)**: Injeção de uma penalidade aleatória de **2 a 5 ticks** desfavoráveis no preço de entrada e saída.
    *   **Ativos de Índices (Nasdaq)**: Injeção de **6 a 12 ticks** desfavoráveis.
    *   *Recálculo Dinâmico:* O TP (Take Profit) é encolhido e o SL (Stop Loss) é expandido. Se o ganho final cair e o risco subir, a relação R:R original é degradada em tempo real.
2.  **Latency Drift (Desvio de Atraso)**:
    *   Simulação de latência de rede e processamento da API de **4 segundos**. Se o preço andar contra o trade nesses 4 segundos, o pior preço possível de execução é assumido.

---

## 3. Matriz de Robustez de Performance: Ideal vs. Estressado
A validação final de consistência segue a regra da **Expectativa Positiva Estressada**:

$$\text{Expectativa Matematica Estressada} = (\text{Win Rate} \times \text{Average Win Estressado}) - (\text{Loss Rate} \times \text{Average Loss Estressado})$$

### Filtro de Validação:
*   **APROVADO**: Se a Expectativa Matemática Estressada permanecer maior que zero ($PnL > 0$), a estratégia possui **robusteza quantitativa real** e está autorizada a operar em conta real.
*   **REPROVADO**: Se o PnL estressado ficar negativo, a estratégia é classificada como **Overfitted** (uma ilusão estatística do passado que quebrará em tempo real). O cérebro RAG rejeitará a implantação.

---

## 4. Como a IA RAG Aplica Este Conhecimento
1.  Antes de sugerir qualquer otimização ou alteração técnica nos arquivos de regras, a IA lê este documento.
2.  Ela está estritamente proibida de propor otimizações baseadas em "ajuste perfeito" de curvas (ex: mudar parâmetros de Fibonacci para coincidir com apenas um caso do passado).
3.  Toda e qualquer mudança deve ser validada sob o estressor de vizinhança para garantir que a robustez seja mantida.

---

---

## 🔗 Conexões Neurais
- [[Cerebro_ICT]]
- [[B03 Regras ICT/Gestao_de_Trade_e_Parciais|Gestão de Trade & Parciais]]
- [[C02 Licoes Aprendidas/Erros_Evitar|Lições Aprendidas & Erros]]
- [[B03 Regras ICT/Daily_Bias_e_Order_Flow]]
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]