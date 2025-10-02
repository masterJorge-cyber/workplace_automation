import time
import pyautogui as gui
from typing import List

class AuthManager:
    def __init__(self):
        self.coordinates = {
            'initial_click': (684, 472),
            'password_click': (805, 550),
            'monitor_click': (1043, 494),
            'search_click': (215, 618),
            'search_button': (147, 976),
            'clear_search': (100, 976)  # Posição para limpar pesquisa (ajuste conforme necessário)
        }
    
    def type_with_delay(self, text: str, delay: float = 0.1):
        """Digita texto com delay entre os caracteres"""
        for char in text:
            gui.write(char)
            time.sleep(delay)
    
    def login_initial(self, email: str, password: str):
        """Realiza login inicial no sistema"""
        gui.moveTo(*self.coordinates['initial_click'])
        gui.leftClick()
        
        self.type_with_delay(email)
        gui.hotkey('tab', 'tab', 'enter')
        time.sleep(1)
        
        gui.moveTo(*self.coordinates['password_click'])
        gui.leftClick()
        self.type_with_delay(password)
        gui.hotkey('tab', 'tab', 'enter')
        time.sleep(2)
        gui.hotkey('enter')
        time.sleep(1)
    
    def login_monitor(self, user: str, password: str):
        """Realiza login no monitor"""
        gui.moveTo(*self.coordinates['monitor_click'])
        time.sleep(2)
        gui.leftClick()
        
        self.type_with_delay(user)
        time.sleep(1)
        gui.hotkey('tab')
        time.sleep(1)
        self.type_with_delay(password)
        time.sleep(1)
        gui.hotkey('tab', 'enter')
    
    def navigate_to_search(self):
        """Navega para a tela de pesquisa"""
        time.sleep(7)
        gui.moveTo(*self.coordinates['search_click'])
        gui.leftClick()
        time.sleep(1)
    
    def clear_search_fields(self):
        """Limpa os campos de pesquisa para nova busca"""
        # Navega para o campo de data
        for _ in range(5):
            gui.hotkey('tab')
        
        # Limpa o campo de data (Ctrl+A + Delete)
        gui.hotkey('ctrl', 'a')
        gui.press('delete')
        time.sleep(0.5)
        
        # Navega para o campo de nota fiscal
        for _ in range(5):
            gui.hotkey('tab')
        
        # Limpa o campo de nota fiscal
        gui.hotkey('ctrl', 'a')
        gui.press('delete')
        time.sleep(0.5)
    
    def fill_search_form(self, initial_date: str, nota_fiscal: str):
        """Preenche formulário de pesquisa para uma nota fiscal específica"""
        self.clear_search_fields()
        
        # Preenche data
        for data in initial_date:
            gui.write(data)
        time.sleep(1)
        
        # Navega para o campo de nota fiscal
        for _ in range(5):
            gui.hotkey('tab')
        
        # Preenche nota fiscal
        for nota in nota_fiscal:
            gui.write(nota)
        
        time.sleep(1)
        gui.moveTo(*self.coordinates['search_button'])
        gui.leftClick()
        time.sleep(3)