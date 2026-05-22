@echo off
chcp 65001 > nul
title IDOR Guvenlik Laboratuvari - Masaustu

echo ============================================================
echo   IDOR Guvenlik Laboratuvari - Masaustu Modu
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

echo [3/3] Masaustu penceresi aciliyor...
python desktop.py
pause
