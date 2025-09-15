from playwright.sync_api import sync_playwright, Page
import pyautogui as gui
import time
from datetime import datetime, timedelta

proxy_host = "10.141.6.12"
proxy_port = 80

def scrap_metadados(page):
    import time
    for _ in range(5):  # tenta 5x
        try:
            metadados = {}
            metadados['title'] = page.title()
            metadados['url'] = page.url

            metatags = page.query_selector_all("meta")
            metadados['meta'] = {}
            for meta in metatags:
                name = meta.get_attribute("name")
                content = meta.get_attribute("content")
                if name:
                    metadados['meta'][name] = content
            return metadados
        except:
            time.sleep(1)  # espera 1 segundo e tenta novamente
    raise Exception("Não foi possível capturar os metadados: página ainda não carregou totalmente")


with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    context = browser.new_context(
        proxy={"server": f"http://{proxy_host}:{proxy_port}"},
        ignore_https_errors=True
    )

    page = context.new_page()
    page.goto("http://nfecd-gpa.unisys.com.br/eFormseMonitor/")
    page.wait_for_load_state("networkidle")
    time.sleep(2)

    # --- LOGIN COM PyAutoGUI ---
    gui.moveTo(684, 472)
    gui.leftClick()
    email = 'eduardo.barros@gpabr.com'
    senha = 'Acessogpa@2023'
    for char in email:
        gui.write(char)
    gui.hotkey('tab', 'tab', 'enter')
    time.sleep(1)
    gui.moveTo(805, 550)
    gui.leftClick()
    for char in senha:
        gui.write(char)
    gui.hotkey('tab', 'tab', 'enter')
    time.sleep(2)
    gui.hotkey('enter')
    time.sleep(1)

    gui.moveTo(1043, 494)
    time.sleep(2)
    gui.leftClick()
    user_monitor = 'GPM.felipe.ferreira'
    senha_monitor = 'Brx@2022'
    for char in user_monitor:
        gui.write(char)
    time.sleep(1)
    gui.hotkey('tab')
    time.sleep(1)
    for char in senha_monitor:
        gui.write(char)
    time.sleep(1)
    gui.hotkey('tab', 'enter')

    # --- SCRAPING DOS METADADOS ---
    time.sleep(7)  # espera a página final carregar
    
    page.wait_for_load_state("networkidle")  
    time.sleep(2)  # pequeno delay extra se necessário
    # metadados = scrap_metadados(page)
    # print("Metadados coletados:")
    # print(metadados)
    time.sleep(2)
    gui.moveTo(215,618)
    gui.leftClick()
    time.sleep(1)

    for i in range(5):
        gui.hotkey('tab')

    date_initial = (datetime.today() - timedelta(days=30)).strftime("%d/%m/%Y").replace('/','')
    for data in date_initial:
        gui.write(data)
    time.sleep(1)
    gui.moveTo(147,976)
    gui.leftClick()
    print("Login realizado! Navegador permanece aberto.")
    input("Pressione Enter no terminal para finalizar o script...")  # mantém o navegador aberto

    
  
    
