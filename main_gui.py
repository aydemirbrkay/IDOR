"""
main_gui.py — IDOR Güvenlik Simülasyonu Ana Arayüzü
=====================================================
Tkinter tabanlı eğitici GUI.
Flask sunucusunu arka planda başlatır ve HTTP istekleri
üzerinden gerçek API çağrıları yapar.

Paneller:
  Sol  → Saldırgan Paneli (attacker perspective)
  Sağ  → Sunucu/Kurban Paneli (server logs + stats)

Çalıştır: python main_gui.py
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, font as tkfont
import threading
import requests
import json
import time
import sys
import os

# Flask uygulamasını import et (aynı dizinde app.py olmalı)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app as flask_app, SECURE_MODE, STATS

# ---------------------------------------------------------------
# RENK PALETİ (Koyu tema)
# ---------------------------------------------------------------
C = {
    "bg":         "#1e1e2e",   # Ana arka plan
    "panel":      "#252540",   # Panel arka planı
    "card":       "#2d2d4e",   # Kart/kutu arka planı
    "border":     "#44446a",   # Kenar çizgisi
    "text":       "#cdd6f4",   # Ana metin
    "dim":        "#6c7086",   # Soluk metin
    "red":        "#f38ba8",   # Hata / saldırı
    "green":      "#a6e3a1",   # Başarı / güvenli
    "yellow":     "#f9e2af",   # Uyarı
    "blue":       "#89b4fa",   # Bilgi / vurgu
    "cyan":       "#89dceb",   # Başlık
    "purple":     "#cba6f7",   # Mod göstergesi
    "btn_red":    "#e06c75",   # Kırmızı buton
    "btn_green":  "#98c379",   # Yeşil buton
    "btn_blue":   "#61afef",   # Mavi buton
    "btn_gray":   "#5c6370",   # Gri buton
}

BASE_URL = "http://localhost:5000"


# ---------------------------------------------------------------
# FLASK SUNUCUSUNU ARKA PLANDA BAŞLAT
# ---------------------------------------------------------------

def start_flask():
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)  # Flask konsolunu sustur
    flask_app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def wait_for_server(timeout: int = 8) -> bool:
    for _ in range(timeout * 2):
        try:
            requests.get(f"{BASE_URL}/admin/mode", timeout=0.5)
            return True
        except Exception:
            time.sleep(0.5)
    return False


# ---------------------------------------------------------------
# YARDIMCI: Metin widget'ına renkli satır ekle
# ---------------------------------------------------------------

def append_log(widget: scrolledtext.ScrolledText, text: str, tag: str = "normal"):
    widget.config(state=tk.NORMAL)
    widget.insert(tk.END, text + "\n", tag)
    widget.see(tk.END)
    widget.config(state=tk.DISABLED)


def clear_log(widget: scrolledtext.ScrolledText):
    widget.config(state=tk.NORMAL)
    widget.delete("1.0", tk.END)
    widget.config(state=tk.DISABLED)


# ---------------------------------------------------------------
# ANA UYGULAMA SINIFI
# ---------------------------------------------------------------

class IDORSimApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IDOR Güvenlik Simülasyonu — Eğitici Demo")
        self.geometry("1200x720")
        self.minsize(1000, 600)
        self.configure(bg=C["bg"])
        self.resizable(True, True)

        self.session = requests.Session()
        self.logged_in = False
        self.current_user = None

        self._build_ui()
        self._start_server()
        self._start_stats_updater()

    # ----------------------------------------------------------
    # UI İNŞASI
    # ----------------------------------------------------------

    def _build_ui(self):
        # ── Başlık çubuğu
        self._build_topbar()

        # ── İki panel
        content = tk.Frame(self, bg=C["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        self.attacker_panel = AttackerPanel(content, self)
        self.attacker_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.server_panel = ServerPanel(content, self)
        self.server_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # ── Alt durum çubuğu
        self._build_statusbar()

    def _build_topbar(self):
        bar = tk.Frame(self, bg=C["card"], height=52)
        bar.pack(fill=tk.X, padx=10, pady=(10, 6))
        bar.pack_propagate(False)

        # Başlık
        tk.Label(bar, text="⬡  IDOR Güvenlik Simülasyonu",
                 bg=C["card"], fg=C["cyan"],
                 font=("Consolas", 15, "bold")).pack(side=tk.LEFT, padx=16)

        # Mod toggle butonu (sağda)
        self.mode_btn = tk.Button(
            bar, text="⚠  ZAFİYETLİ MOD",
            bg=C["btn_red"], fg="white",
            font=("Consolas", 10, "bold"),
            relief=tk.FLAT, padx=14, pady=6,
            cursor="hand2",
            command=self._toggle_mode,
        )
        self.mode_btn.pack(side=tk.RIGHT, padx=16, pady=8)

        # Sunucu durum göstergesi
        self.server_status_lbl = tk.Label(
            bar, text="● Sunucu başlatılıyor...",
            bg=C["card"], fg=C["yellow"],
            font=("Consolas", 9),
        )
        self.server_status_lbl.pack(side=tk.RIGHT, padx=10)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=C["card"], height=26)
        bar.pack(fill=tk.X, padx=10, pady=(0, 6))
        bar.pack_propagate(False)

        self.status_lbl = tk.Label(
            bar, text="Sunucu başlatılıyor...",
            bg=C["card"], fg=C["dim"],
            font=("Consolas", 8),
        )
        self.status_lbl.pack(side=tk.LEFT, padx=10)

        tk.Label(bar, text="Yazılım Güvenliği Eğitim Projesi — IDOR Demo",
                 bg=C["card"], fg=C["dim"],
                 font=("Consolas", 8)).pack(side=tk.RIGHT, padx=10)

    # ----------------------------------------------------------
    # SUNUCU BAŞLATMA
    # ----------------------------------------------------------

    def _start_server(self):
        t = threading.Thread(target=start_flask, daemon=True)
        t.start()

        def check():
            ok = wait_for_server()
            if ok:
                self.server_status_lbl.config(text="● Sunucu hazır", fg=C["green"])
                self.status_lbl.config(text="Flask sunucu http://127.0.0.1:5000 adresinde çalışıyor.")
                self.attacker_panel.on_server_ready()
            else:
                self.server_status_lbl.config(text="● Sunucu başlatılamadı", fg=C["red"])
                self.status_lbl.config(text="HATA: Sunucu başlatılamadı.")

        threading.Thread(target=check, daemon=True).start()

    # ----------------------------------------------------------
    # MOD TOGGLE
    # ----------------------------------------------------------

    def _toggle_mode(self):
        try:
            r = self.session.post(f"{BASE_URL}/admin/toggle-mode")
            data = r.json()
            secure = data["secure"]
            if secure:
                self.mode_btn.config(text="✔  GÜVENLİ MOD", bg=C["btn_green"])
                self.server_panel.log(
                    "━━━ MOD DEĞİŞTİ: GÜVENLİ ━━━ Sahiplik kontrolü AKTİF",
                    "success",
                )
                self.status_lbl.config(text="Mod: GÜVENLİ — Sahiplik kontrolü aktif.")
            else:
                self.mode_btn.config(text="⚠  ZAFİYETLİ MOD", bg=C["btn_red"])
                self.server_panel.log(
                    "━━━ MOD DEĞİŞTİ: ZAFİYETLİ ━━━ Sahiplik kontrolü KAPALI",
                    "danger",
                )
                self.status_lbl.config(text="Mod: ZAFİYETLİ — IDOR açığı aktif!")
        except Exception as e:
            self.status_lbl.config(text=f"Hata: {e}")

    # ----------------------------------------------------------
    # İSTATİSTİK GÜNCELLEYICI (her 1 sn)
    # ----------------------------------------------------------

    def _start_stats_updater(self):
        def update():
            while True:
                try:
                    r = self.session.get(f"{BASE_URL}/admin/stats", timeout=1)
                    if r.status_code == 200:
                        self.server_panel.update_stats(r.json())
                except Exception:
                    pass
                time.sleep(1)
        threading.Thread(target=update, daemon=True).start()

    # ----------------------------------------------------------
    # PANEL'DEN ÇAĞRILAN YARDIMCI METODLAR
    # ----------------------------------------------------------

    def set_logged_in(self, username: str):
        self.logged_in = True
        self.current_user = username
        self.status_lbl.config(text=f"Oturum açık: {username}")

    def set_logged_out(self):
        self.logged_in = False
        self.current_user = None
        self.status_lbl.config(text="Oturum kapalı.")

    def log_to_server(self, text: str, tag: str = "normal"):
        self.server_panel.log(text, tag)


# ---------------------------------------------------------------
# SALDIRGAN PANELİ
# ---------------------------------------------------------------

class AttackerPanel(tk.Frame):
    def __init__(self, parent, app: IDORSimApp):
        super().__init__(parent, bg=C["panel"], bd=0)
        self.app = app
        self.session = app.session
        self._build()

    def _build(self):
        # Başlık
        tk.Label(self, text="🗡  SALDIRGAN PANELİ",
                 bg=C["panel"], fg=C["red"],
                 font=("Consolas", 12, "bold")).pack(pady=(12, 4))
        tk.Label(self, text="Ahmet rolü — API istekleri gönderir",
                 bg=C["panel"], fg=C["dim"],
                 font=("Consolas", 8)).pack(pady=(0, 10))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # ── Giriş formu
        self._build_login_section()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=4)

        # ── Fatura erişim bölümü
        self._build_invoice_section()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=4)

        # ── Yanıt görüntüleyici
        self._build_response_viewer()

    def _build_login_section(self):
        frm = tk.Frame(self, bg=C["panel"])
        frm.pack(fill=tk.X, padx=14, pady=6)

        tk.Label(frm, text="GİRİŞ", bg=C["panel"], fg=C["blue"],
                 font=("Consolas", 9, "bold")).pack(anchor=tk.W)

        row1 = tk.Frame(frm, bg=C["panel"])
        row1.pack(fill=tk.X, pady=2)
        tk.Label(row1, text="Kullanıcı:", bg=C["panel"], fg=C["text"],
                 font=("Consolas", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.user_var = tk.StringVar(value="ahmet")
        user_combo = ttk.Combobox(row1, textvariable=self.user_var, width=14,
                                  values=["ahmet", "mehmet", "admin"])
        user_combo.pack(side=tk.LEFT, padx=4)

        row2 = tk.Frame(frm, bg=C["panel"])
        row2.pack(fill=tk.X, pady=2)
        tk.Label(row2, text="Parola:", bg=C["panel"], fg=C["text"],
                 font=("Consolas", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.pass_var = tk.StringVar(value="ahmet123")
        tk.Entry(row2, textvariable=self.pass_var, show="•", width=16,
                 font=("Consolas", 9),
                 bg=C["card"], fg=C["text"], insertbackground=C["text"],
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=4)

        btn_row = tk.Frame(frm, bg=C["panel"])
        btn_row.pack(fill=tk.X, pady=4)
        self.login_btn = tk.Button(btn_row, text="▶  Giriş Yap",
                                   bg=C["btn_blue"], fg="white",
                                   font=("Consolas", 9, "bold"),
                                   relief=tk.FLAT, padx=10, cursor="hand2",
                                   command=self._login)
        self.login_btn.pack(side=tk.LEFT)

        self.logout_btn = tk.Button(btn_row, text="Çıkış",
                                    bg=C["btn_gray"], fg="white",
                                    font=("Consolas", 9),
                                    relief=tk.FLAT, padx=10, cursor="hand2",
                                    command=self._logout, state=tk.DISABLED)
        self.logout_btn.pack(side=tk.LEFT, padx=6)

        self.login_status = tk.Label(frm, text="⬤ Oturum kapalı",
                                     bg=C["panel"], fg=C["dim"],
                                     font=("Consolas", 8))
        self.login_status.pack(anchor=tk.W)

    def _build_invoice_section(self):
        frm = tk.Frame(self, bg=C["panel"])
        frm.pack(fill=tk.X, padx=14, pady=6)

        tk.Label(frm, text="FATURA ERİŞİM (ID MANİPÜLASYONU)",
                 bg=C["panel"], fg=C["yellow"],
                 font=("Consolas", 9, "bold")).pack(anchor=tk.W)

        row = tk.Frame(frm, bg=C["panel"])
        row.pack(fill=tk.X, pady=4)
        tk.Label(row, text="Fatura ID:", bg=C["panel"], fg=C["text"],
                 font=("Consolas", 9), width=10, anchor=tk.W).pack(side=tk.LEFT)
        self.inv_var = tk.StringVar(value="1001")
        tk.Entry(row, textvariable=self.inv_var, width=10,
                 font=("Consolas", 9, "bold"),
                 bg=C["card"], fg=C["yellow"], insertbackground=C["text"],
                 relief=tk.FLAT).pack(side=tk.LEFT, padx=4)

        # Hızlı erişim butonları
        quick = tk.Frame(frm, bg=C["panel"])
        quick.pack(fill=tk.X, pady=2)
        tk.Label(quick, text="Hızlı:", bg=C["panel"], fg=C["dim"],
                 font=("Consolas", 8), width=10, anchor=tk.W).pack(side=tk.LEFT)
        for inv_id, color, label in [
            (1001, C["btn_green"], "#1001 (Ahmet)"),
            (1002, C["btn_green"], "#1002 (Ahmet)"),
            (2001, C["btn_red"],   "#2001 (Mehmet)"),
            (2002, C["btn_red"],   "#2002 (Mehmet)"),
        ]:
            tk.Button(quick, text=label, bg=color, fg="white",
                      font=("Consolas", 7), relief=tk.FLAT,
                      padx=5, cursor="hand2",
                      command=lambda i=inv_id: self._quick_set(i)).pack(
                          side=tk.LEFT, padx=2)

        btn_row = tk.Frame(frm, bg=C["panel"])
        btn_row.pack(fill=tk.X, pady=4)
        tk.Button(btn_row, text="▶  Fatura Getir",
                  bg=C["btn_red"], fg="white",
                  font=("Consolas", 9, "bold"),
                  relief=tk.FLAT, padx=10, cursor="hand2",
                  command=self._get_invoice).pack(side=tk.LEFT)
        tk.Button(btn_row, text="⟳  Kendi Faturalarım",
                  bg=C["btn_gray"], fg="white",
                  font=("Consolas", 8),
                  relief=tk.FLAT, padx=8, cursor="hand2",
                  command=self._my_invoices).pack(side=tk.LEFT, padx=6)

    def _build_response_viewer(self):
        frm = tk.Frame(self, bg=C["panel"])
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        hdr = tk.Frame(frm, bg=C["panel"])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="SUNUCU YANITI",
                 bg=C["panel"], fg=C["blue"],
                 font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
        self.resp_status = tk.Label(hdr, text="", bg=C["panel"],
                                    font=("Consolas", 9, "bold"))
        self.resp_status.pack(side=tk.LEFT, padx=8)
        tk.Button(hdr, text="Temizle", bg=C["btn_gray"], fg="white",
                  font=("Consolas", 7), relief=tk.FLAT, padx=4, cursor="hand2",
                  command=lambda: clear_log(self.resp_box)).pack(side=tk.RIGHT)

        self.resp_box = scrolledtext.ScrolledText(
            frm, height=10, state=tk.DISABLED,
            font=("Consolas", 9),
            bg=C["card"], fg=C["text"],
            insertbackground=C["text"],
            relief=tk.FLAT, wrap=tk.WORD,
        )
        self.resp_box.pack(fill=tk.BOTH, expand=True, pady=4)
        # Renk tagları
        self.resp_box.tag_config("success", foreground=C["green"])
        self.resp_box.tag_config("danger",  foreground=C["red"])
        self.resp_box.tag_config("warning", foreground=C["yellow"])
        self.resp_box.tag_config("info",    foreground=C["blue"])
        self.resp_box.tag_config("dim",     foreground=C["dim"])

    # ----------------------------------------------------------
    # EYLEMLER
    # ----------------------------------------------------------

    def on_server_ready(self):
        self.login_btn.config(state=tk.NORMAL)

    def _quick_set(self, inv_id: int):
        self.inv_var.set(str(inv_id))

    def _login(self):
        u = self.user_var.get()
        p = self.pass_var.get()
        try:
            r = self.session.post(f"{BASE_URL}/login",
                                  json={"username": u, "password": p})
            data = r.json()
            if r.status_code == 200:
                self.login_status.config(
                    text=f"⬤ {data.get('message', 'Giriş başarılı')}",
                    fg=C["green"],
                )
                self.login_btn.config(state=tk.DISABLED)
                self.logout_btn.config(state=tk.NORMAL)
                self.app.set_logged_in(u)
                self.app.log_to_server(f"→ POST /login | {u} | 200 OK", "success")
                append_log(self.resp_box,
                           f"✓ HTTP 200 — {data.get('message')}", "success")
            else:
                self.app.log_to_server(f"→ POST /login | {u} | 401 FAIL", "danger")
                append_log(self.resp_box,
                           f"✗ HTTP {r.status_code} — {data.get('error')}", "danger")
        except Exception as e:
            append_log(self.resp_box, f"HATA: {e}", "danger")

    def _logout(self):
        try:
            self.session.post(f"{BASE_URL}/logout")
            self.login_status.config(text="⬤ Oturum kapalı", fg=C["dim"])
            self.login_btn.config(state=tk.NORMAL)
            self.logout_btn.config(state=tk.DISABLED)
            self.app.set_logged_out()
            self.app.log_to_server("→ POST /logout | 200 OK", "dim")
            append_log(self.resp_box, "Çıkış yapıldı.", "dim")
        except Exception as e:
            append_log(self.resp_box, f"HATA: {e}", "danger")

    def _get_invoice(self):
        inv_id = self.inv_var.get()
        try:
            r = self.session.get(f"{BASE_URL}/api/invoice/{inv_id}")
            data = r.json()
            is_secure = SECURE_MODE[0]

            if r.status_code == 200:
                owner_id = data.get("owner_id")
                user_id = self.session.get(f"{BASE_URL}/admin/mode")  # trick: get current user
                # Kimin faturası?
                is_own = (data.get("owner") == self.user_var.get().capitalize() or
                          "Ahmet" in data.get("owner", "") and self.user_var.get() == "ahmet" or
                          "Mehmet" in data.get("owner", "") and self.user_var.get() == "mehmet")

                self.resp_status.config(text="HTTP 200 OK", fg=C["green"])
                append_log(self.resp_box,
                           f"── GET /api/invoice/{inv_id} ──────────────", "info")
                append_log(self.resp_box,
                           f"HTTP 200 OK", "success")
                append_log(self.resp_box,
                           json.dumps(data, ensure_ascii=False, indent=2))

                if not is_own and not is_secure:
                    append_log(self.resp_box,
                               f"\n❌ IDOR AÇIĞI! {data.get('owner')}'ın verisi görüntülendi!",
                               "danger")
                    self.app.log_to_server(
                        f"❌ IDOR EXPLOİT! Kullanıcı fatura#{inv_id} ({data.get('owner')}) → 200",
                        "danger",
                    )
                else:
                    self.app.log_to_server(
                        f"→ GET /api/invoice/{inv_id} | 200 OK", "success")
            else:
                self.resp_status.config(
                    text=f"HTTP {r.status_code}", fg=C["green"] if is_secure else C["red"])
                append_log(self.resp_box,
                           f"── GET /api/invoice/{inv_id} ──────────────", "info")
                append_log(self.resp_box,
                           f"HTTP {r.status_code} — {data.get('error')}", "success")
                if is_secure:
                    append_log(self.resp_box,
                               "✅ Exploit engellendi! Güvenlik logu yazıldı.", "success")
                    self.app.log_to_server(
                        f"✅ ENGELLENDİ | GET /api/invoice/{inv_id} | 404", "success")

        except Exception as e:
            append_log(self.resp_box, f"HATA: {e}", "danger")

    def _my_invoices(self):
        try:
            r = self.session.get(f"{BASE_URL}/api/my-invoices")
            data = r.json()
            append_log(self.resp_box, "── GET /api/my-invoices ──────────────", "info")
            append_log(self.resp_box, f"HTTP {r.status_code}")
            if r.status_code == 200:
                append_log(self.resp_box,
                           f"Toplam fatura: {data.get('count')}", "success")
                for inv in data.get("invoices", []):
                    append_log(self.resp_box,
                               f"  #{inv['id']} — {inv['service']} — {inv['amount']}", "success")
            else:
                append_log(self.resp_box, data.get("hata", "Hata"), "danger")
            self.app.log_to_server(f"→ GET /api/my-invoices | {r.status_code}", "dim")
        except Exception as e:
            append_log(self.resp_box, f"HATA: {e}", "danger")


# ---------------------------------------------------------------
# SUNUCU / KURBAN PANELİ
# ---------------------------------------------------------------

class ServerPanel(tk.Frame):
    def __init__(self, parent, app: IDORSimApp):
        super().__init__(parent, bg=C["panel"], bd=0)
        self.app = app
        self._build()

    def _build(self):
        # Başlık
        tk.Label(self, text="🖥  SUNUCU / KURBAN PANELİ",
                 bg=C["panel"], fg=C["green"],
                 font=("Consolas", 12, "bold")).pack(pady=(12, 4))
        tk.Label(self, text="Mehmet'in verileri burada — güvenli mi?",
                 bg=C["panel"], fg=C["dim"],
                 font=("Consolas", 8)).pack(pady=(0, 10))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)

        # ── Mod göstergesi
        self._build_mode_indicator()

        # ── İstatistikler
        self._build_stats()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=4)

        # ── Sunucu log
        self._build_log()

    def _build_mode_indicator(self):
        frm = tk.Frame(self, bg=C["card"], relief=tk.FLAT)
        frm.pack(fill=tk.X, padx=14, pady=8)

        tk.Label(frm, text="  AKTİF MOD:",
                 bg=C["card"], fg=C["dim"],
                 font=("Consolas", 9)).pack(side=tk.LEFT, pady=6)

        self.mode_indicator = tk.Label(
            frm, text="  ⚠  ZAFİYETLİ — Sahiplik kontrolü KAPALI  ",
            bg=C["btn_red"], fg="white",
            font=("Consolas", 10, "bold"),
        )
        self.mode_indicator.pack(side=tk.LEFT, padx=8, pady=4)

        # Açıklama
        self.mode_desc = tk.Label(
            self,
            text="Herhangi bir kullanıcı, herhangi bir fatura ID'sini görebilir.",
            bg=C["panel"], fg=C["red"],
            font=("Consolas", 8),
            wraplength=400,
        )
        self.mode_desc.pack(pady=(0, 4))

    def _build_stats(self):
        frm = tk.Frame(self, bg=C["panel"])
        frm.pack(fill=tk.X, padx=14, pady=4)

        self.stat_labels = {}
        stats_cfg = [
            ("total",    "Toplam İstek:",      C["text"]),
            ("blocked",  "Engellenen:",         C["green"]),
            ("exploits", "Başarılı Exploit:",   C["red"]),
        ]
        for key, label, color in stats_cfg:
            row = tk.Frame(frm, bg=C["panel"])
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=label, bg=C["panel"], fg=C["dim"],
                     font=("Consolas", 9), width=20, anchor=tk.W).pack(side=tk.LEFT)
            lbl = tk.Label(row, text="0", bg=C["panel"], fg=color,
                           font=("Consolas", 11, "bold"))
            lbl.pack(side=tk.LEFT)
            self.stat_labels[key] = lbl

        tk.Button(frm, text="Sıfırla",
                  bg=C["btn_gray"], fg="white",
                  font=("Consolas", 7), relief=tk.FLAT,
                  padx=6, cursor="hand2",
                  command=self._reset_stats).pack(anchor=tk.W, pady=4)

    def _build_log(self):
        frm = tk.Frame(self, bg=C["panel"])
        frm.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        hdr = tk.Frame(frm, bg=C["panel"])
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="SUNUCU LOGLARI",
                 bg=C["panel"], fg=C["cyan"],
                 font=("Consolas", 9, "bold")).pack(side=tk.LEFT)
        tk.Button(hdr, text="Temizle", bg=C["btn_gray"], fg="white",
                  font=("Consolas", 7), relief=tk.FLAT, padx=4, cursor="hand2",
                  command=lambda: clear_log(self.log_box)).pack(side=tk.RIGHT)

        self.log_box = scrolledtext.ScrolledText(
            frm, height=18, state=tk.DISABLED,
            font=("Consolas", 9),
            bg=C["card"], fg=C["text"],
            relief=tk.FLAT, wrap=tk.WORD,
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, pady=4)
        self.log_box.tag_config("success", foreground=C["green"])
        self.log_box.tag_config("danger",  foreground=C["red"])
        self.log_box.tag_config("warning", foreground=C["yellow"])
        self.log_box.tag_config("info",    foreground=C["blue"])
        self.log_box.tag_config("dim",     foreground=C["dim"])

        append_log(self.log_box, "Sunucu başlatılıyor...", "dim")

    # ----------------------------------------------------------
    # DIŞARIDAN ÇAĞRILAN METODLAR
    # ----------------------------------------------------------

    def log(self, text: str, tag: str = "normal"):
        ts = time.strftime("%H:%M:%S")
        append_log(self.log_box, f"[{ts}] {text}", tag)

    def update_stats(self, stats: dict):
        self.stat_labels["total"].config(text=str(stats.get("total_requests", 0)))
        self.stat_labels["blocked"].config(text=str(stats.get("blocked_requests", 0)))
        exploits = stats.get("successful_exploits", 0)
        self.stat_labels["exploits"].config(
            text=str(exploits),
            fg=C["red"] if exploits > 0 else C["dim"],
        )
        # Mod göstergesini güncelle
        is_secure = SECURE_MODE[0]
        if is_secure:
            self.mode_indicator.config(
                text="  ✔  GÜVENLİ — Sahiplik kontrolü AKTİF  ",
                bg=C["btn_green"],
            )
            self.mode_desc.config(
                text="Sahiplik kontrolü aktif. Yetkisiz erişim engelleniyor.",
                fg=C["green"],
            )
        else:
            self.mode_indicator.config(
                text="  ⚠  ZAFİYETLİ — Sahiplik kontrolü KAPALI  ",
                bg=C["btn_red"],
            )
            self.mode_desc.config(
                text="Herhangi bir kullanıcı, herhangi bir fatura ID'sini görebilir.",
                fg=C["red"],
            )

    def _reset_stats(self):
        try:
            self.app.session.post(f"{BASE_URL}/admin/reset-stats")
            self.log("İstatistikler sıfırlandı.", "dim")
        except Exception:
            pass


# ---------------------------------------------------------------
# GİRİŞ NOKTASI
# ---------------------------------------------------------------

if __name__ == "__main__":
    # Windows'ta DPI farkındalığı
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    gui = IDORSimApp()
    gui.mainloop()
