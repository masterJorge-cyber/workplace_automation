import os
import sys
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

# 🔧 CORREÇÃO: Carregar .env de forma explícita
from dotenv import load_dotenv

# Verifica se o .env existe
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    print("❌ ERRO: Arquivo .env não encontrado!")
    print("💡 Verifique se o arquivo .env está na mesma pasta que main.py")
    print(f"📁 Pasta atual: {os.path.dirname(__file__)}")
    print("📁 Arquivos:", [f for f in os.listdir('.') if '.env' in f or f == '.env'])
    sys.exit(1)

load_dotenv(env_path)
print("✅ .env carregado com sucesso!")

# Adiciona o caminho atual ao Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Agora importa os módulos
try:
    from config.settings import AppConfig
    from auth.authentication import AuthManager
    from scrapers.data_scraper import DataScraper
    from models.entities import ScrapingResult, Invoice, BatchScrapingResult
    from utils.helpers import get_date_30_days_ago, validate_credentials
    print("✅ Todos os módulos importados!")
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    sys.exit(1)

class NFScraperApp:
    def __init__(self, config: AppConfig):
        self.config = config
        self.auth_manager = AuthManager()
        self.browser = None
        self.context = None
        self.page = None
        self.data_scraper = None
    
    def setup_browser(self):
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.config.headless)
        
        self.context = self.browser.new_context(
            proxy={"server": f"http://{self.config.proxy.host}:{self.config.proxy.port}"},
            ignore_https_errors=True
        )
        
        self.page = self.context.new_page()
        self.data_scraper = DataScraper(self.page)
    
    def navigate_to_initial_page(self):
        self.page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/")
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
    
    def perform_login(self):
        if not validate_credentials(self.config.credentials.email, self.config.credentials.password):
            raise ValueError("Credenciais inválidas")
        
        self.auth_manager.login_initial(
            self.config.credentials.email,
            self.config.credentials.password
        )
        
        self.auth_manager.login_monitor(
            self.config.credentials.monitor_user,
            self.config.credentials.monitor_password
        )
    
    def search_single_invoice(self, nota_fiscal: str) -> ScrapingResult:
        print(f"🔍 Pesquisando nota fiscal: {nota_fiscal}")
        
        if not hasattr(self, '_search_initialized'):
            self.auth_manager.navigate_to_search()
            self._search_initialized = True
        
        initial_date = get_date_30_days_ago()
        self.auth_manager.fill_search_form(initial_date, nota_fiscal)
        
        metadados = self.data_scraper.scrape_metadata()
        notas_data = self.data_scraper.scrape_invoices()
        
        invoices = [Invoice(numero_nota=nota_fiscal, data=nota) for nota in notas_data]
        
        return ScrapingResult(
            nota_fiscal=nota_fiscal,
            metadata=metadados,
            invoices=invoices,
            total_invoices=len(invoices),
            rejected_count=0
        )
    
    def search_multiple_invoices(self) -> BatchScrapingResult:
        resultados = []
        notas_com_erro = []
        
        print(f"🚀 Iniciando busca para {len(self.config.notas_fiscais)} notas fiscais...")
        
        for i, nota_fiscal in enumerate(self.config.notas_fiscais, 1):
            try:
                print(f"\n[{i}/{len(self.config.notas_fiscais)}] Processando nota: {nota_fiscal}")
                resultado = self.search_single_invoice(nota_fiscal)
                resultados.append(resultado)
                status = "❌ Rejeitada" if resultado.rejected_count > 0 else "✅ Aprovada"
                print(f"   {status} - Encontrados {resultado.total_invoices} registros")
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
    
    def display_batch_results(self, batch_result: BatchScrapingResult):
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*60)
        print(f"✅ Notas processadas com sucesso: {batch_result.total_notas_processadas}")
        print(f"❌ Notas com erro: {len(batch_result.notas_com_erro)}")
        print(f"📊 Total de registros encontrados: {batch_result.total_registros_encontrados}")
        print(f"🚫 Notas com rejeições: {batch_result.total_notas_rejeitadas}")
        
        if batch_result.notas_com_erro:
            print(f"\n📝 Notas com erro: {', '.join(batch_result.notas_com_erro)}")
    
    def run(self):
        try:
            print("🚀 Iniciando NF Scraper...")
            self.setup_browser()
            self.navigate_to_initial_page()
            self.perform_login()
            
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
        if self.browser:
            self.browser.close()

def main():
    try:
        config = AppConfig.from_env()
        print("✅ Configurações carregadas!")
        
        # Verifica credenciais
        if not all([
            config.credentials.email,
            config.credentials.password,
            config.credentials.monitor_user,
            config.credentials.monitor_password
        ]):
            print("❌ Erro: Credenciais incompletas no .env")
            return
        
        print(f"📝 Notas fiscais a serem pesquisadas: {len(config.notas_fiscais)}")
        for nf in config.notas_fiscais:
            print(f"   - {nf}")
        
        app = NFScraperApp(config)
        app.run()
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")

if __name__ == "__main__":
    main()