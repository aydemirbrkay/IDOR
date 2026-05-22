#!/bin/bash
echo "============================================================"
echo "  IDOR Guvenlik Simulasyonu - Baslatiliyor"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
    echo "[HATA] Python3 bulunamadi!"
    echo "Mac: brew install python | Linux: sudo apt install python3 python3-venv"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "[1/3] Sanal ortam olusturuluyor..."
    python3 -m venv .venv
fi

echo "[2/3] Bagimliliklar yukleniyor..."
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[3/3] Uygulama baslatiliyor..."
python3 main_gui.py
