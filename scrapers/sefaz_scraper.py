import time
import logging
from playwright.sync_api import Page, TimeoutError
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class SefazScraper:
    def __init__(self, page: Page):
        self.page = page
        self.timeout = 30000
    
    def wait_and_click(self, selector: str, description: str = ""):
        """Espera elemento e clica"""
        try:
            logger.info(f"🖱️ Clicando em: {description}")
            self.page.wait_for_selector(selector, timeout=self.timeout)
            self.page.click(selector)
            time.sleep(1)
            return True
        except TimeoutError:
            logger.error(f"❌ Não encontrei: {description}")
            return False
    
    def wait_and_fill(self, selector: str, text: str, description: str = ""):
        """Espera elemento e preenche"""
        try:
            logger.info(f"⌨️ Preenchendo {description}")
            self.page.wait_for_selector(selector, timeout=self.timeout)
            self.page.fill(selector, text)
            time.sleep(0.5)
            return True
        except TimeoutError:
            logger.error(f"❌ Não encontrei campo: {description}")
            return False
    
    def marcar_captcha(self) -> bool:
        """Marca o checkbox do captcha 'Sou humano'"""
        try:
            logger.info("🤖 Marcando captcha 'Sou humano'...")
            
            # Seletores possíveis para o captcha hCaptcha
            captcha_selectors = [
                "iframe[src*='hcaptcha']",
                "iframe[title*='hCaptcha']",
                "iframe[src*='captcha']",
                ".h-captcha iframe"
            ]
            
            # Encontrar o iframe do captcha
            captcha_iframe = None
            for selector in captcha_selectors:
                try:
                    captcha_iframe = self.page.wait_for_selector(selector, timeout=5000)
                    if captcha_iframe:
                        logger.info(f"✅ Iframe do captcha encontrado: {selector}")
                        break
                except:
                    continue
            
            if not captcha_iframe:
                logger.error("❌ Iframe do captcha não encontrado")
                return False
            
            # Entrar no iframe do captcha
            captcha_frame = captcha_iframe.content_frame()
            if not captcha_frame:
                logger.error("❌ Não consegui acessar o frame do captcha")
                return False
            
            # Marcar o checkbox dentro do iframe
            checkbox_selectors = [
                "div#checkbox",
                ".challenge-form input[type='checkbox']",
                "input[type='checkbox']",
                ".hcaptcha-box"
            ]
            
            for selector in checkbox_selectors:
                try:
                    captcha_frame.wait_for_selector(selector, timeout=5000)
                    captcha_frame.click(selector)
                    logger.info("✅ Captcha marcado com sucesso")
                    time.sleep(2)
                    return True
                except Exception as e:
                    logger.debug(f"❌ Seletor {selector} falhou: {e}")
                    continue
            
            logger.error("❌ Não consegui marcar o captcha")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao marcar captcha: {e}")
            return False
    
    def marcar_captcha_alternativo(self) -> bool:
        """Alternativa para marcar o captcha usando coordenadas ou abordagem diferente"""
        try:
            logger.info("🔄 Tentando abordagem alternativa para captcha...")
            
            # Tentar encontrar qualquer elemento de captcha visível
            captcha_elements = self.page.query_selector_all("div[class*='captcha'], div[class*='hcaptcha'], .challenge-container, iframe")
            
            for element in captcha_elements:
                try:
                    # Verificar se está visível e clicável
                    if element.is_visible():
                        box = element.bounding_box()
                        if box:
                            # Clicar no centro do elemento
                            self.page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                            logger.info("✅ Captcha clicado via coordenadas")
                            time.sleep(2)
                            return True
                except:
                    continue
            
            # Tentar buscar por texto "Sou humano" ou similar
            sou_humano_selectors = [
                "text=Sou humano",
                "text=I'm human",
                "text=human",
                "div:has-text('humano')",
                "label:has-text('humano')"
            ]
            
            for selector in sou_humano_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=3000)
                    self.page.click(selector)
                    logger.info(f"✅ Captcha encontrado por texto: {selector}")
                    time.sleep(2)
                    return True
                except:
                    continue
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro na abordagem alternativa: {e}")
            return False
    
    def preencher_chave_acesso(self, nota_fiscal: str) -> bool:
        """Preenche a chave de acesso no campo correto"""
        try:
            logger.info(f"🔑 Preenchendo chave de acesso: {nota_fiscal}")
            
            # Usar o seletor que sabemos que funciona
            chave_selector = "input#ctl00_ContentPlaceHolder1_txtChaveAcessoResumo"
            
            self.page.wait_for_selector(chave_selector, timeout=self.timeout)
            self.page.fill(chave_selector, "")
            self.page.fill(chave_selector, nota_fiscal)
            
            # Verificar se preencheu corretamente
            valor_preenchido = self.page.input_value(chave_selector)
            if valor_preenchido == nota_fiscal:
                logger.info("✅ Chave preenchida com sucesso")
                return True
            else:
                logger.warning(f"⚠️ Chave preenchida mas valor diferente: {valor_preenchido}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro ao preencher chave: {e}")
            return False
    
    def clicar_continuar(self) -> bool:
        """Clica no botão Continuar"""
        try:
            logger.info("🖱️ Clicando em Continuar...")
            
            continuar_selectors = [
                "input#ctl00_ContentPlaceHolder1_btnConsultarHCaptcha",
                "input[name='ctl00$ContentPlaceHolder1$btnConsultarHCaptcha']",
                "input.botao[type='submit']",
                "input[value='Continuar']"
            ]
            
            for selector in continuar_selectors:
                try:
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.page.click(selector)
                    logger.info(f"✅ Botão Continuar clicado: {selector}")
                    
                    # Aguardar ação do botão
                    time.sleep(3)
                    return True
                except Exception as e:
                    logger.debug(f"❌ Seletor {selector} falhou: {e}")
                    continue
            
            logger.error("❌ Nenhum botão Continuar funcionou")
            return False
            
        except Exception as e:
            logger.error(f"❌ Erro ao clicar em Continuar: {e}")
            return False
    
    def consultar_nota_sefaz(self, nota_fiscal: str) -> Dict:
        """Consulta nota na Sefaz e extrai protocolo"""
        logger.info(f"🌐 Consultando nota na Sefaz: {nota_fiscal}")
        
        try:
            # 1. Navegar para Sefaz
            logger.info("1. 🌐 Navegando para Sefaz...")
            self.page.goto(
                "https://www.nfe.fazenda.gov.br/portal/consultaRecaptcha.aspx?tipoConsulta=resumo&tipoConteudo=7PhJ+gAVw2g=", 
                wait_until="domcontentloaded"
            )
            time.sleep(3)
            
            # 2. Preencher chave de acesso
            logger.info("2. 🔑 Preenchendo chave de acesso...")
            if not self.preencher_chave_acesso(nota_fiscal):
                return {"nota": nota_fiscal, "protocolo": "Erro: Campo chave não preenchido"}
            
            time.sleep(2)
            
            # 3. Marcar captcha
            logger.info("3. 🤖 Marcando captcha...")
            captcha_marcado = self.marcar_captcha()
            
            if not captcha_marcado:
                logger.warning("🔄 Tentando abordagem alternativa para captcha...")
                captcha_marcado = self.marcar_captcha_alternativo()
            
            if not captcha_marcado:
                logger.error("❌ Não foi possível marcar o captcha")
                return {"nota": nota_fiscal, "protocolo": "Erro: Captcha não marcado"}
            
            time.sleep(2)
            
            # 4. Clicar em Continuar
            logger.info("4. ✅ Clicando em Continuar...")
            if not self.clicar_continuar():
                return {"nota": nota_fiscal, "protocolo": "Erro: Botão Continuar não funcionou"}
            
            # 5. Aguardar resultado
            logger.info("5. ⏳ Aguardando resultado...")
            time.sleep(5)
            self.page.wait_for_load_state("networkidle")
            
            # 6. Extrair protocolo
            logger.info("6. 📄 Extraindo protocolo...")
            protocolo = self.extrair_protocolo(nota_fiscal)
            
            return {
                "nota": nota_fiscal,
                "protocolo": protocolo,
                "consulta_realizada": True,
                "captcha_resolvido": captcha_marcado
            }
            
        except Exception as e:
            logger.error(f"❌ Erro na consulta Sefaz: {e}")
            return {
                "nota": nota_fiscal, 
                "protocolo": f"Erro: {str(e)}",
                "consulta_realizada": False
            }
    
    def extrair_protocolo(self, nota_fiscal: str) -> str:
        """Extrai protocolo da tabela de resultados"""
        try:
            # Aguardar tabela
            self.page.wait_for_selector("table.tabNFe", timeout=10000)
            time.sleep(2)
            
            # Buscar protocolo
            protocolo_selector = "table.tabNFe tbody tr:first-child td:nth-child(2)"
            protocolo_element = self.page.query_selector(protocolo_selector)
            
            if protocolo_element:
                protocolo = protocolo_element.inner_text().strip()
                logger.info(f"✅ Protocolo encontrado: {protocolo}")
                return protocolo
            else:
                logger.warning("⚠️ Protocolo não encontrado na tabela")
                return "Protocolo não encontrado"
                
        except Exception as e:
            logger.error(f"❌ Erro ao extrair protocolo: {e}")
            return f"Erro extração: {str(e)}"