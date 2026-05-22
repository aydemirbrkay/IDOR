"""
app.py — IDOR Eğitici Flask API Sunucusu
=========================================
Bu sunucu iki modda çalışır:
  - VULNERABLE (Zafiyetli): Sahiplik kontrolü yok → IDOR açığı
  - SECURE     (Güvenli):   Sahiplik kontrolü var  → IDOR kapalı

Mod, GUI veya /admin/toggle endpoint'i üzerinden değiştirilebilir.
Bu tasarım, sunum sırasında canlı karşılaştırma yapmayı sağlar.
"""

from flask import Flask, request, session, jsonify
from security_utils import (
    login_required,
    owner_required,
    check_object_ownership,
    log_unauthorized_access,
    security_logger,
)

app = Flask(__name__)
app.secret_key = "idor-egitim-secret-2024"

# ---------------------------------------------------------------
# MOD KONTROLÜ
# Liste kullanıyoruz: Python'da modül-seviyesi bool'ları fonksiyon
# içinden değiştirmek için mutable container gerekir.
# ---------------------------------------------------------------
SECURE_MODE = [False]   # [False] = Zafiyetli | [True] = Güvenli

# İstatistik sayaçları (GUI için)
STATS = {
    "total_requests": 0,
    "blocked_requests": 0,
    "successful_exploits": 0,
}


# ---------------------------------------------------------------
# BELLEK İÇİ VERİTABANI
# ---------------------------------------------------------------

USERS = {
    "ahmet":  {"id": 1, "password": "ahmet123", "name": "Ahmet Yılmaz", "role": "user"},
    "mehmet": {"id": 2, "password": "mehmet123", "name": "Mehmet Kaya",  "role": "user"},
    "admin":  {"id": 3, "password": "admin123",  "name": "Admin",         "role": "admin"},
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
}


# ---------------------------------------------------------------
# ENDPOINT: GİRİŞ
# POST /login
# Body: {"username": "ahmet", "password": "ahmet123"}
# ---------------------------------------------------------------

@app.route("/login", methods=["POST"])
def login():
    STATS["total_requests"] += 1
    data = request.get_json() or {}
    username = data.get("username", "")
    password = data.get("password", "")

    user = USERS.get(username)
    if not user or user["password"] != password:
        return jsonify({"error": "Kullanıcı adı veya parola hatalı."}), 401

    session["user_id"] = user["id"]
    session["username"] = username
    security_logger.info(f"Giriş başarılı | Kullanıcı: {username} | IP: {request.remote_addr}")

    return jsonify({
        "message": f"Hoş geldiniz, {user['name']}!",
        "user_id": user["id"],
        "username": username,
    }), 200


# ---------------------------------------------------------------
# ENDPOINT: ÇIKIŞ
# POST /logout
# ---------------------------------------------------------------

@app.route("/logout", methods=["POST"])
def logout():
    username = session.get("username", "?")
    session.clear()
    security_logger.info(f"Çıkış | Kullanıcı: {username}")
    return jsonify({"message": "Çıkış yapıldı."}), 200


# ---------------------------------------------------------------
# ENDPOINT: FATURA GÖRÜNTÜLEME — ⚠️ IDOR NOKTASI
# GET /api/invoice/<invoice_id>
#
# Bu endpoint iki farklı şekilde davranır:
#   SECURE_MODE = False → Sahiplik kontrolü YOK (ZAFİYETLİ)
#   SECURE_MODE = True  → Sahiplik kontrolü VAR (GÜVENLİ)
# ---------------------------------------------------------------

@app.route("/api/invoice/<int:invoice_id>", methods=["GET"])
@login_required
def get_invoice(invoice_id):
    STATS["total_requests"] += 1
    invoice = INVOICES.get(invoice_id)

    if not invoice:
        return jsonify({"error": "Fatura bulunamadı."}), 404

    current_user_id = session.get("user_id")

    if SECURE_MODE[0]:
        # ✅ GÜVENLİ MOD: Sahiplik kontrolü aktif
        if not check_object_ownership(invoice, current_user_id):
            STATS["blocked_requests"] += 1
            log_unauthorized_access(
                user_id=current_user_id,
                resource_type="invoice",
                resource_id=invoice_id,
                ip=request.remote_addr,
            )
            return jsonify({"error": "Fatura bulunamadı."}), 404
    else:
        # ❌ ZAFİYETLİ MOD: Sahiplik kontrolü YOK
        # Giriş yapmış herkes herhangi bir faturaya erişebilir!
        if invoice["owner_id"] != current_user_id:
            STATS["successful_exploits"] += 1
            security_logger.info(
                f"[ZAFİYET] Kullanıcı {current_user_id} → Fatura {invoice_id} "
                f"({invoice['owner']}) — Sahiplik kontrolü yok!"
            )

    security_logger.info(f"Fatura erişimi | ID: {invoice_id} | Kullanıcı: {current_user_id}")
    return jsonify(invoice), 200


# ---------------------------------------------------------------
# ENDPOINT: KENDİ FATURALARIM
# GET /api/my-invoices
# ---------------------------------------------------------------

@app.route("/api/my-invoices", methods=["GET"])
@login_required
def my_invoices():
    STATS["total_requests"] += 1
    current_user_id = session["user_id"]
    user_invoices = [inv for inv in INVOICES.values() if inv["owner_id"] == current_user_id]
    return jsonify({
        "user_id": current_user_id,
        "count": len(user_invoices),
        "invoices": user_invoices,
    }), 200


# ---------------------------------------------------------------
# ADMIN ENDPOINT'LERİ (GUI kontrolü için)
# ---------------------------------------------------------------

@app.route("/admin/toggle-mode", methods=["POST"])
def toggle_mode():
    """Güvenli/Zafiyetli mod arasında geçiş yapar (GUI kontrolü için)."""
    SECURE_MODE[0] = not SECURE_MODE[0]
    mode = "SECURE" if SECURE_MODE[0] else "VULNERABLE"
    security_logger.info(f"Mod değiştirildi → {mode}")
    return jsonify({"secure": SECURE_MODE[0], "mode": mode}), 200


@app.route("/admin/mode", methods=["GET"])
def get_mode():
    """Mevcut modu döndürür."""
    return jsonify({
        "secure": SECURE_MODE[0],
        "mode": "SECURE" if SECURE_MODE[0] else "VULNERABLE",
    }), 200


@app.route("/admin/stats", methods=["GET"])
def get_stats():
    """İstatistikleri döndürür (GUI için)."""
    return jsonify(STATS), 200


@app.route("/admin/reset-stats", methods=["POST"])
def reset_stats():
    """İstatistikleri sıfırlar."""
    STATS["total_requests"] = 0
    STATS["blocked_requests"] = 0
    STATS["successful_exploits"] = 0
    return jsonify({"message": "İstatistikler sıfırlandı."}), 200


# ---------------------------------------------------------------
# UYGULAMA BAŞLATMA (doğrudan çalıştırıldığında)
# ---------------------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"[IDOR Sunucu] http://localhost:{port} — Mod: ZAFİYETLİ")
    print("  /admin/toggle-mode ile mod değiştirilir.")
    app.run(host="0.0.0.0", port=port, debug=False)
