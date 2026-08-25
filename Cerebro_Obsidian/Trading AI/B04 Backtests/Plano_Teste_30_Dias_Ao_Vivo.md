# 📅 Plano de Teste de 30 Dias ao Vivo (Ambiente Simulado)

Este documento estabelece o protocolo operacional, a infraestrutura e o cronograma para o **Teste de 30 Dias ao Vivo em Ambiente Simulado** (Paper Trading) do seu Cérebro de Trading Cognitivo ICT. 

Durante este período, o robô operará de forma autônoma nas janelas de alta liquidez (**Killzones**), avaliando setups através da IA Gemini, confrontando as regras técnicas no Obsidian e registrando os relatórios de trading.

---

## 🛠️ 1. Checklist de Configuração Rápida

Para garantir a fidelidade matemática do teste de 30 dias, execute as seguintes calibrações:

### 1.1 Ajuste do Saldo da Conta de Simulação (`.env`)
No arquivo [`.env`](file:///e:/AUTOMA%C3%87%C3%83O%20IA/TRADING%20AI/.env), recomendamos ajustar a variável `ACCOUNT_BALANCE` para **`10000.0`** (ou o saldo real de sua preferência).
*   **Por que isso é necessário?**
    *   Com uma conta de `$100.00`, o risco de 1% é de apenas `$1.00`.
    *   No Ouro (XAUUSD), a menor posição permitida (0.01 lotes) oscila `$1.00` por dólar. Se o seu stop loss técnico for de `$2.00` de largura, o risco real da menor operação será de `$2.00` (2% da conta), violando a regra estrita de 1% de risco. O `RiskManager` seria forçado a rejeitar a entrada.
    *   Com uma conta simulada de **`$10.000.00`**, seu risco de 1% é de **`$100.00`**. Um stop loss de `$2.00` de largura no Ouro permite calcular um lote perfeito de **0.50 lotes** (`$2.00 * 0.50 * 100 = $100.00`), garantindo simulações de lotes realistas e estatísticas consistentes.

### 1.2 Configuração das Variáveis no `.env`
Certifique-se de que o seu arquivo [`.env`](file:///e:/AUTOMA%C3%87%C3%83O%20IA/TRADING%20AI/.env) possui as seguintes linhas ativas:
```ini
EXECUTION_MODE=SIMULATOR
ACCOUNT_BALANCE=10000.0
```

---

## 🕒 2. Grade Horária das Janelas Operacionais (Killzones EST)

O robô está hardcoded para varrer os gráficos e avaliar sinais **apenas** dentro das Killzones oficiais do ICT (horário de Nova York / EST). Certifique-se de manter o daemon rodando nos seguintes períodos:

| Estratégia | Ativo | Janela de Operação (EST) | Horário de Brasília (BRT) |
| :--- | :--- | :--- | :--- |
| **London Sweep XAU** | `XAUUSD` | **02:00 AM - 05:00 AM** | **03:00 AM - 06:00 AM** |
| **Silver Bullet NQ** | `NQ` (USTEC) | **10:00 AM - 11:00 AM** | **11:00 AM - 12:00 PM** |

*   *Nota: O robô converterá automaticamente os timestamps dos feeds (UTC) para EST para garantir a precisão milimétrica da abertura e fechamento da janela.*

---

## 🤖 3. Como Manter o Bot Automatizado 24/7

Para que o teste de 30 dias ocorra sem interrupções manuais, você pode automatizar a inicialização do robô em background no seu Windows.

### Método A: Inicialização Silenciosa ao Ligar o PC (Recomendado)
Criamos um atalho na pasta Startup do seu usuário que inicia o bot silenciosamente em segundo plano sempre que você faz login no Windows:
1. Abra o **PowerShell** no diretório do projeto.
2. Execute o script de inicialização do usuário:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\configurar_inicializacao_usuario.ps1
   ```
3. Pronto! O bot rodará de forma 100% oculta. Os logs do daemon serão gravados em tempo real no arquivo `logs_daemon.txt` na raiz do projeto.

### Método B: Execução Manual com Janela Ativa
Caso prefira acompanhar os logs no terminal em tempo real, basta dar um duplo clique no arquivo:
*   [**`iniciar_bot.bat`**](file:///e:/AUTOMA%C3%87%C3%83O%20IA/TRADING%20AI/iniciar_bot.bat) (Modo MT5)
*   Se preferir usar o feed do TradingView via MCP, edite o bat ou execute:
    ```powershell
    python -X utf8 -m execution.live_daemon --feed MCP --interval 15
    ```

---

## 📊 4. Como Acompanhar e Auditar as Operações

Durante os 30 dias, você poderá auditar o progresso do robô de duas formas integradas:

### 1. Dashboard Web Interativo (FastAPI)
O servidor FastAPI está rodando na porta `8000`. Acesse:
*   👉 **`http://localhost:8000`**
*   Clique no botão **"Operações ao Vivo"** no canto superior direito para ver os dados reais da sua conta simulada de `$10.000.00`.
*   Acompanhe o crescimento do patrimônio, a taxa de acerto e as perdas evitadas em tempo real.
*   Clique em qualquer linha da tabela para abrir o drawer lateral e ler a **Cadeia de Raciocínio (CoT)** da IA e ver o checklist das regras ICT validadas.

### 2. Diário do Obsidian (RAG Central)
Todas as noites após as sessões, abra o seu Obsidian:
*   Navegue até a pasta **`Diario_Trades/`**.
*   Cada decisão tomada pelo bot (seja uma entrada simulada ou um setup bloqueado/evitado) terá um relatório técnico completo em markdown.
*   As notas se conectam dinamicamente ao seu **[[Cerebro_ICT|Núcleo Central]]** e às notas das regras técnicas, expandindo o seu grafo do Obsidian de forma orgânica e visual.

---

## 🎯 5. Critérios de Avaliação de Sucesso (Ao Final dos 30 Dias)

No dia **18 de Junho de 2026**, faremos o fechamento do balanço do teste. O robô será considerado aprovado para avançar para a **Fase 6 (Micro Live com dinheiro real)** se atender aos seguintes requisitos:

1.  **Expectativa Matemática Positiva**: Expectancy maior que `$0.00` por trade.
2.  **Profit Factor Robusto**: Profit Factor total superior a **1.5**.
3.  **Controle de Drawdown**: Rebaixamento máximo da conta (Max Drawdown) menor que **10%** do saldo inicial.
4.  **Taxa de Acerto Realista**: Win rate consistente acima de **40%** (com relação R:R média mínima de 1:2.5).
5.  **Perdas Evitadas**: Confirmação de que o filtro RAG do Obsidian e o Gemini bloquearam com sucesso pelo menos 5 falsos setups em dias de notícias ou mercados laterais.

---
> **"A disciplina é o único gargalo entre o conhecimento e a lucratividade."**  
> Que comecem os 30 dias de teste de consistência autônoma! 🚀

---

## 🔗 Conexões Neurais
- [[B03 Regras ICT/ICT_GestaoRisco_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_Killzones_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_ModelosTrade_YouTube_Distilled]]
- [[B03 Regras ICT/ICT_OTE_YouTube_Distilled]]
