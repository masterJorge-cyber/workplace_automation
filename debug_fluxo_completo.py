import time
from playwright.sync_api import sync_playwright
import logging
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DebugFluxoParcial:
    def __init__(self):
        self.proxy_host = os.getenv('PROXY_HOST', '10.141.6.12')
        self.proxy_port = os.getenv('PROXY_PORT', '80')
        self.page = None
        self.selectors_encontrados = {}
    
    def setup_browser(self):
        """Configura o navegador com proxy"""
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(
            headless=False,
            slow_mo=1000
        )
        
        context = browser.new_context(
            proxy={"server": f"http://{self.proxy_host}:{self.proxy_port}"},
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        self.page = context.new_page()
        return browser
    
    def analisar_divs_uteis(self, nome_etapa):
        """Analisa divs, menus e elementos úteis da página"""
        print(f"\n🏗️  ANALISANDO ESTRUTURA DA PÁGINA - {nome_etapa}")
        print("=" * 60)
        
        # Analisar menus e navegação
        menus = self.page.query_selector_all("nav, .menu, .navbar, .navigation, [class*='menu'], [class*='nav']")
        print(f"\n📋 MENUS/NAVEGAÇÃO ({len(menus)}):")
        for i, menu in enumerate(menus[:5], 1):  # Mostra só os 5 primeiros
            menu_text = menu.inner_text().strip()[:100]  # Limita texto
            menu_class = menu.get_attribute("class") or "sem-classe"
            print(f"   {i}. 🧭 {menu_text}...")
            print(f"      class: '{menu_class}'")
        
        # Analisar links importantes
        links_uteis = self.page.query_selector_all("a:visible")
        links_importantes = []
        
        textos_uteis = ['pesquisa', 'consult', 'nota', 'fiscal', 'nfe', 'busca', 'search', 'relator', 'dashboard']
        
        for link in links_uteis:
            link_text = link.inner_text().strip().lower()
            if any(texto in link_text for texto in textos_uteis) and len(link_text) > 0:
                links_importantes.append(link)
        
        print(f"\n🔗 LINKS ÚTEIS ENCONTRADOS ({len(links_importantes)}):")
        for i, link in enumerate(links_importantes[:10], 1):
            link_text = link.inner_text().strip()
            link_href = link.get_attribute("href") or "#"
            print(f"   {i}. 📎 '{link_text}'")
            print(f"      href: {link_href}")
            print(f"      selector: a:has-text('{link_text}')")
        
        # Analisar containers principais
        containers = self.page.query_selector_all(".container, .main, .content, .wrapper, .page, [class*='container'], [class*='content']")
        print(f"\n📦 CONTAINERS PRINCIPAIS ({len(containers)}):")
        for i, container in enumerate(containers[:3], 1):
            container_class = container.get_attribute("class") or "sem-classe"
            container_id = container.get_attribute("id") or "sem-id"
            print(f"   {i}. 🗂️  class: '{container_class}'")
            if container_id != "sem-id":
                print(f"      id: '{container_id}'")
        
        # Analisar tabelas (importante para dados)
        tables = self.page.query_selector_all("table:visible")
        print(f"\n📊 TABELAS VISÍVEIS ({len(tables)}):")
        for i, table in enumerate(tables, 1):
            table_class = table.get_attribute("class") or "sem-classe"
            rows = table.query_selector_all("tr")
            print(f"   {i}. 📑 {len(rows)} linhas - class: '{table_class}'")
    
    def analisar_pagina_atual(self, nome_etapa):
        """Analisa todos os elementos da página atual"""
        print(f"\n🎯 {nome_etapa}")
        print("=" * 50)
        print(f"📍 URL: {self.page.url}")
        print(f"📝 Título: {self.page.title()}")
        
        # Aguardar página estabilizar
        time.sleep(2)
        
        # Analisar inputs
        inputs = self.page.query_selector_all("input:visible")
        print(f"\n📝 INPUTS VISÍVEIS ({len(inputs)}):")
        
        inputs_info = []
        for i, inp in enumerate(inputs, 1):
            input_type = inp.get_attribute("type") or "text"
            input_name = inp.get_attribute("name") or "sem_name"
            input_id = inp.get_attribute("id") or "sem_id"
            input_placeholder = inp.get_attribute("placeholder") or "sem_placeholder"
            
            print(f"   {i}. 🔹 type: '{input_type}'")
            print(f"      name: '{input_name}'")
            print(f"      id: '{input_id}'")
            print(f"      placeholder: '{input_placeholder}'")
            
            # Sugerir seletores
            selectors = []
            if input_type: selectors.append(f"input[type='{input_type}']")
            if input_name and input_name != "sem_name": 
                selectors.append(f"input[name='{input_name}']")
            if input_id and input_id != "sem_id": 
                selectors.append(f"input[id='{input_id}']")
            if input_placeholder and input_placeholder != "sem_placeholder":
                selectors.append(f"input[placeholder='{input_placeholder}']")
            
            if selectors:
                print(f"      💡 Seletores: {', '.join(selectors)}")
            
            inputs_info.append({
                'type': input_type,
                'name': input_name,
                'id': input_id,
                'placeholder': input_placeholder,
                'selectors': selectors
            })
        
        # Analisar botões
        buttons = self.page.query_selector_all("button:visible, input[type='submit']:visible, input[type='button']:visible")
        print(f"\n🖱️ BOTÕES VISÍVEIS ({len(buttons)}):")
        
        buttons_info = []
        for i, btn in enumerate(buttons, 1):
            btn_type = btn.get_attribute("type") or "button"
            btn_text = btn.inner_text().strip() or btn.get_attribute("value") or "sem_texto"
            btn_id = btn.get_attribute("id") or "sem_id"
            
            print(f"   {i}. 🔹 text: '{btn_text}'")
            print(f"      type: '{btn_type}'")
            print(f"      id: '{btn_id}'")
            
            # Sugerir seletores para botões
            btn_selectors = []
            if btn_text and len(btn_text) < 30:
                btn_selectors.append(f"button:has-text('{btn_text}')")
            if btn_id and btn_id != "sem_id":
                btn_selectors.append(f"button[id='{btn_id}']")
            if btn_type != "button":
                btn_selectors.append(f"input[type='{btn_type}']")
            
            if btn_selectors:
                print(f"      💡 Seletores: {', '.join(btn_selectors)}")
            
            buttons_info.append({
                'text': btn_text,
                'type': btn_type,
                'id': btn_id,
                'selectors': btn_selectors
            })
        
        # Analisar divs e estrutura para a ÚLTIMA PÁGINA (após monitor)
        if "TELA PRINCIPAL" in nome_etapa or "DASHBOARD" in nome_etapa:
            self.analisar_divs_uteis(nome_etapa)
        
        # Salvar seletores encontrados
        self.selectors_encontrados[nome_etapa] = {
            'inputs': inputs_info,
            'buttons': buttons_info,
            'url': self.page.url
        }
        
        input("\n⏸️  Pressione ENTER para continuar...")
    
    def executar_fluxo_parcial(self):
        """Executa o debug com página extra entre email e monitor"""
        print("🚀 DEBUG DO FLUXO PARCIAL COMPLETO")
        print("=" * 60)
        print(f"🔌 Proxy: {self.proxy_host}:{self.proxy_port}")
        print("\n🎯 ESTE SCRIPT VAI PARAR EM 5 PÁGINAS:")
        print("   1. 📄 Página inicial de login")
        print("   2. ✉️  Após primeiro email/senha")
        print("   3. 🔄 PÁGINA EXTRA (entre email e monitor)")
        print("   4. 👨‍💼 Tela do monitor")
        print("   5. 🏠 TELA PRINCIPAL (após login do monitor) ← NOVA!")
        print("=" * 60)
        
        browser = self.setup_browser()
        
        try:
            # ETAPA 1: Página inicial de login
            print("\n1. 📄 PÁGINA INICIAL DE LOGIN")
            print("Navegando automaticamente...")
            self.page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/", wait_until="networkidle")
            time.sleep(3)
            
            self.analisar_pagina_atual("PÁGINA INICIAL DE LOGIN")
            
            # ETAPA 2: Após primeiro email/senha
            input("\n2. ✉️ APÓS PRIMEIRO EMAIL/SENHA - Preencha email e senha do primeiro login e pressione ENTER...")
            self.analisar_pagina_atual("APÓS PRIMEIRO EMAIL/SENHA")
            
            # ETAPA 3: PÁGINA EXTRA (entre email e monitor)
            input("\n3. 🔄 PÁGINA EXTRA - Continue navegando até a próxima tela (ANTES do monitor) e pressione ENTER...")
            self.analisar_pagina_atual("PÁGINA EXTRA (ENTRE EMAIL E MONITOR)")
            
            # ETAPA 4: Tela do monitor
            input("\n4. 👨‍💼 TELA DO MONITOR - Faça o login do monitor e pressione ENTER...")
            self.analisar_pagina_atual("TELA DO MONITOR")
            
            # ETAPA 5: TELA PRINCIPAL (NOVA - após login do monitor)
            input("\n5. 🏠 TELA PRINCIPAL - Você está na tela principal/dashboard após o login completo. Pressione ENTER para analisar...")
            self.analisar_pagina_atual("TELA PRINCIPAL APÓS LOGIN COMPLETO")
            
            # ETAPA 6: Relatório final
            self.gerar_relatorio_final()
            
        except Exception as e:
            logger.error(f"❌ Erro durante o debug: {e}")
        finally:
            browser.close()
    
    def gerar_relatorio_final(self):
        """Gera um relatório com todos os seletores encontrados"""
        print("\n" + "=" * 70)
        print("📊 RELATÓRIO FINAL - TODOS OS SELETORES E ELEMENTOS ENCONTRADOS")
        print("=" * 70)
        
        for etapa, dados in self.selectors_encontrados.items():
            print(f"\n🎯 {etapa}")
            print(f"📍 URL: {dados['url']}")
            
            if dados['inputs']:
                print("📝 INPUTS SUGERIDOS:")
                for inp in dados['inputs']:
                    if inp['selectors']:
                        print(f"   🔹 {inp['type']} - {inp['selectors'][0]}")
            
            if dados['buttons']:
                print("🖱️ BOTÕES SUGERIDOS:")
                for btn in dados['buttons'][:3]:  # Mostra só os 3 principais
                    if btn['selectors'] and btn['text']:
                        print(f"   🔹 '{btn['text']}' - {btn['selectors'][0]}")
        
        # Destaques especiais para a tela principal
        if "TELA PRINCIPAL" in self.selectors_encontrados:
            print("\n" + "💡 DICAS PARA TELA PRINCIPAL:")
            print("   - Procure por links com: 'Pesquisa', 'Consulta', 'Nota Fiscal', 'NFE'")
            print("   - Use: a:has-text('Pesquisa') ou button:has-text('Consultar')")
            print("   - Verifique menus laterais ou superiores")
        
        print("\n🎯 COMO USAR NO SEU CÓDIGO:")
        print("   No navigate_to_search_screen(), use os seletores encontrados:")
        print("   - Para navegar: a:has-text('Pesquisa')")
        print("   - Ou: button:has-text('Consultar')")
        print("   - Ou o link específico encontrado acima")
        
        print("\n✅ DEBUG DO FLUXO COMPLETO CONCLUÍDO!")

def main():
    debug = DebugFluxoParcial()
    debug.executar_fluxo_parcial()

if __name__ == "__main__":
    main()