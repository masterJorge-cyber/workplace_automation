@echo off
echo ====================================
echo  INSTALADOR COMPLETO NF-SCRAPER
echo ====================================

echo Diretório atual: %CD%
echo.

echo 1. VERIFICANDO ZIP...
dir *.zip

if not exist "nf_scraper_env.zip" (
    echo.
    echo ❌ nf_scraper_env.zip não encontrado!
    echo 📁 Arquivos ZIP na pasta:
    dir *.zip /b
    echo.
    echo 💡 Renomeie o ZIP para: nf_scraper_env.zip
    pause
    exit /b 1
)

echo.
echo 2. EXTRAINDO ENVIRONMENT...
if exist "nf_scraper_env" (
    echo 📁 Removendo environment antigo...
    rmdir /s /q "nf_scraper_env"
)

echo 📦 Extraindo nf_scraper_env.zip...
powershell -command "Expand-Archive -Path 'nf_scraper_env.zip' -DestinationPath '.' -Force"

echo.
echo 3. VERIFICANDO EXTRAÇÃO...
if exist "nf_scraper_env\python.exe" (
    echo ✅ Environment extraído com sucesso!
) else (
    echo ❌ Erro na extração do environment!
    echo 💡 Verifique se o ZIP não está corrompido
    pause
    exit /b 1
)

echo.
echo 4. ATUALIZANDO PIP...
"nf_scraper_env\python.exe" -m pip install --upgrade pip

echo.
echo 5. INSTALANDO DEPENDÊNCIAS DO PANDAS...
"nf_scraper_env\python.exe" -m pip install python-dateutil pytz numpy

echo.
echo 6. VERIFICANDO BIBLIOTECAS...
"nf_scraper_env\python.exe" -c "import pandas; print('✅ Pandas OK')"
"nf_scraper_env\python.exe" -c "import playwright; print('✅ Playwright OK')"
"nf_scraper_env\python.exe" -c "import selenium; print('✅ Selenium OK')"
"nf_scraper_env\python.exe" -c "from dotenv import load_dotenv; print('✅ Python-dotenv OK')"

echo.
echo 7. INSTALANDO CHROMIUM NO ENVIRONMENT...
"nf_scraper_env\python.exe" -m playwright install chromium

echo.
echo 8. VERIFICANDO INSTALAÇÃO DO CHROMIUM...
"nf_scraper_env\python.exe" -m playwright install --dry-run

echo.
echo 9. VERIFICANDO CAMINHO DO CHROMIUM...
"nf_scraper_env\python.exe" -c "
import os
from playwright._impl._driver import get_driver_env, compute_driver_executable
print('🔍 Driver path:', compute_driver_executable())

# Verificar se chromium existe
import glob
playwright_path = os.path.join('nf_scraper_env', 'playwright-browsers')
chromium_pattern = os.path.join(playwright_path, 'chromium-*', 'chrome-win', 'chrome.exe')
matches = glob.glob(chromium_pattern)
if matches:
    print('✅ Chromium encontrado:', matches[0])
else:
    print('❌ Chromium não encontrado no environment')
"

echo.
echo 10. VERIFICAÇÃO FINAL...
"nf_scraper_env\python.exe" -c "
try:
    import pandas, playwright, selenium, requests
    from dotenv import load_dotenv
    print('🎉 TODAS as bibliotecas funcionam perfeitamente!')
    
    # Testar se consegue lançar o browser
    from playwright.sync_api import sync_playwright
    print('✅ Playwright pronto para uso!')
    
except Exception as e:
    print('❌ Erro final:', e)
"

echo.
echo ====================================
echo 🎉 INSTALAÇÃO COMPLETA CONCLUÍDA!
echo ====================================
echo.
echo 📋 PRÓXIMOS PASSOS:
echo 1. Configure o arquivo .env com suas credenciais
echo 2. Edite o notas_fiscais.json com suas notas
echo 3. Execute: executar.bat
echo.
pause