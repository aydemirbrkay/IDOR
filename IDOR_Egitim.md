# IDOR Güvenlik Eğitimi
## Insecure Direct Object Reference — Kapsamlı Rehber

> **OWASP API Top 10:** API1:2023 — Broken Object Level Authorization
> **Proje:** Dijital Fatura Sistemi Güvenlik Simülasyonu

---

## İçindekiler

1. [IDOR Nedir?](#1-idor-nedir)
2. [Otel Odası Analojisi](#2-otel-odası-analojisi)
3. [Authentication vs Authorization](#3-authentication-vs-authorization)
4. [OWASP API Top 10 Referansı](#4-owasp-api-top-10-referansı)
5. [Saldırı Mekanizması](#5-saldırı-mekanizması)
6. [Proje Mimarisi](#6-proje-mimarisi)
7. [Kod Analizi: Zafiyet vs Düzeltme](#7-kod-analizi-zafiyet-vs-düzeltme)
8. [Gerçek Dünya Vakaları](#8-gerçek-dünya-vakaları)
9. [3 Temel Güvenlik Çıkarımı](#9-3-temel-güvenlik-çıkarımı)
10. [Çalıştırma Rehberi](#10-çalıştırma-rehberi)

---

## 1. IDOR Nedir?

**IDOR (Insecure Direct Object Reference — Güvensiz Doğrudan Nesne Referansı)**, bir web uygulamasının dahili kaynaklara (veritabanı kayıtları, dosyalar, faturalar) erişim izni verirken yalnızca kullanıcının sisteme **giriş yapıp yapmadığını** kontrol etmesi, ancak o kaynağın erişim isteğinde bulunan kullanıcıya **ait olup olmadığını** kontrol etmemesiyle oluşan güvenlik açığıdır.

### Bir Cümleyle

> **"URL'deki ID'yi değiştirmek yeterli — sisteme girmiş olmak her şeye erişim hakkı verir."**

Bu düşünce yanlıştır ve IDOR zafiyetinin tam tanımıdır.

---

## 2. Otel Odası Analojisi

Bu analoji, IDOR'u sezgisel olarak kavramak için kullanılır.

```
┌─────────────────────────────────────────────────────┐
│                    OTEL                             │
│                                                     │
│   Oda 304 ──→ [Anahtar Kart] ──→ SİZİN ODANIZ ✓   │
│                                                     │
│   Oda 305 ──→ [Anahtar Kart] ──→ ???               │
│                                                     │
│   ZAFİYETLİ SİSTEM:  Kapı açılır ❌               │
│   GÜVENLİ SİSTEM:    "Bu oda size ait değil" ✓    │
└─────────────────────────────────────────────────────┘
```

### Detaylı Senaryo

**Güvensiz Otel (IDOR var):**
- Resepsiyona gidip kimliğinizi gösterirsiniz → Giriş kartı alırsınız
- Kart, sadece "bu kişi misafirimizdir" bilgisini taşır
- Herhangi bir oda numarasını denerseniz — açılır
- Çünkü sistem sadece "Kart geçerli mi?" sorusunu sorar

**Güvenli Otel (IDOR yok):**
- Resepsiyona gidip kimliğinizi gösterirsiniz → Giriş kartı alırsınız
- Kart, "bu kişi yalnızca 304 numaralı odaya girebilir" bilgisini taşır
- 305'i denerseniz → "Bu oda size tahsis edilmemiş" yanıtı
- Çünkü sistem hem "Kart geçerli mi?" hem "Bu oda bu karta mı tahsis edilmiş?" sorusunu sorar

### API Karşılığı

| Otel Kavramı | API Karşılığı |
|---|---|
| Kimlik gösterme | Kullanıcı adı/parola |
| Giriş kartı | Session token / JWT |
| Oda numarası | URL'deki ID (`/api/invoice/1001`) |
| Oda tahsis kontrolü | Sahiplik kontrolü (`invoice.owner_id == session.user_id`) |

---

## 3. Authentication vs Authorization

Bu iki kavramın karıştırılması, IDOR'un temel nedenidir.

| Özellik | Authentication (Kimlik Doğrulama) | Authorization (Yetkilendirme) |
|---|---|---|
| **Soru** | "Sen kimsin?" | "Bunu yapmaya hakkın var mı?" |
| **Amaç** | Kimliği doğrula | Kaynağa erişim iznini kontrol et |
| **Örnek** | Parola kontrolü | Faturanın sahibi mi? |
| **Flask kodu** | `@login_required` | `@owner_required` |
| **Başarısız olursa** | 401 Unauthorized | 403 Forbidden / 404 Not Found |
| **IDOR ile ilişki** | Tek başına yeterli değil | IDOR'u kapatan katman budur |

### Kritik Nokta

```
Authentication (Kimlik Doğrulama) ≠ Authorization (Yetkilendirme)

Sisteme giriş yapmış olmak    ≠    Her şeye erişim hakkı
Banka kartı sahibi olmak      ≠    Tüm banka hesaplarına erişim
Otele giriş kartı almak       ≠    Tüm odalara giriş hakkı
```

---

## 4. OWASP API Top 10 Referansı

[OWASP (Open Web Application Security Project)](https://owasp.org), web ve API güvenliğinde küresel referans kabul edilen bir kuruluştur.

### API Top 10 — 2023

| Sıra | Zafiyet | IDOR İlişkisi |
|---|---|---|
| **#1** | **Broken Object Level Authorization** | **← IDOR tam olarak bu** |
| #2 | Broken Authentication | Kimlik doğrulama açıkları |
| #3 | Broken Object Property Level Authorization | Alan bazlı yetki açıkları |
| #4 | Unrestricted Resource Consumption | Rate limiting eksikliği |
| #5 | Broken Function Level Authorization | Admin fonksiyonu erişimi |

### Resmi OWASP Tanımı

> *"API'ler, kullanıcı tarafından sağlanan nesne kimliklerine dayalı kaynaklara erişirken nesne düzeyinde yetkilendirme kontrolleri gerçekleştirmelidir. Bu kontrollerin eksikliği, yetkisiz veri ifşasına, değiştirilmesine veya silinmesine yol açar."*

### Etki Analizi

IDOR başarılı bir şekilde istismar edildiğinde:
- **Gizlilik ihlali:** Başkasının kişisel/ticari verileri görüntülenir
- **Bütünlük ihlali:** Başkasının verileri değiştirilebilir (PUT/PATCH)
- **Silinme:** Başkasının verileri silinebilir (DELETE)
- **Kimlik hırsızlığı:** Profil bilgileri toplanarak kimlik avı yapılır

---

## 5. Saldırı Mekanizması

### Adım Adım Exploit (Bu Proje Senaryosu)

```
1. Ahmet sisteme giriş yapar
   POST /login  {"username": "ahmet", "password": "ahmet123"}
   ← 200 OK

2. Ahmet kendi faturasına erişir
   GET /api/invoice/1001
   ← 200 OK {"id": 1001, "owner": "Ahmet Yılmaz", ...}

3. Saldırgan URL'deki ID'yi değiştirir
   GET /api/invoice/2001   ← 1001 yerine 2001!

4. ZAFİYETLİ SUNUCU YANITI:
   ← 200 OK {"id": 2001, "owner": "Mehmet Kaya", "amount": "₺9.750"}
   ❌ Başka kullanıcının gizli bilgisi sızdırıldı!

5. GÜVENLİ SUNUCU YANITI:
   ← 404 Not Found {"error": "Fatura bulunamadı."}
   ✅ Erişim engellendi, güvenlik logu yazıldı
```

### Sistematik Tarama

Saldırgan basit bir döngüyle tüm faturaları çekebilir:

```python
for invoice_id in range(1000, 9999):
    response = requests.get(f"/api/invoice/{invoice_id}", cookies=session)
    if response.status_code == 200:
        print(f"Bulundu: #{invoice_id} → {response.json()}")
```

Bu script dakikalar içinde sistemdeki tüm faturaları çeker.

### Neden Bu Kadar Yaygın?

1. **Geliştirici varsayımı:** "Kullanıcı başka ID'yi neden denesi ki?"
2. **Yük altında atlatılan kontrol:** Hızlı geliştirmede yetkilendirme sona bırakılır, bazen hiç eklenmez
3. **Test edilmemesi:** Güvenlik testleri genellikle pozitif senaryolara odaklanır
4. **Framework kolaylığı:** ORM'ler ID ile nesne çekmeyi kolaylaştırır, kontrol geliştirici sorumluluğundadır

---

## 6. Proje Mimarisi

```
IDOR PROJE/
│
├── main_gui.py          ← Tkinter GUI (buradan başlatın)
│     ├── Flask sunucusunu arka planda başlatır
│     ├── Saldırgan Paneli (sol)
│     └── Sunucu/Kurban Paneli (sağ)
│
├── app.py               ← Flask REST API
│     ├── /login, /logout
│     ├── /api/invoice/<id>    ← IDOR noktası
│     ├── /api/my-invoices
│     └── /admin/toggle-mode   ← GUI mod kontrolü
│
├── security_utils.py    ← Güvenlik araçları
│     ├── check_object_ownership()   ← Temel savunma fonksiyonu
│     ├── login_required decorator
│     ├── owner_required decorator
│     └── log_unauthorized_access()
│
├── exploit_demo.py      ← Terminal tabanlı saldırı gösterimi
│
├── test_cases.py        ← Unit testler (pytest)
│
├── run.bat / run.sh     ← Tek tıkla başlatma
└── requirements.txt
```

### Veri Akışı

```
main_gui.py
    │
    ├──→ Flask Thread (app.py) ──→ security_utils.py
    │        │                          │
    │        ├── /login                 ├── login_required
    │        ├── /api/invoice/<id>      ├── owner_required
    │        └── /admin/toggle-mode     └── check_object_ownership
    │
    └──→ HTTP requests (requests lib)
```

---

## 7. Kod Analizi: Zafiyet vs Düzeltme

### Zafiyetli Kod

```python
# app.py — ZAFİYETLİ (SECURE_MODE = False)
@app.route("/api/invoice/<int:invoice_id>")
@login_required      # Sadece "giriş yaptın mı?" kontrolü
def get_invoice(invoice_id):
    invoice = INVOICES.get(invoice_id)
    if not invoice:
        return 404

    # ❌ Sahiplik kontrolü YOK
    # "Bu fatura bu kullanıcıya mı ait?" sorusu SORULMUYOR
    return jsonify(invoice), 200
```

### Güvenli Kod

```python
# security_utils.py — Temel savunma fonksiyonu
def check_object_ownership(resource, current_user_id, owner_field="owner_id"):
    return resource.get(owner_field) == current_user_id

# app.py — GÜVENLİ (SECURE_MODE = True)
@app.route("/api/invoice/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    invoice = INVOICES.get(invoice_id)
    if not invoice:
        return 404

    # ✅ TEMEL SAVUNMA: Sahiplik kontrolü
    if not check_object_ownership(invoice, session["user_id"]):
        log_unauthorized_access(...)
        return 404    # 403 değil: bilgi sızıntısını önlemek için

    return jsonify(invoice), 200
```

### User-to-Object Mapping Şeması

```
İstek: GET /api/invoice/2001 (Ahmet'in isteği)

  session["user_id"]        →  1  (Ahmet)
  INVOICES[2001]["owner_id"] →  2  (Mehmet)

  Karşılaştırma: 1 == 2  →  YANLIŞ

  ✅ GÜVENLİ: 404 döndür + güvenlik logu yaz
  ❌ ZAFİYETLİ: 200 döndür + Mehmet'in verisi sızdırıldı
```

### 403 vs 404 — Neden 404?

| Kod | Mesaj | Güvenlik Sorunu |
|---|---|---|
| `403 Forbidden` | "Erişim yasak" | Saldırgana ID'nin geçerli olduğunu söyler |
| `404 Not Found` | "Bulunamadı" | Kaynağın varlığını gizler — tercih edilir |

---

## 8. Gerçek Dünya Vakaları

| Şirket | Yıl | Olay | Etki |
|---|---|---|---|
| **Facebook** | 2013 | Mesaj silme API'sinde IDOR — Zuckerberg'in duvarına yazı yazıldı | $12,500 bug bounty |
| **USPS** | 2018 | 60 milyon kullanıcı profili API ID manipülasyonuyla erişildi | Veri ihlali |
| **Instagram** | 2019 | Özel hesap fotoğrafları IDOR ile görüntülendi | $30,000 bug bounty |
| **Parler** | 2021 | Sıralı ID'lerle 70TB+ veri arşivlendi (silinen içerikler dahil) | Platform çöküşü |
| **T-Mobile** | 2017 | Müşteri bilgisi API'si telefon numarasıyla sorgulanabildi | Veri ihlali |

---

## 9. 3 Temel Güvenlik Çıkarımı

### Çıkarım 1: Authentication ≠ Authorization

> Sisteme giriş yapmak, her şeye erişim hakkı vermez.

Kod örneği:
```python
# YANLIŞ: Sadece giriş kontrolü
@login_required
def get_invoice(invoice_id):
    return INVOICES.get(invoice_id)   # Kimin faturası?

# DOĞRU: Giriş + Sahiplik kontrolü
@login_required
@owner_required(lambda i: INVOICES.get(i))
def get_invoice(invoice_id):
    return INVOICES.get(invoice_id)   # Zaten doğrulandı
```

### Çıkarım 2: Her Nesne İsteğinde Sahiplik Kontrolü Zorunludur

> GET, PUT, DELETE, PATCH — tüm HTTP metodlarında, tüm kaynak türlerinde.

```
Fatura  → invoice.owner_id == session.user_id
Profil  → profile.user_id == session.user_id
Dosya   → file.uploaded_by == session.user_id
Sipariş → order.customer_id == session.user_id
```

"Never trust, always verify" — kullanıcının doğru ID gireceğine güvenme.

### Çıkarım 3: UUID Sahiplik Kontrolünü Tamamlar, Yerine Geçmez

| Yaklaşım | Kaba Kuvvet Riski | IDOR Riski |
|---|---|---|
| Sıralı ID (`/invoice/1001`) | Yüksek | Yüksek |
| UUID (`/invoice/550e8400...`) | Çok düşük | **Hâlâ var!** |
| UUID + Sahiplik kontrolü | Çok düşük | Yok ✅ |

UUID bilinen bir saldırgan için sahiplik kontrolü yoksa erişim hâlâ mümkündür.
**Asıl çözüm sahiplik kontrolüdür.**

---

## 10. Çalıştırma Rehberi

### Gereksinim

- Python 3.8 veya üzeri
- İnternet bağlantısı (ilk kurulumda pip için)

### Windows — GUI ile

```
run.bat dosyasına çift tıkla
```

### Mac / Linux — GUI ile

```bash
chmod +x run.sh && ./run.sh
```

### Manuel Çalıştırma

```bash
# 1. Sanal ortam
python -m venv .venv
source .venv/bin/activate    # Mac/Linux
.venv\Scripts\activate       # Windows

# 2. Bağımlılıklar
pip install -r requirements.txt

# 3. Seçenekler:
python main_gui.py       # GUI (önerilen)
python app.py            # Sadece API sunucu
python test_cases.py     # Unit testler
python exploit_demo.py   # Terminal demo (app.py çalışırken)
```

### Test Kullanıcıları

| Kullanıcı | Parola | Faturaları |
|---|---|---|
| `ahmet` | `ahmet123` | #1001, #1002 |
| `mehmet` | `mehmet123` | #2001, #2002 |

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulama yasal suçtur.
