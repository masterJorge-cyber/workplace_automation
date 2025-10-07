import time
import logging
from playwright.sync_api import Page, TimeoutError
from typing import Optional
from datetime import datetime, timedelta

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuthManager:
    def __init__(self, page: Page):
        self.page = page
        self.timeout = 30000
    
    def wait_and_click(self, selector: str, description: str = ""):
        """Espera elemento e clica com debug"""
        try:
            logger.info(f"🖱️ Clicando em: {description}")
            self.page.wait_for_selector(selector, timeout=self.timeout)
            self.page.click(selector)
            time.sleep(1)
            return True
        except TimeoutError:
            logger.error(f"❌ Não encontrei: {description} - Seletor: {selector}")
            return False
    
    def wait_and_fill(self, selector: str, text: str, description: str = ""):
        """Espera elemento e preenche com debug"""
        try:
            logger.info(f"⌨️ Preenchendo {description}: {text}")
            self.page.wait_for_selector(selector, timeout=self.timeout)
            self.page.fill(selector, text)
            time.sleep(0.5)
            return True
        except TimeoutError:
            logger.error(f"❌ Não encontrei campo: {description} - Seletor: {selector}")
            return False
    
    def wait_and_type(self, selector: str, text: str, description: str = ""):
        """Espera elemento e digita com delay (para campos que precisam de trigger)"""
        try:
            logger.info(f"⌨️ Digitando {description}: {text}")
            self.page.wait_for_selector(selector, timeout=self.timeout)
            self.page.click(selector)  # Clica primeiro para focar
            time.sleep(0.5)
            self.page.keyboard.type(text)
            time.sleep(0.5)
            return True
        except TimeoutError:
            logger.error(f"❌ Não encontrei campo: {description} - Seletor: {selector}")
            return False
    
    def login_initial(self, email: str, password: str):
        """Primeiro login - email e senha inicial"""
        logger.info("🔐 Realizando primeiro login...")
        
        # Estratégia com múltiplos seletores para email
        email_selectors = [
            "input[type='email']",
            "input[name='username']",
            "input[placeholder*='email']",
            "input[placeholder*='Email']",
            "input:visible"
        ]
        
        # Tentar preencher email
        email_filled = False
        for selector in email_selectors:
            if self.wait_and_fill(selector, email, "email"):
                email_filled = True
                logger.info(f"✅ Email preenchido com: {selector}")
                break
        
        if not email_filled:
            logger.error("❌ Não consegui encontrar campo de email")
            return False
        
        time.sleep(1)
        
        # Estratégia para senha
        password_selectors = [
            "input[type='password']",
            "input[name*='password']",
            "input[placeholder*='password']",
            "input[placeholder*='senha']",
            "input:visible"
        ]
        
        # Navegar para senha (Tab + Enter)
        self.page.keyboard.press("Tab")
        time.sleep(0.5)
        self.page.keyboard.press("Tab")
        time.sleep(0.5)
        self.page.keyboard.press("Enter")
        time.sleep(2)
        
        # Preencher senha
        password_filled = False
        for selector in password_selectors:
            if self.wait_and_fill(selector, password, "senha"):
                password_filled = True
                logger.info(f"✅ Senha preenchida com: {selector}")
                break
        
        if not password_filled:
            logger.error("❌ Não consegui encontrar campo de senha")
            return False
        
        time.sleep(1)
        
        # Clicar em botão de login
        login_buttons = [
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Login')",
            "button:has-text('Entrar')", 
            "button:has-text('Acessar')",
            "button:visible"
        ]
        
        for selector in login_buttons:
            if self.wait_and_click(selector, "botão login"):
                logger.info(f"✅ Login acionado com: {selector}")
                break
        
        # Aguardar login e navegação para próxima tela
        time.sleep(5)
        self.page.wait_for_load_state("networkidle")
        logger.info("✅ Primeiro login realizado!")
        return True
    
    def handle_pagina_extra(self):
        """
        Manipula a página extra que aparece entre o primeiro login e o monitor
        """
        logger.info("🔄 Processando página extra/intermediária...")
        
        # Aguardar a página extra carregar
        time.sleep(3)
        self.page.wait_for_load_state("networkidle")
        
        logger.info(f"📄 Página extra - URL: {self.page.url}")
        logger.info(f"📄 Página extra - Título: {self.page.title()}")
        
        # Estratégia para página extra: 
        continuar_buttons = [
            "input[type='submit']",
            "button:has-text('Continuar')",
            "button:has-text('Próximo')", 
            "button:has-text('Avançar')",
            "button:has-text('Next')",
            "button[type='submit']",
            "button:visible",
            "a:visible"
        ]
        
        for selector in continuar_buttons:
            if self.wait_and_click(selector, "botão continuar"):
                logger.info(f"✅ Navegação da página extra com: {selector}")
                break
        
        # Se não encontrar botão específico, esperar redirecionamento automático
        time.sleep(3)
        self.page.wait_for_load_state("networkidle")
        
        logger.info("✅ Página extra processada!")
        return True
    
    def login_monitor(self, user: str, password: str):
        """Login no monitor com seletores específicos"""
        logger.info("👨‍💼 Realizando login no monitor...")
        
        # Aguardar tela do monitor carregar
        self.page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        logger.info(f"📄 Tela do monitor - URL: {self.page.url}")
        logger.info(f"📄 Tela do monitor - Título: {self.page.title()}")
        
        # Estratégia para usuário do monitor
        user_selectors = [
            "input[type='text']",
            "input[name='usuario']",
            "input[name*='user']",
            "input[placeholder*='usuário']",
            "input[placeholder*='usuario']",
            "input[placeholder*='user']", 
            "input:visible"
        ]
        
        # Preencher usuário do monitor
        user_filled = False
        for selector in user_selectors:
            if self.wait_and_fill(selector, user, "usuário monitor"):
                user_filled = True
                logger.info(f"✅ Usuário monitor preenchido com: {selector}")
                break
        
        if not user_filled:
            logger.error("❌ Não encontrei campo de usuário do monitor")
            return False
        
        time.sleep(1)
        
        # Tab para senha do monitor
        self.page.keyboard.press("Tab")
        time.sleep(1)
        
        # Estratégia para senha do monitor
        monitor_password_selectors = [
            "input[name='senha']",
            "input[type='password']",
            "input[name*='password']",
            "input[name*='senha']",
            "input[placeholder*='password']",
            "input[placeholder*='senha']",
            "input:visible"
        ]
        
        # Preencher senha do monitor
        password_filled = False
        for selector in monitor_password_selectors:
            try:
                self.page.wait_for_selector(selector, timeout=5000)
                self.page.fill(selector, password)
                password_filled = True
                logger.info(f"✅ Senha monitor preenchida com: {selector}")
                break
            except:
                continue
        
        if not password_filled:
            logger.error("❌ Não encontrei campo de senha do monitor")
            return False
        
        time.sleep(1)
        
        # Enter para login do monitor
        self.page.keyboard.press("Tab")
        time.sleep(0.5)
        self.page.keyboard.press("Enter")
        
        # Aguardar login do monitor
        time.sleep(5)
        self.page.wait_for_load_state("networkidle")
        logger.info("✅ Login no monitor realizado!")
        return True
    
    def navigate_to_search_screen(self):
        """Navega para tela de pesquisa de notas fiscais"""
        logger.info("🧭 Navegando para tela de pesquisa...")
        
        self.page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # Estratégia para encontrar botão/link de pesquisa
        search_selectors = [
            "//*[contains(text(), 'Pesquisa')]",  # Seletor específico que você encontrou
            "a:has-text('Pesquisa')",
            "button:has-text('Pesquisa')",
            "a:has-text('Consultar')", 
            "button:has-text('Consultar')",
            "a:has-text('Notas')",
            "button:has-text('Notas')",
            "a:visible",
            "button:visible"
        ]
        
        for selector in search_selectors:
            if self.wait_and_click(selector, "tela de pesquisa"):
                logger.info(f"✅ Navegação para pesquisa com: {selector}")
                break
        
        time.sleep(3)
        self.page.wait_for_load_state("networkidle")
        logger.info("✅ Navegação para pesquisa concluída!")
    
    def fill_search_form(self, initial_date: str, nota_fiscal: str):
        """Preenche formulário de pesquisa com chave da nota, datas e status Rejeitado"""
        logger.info(f"📋 Preenchendo pesquisa - Data: {initial_date}, Nota: {nota_fiscal}, Status: Rejeitado")
        
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # 1. Preencher chave da nota fiscal (DocKey)
        logger.info("1. 🔑 Preenchendo chave da nota fiscal...")
        dockey_selectors = [
            "input[name='DocKey']",
            "input[id='DocKey']",
            "input[placeholder*='chave']",
            "input[placeholder*='key']",
            "input[placeholder*='nota']"
        ]
        
        nota_preenchida = False
        for selector in dockey_selectors:
            if self.wait_and_fill(selector, nota_fiscal, "chave da nota"):
                nota_preenchida = True
                logger.info(f"✅ Chave da nota preenchida com: {selector}")
                break
        
        if not nota_preenchida:
            logger.error("❌ Não consegui encontrar campo DocKey")
            return False
        
        time.sleep(1)
        
        # 2. Preencher status "Rejeitado" no campo StatusId-input
        logger.info("2. 🚫 Preenchendo status 'Rejeitado'...")
        status_selectors = [
            "input[name='StatusId-input']",
            "input[id='StatusId-input']",
            "input[placeholder*='status']",
            "input[placeholder*='situação']"
        ]
        
        status_preenchido = False
        for selector in status_selectors:
            if self.wait_and_fill(selector, "Rejeitado", "status Rejeitado"):
                status_preenchido = True
                logger.info(f"✅ Status 'Rejeitado' preenchido com: {selector}")
                break
        
        if not status_preenchido:
            logger.warning("⚠️  Não consegui encontrar campo StatusId-input, continuando sem filtrar por status...")
        
        time.sleep(1)
        
        # 3. Preencher data inicial (StartDate) - 30 dias atrás
        logger.info("3. 📅 Preenchendo data inicial...")
        startdate_selectors = [
            "input[name='StartDate']",
            "input[id='StartDate']",
            "input[placeholder*='inicial']",
            "input[placeholder*='start']"
        ]
        
        # Limpar campo StartDate primeiro (Ctrl+A + Delete)
        for selector in startdate_selectors:
            try:
                self.page.wait_for_selector(selector, timeout=5000)
                self.page.click(selector)
                self.page.keyboard.press("Control+A")
                self.page.keyboard.press("Delete")
                logger.info(f"✅ Campo StartDate limpo com: {selector}")
                
                # Preencher com data inicial
                self.wait_and_type(selector, initial_date, "data inicial")
                break
            except:
                continue
        
        time.sleep(1)
        
        # 4. Data final (EndDate) já deve vir preenchida com hoje
        # Vamos apenas verificar se está correta
        logger.info("4. 📅 Verificando data final...")
        enddate_selectors = [
            "input[name='EndDate']", 
            "input[id='EndDate']"
        ]
        
        for selector in enddate_selectors:
            try:
                self.page.wait_for_selector(selector, timeout=3000)
                end_date_value = self.page.input_value(selector)
                logger.info(f"📅 Data final atual: {end_date_value}")
                break
            except:
                continue
        
        time.sleep(1)
        
        # 5. Clicar em pesquisar
        logger.info("5. 🔍 Clicando em pesquisar...")
        pesquisar_buttons = [
            "//*[contains(text(), 'Pesquisa')]",
            "button:has-text('Pesquisar')",
            "input[type='submit']",
            "button[type='submit']",
            "button:has-text('Consultar')",
            "button:has-text('Buscar')",
            "button:has-text('Search')",
            "button:visible"
        ]
        
        for selector in pesquisar_buttons:
            if self.wait_and_click(selector, "botão pesquisar"):
                logger.info(f"✅ Pesquisa acionada com: {selector}")
                break
        
        # Aguarda resultados
        logger.info("⏳ Aguardando resultados da pesquisa...")
        time.sleep(5)
        self.page.wait_for_load_state("networkidle")
        logger.info("✅ Pesquisa finalizada!")
        return True

    
    def extract_invoice_data(self, nota_fiscal: str):
        """Extrai todos os dados da linha da nota fiscal da tabela"""
        logger.info(f"📊 Extraindo dados completos para nota: {nota_fiscal}")
        
        try:
            # Aguardar tabela de resultados carregar
            try:
                self.page.wait_for_selector("table", timeout=5000)
                time.sleep(2)
            except:
                logger.info(f"🔍 Tabela não encontrada - nota não existe: {nota_fiscal}")
                return {"nota_fiscal": nota_fiscal, "status": "Não tem nota", "dados_completos": {}}
            
            # Encontrar a linha que contém a nota fiscal
            linhas = self.page.query_selector_all("table tr")
            linha_encontrada = None
            
            for linha in linhas:
                try:
                    texto_linha = linha.inner_text()
                    if nota_fiscal in texto_linha:
                        linha_encontrada = linha
                        logger.info(f"✅ Linha da nota encontrada na tabela")
                        break
                except:
                    continue
            
            if not linha_encontrada:
                logger.info(f"🔍 Nota não encontrada na tabela: {nota_fiscal}")
                return {"nota_fiscal": nota_fiscal, "status": "Não tem nota", "dados_completos": {}}
            
            # Marcar a checkbox da linha
            checkbox = linha_encontrada.query_selector("input[type='checkbox'][name='checkedRecords']")
            if checkbox:
                try:
                    checkbox.check()
                    logger.info("✅ Checkbox marcada")
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️  Não consegui marcar a checkbox: {e}")
            
            # Extrair todas as células da linha
            celulas = linha_encontrada.query_selector_all("td")
            dados_linha = {}
            
            # Cabeçalhos prováveis da tabela (baseado no HTML que você mostrou)
            headers = [
                'checkbox', 'codigo', 'numero', 'chave_acesso', 'chave_consulta', 
                'tipo', 'data_processamento', 'status', 'icone1', 'icone2', 
                'icone3', 'icone4', 'icone5', 'valor', 'valor_oculto', 
                'data_emissao', 'id_interno', 'empresa', 'oculto', 'observacao'
            ]
            
            for i, celula in enumerate(celulas):
                if i < len(headers):
                    chave = headers[i]
                    valor = celula.inner_text().strip()
                    dados_linha[chave] = valor
                    logger.info(f"   📝 {chave}: {valor}")
                else:
                    # Para colunas extras
                    chave = f"coluna_{i}"
                    valor = celula.inner_text().strip()
                    dados_linha[chave] = valor
            
            # Extrair status específico (removendo o link de ajuda)
            status_celula = linha_encontrada.query_selector("td:nth-child(8)")  # 8ª coluna é o status
            if status_celula:
                # Remove o conteúdo do link de ajuda para pegar só o texto do status
                status_texto = status_celula.inner_text()
                # Pega apenas a primeira parte (antes do link)
                status_limpo = status_texto.split('Clique aqui')[0].strip() if 'Clique aqui' in status_texto else status_texto
                dados_linha['status_limpo'] = status_limpo
                logger.info(f"✅ Status limpo: {status_limpo}")
            else:
                dados_linha['status_limpo'] = dados_linha.get('status', 'Status não encontrado')
            
            # Extrair observação específica
            observacao_celula = linha_encontrada.query_selector("td.t-last")
            if observacao_celula:
                dados_linha['observacao_detalhada'] = observacao_celula.inner_text().strip()
                logger.info(f"📋 Observação: {dados_linha['observacao_detalhada']}")
            
            return {
                "nota_fiscal": nota_fiscal,
                "status": dados_linha.get('status_limpo', 'Status não encontrado'),
                "dados_completos": dados_linha
            }
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair dados: {e}")
            return {
                "nota_fiscal": nota_fiscal,
                "status": f"Erro: {e}",
                "dados_completos": {}
            }
    def extract_invoice_status(self, nota_fiscal: str):
        """Método legado para compatibilidade - usa extract_invoice_data"""
        logger.info("⚠️  Usando método legado extract_invoice_status, migre para extract_invoice_data")
        resultado = self.extract_invoice_data(nota_fiscal)
        return resultado['status']