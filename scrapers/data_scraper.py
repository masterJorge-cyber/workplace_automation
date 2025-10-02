import time
import pandas as pd
from typing import List, Dict, Any
from playwright.sync_api import Page

class DataScraper:
    def __init__(self, page: Page):
        self.page = page
    
    def scrape_metadata(self, max_retries: int = 5) -> Dict[str, Any]:
        """Coleta metadados da página com retry"""
        for attempt in range(max_retries):
            try:
                metadados = {
                    'title': self.page.title(),
                    'url': self.page.url,
                    'meta': {}
                }
                
                metatags = self.page.query_selector_all("meta")
                for meta in metatags:
                    name = meta.get_attribute("name")
                    content = meta.get_attribute("content")
                    if name:
                        metadados['meta'][name] = content
                
                return metadados
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Não foi possível capturar os metadados: {e}")
                time.sleep(1)
    
    def scrape_invoices(self) -> List[Dict[str, str]]:
        """Extrai dados das notas fiscais da tabela"""
        self.page.wait_for_selector("div.t-grid-content table tbody tr")
        linhas = self.page.query_selector_all("div.t-grid-content table tbody tr")
        notas = []
        
        for idx, linha in enumerate(linhas):
            colunas = linha.query_selector_all("td")
            if not colunas:
                continue
            
            nota = {f"col_{i}": colunas[i].inner_text().strip() for i in range(len(colunas))}
            notas.append(nota)
        
        return notas
    
    def normalize_dataframe(self, notas: List[Dict[str, str]], num_columns: int = 20) -> pd.DataFrame:
        """Normaliza os dados em um DataFrame"""
        linhas_normalizadas = []
        for nota in notas:
            linha = [nota.get(f"col_{i}", "") for i in range(num_columns)]
            linhas_normalizadas.append(linha)
        
        colunas = [f"col_{i}" for i in range(num_columns)]
        return pd.DataFrame(linhas_normalizadas, columns=colunas)
    
    def filter_rejected_invoices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra notas rejeitadas ou pendentes"""
        return df[df['col_7'].str.contains("Rejeitado|Pendente", na=False)]