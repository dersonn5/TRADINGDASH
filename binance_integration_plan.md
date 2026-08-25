# Plano de Integração - Binance Testnet (Futuros)

Este documento descreve o plano de implementação completo para integrar o suporte à **Binance Testnet (Futuros)** no robô **Trading AI**. O foco desta integração é obter dados de altíssima qualidade (3 anos de histórico) e rodar testes de robustez definitivos em ambientes reais de mercado sem a necessidade de KYC.

---

## 📋 Resumo da Estrutura (5 Arquivos Novos)

| Arquivo | Função / Responsabilidade |
| :--- | :--- |
| **`execution/binance_client.py`** | Factory CCXT — Configura e instancia o cliente REST e WebSocket conectado à **Binance Futures Testnet**. |
| **`data/binance_data_provider.py`** | Buffer de candles com bootstrap REST inicial e sincronização contínua via WebSocket (`watch_ohlcv`). |
| **`execution/binance_executor.py`** | Executor de ordens — Traduz o tamanho de risco USD em contratos de futuros Binance e coloca ordens via API. |
| **`live_daemon_binance.py`** | Daemon principal — Gerencia o loop de execução WebSocket, avaliando as estratégias a cada candle M5 fechado. |
| **`backtesting/binance_historical_loader.py`**| Utilitário de dados — Baixa 3 anos completos de candles M5 de `BTC` e `ETH` para backtests robustos. |

---

## 🛠️ 1. Configuração e Setup (Sem KYC)

Uma das maiores vantagens da Binance Futures Testnet é a facilidade de acesso para desenvolvedores:

1.  Acesse: **[testnet.binancefuture.com](https://testnet.binancefuture.com)**
2.  Faça login utilizando sua conta do **GitHub**.
3.  Gere e copie suas credenciais de teste: **API Key** e **Secret Key**.
4.  Abra o arquivo `.env` do seu projeto e adicione as chaves:
    ```env
    # BINANCE FUTURES TESTNET
    BINANCE_TESTNET_API_KEY="sua_api_key_testnet_aqui"
    BINANCE_TESTNET_SECRET="seu_api_secret_testnet_aqui"
    ```

---

## 📊 2. Download e Importação de Dados Históricos

O script `backtesting/binance_historical_loader.py` será responsável por baixar aproximadamente **300.000 candles de M5** de `BTC/USDT` e `ETH/USDT` correspondentes aos anos de 2022, 2023 e 2024.

```powershell
python backtesting/binance_historical_loader.py
```

### O Poder da Validação Multi-Regime (3 Anos):
Testar a estratégia de trading nesses 3 anos oferece uma comprovação estatística irrefutável de sua robustez:
*   **2022 (Bear Market):** Mercado em forte tendência de baixa, ideal para testar setups de venda e proteção de capital.
*   **2023 (Recovery Market):** Fase lateralizada e de recuperação, testando a sensibilidade aos falsos rompimentos (*fakeouts*).
*   **2024 (Bull Market):** Forte tendência de alta, excelente para maximizar lucros em setups de compra e expansões de preço.

> [!TIP]
> Se o modelo algorítmico (ICT ou ORB) for lucrativo e mantiver um **Profit Factor robusto nos 3 regimes**, o edge matemático do sistema está estatisticamente confirmado.

---

## 🚀 3. Roteiro e Ordem de Execução para a Próxima IDE

Quando for iniciar a integração com a Binance na outra IDE, siga este roteiro exato:

1.  **Instalar Dependências:**
    ```powershell
    pip install "ccxt[pro]>=4.4.0"
    ```
2.  **Configurar Credenciais:** Criar conta demo em [testnet.binancefuture.com](https://testnet.binancefuture.com) e salvar as credenciais no `.env`.
3.  **Desenvolver os 5 arquivos** listados na tabela de estrutura acima.
4.  **Validar Conectividade Pública:**
    ```powershell
    python -c "import ccxt; print(ccxt.binance().fetch_ohlcv('BTC/USDT:USDT', '5m', limit=3))"
    ```
5.  **Baixar Histórico de 3 Anos:** Rodar o carregador histórico para alimentar a base de dados local.
6.  **Rodar Backtest Definitivo:** Executar o motor de backtest com a massa de dados reais de 2022-2024 (almejando uma amostra expressiva de `n >= 100` trades).
7.  **Iniciar Operação em Simulador:**
    ```powershell
    python live_daemon_binance.py
    ```
