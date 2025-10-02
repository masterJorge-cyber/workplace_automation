import os
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# Importações dos módulos
from config.settings import AppConfig
from auth.authentication import AuthManager
from scrapers.data_scraper import DataScraper
from models.entities import ScrapingResult, Invoice, BatchScrapingResult
from utils.helpers import get_date_30_days_ago, validate_credentials

class NFScraperApp:
    def __init__(self, config: AppConfig):
        self.config = config
        self.auth_manager = AuthManager()
        self.browser = None
        self.context = None
        self.page = None
        self.data_scraper = None
    
    def setup_browser(self):
        """Configura o navegador e contexto"""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.config.headless)
        
        self.context = self.browser.new_context(
            proxy={
                "server": f"http://{self.config.proxy.host}:{self.config.proxy.port}"
            },
            ignore_https_errors=True
        )
        
        self.page = self.context.new_page()
        self.data_scraper = DataScraper(self.page)
    
    def navigate_to_initial_page(self):
        """Navega para a página inicial"""
        self.page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
    
    def perform_login(self):
        """Executa todo o fluxo de login"""
        # Valida credenciais básicas
        if not validate_credentials(self.config.credentials.email, self.config.credentials.password):
            raise ValueError("Credenciais inválidas")
        
        # Login inicial
        self.auth_manager.login_initial(
            self.config.credentials.email,
            self.config.credentials.password
        )
        
        # Login no monitor
        self.auth_manager.login_monitor(
            self.config.credentials.monitor_user,
            self.config.credentials.monitor_password
        )
    
    def search_single_invoice(self, nota_fiscal: str) -> ScrapingResult:
        """Pesquisa uma única nota fiscal e retorna resultados"""
        print(f"🔍 Pesquisando nota fiscal: {nota_fiscal}")
        
        # Navega para tela de pesquisa (só na primeira vez)
        if not hasattr(self, '_search_initialized'):
            self.auth_manager.navigate_to_search()
            self._search_initialized = True
        
        # Preenche formulário com data e nota fiscal específica
        initial_date = get_date_30_days_ago()
        self.auth_manager.fill_search_form(initial_date, nota_fiscal)
        
        # Coleta dados
        metadados = self.data_scraper.scrape_metadata()
        notas_data = self.data_scraper.scrape_invoices()
        
        # Converte para objetos Invoice
        invoices = [Invoice(numero_nota=nota_fiscal, data=nota) for nota in notas_data]
        
        return ScrapingResult(
            nota_fiscal=nota_fiscal,
            metadata=metadados,
            invoices=invoices,
            total_invoices=len(invoices),
            rejected_count=0  # calculado automaticamente
        )
    
    def search_multiple_invoices(self) -> BatchScrapingResult:
        """Pesquisa múltiplas notas fiscais em lote"""
        resultados = []
        notas_com_erro = []
        
        print(f"🚀 Iniciando busca para {len(self.config.notas_fiscais)} notas fiscais...")
        
        for i, nota_fiscal in enumerate(self.config.notas_fiscais, 1):
            try:
                print(f"\n[{i}/{len(self.config.notas_fiscais)}] Processando nota: {nota_fiscal}")
                
                resultado = self.search_single_invoice(nota_fiscal)
                resultados.append(resultado)
                
                # Exibe resultado rápido
                status = "❌ Rejeitada" if resultado.rejected_count > 0 else "✅ Aprovada"
                print(f"   {status} - Encontrados {resultado.total_invoices} registros")
                
                # Pequena pausa entre pesquisas
                if i < len(self.config.notas_fiscais):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Erro na nota {nota_fiscal}: {e}")
                notas_com_erro.append(nota_fiscal)
                continue
        
        return BatchScrapingResult(
            resultados=resultados,
            total_notas_processadas=len(resultados),
            notas_com_erro=notas_com_erro
        )
    
    def display_single_result(self, result: ScrapingResult):
        """Exibe resultados de uma única nota fiscal"""
        if result.total_invoices == 0:
            print(f"   ⚠️  Nenhum registro encontrado para a nota {result.nota_fiscal}")
            return
        
        # Converte para DataFrame para exibição
        notas_dict = [invoice.data for invoice in result.invoices]
        df = self.data_scraper.normalize_dataframe(notas_dict)
        
        print(f"   📊 Registros encontrados: {result.total_invoices}")
        print(f"   ❌ Rejeitados/Pendentes: {result.rejected_count}")
        
        if result.rejected_count > 0:
            rejeitadas = self.data_scraper.filter_rejected_invoices(df)
            print("   🔍 Detalhes das rejeitadas:")
            print(rejeitadas[['col_2', 'col_1', 'col_6', 'col_7', 'col_19']].to_string(index=False))
    
    def display_batch_results(self, batch_result: BatchScrapingResult):
        """Exibe resultados do processamento em lote"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*60)
        
        print(f"✅ Notas processadas com sucesso: {batch_result.total_notas_processadas}")
        print(f"❌ Notas com erro: {len(batch_result.notas_com_erro)}")
        print(f"📊 Total de registros encontrados: {batch_result.total_registros_encontrados}")
        print(f"🚫 Notas com rejeições: {batch_result.total_notas_rejeitadas}")
        
        if batch_result.notas_com_erro:
            print(f"\n📝 Notas com erro: {', '.join(batch_result.notas_com_erro)}")
        
        # Detalhamento por nota
        print("\n" + "-"*40)
        print("DETALHAMENTO POR NOTA FISCAL:")
        print("-"*40)
        
        for resultado in batch_result.resultados:
            status = "❌" if resultado.rejected_count > 0 else "✅"
            print(f"{status} {resultado.nota_fiscal}: {resultado.total_invoices} registros, {resultado.rejected_count} rejeitados")
    
    def run(self):
        """Executa o fluxo completo do scraper"""
        try:
            print("🚀 Iniciando NF Scraper...")
            self.setup_browser()
            self.navigate_to_initial_page()
            self.perform_login()
            
            # Executa busca em lote
            batch_result = self.search_multiple_invoices()
            self.display_batch_results(batch_result)
            
            print("\n✅ Processo concluído com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            raise
        finally:
            input("\n⏎ Pressione Enter para finalizar...")
            self.close()
    
    def close(self):
        """Fecha os recursos do navegador"""
        if self.browser:
            self.browser.close()

def main():
    # Carrega configurações do ambiente
    config = AppConfig.from_env()
    
    # Verifica credenciais
    if not all([
        config.credentials.email,
        config.credentials.password,
        config.credentials.monitor_user,
        config.credentials.monitor_password
    ]):
        print("❌ Erro: Credenciais não encontradas nas variáveis de ambiente")
        print("💡 Crie um arquivo .env com: EMAIL, PASSWORD, MONITOR_USER, MONITOR_PASSWORD")
        return
    
    print(f"📝 Notas fiscais a serem pesquisadas: {len(config.notas_fiscais)}")
    for nf in config.notas_fiscais:
        print(f"   - {nf}")
    
    # Executa a aplicação
    app = NFScraperApp(config)
    app.run()

if __name__ == "__main__":
    main()