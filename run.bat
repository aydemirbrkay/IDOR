@echo off
chcp 65001 > nul
title IDOR Guvenlik Simulasyonu

echo ============================================================
echo   IDOR Guvenlik Simulasyonu - Baslatiliyor
echo ============================================================

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! https://python.org adresinden yukleyin.
    pause & exit /b 1
)

if not exist ".venv" (
    echo [1/3] Sanal ortam olusturuluyor...
    python -m venv .venv
)

echo [2/3] Bagimliliklar yukleniyor...
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt

echo [3/3] Uygulama baslatiliyor...
echo.
echo  GUI icin : python main_gui.py
echo  API icin : python app.py
echo  Testler  : python test_cases.py
echo  Demo     : python exploit_demo.py (ayri terminalde, app.py calisirken)
echo.

python main_gui.py
pause
