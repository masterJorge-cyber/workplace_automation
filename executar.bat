@echo off
echo ====================================
echo  EXECUTOR NF-SCRAPER
echo ====================================

echo.
echo 1. Ativando ambiente virtual...
call "venv\Scripts\activate.bat"

echo.
echo 2. Executando aplicação...
python main.py

echo.
echo ⏎ Pressione Enter para sair...
pause