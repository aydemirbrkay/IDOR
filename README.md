# IDOR Güvenlik Simülasyonu

> **Insecure Direct Object Reference (Güvensiz Doğrudan Nesne Referansı)** zafiyetini canlı olarak gösteren ve nasıl kapatıldığını anlatan eğitim amaçlı bir proje.
>
> **OWASP API Top 10:** API1:2023 — Broken Object Level Authorization

Dijital bir fatura sistemi üzerinden, aynı API'nin **zafiyetli** ve **güvenli** modlarını yan yana çalıştırarak IDOR saldırısını ve savunmasını canlı olarak karşılaştırmanızı sağlar.

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

## Özellikler

- **Web arayüzü (tarayıcı):** `http://localhost:5000` adresinde açılan interaktif panel — saldırgan/sunucu panelleri, login, fatura ID manipülasyonu ve mod değiştirme. **Kurulumu en kolay yol, ekran/display gerektirmez.**
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
├── app.py               Flask REST API + web arayüzü — IDOR noktası burada
├── templates/
│   └── index.html       Tarayıcı tabanlı interaktif demo paneli
├── main_gui.py          Tkinter masaüstü GUI (alternatif arayüz)
├── security_utils.py    Güvenlik araçları (sahiplik kontrolü, dekoratörler, loglama)
├── exploit_demo.py      Terminal tabanlı saldırı demonstrasyonu
├── test_cases.py        Unit testler (31 senaryo)
├── IDOR_Egitim.md       Kapsamlı eğitim rehberi (teori + analiz)
├── requirements.txt     Bağımlılıklar (Flask, requests)
├── run.sh / run.bat     Tek tıkla başlatma scriptleri
└── README.md
```

Ayrıntılı teori, otel odası analojisi, gerçek dünya vakaları ve kod analizi için
[**IDOR_Egitim.md**](IDOR_Egitim.md) dosyasına bakın. Web arayüzünü adım adım nasıl
kullanacağınızı öğrenmek için [**KULLANIM_KILAVUZU.md**](KULLANIM_KILAVUZU.md) dosyasına bakın.

---

## Kurulum ve Çalıştırma

> Bu bölüm sıfırdan, hiç kod bilmeyen biri de takip edebilsin diye adım adım yazılmıştır.

### Gereksinim
- **Python 3.8+** kurulu olmalı ([python.org](https://www.python.org/downloads/) — kurulumda "Add Python to PATH" işaretleyin).
- **Git** kurulu olmalı ([git-scm.com](https://git-scm.com/downloads)).
- İlk kurulumda internet bağlantısı (pip paketleri için).

### Adım 1 — Projeyi GitHub'dan indirin (klonlayın)

Bir terminal / komut istemi açın ve şunu yazın:

```bash
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR
```

> Git kullanmak istemiyorsanız: GitHub sayfasında yeşil **Code → Download ZIP** ile indirip
> klasörü açabilir, ardından o klasörde terminal açabilirsiniz.

### Adım 2 — Sanal ortam + bağımlılıklar

```bash
# Sanal ortam oluştur
python -m venv .venv

# Aktifleştir
source .venv/bin/activate     # Linux / macOS
.venv\Scripts\activate        # Windows (PowerShell/CMD)

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### Adım 3 — Tarayıcıda çalıştırın (önerilen, en kolay)

```bash
python app.py
```

Ardından tarayıcınızda şu adresi açın:

```
http://localhost:5000
```

İnteraktif panel açılır. Solda **Saldırgan Paneli** (giriş + fatura ID değiştirme),
sağda **Sunucu/Kurban Paneli** (mod, istatistik, loglar) bulunur.
Sunucuyu durdurmak için terminalde `Ctrl + C`.

### Alternatif çalıştırma yolları

```bash
# Tek tıkla başlatma (masaüstü Tkinter GUI'sini açar)
./run.sh                  # Linux / macOS  (chmod +x run.sh gerekebilir)
run.bat                   # Windows (çift tıkla)

python main_gui.py        # Masaüstü GUI (ekran/display gerektirir)
python exploit_demo.py    # Terminal saldırı demosu (app.py çalışırken, ayrı terminalde)
python test_cases.py      # Unit testleri çalıştır (31 test)
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

---

## Güvenlik Sertleştirmeleri

IDOR demosunun çift modlu yapısı korunurken, projedeki API güvenliği eksiklikleri
gerçek dünya en iyi pratiklerine göre kapatılmıştır:

| Alan | OWASP API Top 10 | Uygulanan Önlem |
|---|---|---|
| Parola saklama | API2 — Broken Authentication | Parolalar `werkzeug` ile hash'lenir; sabit-zamanlı doğrulama |
| Secret key | API2 | Ortam değişkeninden okunur, yoksa güvenli rastgele üretilir |
| Oturum çerezi | API2 | `HttpOnly`, `SameSite=Lax`, üretimde `Secure` |
| Yönetim fonksiyonları | API5 — Broken Function Level Authorization | `/admin` durum değiştiren uçlar `admin_required` ile korunur |
| Kaba kuvvet | API4 — Unrestricted Resource Consumption | `/login` IP başına rate-limit (60 sn'de 5 deneme → 429) |
| Bilgi sızıntısı | API3 / genel | Kullanıcı enumeration'ı önleyen genel hata mesajları; JSON hata yanıtları |
| Tarayıcı saldırıları | Genel | Güvenlik başlıkları (`X-Content-Type-Options`, `X-Frame-Options`, CSP, vb.) |

> Not: `/api/invoice/<id>` uç noktası, IDOR taramasını canlı gösterebilmek için
> bilinçli olarak rate-limit dışı bırakılmıştır. Üretimde kaynak uçları da
> sınırlandırılmalıdır (savunma derinliği).

### Yapılandırma (Ortam Değişkenleri)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `FLASK_SECRET_KEY` | rastgele | Oturum imzalama anahtarı (üretimde sabit bir değer verin) |
| `FLASK_ENV` | — | `production` ise çerezler `Secure` (yalnızca HTTPS) olur |
| `PORT` | `5000` | Sunucu portu |
| `ADMIN_API_TOKEN` | `idor-demo-admin-token` | Web panelinin mod değiştirmesi için yönetici anahtarı |

> **Web panelinde mod değiştirme:** Mod toggle ve istatistik sıfırlama yönetimsel
> işlemlerdir (BFLA koruması). Bunları kullanmak için ya **admin** olarak giriş yapın
> ya da panelin sağ üstündeki **"Yönetici anahtarı"** kutusuna yukarıdaki token'ı
> (`idor-demo-admin-token`) girin. Düz kullanıcı (ahmet/mehmet) ile denerseniz sunucu
> bilinçli olarak **403** döner — bu da bir API güvenliği dersidir (yetkisiz yönetim erişimi engellenir).

---

## Sunum Rehberi

> Bu bölüm, projeyi bir sunumda anlatacak kişi için hazırlanmıştır. Sırayla okuyup
> uygulayarak demoyu rahatça yönetebilirsiniz.

### Sunumun amacı (tek cümle)

> "Sisteme giriş yapmış olmak, her veriye erişim hakkı vermez; her istekte
> **kaynağın sahibi mi?** kontrolü yapılmalıdır — yapılmazsa IDOR oluşur."

### Önerilen akış (~10 dk)

| Süre | Bölüm | Ne anlatılır |
|---|---|---|
| 1 dk | IDOR nedir | Tanım + "URL'deki ID'yi değiştirmek" cümlesi |
| 1 dk | Otel odası analojisi | Giriş kartı ≠ her odanın anahtarı (bkz. `IDOR_Egitim.md`) |
| 4 dk | **Canlı demo** | Aşağıdaki senaryo: önce zafiyet, sonra savunma |
| 2 dk | Kod: tek savunma satırı | `check_object_ownership()` ve 404 tercihi |
| 2 dk | API güvenliği sertleştirmeleri | Hash, BFLA, rate-limit, header'lar tablosu |

### Canlı demo senaryosu (adım adım)

Önce sunucuyu başlatın (`python app.py`) ve `http://localhost:5000`'i açın.

**A) Zafiyeti göster (varsayılan: ZAFİYETLİ mod)**
1. Saldırgan panelinde kullanıcı **ahmet** seçili, **Giriş Yap** → "Hoş geldiniz, Ahmet Yılmaz".
2. Fatura ID **1001** → **Fatura Getir** → 200, kendi faturası. *"Bu normal kullanım."*
3. Hızlı butonlardan **#2001 (Mehmet)** → **Fatura Getir** → **200 OK + Mehmet'in verisi!**
   - Konuşma: *"Ahmet, Mehmet'in faturasını gördü. Sadece URL'deki ID'yi değiştirdim. İşte IDOR."*
   - Sağ panelde **Başarılı Exploit** sayacının arttığına dikkat çekin.

**B) Savunmayı göster (GÜVENLİ moda geç)**
4. Sağ üstteki **Yönetici anahtarı** kutusuna `idor-demo-admin-token` yazın, **Mod Değiştir** → mod **GÜVENLİ** olur.
   - Bonus ders: Önce anahtarı **boş bırakıp** denerseniz **403** alırsınız → *"Mod değiştirmek bile yönetici yetkisi ister (BFLA)."*
5. Tekrar **#2001** → **Fatura Getir** → **404**, "Fatura bulunamadı".
   - Konuşma: *"Aynı saldırı, aynı kullanıcı — ama artık sunucu sahiplik kontrolü yapıyor. 403 değil 404 döndü ki saldırgan ID'nin var olduğunu bile anlamasın."*
6. Fatura **1001** (kendi faturası) → hâlâ 200. *"Meşru kullanım bozulmadı."*

### Konuşma noktaları (jüri/soru için)

- **Neden 404, 403 değil?** 403 "bu kaynak var ama yasak" der; saldırgana geçerli ID'yi doğrular. 404 kaynağın varlığını gizler.
- **UUID kullansak IDOR biter mi?** Hayır. UUID kaba kuvveti zorlaştırır ama sahiplik kontrolü olmadan ID'yi ele geçiren erişebilir. Asıl çözüm sahiplik kontrolü.
- **Parolalar nasıl saklanıyor?** Düz metin değil; `werkzeug` ile hash'lenir, sabit-zamanlı doğrulanır.
- **Brute-force?** `/login` IP başına dakikada 5 denemeyle sınırlı (429).

### Demoya hazırlık kontrol listesi

- [ ] `python app.py` çalışıyor, `http://localhost:5000` açılıyor.
- [ ] Sağ panelde mod **ZAFİYETLİ** görünüyor (demoya buradan başlanır).
- [ ] Yönetici anahtarı (`idor-demo-admin-token`) elinizin altında.
- [ ] `python test_cases.py` → 31 test **OK** (kod sağlığını göstermek isterseniz).

---

## Temel Çıkarımlar

1. **Authentication ≠ Authorization** — Sisteme giriş yapmak, her şeye erişim hakkı vermez.
2. **Her nesne isteğinde sahiplik kontrolü zorunludur** — GET, PUT, DELETE, PATCH; tüm kaynak türlerinde.
3. **UUID sahiplik kontrolünü tamamlar, yerine geçmez** — Tahmin edilemez ID'ler kaba kuvveti zorlaştırır ama asıl çözüm sahiplik kontrolüdür.

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulanması yasal suçtur.
