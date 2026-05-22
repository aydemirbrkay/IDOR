"""
security_utils.py — Yetkilendirme Yardımcı Fonksiyonları
=========================================================
Bu modül, IDOR zafiyetini önlemek için gereken tüm güvenlik
araçlarını içerir: dekoratörler, sahiplik kontrolü ve loglama.

Kullanım:
    from security_utils import login_required, owner_required, check_object_ownership
"""

import logging
from functools import wraps
from flask import session, request, jsonify

# ---------------------------------------------------------------
# GÜVENLİK LOGGER'I
# Gerçek sistemde bu loglar SIEM'e (Splunk, ELK vb.) iletilir.
# ---------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
security_logger = logging.getLogger("idor.security")


# ---------------------------------------------------------------
# ÇEKİRDEK FONKSİYON: Nesne Sahipliği Kontrolü
# ---------------------------------------------------------------

def check_object_ownership(resource: dict, current_user_id: int,
                           owner_field: str = "owner_id") -> bool:
    """
    Bir kaynağın belirli bir kullanıcıya ait olup olmadığını kontrol eder.

    Bu fonksiyon IDOR zafiyetini kapatan temel mantıktır.
    Her nesne erişiminde çağrılmalıdır.

    Args:
        resource:        Erişilmek istenen kaynak sözlüğü (fatura, profil vb.)
        current_user_id: Oturumdaki kullanıcının ID'si
        owner_field:     Kaynakta sahip ID'sini tutan alan adı

    Returns:
        True  → Kaynak bu kullanıcıya aittir, erişime izin ver
        False → Kaynak başkasına aittir, erişimi reddet
    """
    return resource.get(owner_field) == current_user_id


# ---------------------------------------------------------------
# DEKORATÖR 1: Authentication (Kimlik Doğrulama)
# ---------------------------------------------------------------

def login_required(f):
    """
    Kullanıcının sisteme giriş yapıp yapmadığını doğrular.

    Bu dekoratör sadece Authentication yapar:
    "Bu kişi kim?" sorusunu cevaplar.
    Yetkilendirme (Authorization) yapmaz — bunun için owner_required gerekir.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            security_logger.warning(
                f"Yetkisiz istek (oturum yok) | Endpoint: {request.path} | IP: {request.remote_addr}"
            )
            return jsonify({"hata": "Bu işlem için giriş yapmalısınız.", "kod": 401}), 401
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------
# DEKORATÖR 2: Authorization (Nesne Seviyesi Yetkilendirme)
# ---------------------------------------------------------------

def owner_required(get_resource_fn, owner_field: str = "owner_id"):
    """
    Bir kaynağa erişmeden önce sahiplik kontrolü yapar.

    Bu dekoratör Authorization yapar:
    "Bu kişinin bu kaynağa erişme hakkı var mı?" sorusunu cevaplar.

    Kullanım örneği:
        @app.route("/api/invoice/<int:invoice_id>")
        @login_required
        @owner_required(lambda inv_id: INVOICES.get(inv_id))
        def get_invoice(invoice_id):
            ...

    Args:
        get_resource_fn: Kaynak ID'sini alıp kaynağı döndüren lambda/fonksiyon
        owner_field:     Kaynakta sahip ID'sini tutan alan adı
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # URL parametrelerinden kaynak ID'sini bul
            resource_id = next(iter(kwargs.values()), None)
            resource = get_resource_fn(resource_id)
            current_user_id = session.get("user_id")

            if resource is None:
                return jsonify({"hata": "Kaynak bulunamadı.", "kod": 404}), 404

            # ✅ TEMEL SAVUNMA: check_object_ownership çağrısı
            if not check_object_ownership(resource, current_user_id, owner_field):
                log_unauthorized_access(
                    user_id=current_user_id,
                    resource_type=f.__name__,
                    resource_id=resource_id,
                    ip=request.remote_addr,
                )
                # 404 döndür: 403 saldırgana "ID geçerli" bilgisini verir
                return jsonify({"hata": "Kaynak bulunamadı.", "kod": 404}), 404

            return f(*args, **kwargs)
        return decorated
    return decorator


# ---------------------------------------------------------------
# YARDIMCI: Güvenlik Olayı Loglama
# ---------------------------------------------------------------

def log_unauthorized_access(user_id: int, resource_type: str,
                             resource_id, ip: str) -> None:
    """
    Yetkisiz erişim girişimini güvenlik loguna yazar.

    Gerçek sistemde bu kayıt:
    - SIEM'e iletilir (Splunk, ELK Stack, Graylog)
    - Anomali tespiti tetikler
    - Belirli eşik aşıldığında otomatik IP engelleme yapar
    - Olay müdahale ekibini uyarır
    """
    security_logger.warning(
        f"YETKİSİZ ERİŞİM GİRİŞİMİ | "
        f"Kullanıcı: {user_id} | "
        f"Kaynak: {resource_type}#{resource_id} | "
        f"IP: {ip}"
    )
