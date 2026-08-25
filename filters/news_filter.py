from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd

class NewsFilter:
    """
    Filtro de Calendário Econômico.
    Evita operar +/- 30 minutos antes e depois de eventos macroeconômicos de alto impacto
    (ex: FOMC, CPI, NFP, PPI, GDP, Payrolls) que causam slippage severa e manipulações.
    """
    # Eventos de alto impacto canônicos a monitorar
    HIGH_IMPACT_KEYWORDS = ["FOMC", "CPI", "NFP", "NON-FARM PAYROLL", "INTEREST RATE", "DECISION", "PPI", "GDP", "INITIAL JOBLESS CLAIMS", "RETAIL SALES"]

    def __init__(self):
        self.news_cache: List[Dict] = []

    def load_simulated_news(self, news_events: List[Dict]):
        """Carrega notícias simuladas para testes e backtesting"""
        self.news_cache = news_events

    def is_news_time(self, current_time: datetime, buffer_minutes: int = 30) -> bool:
        """
        Retorna True se estiver na janela crítica de +/- buffer_minutes minutos
        de qualquer notícia de alto impacto programada.
        """
        for event in self.news_cache:
            event_time = event.get("timestamp")
            if not isinstance(event_time, datetime):
                event_time = pd.to_datetime(event_time)
            
            # Garantir alinhamento de timezones
            if current_time.tzinfo is not None and event_time.tzinfo is None:
                event_time = event_time.tz_localize(current_time.tzinfo)
            elif current_time.tzinfo is None and event_time.tzinfo is not None:
                event_time = event_time.tz_localize(None)
                
            # Verificar se a notícia é de alto impacto
            impact = event.get("impact", "LOW").upper()
            headline = event.get("headline", "").upper()
            
            is_high_impact = impact == "HIGH" or any(kw in headline for kw in self.HIGH_IMPACT_KEYWORDS)
            
            if is_high_impact:
                time_diff = abs((current_time - event_time).total_seconds()) / 60.0
                if time_diff <= buffer_minutes:
                    return True
                    
        return False
