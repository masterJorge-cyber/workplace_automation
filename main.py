import os
import sys
import time
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright
import json
import pandas as pd

# 🔧 CORREÇÃO: Carregar .env de forma explícita
from dotenv import load_dotenv

# Verifica se o .env existe
env_path = os.path.join(os.path.dirname(__file__), '.env')
if not os.path.exists(env_path):
    print("❌ ERRO: Arquivo .env não encontrado!")
    print("💡 Verifique se o arquivo .env está na mesma pasta que main.py")
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
    # Criar classes básicas se não existirem
    class AppConfig:
        @classmethod
        def from_env(cls):
            return cls()
    
    class DataScraper:
        def __init__(self, page): pass

class NFScraperApp:
    def __init__(self, config: AppConfig):
        self.config = config
        self.auth_manager = None
        self.browser = None
        self.context = None
        self.page = None
        self.data_scraper = None
        self.json_path = os.path.join(os.getcwd(), "notas_fiscais.json")
        
        # Carregar notas do JSON
        self.notas_fiscais = self.carregar_notas_do_json()
        
        if not self.notas_fiscais:
            print("❌ Nenhuma nota fiscal encontrada no JSON")
            return
        
        print(f"📋 Notas carregadas do JSON: {len(self.notas_fiscais)}")
    
    def carregar_notas_do_json(self):
        """Carrega notas fiscais do arquivo JSON"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as file:
                    dados = json.load(file)
                    print(f"✅ JSON carregado: {len(dados)} notas")
                    return dados
            else:
                print(f"❌ Arquivo JSON não encontrado: {self.json_path}")
                # Criar arquivo JSON de exemplo
                self.criar_json_exemplo()
                return []
        except Exception as e:
            print(f"❌ Erro ao carregar JSON: {e}")
            return []
    
    def criar_json_exemplo(self):
        """Cria um arquivo JSON de exemplo se não existir"""
        exemplo = [
            {
                "chave": "35251047508411094037551100000220031339359138",
                "fiscal_doc_no": "220031",
                "location_id": "001",
                "series_no": "1",
                "protocolo": "",
                "chave_aux": "NF001"
            },
            {
                "chave": "35251047508411094037551100000220301339362217",
                "fiscal_doc_no": "220301", 
                "location_id": "001",
                "series_no": "1",
                "protocolo": "",
                "chave_aux": "NF002"
            }
        ]
        
        with open(self.json_path, 'w', encoding='utf-8') as file:
            json.dump(exemplo, file, indent=2, ensure_ascii=False)
        
        print(f"📄 Arquivo JSON de exemplo criado: {self.json_path}")
        print("💡 Edite o arquivo com suas notas fiscais reais")
    
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
    
    def search_single_invoice(self, nota_data):
        """Pesquisa uma única nota fiscal usando dados do JSON"""
        chave_acesso = nota_data['chave']
        fiscal_doc_no = nota_data.get('fiscal_doc_no', '')
        series_no = nota_data.get('series_no', '')
        
        print(f"🔍 Pesquisando nota: {chave_acesso}")
        print(f"   📊 Fiscal Doc: {fiscal_doc_no}")
        print(f"   🔢 Série: {series_no}")
        
        try:
            # Preenche formulário de pesquisa
            initial_date = get_date_30_days_ago()
            
            # USAR A CHAVE DO JSON para pesquisa
            success = self.auth_manager.fill_search_form(initial_date, chave_acesso)
            
            if not success:
                return {
                    "nota_data": nota_data,
                    "status": "❌ Erro ao pesquisar nota",
                    "dados_completos": {}
                }
            
            # Extrai todos os dados da nota
            dados_completos = self.auth_manager.extract_invoice_data(chave_acesso)
            
            # Extrai status e dados da estrutura correta
            if isinstance(dados_completos, dict):
                status = dados_completos.get('status', 'Status não encontrado')
                dados = dados_completos.get('dados_completos', {})
            else:
                # Se for string direta (método antigo)
                status = dados_completos
                dados = {}
            
            print(f"   📊 Status: {status}")
            
            return {
                "nota_data": nota_data,
                "status": status,
                "dados_completos": dados
            }
            
        except Exception as e:
            error_msg = f"❌ Erro na nota {chave_acesso}: {e}"
            print(f"   {error_msg}")
            return {
                "nota_data": nota_data,
                "status": error_msg,
                "dados_completos": {}
            }
    
    def search_multiple_invoices(self):
        """Pesquisa múltiplas notas fiscais do JSON"""
        resultados = []
        notas_com_erro = []
        
        print(f"🚀 Iniciando busca para {len(self.notas_fiscais)} notas fiscais...")
        
        for i, nota_data in enumerate(self.notas_fiscais, 1):
            try:
                print(f"\n[{i}/{len(self.notas_fiscais)}] Processando nota...")
                
                # Pesquisa e obtém dados completos
                dados_nota = self.search_single_invoice(nota_data)
                resultados.append(dados_nota)
                
                # Pequena pausa entre pesquisas
                if i < len(self.notas_fiscais):
                    time.sleep(2)
                    
            except Exception as e:
                error_msg = f"❌ Erro crítico na nota {nota_data['chave']}: {e}"
                print(f"   {error_msg}")
                notas_com_erro.append({
                    'nota_data': nota_data,
                    'erro': str(e)
                })
                continue
        
        return {
            'resultados': resultados,
            'notas_com_erro': notas_com_erro,
            'total_notas_processadas': len(resultados),
            'total_registros_encontrados': len(resultados)
        }
    
    def reprocessar_notas_individualmente(self, notas_rejeitadas):
        """Reprocessa CADA nota rejeitada individualmente"""
        if not notas_rejeitadas:
            print("📝 Nenhuma nota rejeitada para reprocessar")
            return True
        
        print(f"🔄 INICIANDO REPROCESSAMENTO INDIVIDUAL DE {len(notas_rejeitadas)} NOTAS")
        print("=" * 60)
        
        sucessos = 0
        for i, nota_data in enumerate(notas_rejeitadas, 1):
            try:
                chave = nota_data['chave']
                print(f"\n[{i}/{len(notas_rejeitadas)}] Reprocessando: {chave}")
                
                # 1. Navegar de volta para tela de pesquisa
                self.auth_manager.navigate_to_search_screen()
                time.sleep(2)
                
                # 2. Pesquisar a nota específica novamente
                initial_date = get_date_30_days_ago()
                success = self.auth_manager.fill_search_form(initial_date, chave)
                
                if not success:
                    print(f"   ❌ Falha ao pesquisar nota: {chave}")
                    continue
                
                # 3. Aguardar resultado da pesquisa
                print("   ⏳ Aguardando resultado da pesquisa...")
                time.sleep(5)
                self.page.wait_for_load_state("networkidle")
                
                # 4. Extrair dados para encontrar a linha da nota
                resultado = self.auth_manager.extract_invoice_data(chave)
                
                if not resultado or 'Não tem nota' in str(resultado.get('status')):
                    print(f"   ❌ Nota não encontrada após pesquisa: {chave}")
                    continue
                
                # 5. AGORA SIM: Chamar o reprocessamento do AuthManager
                print("   🔄 Acionando reprocessamento...")
                success = self.auth_manager.reprocessar_notas_selecionadas()
                
                if success:
                    print(f"   ✅ REPROCESSAMENTO SUCESSO: {chave}")
                    sucessos += 1
                    
                    # Aguardar um pouco após sucesso
                    time.sleep(3)
                else:
                    print(f"   ❌ REPROCESSAMENTO FALHOU: {chave}")
                
                # Pequena pausa entre reprocessamentos
                if i < len(notas_rejeitadas):
                    time.sleep(2)
                    
            except Exception as e:
                print(f"   ❌ Erro no reprocessamento de {chave}: {e}")
                continue
        
        print(f"\n📊 RESUMO REPROCESSAMENTO INDIVIDUAL:")
        print(f"   ✅ Sucessos: {sucessos}/{len(notas_rejeitadas)}")
        print(f"   ❌ Falhas: {len(notas_rejeitadas) - sucessos}/{len(notas_rejeitadas)}")
        
        return sucessos > 0
    
    def display_batch_results(self, batch_result, notas_rejeitadas):
        """Exibe resultados do processamento em lote"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*60)
        
        print(f"✅ Notas processadas com sucesso: {batch_result['total_notas_processadas']}")
        print(f"❌ Notas com erro: {len(batch_result['notas_com_erro'])}")
        print(f"📊 Total de registros encontrados: {batch_result['total_registros_encontrados']}")
        print(f"🚫 Notas rejeitadas: {notas_rejeitadas}")
        
        if batch_result['notas_com_erro']:
            print(f"\n🔴 Notas com erro:")
            for erro in batch_result['notas_com_erro']:
                print(f"   - {erro['nota_data']['chave']}: {erro['erro']}")
        
        # Detalhamento
        print("\n" + "-"*50)
        print("DETALHAMENTO POR NOTA FISCAL:")
        print("-"*50)
        
        for resultado in batch_result['resultados']:
            nota_data = resultado['nota_data']
            status = str(resultado['status'])
            
            # Determina o ícone baseado no status
            if '❌' in status or 'Erro' in status:
                status_icon = "❌"
            elif 'Rejeitado' in status:
                status_icon = "🚫"
            elif 'não tem nota' in status.lower():
                status_icon = "🔍"
            else:
                status_icon = "✅"
            
            # Mostra informações adicionais
            info_extra = f" | Fiscal Doc: {nota_data.get('fiscal_doc_no', 'N/A')}"
            info_extra += f" | Série: {nota_data.get('series_no', 'N/A')}"
            
            print(f"{status_icon} {nota_data['chave']}: {status}{info_extra}")
    
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
            filename = f"resultados_unisys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Definir caminho completo
        filepath = os.path.join(sheets_dir, filename)
        
        # Prepara dados para CSV com estrutura completa do JSON
        dados = []
        
        for resultado in batch_result['resultados']:
            nota_data = resultado['nota_data']
            
            linha_csv = {
                'chave_acesso': nota_data['chave'],
                'fiscal_doc_no': nota_data.get('fiscal_doc_no', ''),
                'series_no': nota_data.get('series_no', ''),
                'location_id': nota_data.get('location_id', ''),
                'chave_aux': nota_data.get('chave_aux', ''),
                'status': resultado['status'],
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'protocolo': nota_data.get('protocolo', '')
            }
            
            # Adiciona dados completos da consulta
            dados_completos = resultado.get('dados_completos', {})
            if dados_completos and isinstance(dados_completos, dict):
                for chave, valor in dados_completos.items():
                    linha_csv[chave] = valor
            
            dados.append(linha_csv)
        
        for erro in batch_result['notas_com_erro']:
            nota_data = erro['nota_data']
            dados.append({
                'chave_acesso': nota_data['chave'],
                'fiscal_doc_no': nota_data.get('fiscal_doc_no', ''),
                'series_no': nota_data.get('series_no', ''),
                'location_id': nota_data.get('location_id', ''),
                'chave_aux': nota_data.get('chave_aux', ''),
                'status': f"ERRO: {erro['erro']}",
                'data_consulta': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
            })
        
        if dados:
            df = pd.DataFrame(dados)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            print(f"💾 Resultados COMPLETOS salvos em: {filepath}")
            print(f"   📊 Total de colunas: {len(df.columns)}")
            print(f"   📋 Colunas: {', '.join(df.columns.tolist()[:8])}...")
            return filepath
        else:
            print("📝 Nenhum dado para salvar.")
            return None
    
    def executar_fluxo_unisys(self):
        """Fluxo 1: Unisys (atual) usando JSON"""
        print("🚀 Iniciando Fluxo 1 - Unisys com JSON...")
        
        if not self.notas_fiscais:
            print("❌ Nenhuma nota para processar")
            return
        
        self.setup_browser()
        self.navigate_to_initial_page()
        self.perform_full_login()
        
        # PRIMEIRA CONSULTA
        batch_result = self.search_multiple_invoices()
        
        # IDENTIFICAR NOTAS REJEITADAS
        notas_rejeitadas = []
        for resultado in batch_result['resultados']:
            status = str(resultado.get('status', ''))
            if 'Rejeitado' in status or '❌' in status:
                notas_rejeitadas.append(resultado['nota_data'])
        
        # REPROCESSAMENTO INDIVIDUAL APENAS SE HOUVER NOTAS REJEITADAS
        if notas_rejeitadas:
            print(f"\n🔄 INICIANDO REPROCESSAMENTO INDIVIDUAL PARA {len(notas_rejeitadas)} NOTAS REJEITADAS")
            print("=" * 60)
            
            success = self.reprocessar_notas_individualmente(notas_rejeitadas)
            if success:
                print("✅ Reprocessamento individual concluído!")
            else:
                print("❌ Alguns reprocessamentos individuais falharam")
        else:
            print("📝 Nenhuma nota rejeitada para reprocessar")
        
        self.display_batch_results(batch_result, len(notas_rejeitadas))
        arquivo_salvo = self.save_results_to_file(batch_result)
        
        print(f"\n✅ Processo Unisys concluído com sucesso!")
        if arquivo_salvo:
            print(f"💾 Arquivo salvo: {arquivo_salvo}")
    
    def run(self):
        """Executa o fluxo completo baseado no FLUXO configurado"""
        try:
            print(f"🎯 Fluxo configurado: {self.config.fluxo}")
            
            if self.config.fluxo == 1:
                self.executar_fluxo_unisys()
            else:
                print(f"❌ Fluxo {self.config.fluxo} não reconhecido. Use 1 (Unisys)")
                
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
        
        # Executa aplicação
        app = NFScraperApp(config)
        app.run()
        
    except Exception as e:
        print(f"❌ Erro na execução: {e}")

if __name__ == "__main__":
    main()