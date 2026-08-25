from datetime import datetime, time
import pandas as pd

class TimeFilter:
    """
    Filtro de Tempo Avançado.
    Valida se as operações ocorrem estritamente dentro das killzones de liquidez de NY e Londres,
    com suporte robusto a fusos horários e horário de verão (DST) dos EUA.
    """
    @staticmethod
    def is_in_killzone(dt: datetime, session: str) -> bool:
        """
        Verifica se o timestamp dt está na killzone correta (EST/EDT).
        session: 'NY_SILVER_BULLET' ou 'LONDON_OPEN' ou 'ASIAN_RANGE'
        """
        if not isinstance(dt, datetime):
            dt = pd.to_datetime(dt)
            
        # Converter para America/New_York
        if dt.tzinfo is None:
            dt_est = dt.tz_localize('UTC').tz_convert('America/New_York')
        else:
            dt_est = dt.tz_convert('America/New_York')
            
        time_only = dt_est.time()
        
        if session == 'NY_SILVER_BULLET':
            # 10:00 AM - 11:00 AM EST
            return time(10, 0) <= time_only < time(11, 0)
        elif session == 'LONDON_OPEN':
            # 02:00 AM - 05:00 AM EST
            return time(2, 0) <= time_only < time(5, 0)
        elif session == 'ASIAN_RANGE':
            # 00:00 AM - 02:00 AM EST
            return time(0, 0) <= time_only < time(2, 0)
            
        return False
