"""
app.py — IDOR Eğitici Flask API Sunucusu
=========================================
Bu sunucu iki modda çalışır:
  - VULNERABLE (Zafiyetli): Sahiplik kontrolü yok → IDOR açığı
  - SECURE     (Güvenli):   Sahiplik kontrolü var  → IDOR kapalı

Mod, GUI veya /admin/toggle endpoint'i üzerinden değiştirilebilir.
Bu tasarım, sunum sırasında canlı karşılaştırma yapmayı sağlar.
"""

import os
import secrets

from flask import Flask, request, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from security_utils import (
    login_required,
    admin_required,
    owner_required,
    check_object_ownership,
    log_unauthorized_access,
    security_logger,
    RateLimiter,
)

app = Flask(__name__)

# ---------------------------------------------------------------
# GÜVENLİK YAPILANDIRMASI (OWASP API2 — Broken Authentication)
# Secret key sabit kodlanmaz: ortam değişkeninden okunur, yoksa
# her başlangıçta güvenli rastgele bir değer üretilir.
# ---------------------------------------------------------------
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# Oturum çerezi güvenlik bayrakları
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # JS ile çereze erişimi engeller (XSS hırsızlığı)
    SESSION_COOKIE_SAMESITE="Lax",  # CSRF'yi azaltır
    # HTTPS dışı yerel demoda Secure kapalı; üretimde FLASK_ENV=production ile açılır
    SESSION_COOKIE_SECURE=os.environ.get("FLASK_ENV") == "production",
)

# Brute-force koruması: IP başına 60 saniyede en fazla 5 giriş denemesi
login_limiter = RateLimiter(max_requests=5, window_seconds=60)

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

# Parolalar düz metin saklanmaz: tek yönlü hash olarak tutulur (OWASP API2).
# Demo kimlik bilgileri aynıdır (ahmet123 vb.); yalnızca saklama biçimi güvenli.
USERS = {
    "ahmet":  {"id": 1, "password_hash": generate_password_hash("ahmet123"),
               "name": "Ahmet Yılmaz", "role": "user"},
    "mehmet": {"id": 2, "password_hash": generate_password_hash("mehmet123"),
               "name": "Mehmet Kaya",  "role": "user"},
    "admin":  {"id": 3, "password_hash": generate_password_hash("admin123"),
               "name": "Admin",         "role": "admin"},
}

# Kullanıcı bulunamadığında bile sabit-zamanlı doğrulama yapmak için kukla hash.
# Bu, yanıt süresinden kullanıcı adı sızdıran timing saldırılarını önler.
_DUMMY_HASH = generate_password_hash("dummy-password-not-used")

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

    # OWASP API4: Brute-force denemelerini IP başına sınırla
    if not login_limiter.is_allowed(request.remote_addr or "unknown"):
        security_logger.warning(
            f"Rate limit aşıldı (giriş) | IP: {request.remote_addr}"
        )
        return jsonify({
            "error": "Çok fazla giriş denemesi. Lütfen biraz sonra tekrar deneyin."
        }), 429

    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    user = USERS.get(username)
    # Sabit-zamanlı doğrulama: kullanıcı yoksa bile bir hash karşılaştırması yap.
    stored_hash = user["password_hash"] if user else _DUMMY_HASH
    password_ok = check_password_hash(stored_hash, password)

    if not user or not password_ok:
        # Aynı genel mesaj: kullanıcı adı geçerli mi bilgisini sızdırmaz.
        security_logger.warning(
            f"Başarısız giriş | Kullanıcı: {username!r} | IP: {request.remote_addr}"
        )
        return jsonify({"error": "Kullanıcı adı veya parola hatalı."}), 401

    # Oturum sabitleme (session fixation) saldırılarını önlemek için oturumu yenile.
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = username
    session["role"] = user["role"]
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

# Durumu değiştiren yönetimsel işlemler admin yetkisi gerektirir (OWASP API5: BFLA).
@app.route("/admin/toggle-mode", methods=["POST"])
@admin_required
def toggle_mode():
    """Güvenli/Zafiyetli mod arasında geçiş yapar (yalnızca admin)."""
    SECURE_MODE[0] = not SECURE_MODE[0]
    mode = "SECURE" if SECURE_MODE[0] else "VULNERABLE"
    security_logger.info(f"Mod değiştirildi → {mode}")
    return jsonify({"secure": SECURE_MODE[0], "mode": mode}), 200


@app.route("/admin/mode", methods=["GET"])
def get_mode():
    """Mevcut modu döndürür (yalnızca okuma, hassas değil)."""
    return jsonify({
        "secure": SECURE_MODE[0],
        "mode": "SECURE" if SECURE_MODE[0] else "VULNERABLE",
    }), 200


@app.route("/admin/stats", methods=["GET"])
def get_stats():
    """İstatistikleri döndürür (yalnızca okuma)."""
    return jsonify(STATS), 200


@app.route("/admin/reset-stats", methods=["POST"])
@admin_required
def reset_stats():
    """İstatistikleri sıfırlar (yalnızca admin)."""
    STATS["total_requests"] = 0
    STATS["blocked_requests"] = 0
    STATS["successful_exploits"] = 0
    return jsonify({"message": "İstatistikler sıfırlandı."}), 200


# ---------------------------------------------------------------
# GÜVENLİK BAŞLIKLARI + JSON HATA YÖNETİMİ
# ---------------------------------------------------------------

@app.after_request
def set_security_headers(response):
    """Yaygın saldırı vektörlerini azaltan güvenlik başlıkları ekler."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(404)
def handle_404(_e):
    return jsonify({"error": "Kaynak bulunamadı.", "kod": 404}), 404


@app.errorhandler(405)
def handle_405(_e):
    return jsonify({"error": "Bu metoda izin verilmiyor.", "kod": 405}), 405


@app.errorhandler(500)
def handle_500(_e):
    # Stack trace / iç ayrıntı sızdırma — genel mesaj döndür.
    return jsonify({"error": "Sunucu hatası.", "kod": 500}), 500


# ---------------------------------------------------------------
# UYGULAMA BAŞLATMA (doğrudan çalıştırıldığında)
# ---------------------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"[IDOR Sunucu] http://localhost:{port} — Mod: ZAFİYETLİ")
    print("  /admin/toggle-mode ile mod değiştirilir.")
    app.run(host="0.0.0.0", port=port, debug=False)
