import time
from datetime import datetime, timedelta

def get_date_30_days_ago() -> str:
    """Retorna a data de 30 dias atrás no formato DDMMYYYY"""
    date_30_days_ago = datetime.today() - timedelta(days=30)
    return date_30_days_ago.strftime("%d/%m/%Y").replace('/', '')

def safe_wait(seconds: int):
    """Wait com tratamento de erro"""
    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        raise
    except:
        pass

def validate_credentials(email: str, password: str) -> bool:
    """Valida se as credenciais têm formato básico"""
    return '@' in email and len(password) >= 3