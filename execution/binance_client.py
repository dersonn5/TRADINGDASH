"""
Factory de exchange Binance Futures via CCXT.
- ccxt.binance: REST puro (bootstrap histórico)
- ccxt.pro.binance: REST + WebSocket (daemon ao vivo)
Demo: URLs manuais para demo-fapi.binance.com (set_sandbox_mode aponta pro testnet bloqueado).
"""
import ccxt
import ccxt.pro as ccxtpro
from dataclasses import dataclass

_DEMO_BASE = 'https://demo-fapi.binance.com'

_DEMO_URLS = {
    'fapiPublic':    f'{_DEMO_BASE}/fapi/v1',
    'fapiPublicV2':  f'{_DEMO_BASE}/fapi/v2',
    'fapiPublicV3':  f'{_DEMO_BASE}/fapi/v3',
    'fapiPrivate':   f'{_DEMO_BASE}/fapi/v1',
    'fapiPrivateV2': f'{_DEMO_BASE}/fapi/v2',
    'fapiPrivateV3': f'{_DEMO_BASE}/fapi/v3',
    'fapiData':      f'{_DEMO_BASE}/futures/data',
    # Redireciona sapi para demo-fapi para evitar chamadas ao api.binance.com real
    'sapi':          f'{_DEMO_BASE}/sapi/v1',
}


@dataclass
class BinanceConfig:
    api_key: str
    api_secret: str
    paper_trading: bool = True  # SEMPRE True até validar edge real


def make_binance(config: BinanceConfig, pro: bool = False):
    """
    Cria instância Binance CCXT.
    pro=True → ccxt.pro (WebSocket + REST)
    pro=False → ccxt (REST apenas, mais leve para bootstrap)
    """
    params = {
        'apiKey': config.api_key,
        'secret': config.api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
        },
    }

    cls = ccxtpro.binance if pro else ccxt.binance
    exchange = cls(params)

    if config.paper_trading:
        api_urls = exchange.urls.setdefault('api', {})
        for key, url in _DEMO_URLS.items():
            api_urls[key] = url
        # Só mercados linear — evita bater em api.binance.com
        exchange.options['fetchMarkets'] = ['linear']
        # Desabilita fetchCurrencies que chama sapi/v1/capital/config/getall no api.binance.com real
        exchange.options['fetchCurrencies'] = False
        exchange.options['adjustForTimeDifference'] = True

    return exchange
