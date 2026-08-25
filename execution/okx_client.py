"""
Factory de exchange OKX via CCXT.
- ccxt.okx: REST puro (bootstrap histórico)
- ccxt.pro.okx: REST + WebSocket (daemon ao vivo)
Paper trading: header x-simulated-trading: 1 injetado automaticamente.
"""
import ccxt
import ccxt.pro as ccxtpro
from dataclasses import dataclass


@dataclass
class OKXConfig:
    api_key: str
    api_secret: str
    passphrase: str
    paper_trading: bool = True  # SEMPRE True até validar edge real


def make_okx(config: OKXConfig, pro: bool = False):
    """
    Cria instância OKX CCXT.
    pro=True → ccxt.pro (WebSocket + REST)
    pro=False → ccxt (REST apenas, mais leve para bootstrap)
    """
    params = {
        'apiKey': config.api_key,
        'secret': config.api_secret,
        'password': config.passphrase,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',  # perpetual contracts por padrão
        },
    }
    if config.paper_trading:
        params['headers'] = {'x-simulated-trading': '1'}

    cls = ccxtpro.okx if pro else ccxt.okx
    return cls(params)
