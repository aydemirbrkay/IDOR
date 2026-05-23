"""
security_utils.py — Yetkilendirme Yardımcı Fonksiyonları
=========================================================
Bu modül, IDOR zafiyetini önlemek için gereken tüm güvenlik
araçlarını içerir: dekoratörler, sahiplik kontrolü ve loglama.

Kullanım:
    from security_utils import login_required, owner_required, check_object_ownership
"""

import logging
import time
from collections import defaultdict
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
# DEKORATÖR 1b: Function-Level Authorization (Rol Kontrolü)
# OWASP API5:2023 — Broken Function Level Authorization
# ---------------------------------------------------------------

def admin_required(f):
    """
    Yalnızca 'admin' rolündeki kullanıcıların endpoint'e erişmesine izin verir.

    Yönetimsel işlemler (mod değiştirme, istatistik sıfırlama) düz kullanıcılara
    açık olmamalıdır. Bu kontrolün eksikliği, BFLA (API5) zafiyetini oluşturur:
    sıradan bir kullanıcı yönetimsel fonksiyonları tetikleyebilir.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"hata": "Bu işlem için giriş yapmalısınız.", "kod": 401}), 401
        if session.get("role") != "admin":
            security_logger.warning(
                f"Yetkisiz yönetim isteği | Kullanıcı: {session.get('user_id')} "
                f"| Endpoint: {request.path} | IP: {request.remote_addr}"
            )
            return jsonify({"hata": "Bu işlem için yönetici yetkisi gerekir.", "kod": 403}), 403
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


# ---------------------------------------------------------------
# RATE LIMITER: Kaba Kuvvet / Aşırı İstek Koruması
# OWASP API4:2023 — Unrestricted Resource Consumption
# ---------------------------------------------------------------

class RateLimiter:
    """
    Basit, bellek içi kayan pencere (sliding window) rate limiter.

    Belirli bir anahtar (örn. IP adresi) için verilen pencere süresinde
    izin verilen istek sayısını sınırlar. Brute-force parola denemelerini
    ve otomatik taramayı yavaşlatmak için kullanılır.

    Not: Tek süreçli demo için bellek içi yeterlidir. Üretimde dağıtık
    bir depo (Redis vb.) ile uygulanmalıdır.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        recent = [t for t in self._hits[key] if t > window_start]
        self._hits[key] = recent
        if len(recent) >= self.max_requests:
            return False
        recent.append(now)
        return True

    def reset(self, key: str = None) -> None:
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)
