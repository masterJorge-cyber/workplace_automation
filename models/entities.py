from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class Invoice:
    """Representa uma nota fiscal"""
    numero_nota: str  # Número da nota fiscal sendo pesquisada
    data: Dict[str, str]  # Dados extraídos
    
    @property
    def is_rejected(self) -> bool:
            return "Rejeitado" in self.data.get('col_7', '')
    
    @property
    def is_pending(self) -> bool:
        return "Pendente" in self.data.get('col_7', '')
    
    @property
    def status(self) -> str:
        status_text = self.data.get('col_7', '')
        if "Rejeitado" in status_text:
            return "Rejeitado"
        elif "Pendente" in status_text:
            return "Pendente"
        else:
            return "Aprovado"

@dataclass
class ScrapingResult:
    """Resultado do processo de scraping para uma nota fiscal"""
    nota_fiscal: str
    metadata: Dict[str, Any]
    invoices: List[Invoice]  # Pode ter múltiplas linhas/resultados
    total_invoices: int
    rejected_count: int
    
    def __post_init__(self):
        self.rejected_count = len([inv for inv in self.invoices if inv.is_rejected])

@dataclass
class BatchScrapingResult:
    """Resultado do processamento em lote"""
    resultados: List[ScrapingResult]
    total_notas_processadas: int
    notas_com_erro: List[str]
    
    @property
    def total_notas_rejeitadas(self) -> int:
        return sum(1 for result in self.resultados if result.rejected_count > 0)
    
    @property
    def total_registros_encontrados(self) -> int:
        return sum(result.total_invoices for result in self.resultados)