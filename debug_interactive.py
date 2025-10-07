from playwright.sync_api import sync_playwright
import time
import os
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

def interactive_debug():
    """
    🎮 DEBUG INTERATIVO COM PROXY
    """
    
    print("🎮 DEBUG INTERATIVO INICIADO COM PROXY")
    print("=" * 50)
    
    # Configurações do proxy
    proxy_host = os.getenv('PROXY_HOST', '10.141.6.12')
    proxy_port = os.getenv('PROXY_PORT', '80')
    
    print(f"🔌 Proxy: {proxy_host}:{proxy_port}")
    print("Você controla cada etapa! Configure a tela e pressione ENTER")
    print("=" * 50)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False, 
            slow_mo=1000
        )
        
        context = browser.new_context(
            proxy={
                "server": f"http://{proxy_host}:{proxy_port}"
            },
            ignore_https_errors=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        page = context.new_page()
        
        try:
            # ETAPA 1: Página inicial de login
            print("\n🔄 ETAPA 1 - Página inicial de login")
            print("Aguardando navegação automática...")
            page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/", wait_until="networkidle")
            time.sleep(3)
            
            input("⏸️  Página carregada! Pressione ENTER para analisar...")
            analyze_page(page, "PÁGINA INICIAL DE LOGIN")
            
            # ETAPA 2: Após primeiro login
            input("\n🔄 ETAPA 2 - Após primeiro login - Faça o login manualmente e pressione ENTER...")
            analyze_page(page, "APÓS PRIMEIRO LOGIN")
            
            # ETAPA 3: Tela do monitor
            input("\n🔄 ETAPA 3 - Tela do monitor - Faça o login do monitor manualmente e pressione ENTER...")
            analyze_page(page, "TELA DO MONITOR")
            
            # ETAPA 4: Tela de pesquisa
            input("\n🔄 ETAPA 4 - Tela de pesquisa - Navegue até a tela de pesquisa e pressione ENTER...")
            analyze_page(page, "TELA DE PESQUISA")
            
            # ETAPA 5: Formulário de pesquisa
            input("\n🔄 ETAPA 5 - Formulário de pesquisa - Abra o formulário e pressione ENTER...")
            analyze_page(page, "FORMULÁRIO DE PESQUISA")
            
            print("\n🎊 TODAS AS ETAPAS MAPEADAS COM SUCESSO!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
        finally:
            browser.close()

def analyze_page(page, etapa_nome):
    """Analisa uma página específica"""
    print(f"\n📊 {etapa_nome}")
    print("-" * 40)
    print(f"📍 URL: {page.url}")
    print(f"📝 Título: {page.title()}")
    
    # Elementos visíveis
    inputs = page.query_selector_all("input:visible")
    buttons = page.query_selector_all("button:visible, input[type='submit']:visible")
    
    print(f"📝 Inputs visíveis: {len(inputs)}")
    for i, inp in enumerate(inputs[:5], 1):
        input_type = inp.get_attribute("type") or "text"
        input_name = inp.get_attribute("name") or inp.get_attribute("id") or f"input_{i}"
        print(f"   {i}. {input_type} - {input_name}")
    
    print(f"🖱️ Botões visíveis: {len(buttons)}")
    for i, btn in enumerate(buttons[:5], 1):
        btn_text = btn.inner_text().strip() or btn.get_attribute("value") or f"botao_{i}"
        print(f"   {i}. {btn_text}")

if __name__ == "__main__":
    interactive_debug()