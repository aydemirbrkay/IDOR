#!/bin/bash
# IDOR Güvenlik Laboratuvarı — macOS/Linux başlatıcı
# ----------------------------------------------------
# Bu script şunları yapar:
#   1) Python3 var mı kontrol eder
#   2) .venv adında bir sanal ortam yoksa oluşturur
#   3) requirements.txt içindeki paketleri yükler
#   4) Flask sunucusunu başlatır → http://localhost:5000
#
# İLK KULLANIM:
#   chmod +x run.sh    (sadece bir kez gerekir)
#   ./run.sh
#
# Tarayıcından açacağın adres: http://localhost:5000
# Demo kullanıcı: ahmet / ahmet123
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  IDOR Guvenlik Laboratuvari"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
  echo "[HATA] python3 bulunamadi."
  echo
  echo "  macOS  : brew install python    (Homebrew kuruluysa)"
  echo "           veya https://python.org adresinden indir"
  echo "  Linux  : sudo apt install python3 python3-venv"
  echo "  (Debian/Ubuntu tabanli sistemler icin)"
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "  Python suru          : ${PY_VERSION}"

if [ ! -d ".venv" ]; then
  echo "[1/3] Sanal ortam olusturuluyor (.venv)..."
  python3 -m venv .venv
else
  echo "[1/3] Sanal ortam zaten mevcut (.venv) — atlandi."
fi

echo "[2/3] Bagimliliklar yukleniyor (Flask, requests)..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo
echo "[3/3] Uygulama baslatiliyor..."
echo "  Tarayicidan ac       : http://localhost:5000"
echo "  Demo kullanicilar    : ahmet/ahmet123, mehmet/mehmet123,"
echo "                          ayse/ayse123, admin/admin123"
echo "  Durdurmak icin       : Ctrl+C"
echo "============================================================"
python3 app.py
