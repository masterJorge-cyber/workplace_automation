@echo off
echo ====================================
echo  INSTALANDO PLAYWRIGHT
echo ====================================

call "venv\Scripts\activate.bat"
playwright install chromium

echo.
echo ✅ Playwright instalado!
pause