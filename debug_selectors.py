import time
from playwright.sync_api import sync_playwright
import logging
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

# Configurar logging detalhado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_selectors():
    """
    🎯 SCRIPT DE DEBUG PARA ENCONTRAR SELETORES COM PROXY
    """
    
    print("🚀 INICIANDO DEBUG DE SELETORES COM PROXY")
    print("=" * 60)
    
    # Configurações do proxy do .env
    proxy_host = os.getenv('PROXY_HOST', '10.141.6.12')
    proxy_port = os.getenv('PROXY_PORT', '80')
    
    print(f"🔌 Usando Proxy: {proxy_host}:{proxy_port}")
    
    with sync_playwright() as p:
        # 🔥 Browser VISÍVEL com proxy
        browser = p.chromium.launch(
            headless=False,
            slow_mo=500
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 720},
            ignore_https_errors=True,
            proxy={
                "server": f"http://{proxy_host}:{proxy_port}"
            }
        )
        
        page = context.new_page()
        
        try:
            # 1. 📄 IR PARA A PÁGINA INICIAL
            print("\n1. 🌐 Navegando para a página inicial com proxy...")
            page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/", wait_until="networkidle")
            time.sleep(3)
            
            print("✅ Página carregada com proxy!")
            print(f"   📍 URL: {page.url}")
            print(f"   📝 Título: {page.title()}")
            
            input("\n⏸️  Pressione ENTER para analisar os elementos da página...")
            
            # 2. 🔍 ANALISAR ELEMENTOS (mesmo código anterior)
            print("\n2. 🔍 ANALISANDO ELEMENTOS DA PÁGINA")
            print("-" * 50)
            
            inputs = page.query_selector_all("input")
            visible_inputs = [inp for inp in inputs if inp.is_visible()]
            
            print(f"\n📝 INPUTS (Total: {len(inputs)}, Visíveis: {len(visible_inputs)}):")
            print("-" * 30)
            
            for i, inp in enumerate(visible_inputs, 1):
                input_type = inp.get_attribute("type") or "text"
                input_name = inp.get_attribute("name") or "sem_name"
                input_id = inp.get_attribute("id") or "sem_id"
                input_placeholder = inp.get_attribute("placeholder") or "sem_placeholder"
                
                print(f"   {i}. 🎯 INPUT VISÍVEL:")
                print(f"      🔹 type: '{input_type}'")
                print(f"      🔹 name: '{input_name}'")
                print(f"      🔹 id: '{input_id}'")
                print(f"      🔹 placeholder: '{input_placeholder}'")
                
                selectors = []
                if input_type: selectors.append(f"input[type='{input_type}']")
                if input_name: selectors.append(f"input[name='{input_name}']")
                if input_id: selectors.append(f"input[id='{input_id}']")
                
                if selectors:
                    print(f"      💡 Seletores: {', '.join(selectors)}")
            
            input("\n🎊 Pressione ENTER para finalizar o debug...")
            
        except Exception as e:
            logger.error(f"❌ Erro durante o debug: {e}")
        finally:
            browser.close()
    
    print("\n✅ DEBUG SELECTORS CONCLUÍDO!")

if __name__ == "__main__":
    debug_selectors()