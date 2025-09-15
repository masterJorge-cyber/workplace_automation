from playwright.sync_api import sync_playwright, Page
import pyautogui as gui
import time
from datetime import datetime, timedelta
import pandas as pd

proxy_host = "10.141.6.12"
proxy_port = 80
chave_not = '33250947508411264641551100000702955335309202'

def scrap_nf(page):
    page.wait_for_selector("div.t-grid-content table tbody tr")

    linhas = page.query_selector_all("div.t-grid-content table tbody tr")
    notas = []

    for idx, linha in enumerate(linhas):
        colunas = linha.query_selector_all("td")
        #print(f"\n➡ Linha {idx} tem {len(colunas)} colunas")
        valores = [c.inner_text().strip() for c in colunas]
        #print(valores)  # 

        if not colunas:
            continue

        # Monta dicionário dinâmico
        nota = {f"col_{i}": colunas[i].inner_text().strip() for i in range(len(colunas))}
        notas.append(nota)

    return notas


def scrap_metadados(page):
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
            time.sleep(1)
    raise Exception("Não foi possível capturar os metadados")


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
    time.sleep(2)

    gui.moveTo(215, 618)
    gui.leftClick()
    time.sleep(1)

    for i in range(5):
        gui.hotkey('tab')

    date_initial = (datetime.today() - timedelta(days=30)).strftime("%d/%m/%Y").replace('/','')
    for data in date_initial:
        gui.write(data)
    time.sleep(1)

    for i in range(5):
        gui.hotkey('tab')

    for nota in chave_not:
        gui.write(nota)
        
    time.sleep(1)
    gui.moveTo(147, 976)
    gui.leftClick()
    time.sleep(3)

    metadados = scrap_metadados(page)
    print("Metadados coletados:")
    print(metadados)

    print("\nColetando notas fiscais da tabela...")
    notas = scrap_nf(page)

    linhas_normalizadas = []
    for n in notas:
        linha = [n.get(f"col_{i}", "") for i in range(20)]
        linhas_normalizadas.append(linha)

    colunas = [f"col_{i}" for i in range(20)]
    df = pd.DataFrame(linhas_normalizadas, columns=colunas)

    rejeitadas = df[df['col_7'].str.contains("Rejeitado|Pendente", na=False)]

    print("\n📌 Todas as notas normalizadas:")
    print(df.head())

    print("\n❌ Notas rejeitadas/pendentes:")
    print(rejeitadas[['col_2','col_1','col_6','col_7','col_19']])

    print("\nLogin realizado! Navegador permanece aberto.")
    input("Pressione Enter no terminal para finalizar o script...")
