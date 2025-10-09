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
        
        # 2. Preencher status "Rejeitado" no campo StatusId-input + TAB + espera
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
                    
                # 🔥 NOVO: Tab + espera de 1 segundo após escrever "Rejeitado"
                self.page.keyboard.press("Tab")
                logger.info("   ↪️  Tab pressionado após status")
                time.sleep(0.1)  # 🔥 Espera 1 segundo após o Tab
                break
        
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
                self.page.wait_for_selector("table", timeout=10000)
                time.sleep(3)
            except:
                logger.info(f"🔍 Tabela não encontrada - nota não existe: {nota_fiscal}")
                return {"nota_fiscal": nota_fiscal, "status": "Não tem nota", "dados_completos": {}}
            
            # BUSCAR PELA NOTA FISCAL - Estratégia mais abrangente
            linhas = self.page.query_selector_all("table tr")
            linha_encontrada = None
            
            for linha in linhas:
                try:
                    texto_linha = linha.inner_text()
                    
                    # Estratégias de busca:
                    # 1. Busca direta pela nota completa
                    if nota_fiscal in texto_linha:
                        linha_encontrada = linha
                        logger.info(f"✅ Nota encontrada (busca direta): {nota_fiscal}")
                        break
                    
                    # 2. Busca pelos últimos dígitos (pode estar truncada)
                    ultimos_12_digitos = nota_fiscal[-12:]
                    if ultimos_12_digitos in texto_linha:
                        linha_encontrada = linha
                        logger.info(f"✅ Nota encontrada (últimos 12 dígitos): {ultimos_12_digitos}")
                        break
                        
                    # 3. Busca por parte da chave (pode estar em colunas diferentes)
                    partes_nota = [nota_fiscal[i:i+8] for i in range(0, len(nota_fiscal), 8)]
                    for parte in partes_nota:
                        if parte in texto_linha:
                            linha_encontrada = linha
                            logger.info(f"✅ Nota encontrada (parte: {parte})")
                            break
                    if linha_encontrada:
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️  Erro ao buscar linha: {e}")
                    continue
            
            if not linha_encontrada:
                logger.info(f"🔍 Nota não encontrada na tabela após busca completa: {nota_fiscal}")
                # DEBUG: Mostra o que tem na tabela
                try:
                    primeira_linha = self.page.query_selector("table tr")
                    if primeira_linha:
                        logger.info(f"🔍 Primeira linha da tabela: {primeira_linha.inner_text()[:200]}...")
                except:
                    pass
                return {"nota_fiscal": nota_fiscal, "status": "Não tem nota", "dados_completos": {}}
            
            # EXTRAIR DADOS DA LINHA ENCONTRADA
            logger.info("🎯 Extraindo dados da linha encontrada...")
            
            # 1. Marcar a checkbox
            checkbox = linha_encontrada.query_selector("input[type='checkbox'][name='checkedRecords']")
            if checkbox:
                try:
                    checkbox.check()
                    valor_checkbox = checkbox.get_attribute('value') or ''
                    logger.info(f"✅ Checkbox marcada - Value: {valor_checkbox}")
                    time.sleep(1)
                except Exception as e:
                    logger.warning(f"⚠️  Não consegui marcar a checkbox: {e}")
            
            # 2. Extrair todas as células
            celulas = linha_encontrada.query_selector_all("td")
            dados_linha = {}
            
            # Mapeamento baseado no HTML que você mostrou
            headers = [
                'checkbox', 'codigo', 'numero_documento', 'chave_acesso', 'chave_consulta', 
                'tipo_documento', 'data_processamento', 'status', 'icone1', 'icone2', 
                'icone3', 'icone4', 'icone5', 'valor_total', 'valor_oculto', 
                'data_emissao', 'id_interno', 'nome_empresa', 'oculto', 'observacao'
            ]
            
            for i, celula in enumerate(celulas):
                if i < len(headers):
                    chave = headers[i]
                    valor = celula.inner_text().strip()
                    dados_linha[chave] = valor
                    logger.info(f"   📝 {chave}: {valor}")
                else:
                    chave = f"coluna_extra_{i}"
                    valor = celula.inner_text().strip()
                    dados_linha[chave] = valor
            
            # 3. Extrair dados específicos importantes
            # Status limpo (sem o link de ajuda)
            if celulas and len(celulas) > 7:
                status_com_limpeza = celulas[7].inner_text()
                status_limpo = status_com_limpeza.split('Clique aqui')[0].strip() if 'Clique aqui' in status_com_limpeza else status_com_limpeza
                dados_linha['status_limpo'] = status_limpo
                logger.info(f"✅ Status detalhado: {status_limpo}")
            
            # Observação completa
            observacao_celula = linha_encontrada.query_selector("td.t-last")
            if observacao_celula:
                observacao = observacao_celula.inner_text().strip()
                dados_linha['observacao_completa'] = observacao
                logger.info(f"📋 Observação completa: {observacao}")
            
            # Cor da linha (indica status)
            cor_linha = linha_encontrada.get_attribute('style') or ''
            if 'color: rgb(255, 0, 0)' in cor_linha:
                dados_linha['cor_status'] = 'VERMELHO-REJEITADO'
                logger.info("🎨 Status visual: REJEITADO (vermelho)")
            
            # Valor do checkbox
            if checkbox:
                dados_linha['checkbox_value'] = valor_checkbox
            
            logger.info(f"✅ Dados extraídos com sucesso: {len(dados_linha)} campos")
            
            return {
                "nota_fiscal": nota_fiscal,
                "status": dados_linha.get('status_limpo', dados_linha.get('status', 'Status não encontrado')),
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
        """Método legado para compatibilidade - usa extract_invoice_data mas retorna apenas o status"""
        logger.info("⚠️  Usando método legado extract_invoice_status")
        resultado = self.extract_invoice_data(nota_fiscal)
        
        # Se extract_invoice_data retornar a estrutura completa, extrai apenas o status
        if isinstance(resultado, dict) and 'status' in resultado:
            return resultado['status']
        else:
            # Se já for apenas o status, retorna direto
            return resultado
    def reprocessar_notas_selecionadas(self):
            """Clica em Reprocessar, marca Normal e confirma"""
            logger.info("🔄 Iniciando reprocessamento das notas selecionadas...")
            
            try:
                # 1. Clicar no botão "Reprocessar"
                logger.info("1. 📝 Clicando em 'Reprocessar'...")
                reprocessar_selectors = [
                    "div.div-action-act.Reprocess",
                    "div[title*='Reprocessar']",
                    "div[title*='reprocess']",
                    "//div[contains(@class, 'Reprocess')]",
                    "//div[contains(text(), 'Reprocessar')]"
                ]
                
                reprocessado = False
                for selector in reprocessar_selectors:
                    if self.wait_and_click(selector, "botão Reprocessar"):
                        reprocessado = True
                        logger.info(f"✅ Botão Reprocessar clicado com: {selector}")
                        break
                
                if not reprocessado:
                    logger.error("❌ Não consegui encontrar botão Reprocessar")
                    return False
                
                # Aguardar dialog abrir
                time.sleep(3)
                
                # 2. Marcar radio button "Normal" (já vem checked, mas vamos garantir)
                logger.info("2. 🔘 Marcando opção 'Normal'...")
                normal_selectors = [
                    "input#EmissionType[value='0']",
                    "input[name='EmissionType'][value='0']",
                    "input[type='radio'][value='0']"
                ]
                
                normal_marcado = False
                for selector in normal_selectors:
                    try:
                        self.page.wait_for_selector(selector, timeout=5000)
                        # Só clica se não estiver checked
                        is_checked = self.page.is_checked(selector)
                        if not is_checked:
                            self.page.click(selector)
                            logger.info(f"✅ Radio 'Normal' marcado com: {selector}")
                        else:
                            logger.info("✅ Radio 'Normal' já estava marcado")
                        normal_marcado = True
                        break
                    except:
                        continue
                
                if not normal_marcado:
                    logger.warning("⚠️  Não consegui encontrar/marcar radio 'Normal'")
                
                time.sleep(1)
                
                # 3. Clicar em "OK"
                logger.info("3. ✅ Clicando em 'OK'...")
                ok_selectors = [
                    "span.ui-button-text:has-text('OK')",
                    "button:has-text('OK')",
                    "input[value='OK']",
                    "//span[contains(text(), 'OK')]",
                    "//button[contains(text(), 'OK')]"
                ]
                
                ok_clicado = False
                for selector in ok_selectors:
                    if self.wait_and_click(selector, "botão OK"):
                        ok_clicado = True
                        logger.info(f"✅ Botão OK clicado com: {selector}")
                        break
                
                if not ok_clicado:
                    logger.error("❌ Não consegui encontrar botão OK")
                    return False
                
                # Aguardar processamento
                time.sleep(5)
                self.page.wait_for_load_state("networkidle")
                logger.info("✅ Reprocessamento concluído com sucesso!")
                return True
                
            except Exception as e:
                logger.error(f"❌ Erro durante reprocessamento: {e}")
                return False