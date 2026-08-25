"""
Script utilitário para baixar dados históricos de futuros da Binance.
Salva diretamente em formato Parquet no diretório de cache do projeto,
garantindo compatibilidade com o DataLoader existente do backtester.
"""
import os
import sys
import argparse
import time
from pathlib import Path
import pandas as pd
import ccxt


def load_historical_data(symbol: str, timeframe: str, start_date: str, end_date: str):
    # Usamos o cliente público da Binance (sem chaves necessárias para dados públicos de K-lines)
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
        }
    })
    
    since = exchange.parse8601(start_date)
    end_ts = exchange.parse8601(end_date)
    
    print(f"[LOADER] Iniciando download histórico de {symbol} ({timeframe})")
    print(f"[LOADER] Período: {start_date} até {end_date}")
    
    all_candles = []
    limit = 1000
    
    while since < end_ts:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not ohlcv:
                print("[LOADER] Nenhum candle retornado. Fim do histórico disponível no servidor.")
                break
                
            all_candles.extend(ohlcv)
            print(f"[LOADER] Baixados {len(ohlcv)} candles. Total acumulado: {len(all_candles)} | Último: {exchange.iso8601(ohlcv[-1][0])}")
            
            # Atualiza since para o próximo lote para evitar duplicações
            since = ohlcv[-1][0] + 1
            
            # Se retornou menos que o limite, chegamos ao momento atual
            if len(ohlcv) < limit:
                break
                
            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"[LOADER ERROR] Erro na requisição: {e}. Aguardando 5s antes de re-tentar...")
            time.sleep(5)
            
    if not all_candles:
        print("[LOADER ERROR] Nenhum dado pôde ser recuperado da Binance.")
        return
        
    df = pd.DataFrame(all_candles, columns=["ts", "open", "high", "low", "close", "volume"])
    # Filtrar qualquer candle que ultrapasse a data limite final solicitada
    df = df[df["ts"] <= end_ts]
    
    # Formata a coluna timestamp e configura como índice da série temporal
    df["timestamp"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = df.set_index("timestamp").drop(columns=["ts"])
    
    # Salvar no diretório de cache local do DataLoader do projeto
    cache_dir = Path(__file__).resolve().parent.parent / "data" / "cached"
    safe_symbol = symbol.replace(":", "_").replace("^", "_").replace("=", "_")
    cache_file = cache_dir / f"{safe_symbol}_{timeframe}.parquet"
    
    # Cria o diretório de cache de forma recursiva (resolve o problema do caractere '/' do CCXT no Windows)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(cache_file)
    
    print(f"[LOADER SUCCESS] Salvo com sucesso {len(df)} candles de {symbol} em {cache_file}!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download de histórico da Binance para Backtest")
    parser.add_argument("--symbol", type=str, default="BTC/USDT:USDT", help="Símbolo no formato CCXT (ex: BTC/USDT:USDT)")
    parser.add_argument("--timeframe", type=str, default="5m", help="Timeframe (1m, 5m, 15m, 1h, 1d)")
    parser.add_argument("--start", type=str, default="2022-01-01T00:00:00Z", help="Data início ISO8601")
    parser.add_argument("--end", type=str, default="2024-12-31T23:59:59Z", help="Data fim ISO8601")
    
    args = parser.parse_args()
    load_historical_data(args.symbol, args.timeframe, args.start, args.end)
