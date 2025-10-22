@echo off
echo ====================================
echo  ATUALIZANDO NF-SCRAPER
echo ====================================

echo.
echo 1. Ativando ambiente virtual...
call "venv\Scripts\activate.bat"

echo.
echo 2. Atualizando dependências...
pip install -r requirements.txt --upgrade

echo.
echo 3. Verificando atualizações...
pip list

echo.
echo ✅ Atualização concluída!
pause