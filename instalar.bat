@echo off
echo ====================================
echo  INSTALADOR NF-SCRAPER
echo ====================================

echo.
echo 1. Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python não encontrado!
    echo 📥 Baixe em: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo.
echo 2. Criando ambiente virtual...
python -m venv "venv"

echo.
echo 3. Ativando ambiente virtual...
call "venv\Scripts\activate.bat"

echo.
echo 4. Instalando dependências...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo 5. Verificando instalação...
pip list

echo.
echo ✅ Instalação concluída!
echo.
echo Para executar o projeto:
echo   venv\Scripts\activate.bat
echo   python main.py
echo.
pause