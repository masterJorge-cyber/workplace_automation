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
        self.auth_manager = None
        self.browser = None
        self.context = None
        self.page = None
        self.data_scraper = None
    
    def setup_browser(self):
        """Configura o navegador e contexto"""
        print("🌐 Iniciando navegador...")
        
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.config.headless)
        
        self.context = self.browser.new_context(
            proxy={"server": f"http://{self.config.proxy.host}:{self.config.proxy.port}"},
            ignore_https_errors=True
        )
        
        self.page = self.context.new_page()
        self.data_scraper = DataScraper(self.page)
        self.auth_manager = AuthManager(self.page)
        
        print("✅ Navegador configurado!")
    
    def navigate_to_initial_page(self):
        """Navega para a página inicial"""
        print("🌍 Navegando para página inicial...")
        self.page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/", wait_until="networkidle")
        time.sleep(2)
        print("✅ Página carregada!")
    
    def perform_full_login(self):
        """Executa todo o fluxo de login com a página extra"""
        print("🔐 Iniciando processo de autenticação completo...")
        
        # Valida credenciais básicas
        if not validate_credentials(self.config.credentials.email, self.config.credentials.password):
            raise ValueError("Credenciais inválidas")
        
        # 1. Login inicial (email + senha)
        print("1. 🔐 Primeiro login...")
        success = self.auth_manager.login_initial(
            self.config.credentials.email,
            self.config.credentials.password
        )
        if not success:
            raise Exception("❌ Falha no primeiro login")
        
        # 2. Página extra
        print("2. 🔄 Processando página intermediária...")
        success = self.auth_manager.handle_pagina_extra()
        if not success:
            print("⚠️  Aviso: Página extra não processada completamente, continuando...")
        
        # 3. Login monitor
        print("3. 👨‍💼 Login no monitor...")
        success = self.auth_manager.login_monitor(
            self.config.credentials.monitor_user,
            self.config.credentials.monitor_password
        )
        if not success:
            raise Exception("❌ Falha no login do monitor")
        
        # 4. Navegação
        print("4. 🧭 Navegando para tela de pesquisa...")
        self.auth_manager.navigate_to_search_screen()
        
        print("✅ Autenticação completa com página extra!")
    def search_single_invoice(self, nota_fiscal: str):
        """Pesquisa uma única nota fiscal e retorna todos os dados"""
        print(f"🔍 Pesquisando nota: {nota_fiscal}")
        
        try:
            # Preenche formulário de pesquisa
            initial_date = get_date_30_days_ago()
            success = self.auth_manager.fill_search_form(initial_date, nota_fiscal)
            
            if not success:
                return {
                    "nota_fiscal": nota_fiscal,
                    "status": "❌ Erro ao pesquisar nota",
                    "dados_completos": {}
                }
            
            # Extrai todos os dados da nota usando o método correto
            dados_completos = self.auth_manager.extract_invoice_data(nota_fiscal)
            
            # DEBUG: Mostra o que está retornando
            print(f"   🔍 DEBUG - Tipo retornado: {type(dados_completos)}")
            print(f"   🔍 DEBUG - Conteúdo: {dados_completos}")
            
            # Extrai status e dados da estrutura correta
            if isinstance(dados_completos, dict):
                status = dados_completos.get('status', 'Status não encontrado')
                dados = dados_completos.get('dados_completos', {})
            else:
                # Se for string direta (método antigo)
                status = dados_completos
                dados = {}
            
            print(f"   📊 Status: {status}")
            if dados:
                print(f"   📋 Dados extraídos: {len(dados)} campos")
            
            return {
                "nota_fiscal": nota_fiscal,
                "status": status,
                "dados_completos": dados
            }
            
        except Exception as e:
            error_msg = f"❌ Erro na nota {nota_fiscal}: {e}"
            print(f"   {error_msg}")
            return {
                "nota_fiscal": nota_fiscal,
                "status": error_msg,
                "dados_completos": {}
            }    

    def search_multiple_invoices(self):
        """Pesquisa múltiplas notas fiscais e retorna status"""
        resultados = []
        notas_com_erro = []
        
        print(f"🚀 Iniciando busca para {len(self.config.notas_fiscais)} notas fiscais...")
        
        for i, nota_fiscal in enumerate(self.config.notas_fiscais, 1):
            try:
                print(f"\n[{i}/{len(self.config.notas_fiscais)}] Processando nota: {nota_fiscal}")
                
                # Pesquisa e obtém dados completos
                dados_nota = self.search_single_invoice(nota_fiscal)
                resultados.append(dados_nota)
                
                # Pequena pausa entre pesquisas
                if i < len(self.config.notas_fiscais):
                    time.sleep(2)
                    
            except Exception as e:
                error_msg = f"❌ Erro crítico na nota {nota_fiscal}: {e}"
                print(f"   {error_msg}")
                notas_com_erro.append({
                    'nota_fiscal': nota_fiscal,
                    'erro': str(e)
                })
                continue
        
        # CORREÇÃO: Conta notas rejeitadas corretamente
        notas_rejeitadas = 0
        for resultado in resultados:
            status = str(resultado.get('status', ''))
            if 'Rejeitado' in status:
                notas_rejeitadas += 1
        
        return {
            'resultados': resultados,
            'notas_com_erro': notas_com_erro,
            'total_notas_processadas': len(resultados),
            'total_registros_encontrados': len(resultados),
            'total_notas_rejeitadas': notas_rejeitadas
        }
    
    def display_batch_results(self, batch_result):
        """Exibe resultados do processamento em lote"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*60)
        
        print(f"✅ Notas processadas com sucesso: {batch_result['total_notas_processadas']}")
        print(f"❌ Notas com erro: {len(batch_result['notas_com_erro'])}")
        print(f"📊 Total de registros encontrados: {batch_result['total_registros_encontrados']}")
        print(f"🚫 Notas com rejeições: {batch_result['total_notas_rejeitadas']}")
        
        if batch_result['notas_com_erro']:
            print(f"\n🔴 Notas com erro:")
            for erro in batch_result['notas_com_erro']:
                print(f"   - {erro['nota_fiscal']}: {erro['erro']}")
        
        # Detalhamento
        print("\n" + "-"*50)
        print("DETALHAMENTO POR NOTA FISCAL:")
        print("-"*50)
        
        for resultado in batch_result['resultados']:
            # Garante que status é string
            status = str(resultado['status'])
            
            # Pega dados_completos com valor padrão seguro
            dados = resultado.get('dados_completos', {})
            if not isinstance(dados, dict):
                dados = {}
            
            # Determina o ícone baseado no status
            if '❌' in status or 'Erro' in status:
                status_icon = "❌"
            elif 'Rejeitado' in status:
                status_icon = "🚫"
            elif 'não tem nota' in status.lower():
                status_icon = "🔍"
            else:
                status_icon = "✅"
            
            # Mostra informações adicionais se disponíveis
            info_extra = ""
            if dados:
                if dados.get('numero_documento'):
                    info_extra += f" | Nº: {dados['numero_documento']}"
                if dados.get('data_emissao'):
                    info_extra += f" | Emissão: {dados['data_emissao']}"
                if dados.get('valor_total'):
                    info_extra += f" | Valor: {dados['valor_total']}"
            
            print(f"{status_icon} {resultado['nota_fiscal']}: {status}{info_extra}")

    def save_results_to_file(self, batch_result, filename=None):
        """Salva os resultados completos em um arquivo CSV na pasta /sheets"""
        import pandas as pd
        from datetime import datetime
        import os

        # Criar pasta sheets se não existir
        sheets_dir = "sheets"
        if not os.path.exists(sheets_dir):
            os.makedirs(sheets_dir)
            print(f"📁 Pasta '{sheets_dir}' criada com sucesso!")
        
        if not filename:
            filename = f"resultados_completos_notas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Definir caminho completo
        filepath = os.path.join(sheets_dir, filename)
        
        # Prepara dados para CSV com todas as colunas
        dados = []
        
        for resultado in batch_result['resultados']:
            # ESTRUTURA CORRETA: resultado é um dict com 'nota_fiscal', 'status', 'dados_completos'
            linha_csv = {
                'nota_fiscal': resultado['nota_fiscal'],
                'status': resultado['status'],
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            }
            
            # Adiciona todos os dados completos da linha (se existirem)
            dados_completos = resultado.get('dados_completos', {})
            if dados_completos and isinstance(dados_completos, dict):
                for chave, valor in dados_completos.items():
                    linha_csv[chave] = valor
            
            dados.append(linha_csv)
        
        for erro in batch_result['notas_com_erro']:
            dados.append({
                'nota_fiscal': erro['nota_fiscal'],
                'status': f"ERRO: {erro['erro']}",
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
        
        if dados:
            df = pd.DataFrame(dados)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"💾 Resultados COMPLETOS salvos em: {filepath}")
            print(f"   📊 Total de colunas: {len(df.columns)}")
            print(f"   📋 Colunas: {', '.join(df.columns.tolist()[:10])}...")  # Mostra só as 10 primeiras
            return filepath
        else:
            print("📝 Nenhum dado para salvar.")
            return None
            
    def run(self):
        """Executa o fluxo completo do scraper"""
        try:
            print("🚀 Iniciando NF Scraper...")
            self.setup_browser()
            self.navigate_to_initial_page()
            self.perform_full_login()
            
            # Processa as notas
            batch_result = self.search_multiple_invoices()
            
            # Gera relatório
            self.display_batch_results(batch_result)
            
            # Salva em arquivo
            arquivo_salvo = self.save_results_to_file(batch_result)
            
            print(f"\n✅ Processo concluído com sucesso!")
            if arquivo_salvo:
                print(f"💾 Arquivo salvo: {arquivo_salvo}")
            
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            raise
        finally:
            input("\n⏎ Pressione Enter para finalizar...")
            self.close()
    
    def close(self):
        """Fecha recursos"""
        if self.browser:
            self.browser.close()
            print("🔚 Navegador fechado.")
   
def display_batch_results(self, batch_result):
    """Exibe resultados do processamento em lote"""
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
    print("="*60)
    
    print(f"✅ Notas processadas com sucesso: {batch_result['total_notas_processadas']}")
    print(f"❌ Notas com erro: {len(batch_result['notas_com_erro'])}")
    print(f"📊 Total de registros encontrados: {batch_result['total_registros_encontrados']}")
    print(f"🚫 Notas com rejeições: {batch_result['total_notas_rejeitadas']}")
    
    if batch_result['notas_com_erro']:
        print(f"\n🔴 Notas com erro:")
        for erro in batch_result['notas_com_erro']:
            print(f"   - {erro['nota_fiscal']}: {erro['erro']}")
    
    # Detalhamento
    print("\n" + "-"*50)
    print("DETALHAMENTO POR NOTA FISCAL:")
    print("-"*50)
    
    for resultado in batch_result['resultados']:
        status = resultado['status']
        if '❌' in status or 'Erro' in status:
            status_icon = "❌"
        elif 'Rejeitado' in status:
            status_icon = "🚫"
        elif 'não encontrado' in status.lower() or 'filtro não achou' in status.lower():
            status_icon = "🔍"
        else:
            status_icon = "✅"
        
        print(f"{status_icon} {resultado['nota_fiscal']}: {status}")
    def save_results_to_file(self, batch_result, filename=None):
        """Salva os resultados em um arquivo CSV"""
        import pandas as pd
        from datetime import datetime
        
        if not filename:
            filename = f"/sheets/resultados_notas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Prepara dados para CSV
        dados = []
        for resultado in batch_result['resultados']:
            dados.append({
                'nota_fiscal': resultado['nota_fiscal'],
                'status': resultado['status'],
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
        
        for erro in batch_result['notas_com_erro']:
            dados.append({
                'nota_fiscal': erro['nota_fiscal'],
                'status': f"ERRO: {erro['erro']}",
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
        
        if dados:
            df = pd.DataFrame(dados)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 Resultados salvos em: {filename}")
            return filename
        else:
            print("📝 Nenhum dado para salvar.")
            return None
         
    def run(self):
        """Executa o fluxo completo do scraper"""
        try:
            print("🚀 Iniciando NF Scraper...")
            self.setup_browser()
            self.navigate_to_initial_page()
            self.perform_full_login()  # ← CORRIGIDO: nome completo do método
            
            # Processa as notas
            batch_result = self.search_multiple_invoices()
            
            # Gera relatório
            self.display_batch_results(batch_result)

                    # Salva em arquivo
            arquivo_salvo = self.save_results_to_file(batch_result)
        
            print(f"\n✅ Processo concluído com sucesso!")
            if arquivo_salvo:
                print(f"💾 Arquivo salvo: {arquivo_salvo}")
            
                print("\n✅ Processo concluído com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro durante a execução: {e}")
            raise
        finally:
            input("\n⏎ Pressione Enter para finalizar...")
            self.close()
    
    def close(self):
        """Fecha recursos"""
        if self.browser:
            self.browser.close()
            print("🔚 Navegador fechado.")

def main():
    try:
        # Carrega configurações
        config = AppConfig.from_env()
        print("✅ Configurações carregadas!")
        
        # Validações
        if not all([
            config.credentials.email,
            config.credentials.password,
            config.credentials.monitor_user,
            config.credentials.monitor_password
        ]):
            print("❌ Credenciais incompletas no arquivo .env")
            return
        
        if not config.notas_fiscais:
            print("❌ Nenhuma nota fiscal configurada")
            return
        
        print(f"📋 Notas a processar: {len(config.notas_fiscais)}")
        
        # Executa aplicação
        app = NFScraperApp(config)
        app.run()
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    main()