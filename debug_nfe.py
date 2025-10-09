import time
from playwright.sync_api import sync_playwright
import logging
import os
import xml.etree.ElementTree as ET
import csv
from datetime import datetime
import glob

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultaDanfeScraper:
    def __init__(self):
        self.page = None
        self.download_path = os.path.join(os.getcwd(), "xmls")
        self.csv_path = os.path.join(os.getcwd(),"sheets", "resultados_consultas.csv")
        
        # EXCLUIR XMLs ANTIGOS no início
        self.limpar_xmls_antigos()
        
        # Inicializar CSV
        self.inicializar_csv()
    
    def limpar_xmls_antigos(self):
        """Exclui todos os XMLs da pasta xmls no início"""
        if os.path.exists(self.download_path):
            xml_files = glob.glob(os.path.join(self.download_path, "*.xml"))
            for xml_file in xml_files:
                try:
                    os.remove(xml_file)
                    print(f"🗑️  Removido: {os.path.basename(xml_file)}")
                except Exception as e:
                    print(f"❌ Erro ao remover {xml_file}: {e}")
        else:
            os.makedirs(self.download_path)
            print(f"📁 Pasta 'xmls' criada: {self.download_path}")
    
    def inicializar_csv(self):
        """Cria/limpa o arquivo CSV com cabeçalhos"""
        # Garantir que a pasta sheets existe
        sheets_dir = os.path.dirname(self.csv_path)
        if not os.path.exists(sheets_dir):
            os.makedirs(sheets_dir)
        
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Nota_Fiscal', 'Protocolo', 'Data_Consulta', 'Arquivo_XML'])
        print(f"📄 CSV criado: {self.csv_path}")
    
    def adicionar_ao_csv(self, nota, protocolo, arquivo_xml):
        """Adiciona resultado ao CSV"""
        with open(self.csv_path, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                nota, 
                protocolo, 
                datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                arquivo_xml
            ])
        print(f"💾 Adicionado ao CSV: {nota} -> {protocolo}")
    
    def setup_browser(self):
        """Configura o navegador"""
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=False)
        
        context = browser.new_context(
            accept_downloads=True,
            viewport={'width': 1280, 'height': 720}
        )
        
        self.page = context.new_page()
        return browser

    def fazer_consulta_com_controle(self, chave_acesso):
        """Faz consulta com controle manual do captcha"""
        print(f"🔍 CONSULTANDO: {chave_acesso}")
        
        try:
            # Navegar para o site (apenas na primeira vez)
            if self.page.url != "https://consultadanfe.com/":
                self.page.goto("https://consultadanfe.com/", wait_until="networkidle")
                time.sleep(3)
            
            # Preencher campo da chave
            campo_chave = self.page.wait_for_selector("input#chave")
            campo_chave.click()
            campo_chave.fill("")
            campo_chave.fill(chave_acesso)
            
            print("✅ Chave preenchida!")
            print("🤖 AGORA: Resolva o CAPTCHA se aparecer...")
            input("⏯️  Após resolver o captcha (ou se não aparecer), pressione ENTER para BUSCAR...")
            
            # Clicar em BUSCAR após sua confirmação
            btn_buscar = self.page.wait_for_selector("#btn-chave")
            btn_buscar.click()
            
            print("🔄 Aguardando resultado...")
            time.sleep(5)
            
            # Verificar e baixar XML
            return self.verificar_e_baixar_xml(chave_acesso)
            
        except Exception as e:
            print(f"❌ Erro na consulta: {e}")
            return None

    def verificar_e_baixar_xml(self, chave_acesso):
        """Verifica se a consulta foi bem sucedida e baixa o XML"""
        try:
            # Verificar se apareceu o botão de download XML
            btn_xml = self.page.query_selector(".btn-download-premium.xml")
            
            if btn_xml and btn_xml.is_visible():
                print("📥 Baixando XML...")
                
                # Configurar handler de download
                with self.page.expect_download() as download_info:
                    btn_xml.click()
                    download = download_info.value
                    
                    # Salvar arquivo com nome da chave
                    arquivo_path = os.path.join(self.download_path, f"{chave_acesso}.xml")
                    download.save_as(arquivo_path)
                    
                    print(f"💾 XML salvo: {arquivo_path}")
                    
                    # Extrair protocolo do XML
                    protocolo = self.extrair_protocolo_xml(arquivo_path)
                    
                    # Adicionar ao CSV
                    self.adicionar_ao_csv(chave_acesso, protocolo, os.path.basename(arquivo_path))
                    
                    return {
                        "sucesso": True,
                        "chave": chave_acesso,
                        "arquivo": arquivo_path,
                        "protocolo": protocolo
                    }
            else:
                print("❌ Botão de download não encontrado")
                print("🖥️  Colocando navegador em PRIMEIRO PLANO...")
                
                # COLOCAR EM PRIMEIRO PLANO
                #self.page.bring_to_front()
                
                print("🤖 PROBLEMA NO DOWNLOAD DETECTADO!")
                print("💡 Verifique a página manualmente:")
                print("   - Se apareceu captcha, resolva")
                print("   - Se o download está disponível, clique manualmente")
                print("   - Ou se há algum erro na página")
                input("⏯️  Após resolver o problema, pressione ENTER para CONTINUAR...")
                
                # Tentar novamente após a intervenção manual
                return self.tentar_download_apos_intervencao(chave_acesso)
                
        except Exception as e:
            print(f"❌ Erro ao baixar XML: {e}")
            self.adicionar_ao_csv(chave_acesso, f"ERRO: {str(e)}", "N/A")
            return None

    def tentar_download_apos_intervencao(self, chave_acesso):
        """Tenta fazer o download após intervenção manual"""
        try:
            # Verificar novamente se o botão de download apareceu
            btn_xml = self.page.query_selector(".btn-download-premium.xml")
            
            if btn_xml and btn_xml.is_visible():
                print("🔄 Tentando download novamente...")
                
                with self.page.expect_download() as download_info:
                    btn_xml.click()
                    download = download_info.value
                    
                    arquivo_path = os.path.join(self.download_path, f"{chave_acesso}.xml")
                    download.save_as(arquivo_path)
                    
                    print(f"💾 XML salvo: {arquivo_path}")
                    
                    protocolo = self.extrair_protocolo_xml(arquivo_path)
                    self.adicionar_ao_csv(chave_acesso, protocolo, os.path.basename(arquivo_path))
                    
                    return {
                        "sucesso": True,
                        "chave": chave_acesso,
                        "arquivo": arquivo_path,
                        "protocolo": protocolo
                    }
            else:
                print("❌ Ainda não foi possível baixar o XML")
                self.adicionar_ao_csv(chave_acesso, "DOWNLOAD_FALHOU_APOS_INTERVENCAO", "N/A")
                return None
                
        except Exception as e:
            print(f"❌ Erro no download após intervenção: {e}")
            self.adicionar_ao_csv(chave_acesso, f"ERRO_INTERVENCAO: {str(e)}", "N/A")
            return None

    def extrair_protocolo_xml(self, xml_path):
        """Extrai o protocolo do arquivo XML baixado"""
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            # Namespace do XML da NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Buscar protocolo
            protNFe = root.find('.//nfe:protNFe', ns)
            if protNFe is not None:
                infProt = protNFe.find('nfe:infProt', ns)
                if infProt is not None:
                    protocolo = infProt.find('nfe:nProt', ns)
                    if protocolo is not None:
                        return protocolo.text
            
            return "Protocolo não encontrado no XML"
            
        except Exception as e:
            print(f"❌ Erro ao extrair protocolo: {e}")
            return f"Erro: {str(e)}"

    def clicar_nova_consulta(self):
        """Clica no botão 'Nova Consulta' para limpar o formulário"""
        try:
            btn_nova = self.page.query_selector(".btn-new-search")
            if btn_nova and btn_nova.is_visible():
                print("🔄 Clicando em 'Nova Consulta'...")
                btn_nova.click()
                time.sleep(2)
                return True
            else:
                print("⚠️  Botão 'Nova Consulta' não encontrado")
                return False
        except Exception as e:
            print(f"❌ Erro ao clicar em Nova Consulta: {e}")
            return False

    def consultar_nota_rapida(self, chave_acesso):
        """Consulta rápida para notas subsequentes"""
        try:
            print(f"🔍 CONSULTA RÁPIDA: {chave_acesso}")
            
            # Preencher campo da chave
            campo_chave = self.page.wait_for_selector("input#chave")
            campo_chave.click()
            campo_chave.fill("")
            campo_chave.fill(chave_acesso)
            time.sleep(1)
            
            # Clicar em BUSCAR (sem captcha nas demais)
            btn_buscar = self.page.wait_for_selector("#btn-chave")
            btn_buscar.click()
            
            print("🔄 Aguardando resultado...")
            time.sleep(5)
            
            return self.verificar_e_baixar_xml(chave_acesso)
            
        except Exception as e:
            print(f"❌ Erro na consulta rápida: {e}")
            self.adicionar_ao_csv(chave_acesso, f"ERRO: {str(e)}", "N/A")
            return None

    def consultar_multiplas_notas(self, lista_chaves):
        """Consulta múltiplas notas com controle manual do captcha"""
        print(f"🚀 INICIANDO CONSULTA DE {len(lista_chaves)} NOTAS")
        print("=" * 50)
        
        browser = self.setup_browser()
        resultados = []
        
        try:
            for i, chave in enumerate(lista_chaves, 1):
                print(f"\n[{i}/{len(lista_chaves)}] Processando: {chave}")
                
                if i == 1:
                    # Primeira nota - controle manual do captcha
                    resultado = self.fazer_consulta_com_controle(chave)
                else:
                    # Demais notas - consulta rápida
                    resultado = self.consultar_nota_rapida(chave)
                
                if resultado:
                    resultados.append(resultado)
                    
                    # Clicar em "Nova Consulta" após baixar o XML (exceto na última)
                    if i < len(lista_chaves):
                        self.clicar_nova_consulta()
                else:
                    resultados.append({
                        "sucesso": False,
                        "chave": chave,
                        "erro": "Falha na consulta"
                    })
                
                # Pausa entre consultas
                if i < len(lista_chaves):
                    time.sleep(2)
            
            return resultados
            
        except Exception as e:
            print(f"❌ Erro no processamento: {e}")
            return resultados
        finally:
            input("\n⏹️  Pressione ENTER para fechar o navegador...")
            browser.close()

    def exibir_resultados(self, resultados):
        """Exibe relatório final"""
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        
        sucessos = [r for r in resultados if r.get('sucesso')]
        falhas = [r for r in resultados if not r.get('sucesso')]
        
        print(f"✅ Notas baixadas com sucesso: {len(sucessos)}")
        print(f"❌ Notas com falha: {len(falhas)}")
        print(f"💾 Arquivo CSV: {self.csv_path}")
        print(f"📁 Pasta XMLs: {self.download_path}")
        
        if sucessos:
            print(f"\n📋 XMLs BAIXADOS:")
            for resultado in sucessos:
                print(f"   🎯 {resultado['chave']}")
                print(f"      📄 Protocolo: {resultado['protocolo']}")

# USO
def main():
    scraper = ConsultaDanfeScraper()
    
    # Suas notas fiscais
    notas_fiscais = [
    "35251047508411094037551100000220031339359138","35251047508411094037551100000220301339362217","35251047508411102900551100000257661339479187","35251047508411094037551100000218421339342062","35251047508411094037551100000220211339359497","35251047508411094037551100000218541339346352","35251047508411102153551100000214721339479439","35251047508411102900551100000258134339481498","35251047508411094037551100000217281339328073","35251047508411094037551100000218861339345600","35251047508411094037551100000218891339348962","35251047508411094037551100000218231339341257","35251047508411094037551100000217161339327033","35251047508411094037551100000220871339371081","35251047508411094037551100000217961339337218","35251047508411094037551100000217981339338723","35251047508411094037551100000220231339360708","35251047508411239884551100000262341339549180","35251047508411094037551100000216761339315577","35251047508411094037551100000218921339349212","35251047508411094037551100000218941339349101","35251047508411094037551100000217131339327317","35251047508411000903551100000309871339428060","35251047508411094037551100000219741339356178","35251047508411094037551100000218191339341041","35251047508411094037551100000217111339325468","35251047508411094037551100000218391339342814","35251047508411094037551100000218771339348309","35251047508411102900551100000260971339491090","35251047508411094037551100000216451339302380","35251047508411094037551100000218791339348206","35251047508411102153551100000216761339488012","35251047508411094037551100000218171339340938","35251047508411094037551100000218271339341850","35251047508411094037551100000218851339348670","35251047508411094037551100000216851339315622","35251047508411102900551100000259041339485312","35251047508411094037551100000217641339333227","35251047508411102900551100000258304339482126","35251047508411094037551100000217241339329283","35251047508411094037551100000218111339340608","35251047508411094037551100000218811339348395","35251047508411102900551100000260251339489038","35251047508411094037551100000219321339353446","35251047508411094037551100000218031339339497","35251047508411094037551100000220711339368161","35251047508411094037551100000220901339371753","35251047508411102900551100000256031339472136","35251047508411239884551100000258471339440770","35251047508411102900551100000257091339477102","35251047508411102900551100000259381339486562","35251047508411094037551100000216961339319338","35251047508411094037551100000216291339297153","35251047508411102900551100000257701339479260","35251047508411094037551100000220561339364356","35251047508411102900551100000260631339489853","35251047508411102153551100000219181339499041","35251047508411102153551100000215614339482991","35251047508411094037551100000220021339360171","35251047508411094037551100000218751339348118","35251047508411000903551100000311831339441025","35251047508411094037551100000217361339331378","35251047508411094037551100000219511339355053","35251047508411000903551100000310091339429324","35251047508411102900551100000260131339488510","35251047508411094037551100000218291339341293","35251047508411094037551100000217941339337507","35251047508411094037551100000219111339358626","35251047508411102900551100000261181339492021","35251047508411102900551100000259851339487542","35251047508411239884551100000258301339439618","35251047508411092921551100000294951339817143","35251047508411028409551100000279744339292894","35251047508411094037551100000216601339308570","35251047508411000903551100000309571339423786","35251047508411239884551100000260861339457477","35251047508411094037551100000216591339308200","35251047508411094037551100000217801339334839","35251047508411094037551100000219371339355097","35251047508411094037551100000218761339348271","35251047508411094037551100000218841339348567","35251047508411102153551100000217611339490087","35251047508411094037551100000218901339348505","35251047508411094037551100000219281339352447","35251047508411094037551100000217991339338747","35251047508411094037551100000217211339328366","35251047508411000903551100000314231339467901","35251047508411094037551100000216111339292017","35251047508411094037551100000219231339352033"

    ]
    
    print("🎯 FLUXO OTIMIZADO:")
    print("1. ✅ Limpa XMLs antigos automaticamente")
    print("2. Preenche nota automaticamente")
    print("3. PAUSA: Você resolve captcha se aparecer") 
    print("4. Pressione ENTER para BUSCAR")
    print("5. ⚠️  Se download falhar: Navegador vai para PRIMEIRO PLANO")
    print("6. 🔧 Você resolve problema manualmente")
    print("7. ⏯️  Pressione ENTER para continuar")
    print("8. Sistema tenta download novamente")
    print("9. Clica em 'Nova Consulta' automaticamente")
    print("10. Demais notas: Totalmente automático")
    print("=" * 50)
    
    resultados = scraper.consultar_multiplas_notas(notas_fiscais)
    scraper.exibir_resultados(resultados)

if __name__ == "__main__":
    main()