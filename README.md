# IDOR Güvenlik Simülasyonu

> **Insecure Direct Object Reference (Güvensiz Doğrudan Nesne Referansı)** zafiyetini canlı olarak gösteren ve nasıl kapatıldığını anlatan eğitim amaçlı bir proje.
>
> **OWASP API Top 10:** API1:2023 — Broken Object Level Authorization

Dijital bir fatura sistemi üzerinden, aynı API'nin **zafiyetli** ve **güvenli** modlarını yan yana çalıştırarak IDOR saldırısını ve savunmasını canlı olarak karşılaştırmanızı sağlar.

---

## 📂 Hangi Dosya Ne İşe Yarar? (Nereden Başlamalı)

Bu repodaki belgeler, başlığına bakarak ne için olduğunu anlayacağınız şekilde adlandırılmıştır:

| Ne yapmak istiyorsanız | Şu dosyaya tıklayın |
|---|---|
| **Kurmak ve çalıştırmak** (klonla → localhost'ta web'de aç) | 👉 [**KURULUM_VE_CALISTIRMA.md**](KURULUM_VE_CALISTIRMA.md) |
| **Uygulamayı kullanmak** (web panelini adım adım nasıl kullanırım) | 👉 [**KULLANIM_KILAVUZU.md**](KULLANIM_KILAVUZU.md) |
| **Sunum yapmak / projeyi anlatmak** (anlatım metni + sunum senaryosu) | 👉 [**SUNUM_VE_PROJE_ANLATIMI.md**](SUNUM_VE_PROJE_ANLATIMI.md) |
| **Konuyu derinlemesine öğrenmek** (teori, analoji, gerçek vakalar) | 👉 [**IDOR_Egitim.md**](IDOR_Egitim.md) |
| **Genel bakış + teknik özet** | Bu dosya (README) |

> **İlk kez mi açıyorsunuz?** Sırayla: önce **KURULUM_VE_CALISTIRMA.md** ile çalıştırın,
> sonra **KULLANIM_KILAVUZU.md** ile kullanın.

---

## IDOR Nedir?

IDOR, bir uygulamanın kaynaklara (fatura, profil, dosya) erişim verirken yalnızca kullanıcının **giriş yapıp yapmadığını** kontrol etmesi, ancak o kaynağın isteği yapan kullanıcıya **ait olup olmadığını** kontrol etmemesiyle oluşan açıktır.

```
GET /api/invoice/1001   →  Ahmet'in kendi faturası      ✓
GET /api/invoice/2001   →  Mehmet'in faturası (ID değişti)

  ZAFİYETLİ MOD:  200 OK   → Mehmet'in verisi sızdırılır  ❌
  GÜVENLİ MOD:    404      → Erişim engellenir, log yazılır ✓
```

Tek savunma satırı, her nesne erişiminde yapılan **sahiplik kontrolüdür**:

```python
invoice["owner_id"] == session["user_id"]
```

---

## ⚡ Hızlı Başlangıç

Ayrıntılı adımlar için → [**KURULUM_VE_CALISTIRMA.md**](KURULUM_VE_CALISTIRMA.md)

```bash
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Sonra tarayıcıda: **http://localhost:5000**

---

## Özellikler

- **Web arayüzü (tarayıcı):** `http://localhost:5000` adresinde açılan interaktif panel — saldırgan/sunucu panelleri, login, fatura ID manipülasyonu ve mod değiştirme. **En kolay yol, ekran/display gerektirmez.**
- **Çift mod:** Tek tıkla `VULNERABLE` (zafiyetli) ve `SECURE` (güvenli) modları arasında geçiş — canlı karşılaştırma.
- **Flask REST API:** Login/logout, fatura erişimi ve mod kontrolü için endpoint'ler.
- **Tkinter GUI:** Saldırgan paneli ile sunucu/kurban panelini yan yana gösteren masaüstü arayüz (alternatif).
- **Terminal exploit demosu:** ID manipülasyonu ve sistematik taramayı renkli çıktıyla adım adım gösterir.
- **Güvenlik loglama:** Yetkisiz erişim girişimleri loglanır (gerçek sistemde SIEM'e iletilir).
- **Unit testler:** Auth, IDOR (her iki mod) ve API sertleştirmelerini doğrulayan 31 test.

---

## Proje Yapısı

```
IDOR/
├── README.md                   Genel bakış + belge indeksi (bu dosya)
├── KURULUM_VE_CALISTIRMA.md    Kurulum + localhost'ta çalıştırma adımları
├── KULLANIM_KILAVUZU.md        Web arayüzü kullanım kılavuzu
├── SUNUM_VE_PROJE_ANLATIMI.md  Sunum rehberi + projeyi anlatan metin
├── IDOR_Egitim.md              Kapsamlı eğitim rehberi (teori + analiz)
│
├── app.py                      Flask REST API + web arayüzü — IDOR noktası burada
├── templates/
│   └── index.html              Tarayıcı tabanlı interaktif demo paneli
├── main_gui.py                 Tkinter masaüstü GUI (alternatif arayüz)
├── security_utils.py           Güvenlik araçları (sahiplik kontrolü, dekoratörler, loglama)
├── exploit_demo.py             Terminal tabanlı saldırı demonstrasyonu
├── test_cases.py               Unit testler (31 senaryo)
├── requirements.txt            Bağımlılıklar (Flask, requests)
└── run.sh / run.bat            Tek tıkla başlatma scriptleri
```

---

## API Endpoint'leri

| Metot | Endpoint | Erişim | Açıklama |
|---|---|---|---|
| `GET`  | `/` | Herkes | Tarayıcı tabanlı interaktif demo paneli (HTML) |
| `POST` | `/login` | Herkes | Giriş yapar, oturum açar (rate-limit'li) |
| `POST` | `/logout` | Herkes | Oturumu kapatır |
| `GET`  | `/api/invoice/<id>` | Giriş gerekli | Fatura görüntüler — **IDOR noktası** |
| `GET`  | `/api/my-invoices` | Giriş gerekli | Kullanıcının kendi faturalarını listeler |
| `POST` | `/admin/toggle-mode` | **Admin** | Zafiyetli/güvenli mod arasında geçiş yapar |
| `GET`  | `/admin/mode` | Herkes | Mevcut modu döndürür (yalnızca okuma) |
| `GET`  | `/admin/stats` | Herkes | İstek istatistiklerini döndürür |
| `POST` | `/admin/reset-stats` | **Admin** | İstatistikleri sıfırlar |

---

## Test Kullanıcıları

| Kullanıcı | Parola | Faturaları |
|---|---|---|
| `ahmet` | `ahmet123` | #1001, #1002 |
| `mehmet` | `mehmet123` | #2001, #2002 |
| `admin` | `admin123` | — |

> Web panelinde mod değiştirmek için **admin** ile giriş yapın **veya** üstteki
> "Yönetici anahtarı" kutusuna `idor-demo-admin-token` yazın. Düz kullanıcı denerse
> sunucu bilinçli olarak **403** döner (BFLA koruması — bu da bir API güvenliği dersidir).

---

## Güvenlik Sertleştirmeleri

IDOR demosunun çift modlu yapısı korunurken, projedeki API güvenliği eksiklikleri gerçek dünya en iyi pratiklerine göre kapatılmıştır:

| Alan | OWASP API Top 10 | Uygulanan Önlem |
|---|---|---|
| Parola saklama | API2 — Broken Authentication | Parolalar `werkzeug` ile hash'lenir; sabit-zamanlı doğrulama |
| Secret key | API2 | Ortam değişkeninden okunur, yoksa güvenli rastgele üretilir |
| Oturum çerezi | API2 | `HttpOnly`, `SameSite=Lax`, üretimde `Secure` |
| Yönetim fonksiyonları | API5 — Broken Function Level Authorization | `/admin` durum değiştiren uçlar `admin_required` ile korunur |
| Kaba kuvvet | API4 — Unrestricted Resource Consumption | `/login` IP başına rate-limit (60 sn'de 5 deneme → 429) |
| Bilgi sızıntısı | API3 / genel | Kullanıcı enumeration'ı önleyen genel hata mesajları; JSON hata yanıtları |
| Tarayıcı saldırıları | Genel | Güvenlik başlıkları (`X-Content-Type-Options`, `X-Frame-Options`, CSP, vb.) |

> Not: `/api/invoice/<id>` uç noktası, IDOR taramasını canlı gösterebilmek için bilinçli olarak rate-limit dışı bırakılmıştır. Üretimde kaynak uçları da sınırlandırılmalıdır (savunma derinliği).

---

## Temel Çıkarımlar

1. **Authentication ≠ Authorization** — Sisteme giriş yapmak, her şeye erişim hakkı vermez.
2. **Her nesne isteğinde sahiplik kontrolü zorunludur** — GET, PUT, DELETE, PATCH; tüm kaynak türlerinde.
3. **UUID sahiplik kontrolünü tamamlar, yerine geçmez** — Tahmin edilemez ID'ler kaba kuvveti zorlaştırır ama asıl çözüm sahiplik kontrolüdür.

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulanması yasal suçtur.
