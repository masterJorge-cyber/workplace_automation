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
                "chave": "35251047508411159007551100000183854341594564",
                "fiscal_doc_no": "18385",
                "location_id": "001",
                "series_no": "110",
                "protocolo": "",
                "chave_aux": "NF001"
            },
            {
                "chave": "35251047508411159007551100000184344341597667", 
                "fiscal_doc_no": "18434",
                "location_id": "001",
                "series_no": "110",
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
    
    def search_single_invoice_with_immediate_reprocess(self, nota_data):
        """Pesquisa uma única nota fiscal e já reprocessa imediatamente se rejeitada - SEM REPESQUISAR"""
        chave_acesso = nota_data['chave']
        fiscal_doc_no = nota_data.get('fiscal_doc_no', '')
        series_no = nota_data.get('series_no', '')
        
        print(f"🔍 Pesquisando nota: {chave_acesso}")
        print(f"   📊 Fiscal Doc: {fiscal_doc_no}")
        print(f"   🔢 Série: {series_no}")
        
        try:
            # PRIMEIRA E ÚNICA CONSULTA
            initial_date = get_date_30_days_ago()
            success = self.auth_manager.fill_search_form(initial_date, chave_acesso)
            
            if not success:
                return {
                    "nota_data": nota_data,
                    "status": "❌ Erro ao pesquisar nota",
                    "dados_completos": {},
                    "reprocessado": False
                }
            
            # Extrai dados da consulta
            dados_completos = self.auth_manager.extract_invoice_data(chave_acesso)
            
            # Extrai status e dados da estrutura correta
            if isinstance(dados_completos, dict):
                status = dados_completos.get('status', 'Status não encontrado')
                dados = dados_completos.get('dados_completos', {})
            else:
                status = dados_completos
                dados = {}
            
            print(f"   📊 Status: {status}")
            
            # VERIFICA SE PRECISA REPROCESSAR IMEDIATAMENTE
            precisa_reprocessar = 'Rejeitado' in status or '❌' in status
            
            if precisa_reprocessar:
                print(f"   🚫 Nota rejeitada, INICIANDO REPROCESSAMENTO IMEDIATO...")
                
                # REPROCESSAMENTO DIRETO - SEM REPESQUISAR
                sucesso_reprocessamento = self.reprocessar_nota_diretamente()
                
                if sucesso_reprocessamento:
                    status = "✅ REPROCESSADO COM SUCESSO"
                    reprocessado = True
                    print(f"   ✅ Status final: REPROCESSADO COM SUCESSO")
                else:
                    status = "❌ FALHA NO REPROCESSAMENTO"
                    reprocessado = False
                    print(f"   ❌ Status final: FALHA NO REPROCESSAMENTO")
            else:
                reprocessado = False
                print(f"   ✅ Status final: {status}")
            
            return {
                "nota_data": nota_data,
                "status": status,
                "dados_completos": dados,
                "reprocessado": reprocessado
            }
            
        except Exception as e:
            error_msg = f"❌ Erro na nota {chave_acesso}: {e}"
            print(f"   {error_msg}")
            return {
                "nota_data": nota_data,
                "status": error_msg,
                "dados_completos": {},
                "reprocessado": False
            }
    
    def reprocessar_nota_diretamente(self):
        """Reprocessa a nota diretamente sem repesquisar - usa a nota já encontrada"""
        try:
            print("   🔄 EXECUTANDO REPROCESSAMENTO DIRETO...")
            
            # 1. Chamar o reprocessamento do AuthManager DIRETAMENTE
            # A nota já está selecionada/identificada na tela atual
            print("   🔄 Acionando reprocessamento direto...")
            success = self.auth_manager.reprocessar_notas_selecionadas()
            
            if success:
                print("   ✅ REPROCESSAMENTO DIRETO CONCLUÍDO!")
                
                # Aguarda um pouco após sucesso
                time.sleep(3)
                
                # Volta para tela de pesquisa para próxima nota
                print("   🧭 Voltando para tela de pesquisa...")
                self.auth_manager.navigate_to_search_screen()
                time.sleep(2)
                
                return True
            else:
                print("   ❌ REPROCESSAMENTO DIRETO FALHOU")
                return False
                
        except Exception as e:
            print(f"   ❌ Erro no reprocessamento direto: {e}")
            return False
    
    def search_multiple_invoices(self):
        """Pesquisa múltiplas notas fiscais com reprocessamento imediato integrado"""
        resultados = []
        notas_com_erro = []
        
        print(f"🚀 Iniciando busca para {len(self.notas_fiscais)} notas fiscais...")
        print("💡 MODO: CONSULTA ÚNICA + REPROCESSAMENTO DIRETO")
        print("=" * 60)
        
        for i, nota_data in enumerate(self.notas_fiscais, 1):
            try:
                print(f"\n[{i}/{len(self.notas_fiscais)}] Processando nota...")
                
                # 🔥 AGORA: Faz a consulta E reprocessamento DIRETO na mesma chamada
                dados_nota = self.search_single_invoice_with_immediate_reprocess(nota_data)
                resultados.append(dados_nota)
                
                # Pequena pausa entre notas
                if i < len(self.notas_fiscais):
                    print("   ⏳ Aguardando antes da próxima nota...")
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
    
    def display_batch_results(self, batch_result):
        """Exibe resultados do processamento em lote"""
        print("\n" + "="*60)
        print("📋 RELATÓRIO FINAL DO PROCESSAMENTO")
        print("="*60)
        
        # Contadores
        notas_reprocessadas = sum(1 for r in batch_result['resultados'] if r.get('reprocessado', False))
        notas_com_sucesso = sum(1 for r in batch_result['resultados'] if '✅' in str(r.get('status', '')) and 'REPROCESSADO' not in str(r.get('status', '')))
        notas_reprocessadas_sucesso = sum(1 for r in batch_result['resultados'] if 'REPROCESSADO COM SUCESSO' in str(r.get('status', '')))
        notas_com_erro = sum(1 for r in batch_result['resultados'] if '❌' in str(r.get('status', '')) or 'FALHA' in str(r.get('status', '')))
        
        print(f"✅ Notas processadas com sucesso: {notas_com_sucesso}")
        print(f"🔄 Notas reprocessadas com sucesso: {notas_reprocessadas_sucesso}")
        print(f"❌ Notas com erro: {notas_com_erro}")
        print(f"📊 Total de registros processados: {batch_result['total_registros_encontrados']}")
        
        if batch_result['notas_com_erro']:
            print(f"\n🔴 Notas com erro crítico:")
            for erro in batch_result['notas_com_erro']:
                print(f"   - {erro['nota_data']['chave']}: {erro['erro']}")
        
        # Detalhamento
        print("\n" + "-"*50)
        print("DETALHAMENTO POR NOTA FISCAL:")
        print("-"*50)
        
        for resultado in batch_result['resultados']:
            nota_data = resultado['nota_data']
            status = str(resultado['status'])
            reprocessado = resultado.get('reprocessado', False)
            
            # Determina o ícone baseado no status
            if '❌' in status or 'Erro' in status or 'FALHA' in status:
                status_icon = "❌"
            elif 'Rejeitado' in status:
                status_icon = "🚫"
            elif 'não tem nota' in status.lower():
                status_icon = "🔍"
            elif 'REPROCESSADO' in status:
                status_icon = "🔄"
            else:
                status_icon = "✅"
            
            # Adiciona ícone de reprocessamento se aplicável
            reprocess_icon = " 🔄" if reprocessado else ""
            
            # Mostra informações adicionais
            info_extra = f" | Fiscal Doc: {nota_data.get('fiscal_doc_no', 'N/A')}"
            info_extra += f" | Série: {nota_data.get('series_no', 'N/A')}"
            
            print(f"{status_icon}{reprocess_icon} {nota_data['chave']}: {status}{info_extra}")
    
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
                'reprocessado': 'Sim' if resultado.get('reprocessado', False) else 'Não',
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
                'reprocessado': 'Não',
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
        """Fluxo 1: Unisys (atual) usando JSON com reprocessamento direto"""
        print("🚀 Iniciando Fluxo 1 - Unisys com JSON...")
        print("🔄 MODO: CONSULTA ÚNICA + REPROCESSAMENTO DIRETO")
        print("=" * 60)
        
        if not self.notas_fiscais:
            print("❌ Nenhuma nota para processar")
            return
        
        self.setup_browser()
        self.navigate_to_initial_page()
        self.perform_full_login()
        
        # 🔥 AGORA: Só uma chamada - já inclui consulta E reprocessamento DIRETO
        batch_result = self.search_multiple_invoices()
        
        self.display_batch_results(batch_result)
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