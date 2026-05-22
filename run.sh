#!/bin/bash
# IDOR Güvenlik Laboratuvarı — Web sunucusunu başlatır
set -e

cd "$(dirname "$0")"

echo "============================================================"
echo "  IDOR Güvenlik Laboratuvarı"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
  echo "[HATA] python3 bulunamadı."
  echo "       Mac:   brew install python"
  echo "       Linux: sudo apt install python3 python3-venv"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "[1/3] Sanal ortam oluşturuluyor (.venv)..."
  python3 -m venv .venv
fi

echo "[2/3] Bağımlılıklar yükleniyor..."
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[3/3] Uygulama başlatılıyor → http://localhost:5000"
echo "      Demo kullanıcılar: ahmet/ahmet123, mehmet/mehmet123,"
echo "                          ayse/ayse123, admin/admin123"
python3 app.py
