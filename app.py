"""
app.py — IDOR Eğitici Flask Uygulaması
=======================================
Bu uygulama iki modda çalışır:
  - VULNERABLE (Zafiyetli): Sahiplik kontrolü yok → IDOR açığı
  - SECURE     (Güvenli):   Sahiplik kontrolü var  → IDOR kapalı

Mod, admin paneli veya /admin/toggle-mode endpoint'i ile değiştirilebilir.
Bu tasarım, canlı karşılaştırma yapmayı (aynı saldırı önce başarılı,
sonra engellenmiş) mümkün kılar.

UYARI: Sadece eğitim amaçlıdır. Üretimde kullanmayın.
"""

from collections import deque
from datetime import datetime

from flask import Flask, render_template, request, session, jsonify, redirect, url_for

from security_utils import (
    login_required,
    check_object_ownership,
    log_unauthorized_access,
    security_logger,
    register_log_sink,
)

app = Flask(__name__)
app.secret_key = "idor-egitim-secret-2024"


# ---------------------------------------------------------------
# MOD KONTROLÜ
# Mutable container kullanıyoruz ki endpoint'lerden değiştirebilelim.
# ---------------------------------------------------------------
SECURE_MODE = [False]   # [False] = Zafiyetli | [True] = Güvenli

# İstatistik sayaçları (admin paneli için)
STATS = {
    "total_requests": 0,
    "blocked_requests": 0,
    "successful_exploits": 0,
}

# Son 200 güvenlik olayı (canlı log akışı için)
LOG_BUFFER: "deque[dict]" = deque(maxlen=200)


def _push_log(level: str, message: str) -> None:
    LOG_BUFFER.append({
        "ts": datetime.now().strftime("%H:%M:%S"),
        "level": level,
        "message": message,
    })


# security_utils'in logger'ı her mesaj attığında buffer'a da yazsın
register_log_sink(_push_log)


# ---------------------------------------------------------------
# BELLEK İÇİ VERİTABANI
# ---------------------------------------------------------------

USERS = {
    "ahmet":  {"id": 1, "password": "ahmet123",  "name": "Ahmet Yılmaz", "role": "user"},
    "mehmet": {"id": 2, "password": "mehmet123", "name": "Mehmet Kaya",  "role": "user"},
    "ayse":   {"id": 3, "password": "ayse123",   "name": "Ayşe Demir",   "role": "user"},
    "admin":  {"id": 99, "password": "admin123", "name": "Sistem Yöneticisi", "role": "admin"},
}

INVOICES = {
    1001: {"id": 1001, "owner_id": 1, "owner": "Ahmet Yılmaz",
           "amount": "₺2.500,00", "service": "Web Tasarım Hizmeti",
           "date": "2024-01-15", "status": "Ödendi"},
    1002: {"id": 1002, "owner_id": 1, "owner": "Ahmet Yılmaz",
           "amount": "₺1.800,00", "service": "SEO Danışmanlığı",
           "date": "2024-02-10", "status": "Bekliyor"},
    2001: {"id": 2001, "owner_id": 2, "owner": "Mehmet Kaya",
           "amount": "₺9.750,00", "service": "Yazılım Geliştirme",
           "date": "2024-01-20", "status": "Ödendi"},
    2002: {"id": 2002, "owner_id": 2, "owner": "Mehmet Kaya",
           "amount": "₺3.200,00", "service": "Sunucu Bakımı",
           "date": "2024-03-05", "status": "Bekliyor"},
    3001: {"id": 3001, "owner_id": 3, "owner": "Ayşe Demir",
           "amount": "₺12.400,00", "service": "Mobil Uygulama Geliştirme",
           "date": "2024-02-22", "status": "Ödendi"},
    3002: {"id": 3002, "owner_id": 3, "owner": "Ayşe Demir",
           "amount": "₺4.900,00", "service": "UI/UX Danışmanlığı",
           "date": "2024-04-01", "status": "Bekliyor"},
}


# ---------------------------------------------------------------
# WEB ARAYÜZÜ ROUTE'LARI (HTML)
# ---------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login_page"))


@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


def _current_user_view():
    """USERS kaydını döndürür + 'username' alanı (parolasız) — template'lere."""
    username = session.get("username")
    user = USERS.get(username)
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["name"],
        "role": user["role"],
        "username": username,
    }


@app.route("/dashboard", methods=["GET"])
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("dashboard.html", user=_current_user_view())


@app.route("/attack-lab", methods=["GET"])
def attack_lab():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    user = _current_user_view()
    all_ids = sorted(INVOICES.keys())
    my_ids = sorted(
        inv_id for inv_id, inv in INVOICES.items()
        if inv["owner_id"] == session["user_id"]
    )
    # "Başkasına ait" örnek ID — UI'da öneri olarak gösterilir
    other_example_id = next((i for i in all_ids if i not in my_ids), None)
    return render_template(
        "attack_lab.html",
        user=user,
        all_ids=all_ids,
        my_ids=my_ids,
        other_example_id=other_example_id,
    )


@app.route("/admin", methods=["GET"])
def admin_panel():
    if "user_id" not in session:
        return redirect(url_for("login_page"))
    return render_template("admin.html", user=_current_user_view())


# ---------------------------------------------------------------
# API: KİMLİK DOĞRULAMA
# ---------------------------------------------------------------

@app.route("/api/login", methods=["POST"])
def api_login():
    STATS["total_requests"] += 1
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = USERS.get(username)
    if not user or user["password"] != password:
        security_logger.warning(f"Başarısız giriş denemesi | Kullanıcı: {username!r}")
        return jsonify({"error": "Kullanıcı adı veya parola hatalı."}), 401

    session["user_id"] = user["id"]
    session["username"] = username
    security_logger.info(f"Giriş başarılı | Kullanıcı: {username}")

    return jsonify({
        "message": f"Hoş geldiniz, {user['name']}!",
        "user_id": user["id"],
        "username": username,
        "name": user["name"],
        "role": user["role"],
    }), 200


@app.route("/api/logout", methods=["POST"])
def api_logout():
    username = session.get("username", "?")
    session.clear()
    security_logger.info(f"Çıkış | Kullanıcı: {username}")
    return jsonify({"message": "Çıkış yapıldı."}), 200


@app.route("/api/me", methods=["GET"])
def api_me():
    if "user_id" not in session:
        return jsonify({"authenticated": False}), 200
    username = session["username"]
    user = USERS.get(username)
    return jsonify({
        "authenticated": True,
        "user_id": user["id"],
        "username": username,
        "name": user["name"],
        "role": user["role"],
    }), 200


# ---------------------------------------------------------------
# API: FATURA GÖRÜNTÜLEME — ⚠️ IDOR NOKTASI
# ---------------------------------------------------------------

@app.route("/api/invoice/<int:invoice_id>", methods=["GET"])
@login_required
def get_invoice(invoice_id):
    """
    İki davranış:
      SECURE_MODE = False → sahiplik kontrolü YOK (zafiyetli)
      SECURE_MODE = True  → sahiplik kontrolü VAR (güvenli)
    """
    STATS["total_requests"] += 1
    invoice = INVOICES.get(invoice_id)
    current_user_id = session.get("user_id")

    if not invoice:
        return jsonify({"error": "Fatura bulunamadı."}), 404

    is_owner = invoice["owner_id"] == current_user_id
    is_admin = session.get("username") == "admin"

    if SECURE_MODE[0]:
        # ✅ GÜVENLİ MOD
        if not (is_owner or is_admin):
            STATS["blocked_requests"] += 1
            log_unauthorized_access(
                user_id=current_user_id,
                resource_type="invoice",
                resource_id=invoice_id,
                ip=request.remote_addr,
            )
            # 404 dön: 403, "ID gerçek ama erişimin yok" bilgisini sızdırır
            return jsonify({"error": "Fatura bulunamadı."}), 404
    else:
        # ❌ ZAFİYETLİ MOD: sahiplik kontrolü yok
        if not is_owner and not is_admin:
            STATS["successful_exploits"] += 1
            security_logger.warning(
                f"[IDOR EXPLOIT] Kullanıcı #{current_user_id} → Fatura #{invoice_id} "
                f"(sahibi: {invoice['owner']}) — sahiplik kontrolü atlandı!"
            )

    security_logger.info(f"Fatura erişimi | ID: {invoice_id} | Kullanıcı: #{current_user_id}")

    # Yanıta erişim bağlamı ekle — UI yetkisiz erişimi vurgulayabilsin
    response = dict(invoice)
    response["_access"] = {
        "requested_by_user_id": current_user_id,
        "is_owner": is_owner,
        "is_admin": is_admin,
        "unauthorized": (not is_owner and not is_admin),
        "mode": "SECURE" if SECURE_MODE[0] else "VULNERABLE",
    }
    return jsonify(response), 200


@app.route("/api/my-invoices", methods=["GET"])
@login_required
def my_invoices():
    STATS["total_requests"] += 1
    current_user_id = session["user_id"]
    is_admin = session.get("username") == "admin"
    if is_admin:
        items = list(INVOICES.values())
    else:
        items = [inv for inv in INVOICES.values() if inv["owner_id"] == current_user_id]
    return jsonify({
        "user_id": current_user_id,
        "count": len(items),
        "invoices": items,
    }), 200


# ---------------------------------------------------------------
# ADMIN API (mod kontrolü, log akışı, istatistik)
# ---------------------------------------------------------------

@app.route("/admin/toggle-mode", methods=["POST"])
def toggle_mode():
    SECURE_MODE[0] = not SECURE_MODE[0]
    mode = "SECURE" if SECURE_MODE[0] else "VULNERABLE"
    security_logger.info(f"Mod değiştirildi → {mode}")
    return jsonify({"secure": SECURE_MODE[0], "mode": mode}), 200


@app.route("/admin/mode", methods=["GET"])
def get_mode():
    return jsonify({
        "secure": SECURE_MODE[0],
        "mode": "SECURE" if SECURE_MODE[0] else "VULNERABLE",
    }), 200


@app.route("/admin/stats", methods=["GET"])
def get_stats():
    return jsonify(STATS), 200


@app.route("/admin/reset-stats", methods=["POST"])
def reset_stats():
    STATS["total_requests"] = 0
    STATS["blocked_requests"] = 0
    STATS["successful_exploits"] = 0
    return jsonify({"message": "İstatistikler sıfırlandı."}), 200


@app.route("/admin/logs", methods=["GET"])
def get_logs():
    """Son N güvenlik logunu döndürür (canlı akış için polling)."""
    return jsonify({"logs": list(LOG_BUFFER)}), 200


@app.route("/admin/clear-logs", methods=["POST"])
def clear_logs():
    LOG_BUFFER.clear()
    return jsonify({"message": "Loglar temizlendi."}), 200


# ---------------------------------------------------------------
# UYGULAMA BAŞLATMA
# ---------------------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print("=" * 60)
    print(f"  IDOR Eğitim Sunucusu — http://localhost:{port}")
    print(f"  Başlangıç modu: ZAFİYETLİ")
    print(f"  Test kullanıcıları: ahmet/ahmet123, mehmet/mehmet123,")
    print(f"                      ayse/ayse123, admin/admin123")
    print("=" * 60)
    app.run(host="0.0.0.0", port=port, debug=False)
