"""
desktop.py — IDOR Güvenlik Laboratuvarı (Masaüstü Uygulaması)
==============================================================
Flask sunucusunu arka planda başlatır ve web arayüzünü native bir
masaüstü penceresinde gösterir (pywebview).

  Windows  → Edge WebView2 (Win10/11 ön yüklü)
  macOS    → WebKit
  Linux    → WebKitGTK (paket: gir1.2-webkit2-4.0 / 4.1)

Çalıştırma:
    python3 desktop.py
"""

import os
import socket
import sys
import threading
import time

try:
    import webview  # pywebview
except ImportError:
    print("[HATA] 'pywebview' kurulu değil.")
    print("       Kurmak için: pip install pywebview")
    print("       Linux'ta ek olarak: sudo apt install gir1.2-webkit2-4.1 \\")
    print("                                          python3-gi gir1.2-gtk-3.0")
    sys.exit(1)

from app import app as flask_app


def _find_free_port(preferred: int = 5000) -> int:
    """Önce 5000'i dene, doluysa boş bir port bul."""
    for port in [preferred, 5050, 5500, 8000, 8080]:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    # Hepsi doluysa OS rastgele bir port versin
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _run_flask(port: int) -> None:
    # Sunucu thread'de çalışır; debug/reload kapalı
    flask_app.run(host="127.0.0.1", port=port, debug=False,
                  use_reloader=False, threaded=True)


def _wait_for_server(port: int, timeout: float = 5.0) -> bool:
    """Sunucunun gerçekten dinlemeye başlamasını bekle."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.1)
    return False


def main() -> int:
    port = _find_free_port()
    url = f"http://127.0.0.1:{port}/"

    print("=" * 60)
    print("  IDOR Güvenlik Laboratuvarı (Masaüstü)")
    print(f"  Yerel sunucu  : {url}")
    print(f"  Demo kullanıcı: ahmet / ahmet123")
    print("=" * 60)

    flask_thread = threading.Thread(
        target=_run_flask, args=(port,), daemon=True, name="flask-server")
    flask_thread.start()

    if not _wait_for_server(port):
        print("[HATA] Flask sunucusu beklenen sürede başlamadı.")
        return 1

    webview.create_window(
        title="IDOR Güvenlik Laboratuvarı",
        url=url,
        width=1280,
        height=820,
        min_size=(900, 600),
        # confirm_close yok — kullanıcı X'e basınca uygulama kapansın
    )

    # gui="" → en uygun backend otomatik seçilir
    # debug=False → DevTools kapalı (sunum için temiz görünüm)
    webview.start(debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
