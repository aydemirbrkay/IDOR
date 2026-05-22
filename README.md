# IDOR Güvenlik Laboratuvarı

> **API Güvenliği — Broken Object Level Authorization (OWASP API1:2023)**
> Eğitim/sunum için tasarlanmış canlı IDOR demosu: tek tıkla
> **VULNERABLE ↔ SECURE** modları arasında geçiş, web UI üzerinden saldırı
> denemesi, gerçek zamanlı güvenlik logu izleme.

---

## ✨ Neler İçeriyor

- **Web UI** (Flask + HTML/CSS/JS) — koyu tema, modern, sıfır build adımı
  - `/login` — kullanıcı girişi (demo kullanıcılarını tek tıkla doldur)
  - `/dashboard` — kullanıcının kendi faturaları (meşru kullanım)
  - `/attack-lab` — **IDOR saldırı laboratuvarı**: ID'yi değiştir, canlı dene
  - `/admin` — modu değiştir, istatistikleri ve **canlı güvenlik loglarını** izle
- **Aynı endpoint, iki mod** — sunumda canlı karşılaştırma:
  - `VULNERABLE`: sahiplik kontrolü yok → IDOR çalışır
  - `SECURE`: `check_object_ownership` aktif → 404 ile engellenir
- **Otomatik exploit script'i** (`exploit_demo.py`) — terminalden saldırı + savunma
- **Unit testleri** (`test_cases.py`) — 19 test, hem zafiyetli hem güvenli davranışı doğrular
- **Türkçe arayüz ve loglar**

---

## 🚀 Çalıştırma

### Hızlı başlangıç

**macOS / Linux:**
```bash
chmod +x run.sh
./run.sh
```

**Windows:**
```cmd
run.bat
```

Ardından tarayıcıdan **<http://localhost:5000>** adresini aç.

### Manuel kurulum

```bash
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

---

## 👥 Demo Kullanıcıları

| Kullanıcı | Parola      | Faturaları       | Rol   |
| --------- | ----------- | ---------------- | ----- |
| `ahmet`   | `ahmet123`  | 1001, 1002       | user  |
| `mehmet`  | `mehmet123` | 2001, 2002       | user  |
| `ayse`    | `ayse123`   | 3001, 3002       | user  |
| `admin`   | `admin123`  | (hepsine erişir) | admin |

---

## 🎬 Sunum / Demo Akışı (5 dakika)

1. **Giriş** — `ahmet` / `ahmet123` ile giriş yap.
2. **Faturalarım** — Ahmet'in sadece kendi 2 faturasını gördüğünü göster.
3. **Saldırı Laboratuvarı** sekmesine geç.
   - Sağ üstte mod rozeti **VULNERABLE** olmalı.
   - **#2001**'e tıkla → Mehmet'in faturası **görülür** ❌
   - UI "IDOR başarıyla sömürüldü" uyarısı verir.
   - Sayfada gösterilen `curl` komutunu terminalden de çalıştırabilirsin.
4. **Admin Paneli** sekmesine geç.
   - Canlı log akışında **`[IDOR EXPLOIT]`** kaydını göster.
   - **"Modu Değiştir"** butonuna bas → SECURE moda geç.
5. Geri **Saldırı Laboratuvarı**'na dön, aynı #2001 isteğini tekrarla.
   - Sunucu artık **HTTP 404** döner → 🛡 engellendi.
   - Admin panelinde **"YETKİSİZ ERİŞİM GİRİŞİMİ"** logu belirir, sayaç artar.
6. Tek farkı `app.py` içindeki `check_object_ownership` çağrısı olduğunu göster.

---

## 🧪 Otomatik Testler

```bash
# Unit testler (Flask test client kullanır, sunucu çalışmasına gerek yok)
python3 test_cases.py

# Tam exploit demosu (önce sunucu çalışmalı: python3 app.py)
python3 exploit_demo.py
```

19/19 test geçmelidir.

---

## 🔑 Zafiyet ve Yama — Kod Seviyesinde

`app.py` → `get_invoice()` fonksiyonu:

```python
@app.route("/api/invoice/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    invoice = INVOICES.get(invoice_id)
    if not invoice:
        return jsonify({"error": "Fatura bulunamadı."}), 404

    if SECURE_MODE[0]:
        # ✅ TEK SAVUNMA SATIRI:
        if not check_object_ownership(invoice, session["user_id"]):
            log_unauthorized_access(...)
            return jsonify({"error": "Fatura bulunamadı."}), 404
        # ↑ 403 değil 404 dön: 403 saldırgana "ID gerçek ama erişimin yok"
        #   bilgisini sızdırır (information disclosure).

    return jsonify(invoice), 200
```

**Authentication ≠ Authorization.** `@login_required` "Bu kişi kim?" sorusunu
cevaplar. IDOR'u kapatan ise "Bu kişinin **bu nesneye** erişme hakkı var mı?"
sorusunu cevaplayan **nesne-seviyesi yetkilendirme** kontrolüdür.

---

## 📁 Proje Yapısı

```
IDOR/
├── app.py                  # Flask uygulaması (web + API)
├── security_utils.py       # login_required, check_object_ownership, loglama
├── exploit_demo.py         # Otomatik saldırı script'i (CLI)
├── test_cases.py           # 19 unit test
├── main_gui.py             # Tkinter GUI (opsiyonel, desktop için)
├── requirements.txt
├── run.sh / run.bat        # Tek komutla başlatma
├── IDOR_Egitim.md          # Kavramsal Türkçe rehber
├── templates/              # HTML şablonları
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── attack_lab.html
│   └── admin.html
└── static/
    ├── css/style.css
    └── js/main.js
```

---

## 🔬 API Referansı

| Yöntem | Endpoint                       | Açıklama                                   |
| ------ | ------------------------------ | ------------------------------------------ |
| POST   | `/api/login`                   | Giriş (`{username, password}` JSON)        |
| POST   | `/api/logout`                  | Çıkış                                      |
| GET    | `/api/me`                      | Mevcut oturumu döndürür                    |
| GET    | `/api/my-invoices`             | Kullanıcının kendi faturaları              |
| GET    | `/api/invoice/<id>`            | **IDOR noktası** — mod'a göre kontrol     |
| POST   | `/admin/toggle-mode`           | VULNERABLE ↔ SECURE                        |
| GET    | `/admin/mode`                  | Mevcut mod                                 |
| GET    | `/admin/stats`                 | İstatistik sayaçları                       |
| POST   | `/admin/reset-stats`           | Sayaçları sıfırla                          |
| GET    | `/admin/logs`                  | Son 200 güvenlik logu (UI polling)         |
| POST   | `/admin/clear-logs`            | Log buffer'ı temizle                       |

---

## ⚠️ Uyarı

Bu proje **sadece eğitim amaçlıdır.** Açıkça zafiyetli kod yolu içerir,
parolalar açık metin saklanır, secret key sabittir. **Asla** bu kodun
zafiyetli sürümünü üretim ortamına almayın.

---

## 📚 Daha Fazla Okuma

- [OWASP API Security Top 10 — API1:2023 BOLA](https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/)
- `IDOR_Egitim.md` — projenin Türkçe kavramsal rehberi
