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

- **Çift mod:** Tek tıkla `VULNERABLE` (zafiyetli) ve `SECURE` (güvenli) modları arasında geçiş — canlı karşılaştırma.
- **Flask REST API:** Login/logout, fatura erişimi ve mod kontrolü için endpoint'ler.
- **Tkinter GUI:** Saldırgan paneli ile sunucu/kurban panelini yan yana gösteren arayüz.
- **Terminal exploit demosu:** ID manipülasyonu ve sistematik taramayı renkli çıktıyla adım adım gösterir.
- **Güvenlik loglama:** Yetkisiz erişim girişimleri loglanır (gerçek sistemde SIEM'e iletilir).
- **Unit testler:** Hem zafiyetli hem güvenli mod davranışını doğrulayan pytest senaryoları.

---

## Proje Yapısı

```
IDOR/
├── main_gui.py          Tkinter GUI (önerilen başlangıç noktası)
├── app.py               Flask REST API — IDOR noktası burada
├── security_utils.py    Güvenlik araçları (sahiplik kontrolü, dekoratörler, loglama)
├── exploit_demo.py      Terminal tabanlı saldırı demonstrasyonu
├── test_cases.py        Unit testler
├── IDOR_Egitim.md       Kapsamlı eğitim rehberi (teori + analiz)
├── requirements.txt     Bağımlılıklar (Flask, requests)
├── run.sh / run.bat     Tek tıkla başlatma scriptleri
└── README.md
```

Ayrıntılı teori, otel odası analojisi, gerçek dünya vakaları ve kod analizi için
[**IDOR_Egitim.md**](IDOR_Egitim.md) dosyasına bakın.

---

## Kurulum ve Çalıştırma

### Gereksinim
- Python 3.8 veya üzeri
- İlk kurulumda internet bağlantısı (pip için)

### Hızlı Başlangıç

**Linux / macOS:**
```bash
chmod +x run.sh && ./run.sh
```

**Windows:**
```
run.bat dosyasına çift tıklayın
```

### Manuel Çalıştırma

```bash
# 1. Sanal ortam
python -m venv .venv
source .venv/bin/activate     # Linux/macOS
.venv\Scripts\activate        # Windows

# 2. Bağımlılıklar
pip install -r requirements.txt

# 3. Çalıştırma seçenekleri
python main_gui.py        # GUI (önerilen)
python app.py             # Sadece API sunucusu (http://localhost:5000)
python exploit_demo.py    # Terminal demosu (app.py çalışırken)
python test_cases.py      # Unit testler
```

---

## API Endpoint'leri

| Metot | Endpoint | Açıklama |
|---|---|---|
| `POST` | `/login` | Giriş yapar, oturum açar |
| `POST` | `/logout` | Oturumu kapatır |
| `GET`  | `/api/invoice/<id>` | Fatura görüntüler — **IDOR noktası** |
| `GET`  | `/api/my-invoices` | Kullanıcının kendi faturalarını listeler |
| `POST` | `/admin/toggle-mode` | Zafiyetli/güvenli mod arasında geçiş yapar |
| `GET`  | `/admin/mode` | Mevcut modu döndürür |
| `GET`  | `/admin/stats` | İstek istatistiklerini döndürür |
| `POST` | `/admin/reset-stats` | İstatistikleri sıfırlar |

---

## Test Kullanıcıları

| Kullanıcı | Parola | Faturaları |
|---|---|---|
| `ahmet` | `ahmet123` | #1001, #1002 |
| `mehmet` | `mehmet123` | #2001, #2002 |
| `admin` | `admin123` | — |

---

## Temel Çıkarımlar

1. **Authentication ≠ Authorization** — Sisteme giriş yapmak, her şeye erişim hakkı vermez.
2. **Her nesne isteğinde sahiplik kontrolü zorunludur** — GET, PUT, DELETE, PATCH; tüm kaynak türlerinde.
3. **UUID sahiplik kontrolünü tamamlar, yerine geçmez** — Tahmin edilemez ID'ler kaba kuvveti zorlaştırır ama asıl çözüm sahiplik kontrolüdür.

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulanması yasal suçtur.
