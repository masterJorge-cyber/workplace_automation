# 🚀 Como Executar o NF-Scraper

## 📋 Pré-requisitos
- Windows 10/11
- Python 3.8 ou superior
- Conexão com internet

## 🛠️ Instalação (Primeira Vez)

### Opção 1 - Automática (Recomendado)
1. Extraia o projeto em qualquer pasta (ex: `C:\Users\SeuNome\Documents\nf-scraper`)
2. Execute `installar.bat` como Administrador
3. Execute `instalar-playwright.bat`

### Opção 2 - Manual
```cmd
# 1. Criar ambiente virtual
python -m venv "venv"

# 2. Ativar ambiente
venv\Scripts\activate.bat

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Instalar Playwright
playwright install chromium