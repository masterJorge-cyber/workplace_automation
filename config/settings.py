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
    notas_fiscais: List[str]  # Agora é uma lista
    headless: bool = False
    timeout: int = 30000
    
    @classmethod
    def from_env(cls):
        """Carrega configurações de variáveis de ambiente"""
        # Carrega a lista de notas fiscais do environment
        notas_env = os.getenv('NOTAS_FISCAIS', '')
        if notas_env:
            notas_fiscais = [nf.strip() for nf in notas_env.split(',')]
        else:
            # Fallback para uma nota única (compatibilidade)
            chave_unica = os.getenv('CHAVE_NOT', '33250947508411264641551100000702955335309202')
            notas_fiscais = [chave_unica]
        
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
            headless=os.getenv('HEADLESS', 'false').lower() == 'true'
        )