"""
test_cases.py — IDOR Güvenlik Unit Testleri
=============================================
Bu modül, sistemin güvenli ve güvensiz hallerini doğrular.

Çalıştırmak için:
    python -m pytest test_cases.py -v
    python test_cases.py          (pytest yoksa)

Test kategorileri:
  TestAuthentication  — Giriş/çıkış mekanizmaları
  TestVulnerableMode  — Zafiyetli modda beklenen (kötü) davranışlar
  TestSecureMode      — Güvenli modda beklenen (iyi) davranışlar
  TestSecurityUtils   — security_utils modülünün doğruluğu
"""

import unittest
import json
import sys
import os

# app.py'nin aynı dizinde olduğundan emin ol
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, SECURE_MODE, STATS
from security_utils import check_object_ownership


class BaseTestCase(unittest.TestCase):
    """Tüm test sınıfları için ortak kurulum."""

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        self.client = app.test_client()
        # Her test öncesi istatistikleri sıfırla
        STATS["total_requests"] = 0
        STATS["blocked_requests"] = 0
        STATS["successful_exploits"] = 0

    def login(self, username: str, password: str):
        return self.client.post(
            "/login",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
        )

    def login_as_ahmet(self):
        return self.login("ahmet", "ahmet123")

    def login_as_mehmet(self):
        return self.login("mehmet", "mehmet123")

    def set_vulnerable(self):
        SECURE_MODE[0] = False

    def set_secure(self):
        SECURE_MODE[0] = True


# ---------------------------------------------------------------
# TEST 1: KİMLİK DOĞRULAMA (Authentication)
# ---------------------------------------------------------------

class TestAuthentication(BaseTestCase):
    """Giriş/çıkış mekanizmalarını test eder."""

    def test_valid_login_returns_200(self):
        """Geçerli kimlik bilgileriyle giriş başarılı olmalı."""
        r = self.login_as_ahmet()
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIn("message", data)
        self.assertEqual(data["user_id"], 1)

    def test_wrong_password_returns_401(self):
        """Hatalı parola ile giriş reddedilmeli."""
        r = self.login("ahmet", "yanlis_parola")
        self.assertEqual(r.status_code, 401)

    def test_unknown_user_returns_401(self):
        """Olmayan kullanıcı ile giriş reddedilmeli."""
        r = self.login("hacker", "password")
        self.assertEqual(r.status_code, 401)

    def test_access_without_login_returns_401(self):
        """Giriş yapmadan faturaya erişim reddedilmeli."""
        r = self.client.get("/api/invoice/1001")
        self.assertEqual(r.status_code, 401)

    def test_logout_clears_session(self):
        """Çıkış sonrası oturum temizlenmeli."""
        self.login_as_ahmet()
        self.client.post("/logout")
        # Çıkış sonrası faturaya erişim reddedilmeli
        r = self.client.get("/api/invoice/1001")
        self.assertEqual(r.status_code, 401)


# ---------------------------------------------------------------
# TEST 2: ZAFİYETLİ MOD (Kötü Davranışların Kanıtı)
# ---------------------------------------------------------------

class TestVulnerableMode(BaseTestCase):
    """
    Zafiyetli modda sistemin açığını kanıtlayan testler.
    Bu testler 'başarılı exploit = test geçer' mantığıyla yazılmıştır.
    Sunum için: "Bu testlerin geçmesi SİSTEMİN BOZUK olduğunu gösterir."
    """

    def setUp(self):
        super().setUp()
        self.set_vulnerable()
        self.login_as_ahmet()

    def test_own_invoice_accessible(self):
        """Kullanıcı kendi faturasına erişebilmeli (her iki modda da)."""
        r = self.client.get("/api/invoice/1001")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["owner_id"], 1)  # Ahmet'in faturası

    def test_idor_exploit_succeeds_in_vulnerable_mode(self):
        """
        ⚠️  Bu testin GEÇMESİ BEKLENEN BİR BAŞARISIZLIKTIR.
        Zafiyetli modda Ahmet, Mehmet'in faturasına erişebilir.
        Bu test, açığın varlığını kanıtlar.
        """
        r = self.client.get("/api/invoice/2001")
        # Zafiyetli modda 200 dönmeli → saldırı başarılı
        self.assertEqual(r.status_code, 200, "Zafiyetli modda exploit çalışmıyor!")
        data = json.loads(r.data)
        self.assertEqual(data["owner_id"], 2, "Mehmet'in faturası döndürülmeli")

    def test_all_invoices_accessible_vulnerable(self):
        """Zafiyetli modda tüm faturalara erişilebilir."""
        invoice_ids = [1001, 1002, 2001, 2002]
        for inv_id in invoice_ids:
            r = self.client.get(f"/api/invoice/{inv_id}")
            self.assertEqual(r.status_code, 200,
                             f"Fatura #{inv_id} zafiyetli modda erişilemedi")

    def test_nonexistent_invoice_returns_404(self):
        """Var olmayan fatura her iki modda da 404 döndürmeli."""
        r = self.client.get("/api/invoice/9999")
        self.assertEqual(r.status_code, 404)


# ---------------------------------------------------------------
# TEST 3: GÜVENLİ MOD (Doğru Davranışların Doğrulanması)
# ---------------------------------------------------------------

class TestSecureMode(BaseTestCase):
    """Güvenli modda sistemin doğru çalıştığını doğrulayan testler."""

    def setUp(self):
        super().setUp()
        self.set_secure()
        self.login_as_ahmet()

    def test_own_invoice_still_accessible(self):
        """Güvenli modda kullanıcı kendi faturasına erişebilmeli."""
        r = self.client.get("/api/invoice/1001")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["owner_id"], 1)

    def test_idor_exploit_blocked_in_secure_mode(self):
        """
        ✅ Güvenli modda IDOR exploiti engellenmelidir.
        Ahmet Mehmet'in faturasını görememeli.
        """
        r = self.client.get("/api/invoice/2001")
        self.assertEqual(r.status_code, 404,
                         "Güvenli modda yetkisiz erişim engellenmeli!")

    def test_blocked_request_increments_counter(self):
        """Engellenen istek istatistik sayacını artırmalı."""
        before = STATS["blocked_requests"]
        self.client.get("/api/invoice/2001")
        self.assertEqual(STATS["blocked_requests"], before + 1)

    def test_other_user_invoices_blocked(self):
        """Güvenli modda tüm başka kullanıcı faturaları engellenmelidir."""
        mehmet_invoices = [2001, 2002]
        for inv_id in mehmet_invoices:
            r = self.client.get(f"/api/invoice/{inv_id}")
            self.assertEqual(r.status_code, 404,
                             f"Fatura #{inv_id} güvenli modda erişilebilir!")

    def test_mehmet_can_access_own_invoices(self):
        """Mehmet kendi oturumunda kendi faturalarına erişebilmeli."""
        self.client.post("/logout")
        self.login_as_mehmet()
        r = self.client.get("/api/invoice/2001")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertEqual(data["owner_id"], 2)

    def test_mode_toggle_works(self):
        """Mod değiştirme endpoint'i çalışmalı."""
        r = self.client.post("/admin/toggle-mode")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        # Güvenli moddan başladık, toggle sonrası zafiyetli olmalı
        self.assertFalse(data["secure"])


# ---------------------------------------------------------------
# TEST 4: security_utils MODÜLÜ
# ---------------------------------------------------------------

class TestSecurityUtils(unittest.TestCase):
    """security_utils.py fonksiyonlarını bağımsız test eder."""

    def test_ownership_check_correct_owner(self):
        """Doğru kullanıcı için sahiplik kontrolü True döndürmeli."""
        invoice = {"id": 1001, "owner_id": 1, "amount": "₺1000"}
        self.assertTrue(check_object_ownership(invoice, current_user_id=1))

    def test_ownership_check_wrong_owner(self):
        """Yanlış kullanıcı için sahiplik kontrolü False döndürmeli."""
        invoice = {"id": 2001, "owner_id": 2, "amount": "₺2000"}
        self.assertFalse(check_object_ownership(invoice, current_user_id=1))

    def test_ownership_check_custom_field(self):
        """Özel alan adıyla sahiplik kontrolü çalışmalı."""
        profile = {"user_id": 42, "name": "Test"}
        self.assertTrue(check_object_ownership(profile, 42, owner_field="user_id"))
        self.assertFalse(check_object_ownership(profile, 99, owner_field="user_id"))

    def test_ownership_check_missing_field(self):
        """Eksik alan durumunda False döndürmeli."""
        resource = {"id": 1}  # owner_id yok
        self.assertFalse(check_object_ownership(resource, current_user_id=1))


# ---------------------------------------------------------------
# ÇALIŞTIRMA
# ---------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("  IDOR Güvenlik Unit Testleri")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for cls in [TestAuthentication, TestVulnerableMode, TestSecureMode, TestSecurityUtils]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
