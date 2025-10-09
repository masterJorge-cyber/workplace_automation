import os
from dataclasses import dataclass
from typing import List

@dataclass
class ProxyConfig:
    host: str = "10.141.6.12"
    port: int = 80

@dataclass
class Credentials:
    email: str
    password: str
    monitor_user: str
    monitor_password: str

@dataclass
class AppConfig:
    proxy: ProxyConfig
    credentials: Credentials
    notas_fiscais: List[str]
    headless: bool = True
    timeout: int = 60000
    slow_mo: int = 100
    fluxo: int = 1  # ← NOVO: 1 = Unisys, 2 = Sefaz
    
    @classmethod
    def from_env(cls):
        notas_env = os.getenv('NOTAS_FISCAIS', '')
        if notas_env:
            notas_fiscais = [nf.strip() for nf in notas_env.split(',')]
        else:
            chave_unica = os.getenv('CHAVE_NOT', '')
            notas_fiscais = [chave_unica] if chave_unica else []
        
        return cls(
            proxy=ProxyConfig(
                host=os.getenv('PROXY_HOST', '10.141.6.12'),
                port=int(os.getenv('PROXY_PORT', '80'))
            ),
            credentials=Credentials(
                email=os.getenv('EMAIL'),
                password=os.getenv('PASSWORD'),
                monitor_user=os.getenv('MONITOR_USER'),
                monitor_password=os.getenv('MONITOR_PASSWORD')
            ),
            notas_fiscais=notas_fiscais,
            headless=os.getenv('HEADLESS', 'true').lower() == 'true',
            slow_mo=int(os.getenv('SLOW_MO', '100')),
            fluxo=int(os.getenv('FLUXO', '1'))  # ← NOVO
        )