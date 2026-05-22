@echo off
chcp 65001 > nul
title IDOR Guvenlik Laboratuvari
REM IDOR Guvenlik Laboratuvari - Windows baslatici
REM ------------------------------------------------
REM Bu script sunlari yapar:
REM   1) Python kurulu mu kontrol eder
REM   2) .venv yoksa olusturur
REM   3) requirements.txt'i yukler
REM   4) Flask sunucusunu baslatir
REM
REM ILK KULLANIM: run.bat dosyasina cift tikla.
REM Tarayicidan acacagin adres: http://localhost:5000
REM Demo kullanici: ahmet / ahmet123

echo ============================================================
echo   IDOR Guvenlik Laboratuvari
echo ============================================================

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi!
    echo.
    echo   1) https://python.org adresinden Python 3.10+ indir
    echo   2) Kurulumda "Add Python to PATH" kutucugunu mutlaka isaretle
    echo   3) Bilgisayari yeniden baslat, sonra bu dosyaya tekrar cift tikla
    pause
    exit /b 1
)

if not exist ".venv" (
    echo [1/3] Sanal ortam olusturuluyor (.venv)...
    python -m venv .venv
) else (
    echo [1/3] Sanal ortam zaten mevcut - atlandi.
)

echo [2/3] Bagimliliklar yukleniyor (Flask, requests)...
call .venv\Scripts\activate.bat
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo [3/3] Uygulama baslatiliyor...
echo   Tarayicidan ac       : http://localhost:5000
echo   Demo kullanicilar    : ahmet/ahmet123, mehmet/mehmet123,
echo                           ayse/ayse123, admin/admin123
echo   Durdurmak icin       : Ctrl+C
echo ============================================================
python app.py
pause
