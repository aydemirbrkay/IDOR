#!/bin/bash
# IDOR Güvenlik Laboratuvarı — Masaüstü uygulamasını başlatır (pywebview)
set -e
cd "$(dirname "$0")"

echo "============================================================"
echo "  IDOR Güvenlik Laboratuvarı — Masaüstü Modu"
echo "============================================================"

if ! command -v python3 &> /dev/null; then
  echo "[HATA] python3 bulunamadı."
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

# Linux'ta WebKitGTK gerekli — yoksa kullanıcıya net bir mesaj ver
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  if ! python3 -c "import gi; gi.require_version('WebKit2', '4.1')" 2>/dev/null && \
     ! python3 -c "import gi; gi.require_version('WebKit2', '4.0')" 2>/dev/null; then
    echo
    echo "[UYARI] Linux'ta pywebview için WebKitGTK gerekli."
    echo "  Debian/Ubuntu: sudo apt install gir1.2-webkit2-4.1 python3-gi gir1.2-gtk-3.0"
    echo "  Fedora       : sudo dnf install python3-gobject webkit2gtk4.1"
    echo
  fi
fi

echo "[3/3] Masaüstü penceresi açılıyor..."
python3 desktop.py
