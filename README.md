# IDOR Güvenlik Laboratuvarı

> **API Güvenliği eğitim uygulaması — Broken Object Level Authorization (OWASP API1:2023)**
>
> Bu uygulama, gerçek dünyada en sık karşılaşılan API zafiyetlerinden biri olan
> **IDOR**'u **canlı**, **tıklanabilir** ve **anlaşılır** şekilde göstermek için
> tasarlandı. Hiç bilmediğin halde, 5 dakika içinde gerçek bir IDOR saldırısı yapıp,
> ardından kodu tek satırla nasıl düzelteceğimizi göreceksin.
>
> 🎯 **Kim için?** Bilgisayar mühendisliği / siber güvenlik öğrencileri,
>    junior backend geliştiriciler, güvenlik farkındalığı eğitimi alanlar,
>    OWASP konularına sunum hazırlayanlar.

---

## 📑 İçindekiler

1. [Bu proje ne anlatıyor?](#-bu-proje-ne-anlatıyor)
2. [IDOR nedir? (Sıfır bilgi varsayımıyla)](#-idor-nedir-sıfır-bilgi-varsayımıyla)
3. [Gerçek hayatta nerede görülür?](#-gerçek-hayatta-nerede-görülür)
4. [Neyi gösteriyor bu uygulama?](#-neyi-gösteriyor-bu-uygulama)
5. [Ön gereksinimler (ne kurulu olmalı?)](#-ön-gereksinimler-ne-kurulu-olmalı)
6. [Hızlı başlangıç (5 dakikada çalıştır)](#-hızlı-başlangıç-5-dakikada-çalıştır)
7. [Adım adım kurulum (her işletim sistemi için)](#-adım-adım-kurulum)
8. [Uygulamayı ilk kez açtığında — gezi turu](#-uygulamayı-ilk-kez-açtığında--gezi-turu)
9. [🎯 Saldırıyı **kendi başına** nasıl yaparsın](#-saldırıyı-kendi-başına-nasıl-yaparsın)
10. [Saldırı nasıl engellenir — kod seviyesinde fix](#-saldırı-nasıl-engellenir--kod-seviyesinde-fix)
11. [Sunum senaryosu (5 dakikalık demo)](#-sunum-senaryosu-5-dakikalık-demo)
12. [Demo kullanıcıları](#-demo-kullanıcıları)
13. [API referansı](#-api-referansı)
14. [Testler](#-testler)
15. [Proje dosya yapısı](#-proje-dosya-yapısı)
16. [Sıkça karşılaşılan sorunlar (Troubleshooting)](#-sıkça-karşılaşılan-sorunlar)
17. [SSS](#-sss)
18. [İleri okuma](#-ileri-okuma)
19. [Yasal uyarı](#-yasal-uyarı)

---

## 🧭 Bu proje ne anlatıyor?

Düşün ki bir muhasebe yazılımı kullanıyorsun. Tarayıcının URL çubuğunda şunu
görüyorsun:

```
https://muhasebe-yazilimi.com/fatura/1023
```

Buradaki `1023` senin faturanın numarası. **Peki ya bu sayıyı `1024` yapıp Enter'a
basarsan?** Eğer sunucu "Bu fatura sana ait mi?" sorusunu kontrol etmiyorsa,
başka bir kullanıcının faturasını okuyabilirsin. İşte buna **IDOR (Insecure
Direct Object Reference)** denir. Banka, kargo, e-ticaret, sağlık, hatta sosyal
medya uygulamalarında çok karşılaşılan, çoğu zaman **tek satır kod** ile
kapatılabilen ama kapatılmadığında milyonlarca kullanıcının verisini
sızdırabilen bir zafiyettir.

Bu proje **tam olarak bu zafiyeti** simüle ediyor. Sahte bir muhasebe arayüzünde
giriş yapıyorsun, kendi faturalarını görüyorsun, sonra "Saldırı Laboratuvarı"
sekmesinden başkasının fatura numarasını deniyorsun. **VULNERABLE** modda
sunucu sana o veriyi veriyor (zafiyet). Admin panelinden tek tıkla **SECURE**
moda alıyorsun, aynı saldırıyı tekrarladığında sunucu artık `404 Not Found`
diyor (zafiyet kapatıldı). Hepsi tarayıcıda, canlı, görsel.

---

## 🤔 IDOR nedir? (Sıfır bilgi varsayımıyla)

### Önce iki kavramı ayıralım

| Kavram                            | Sorunun cevabı                              | Örnek                                       |
| --------------------------------- | ------------------------------------------- | ------------------------------------------- |
| **Authentication** (Kimlik doğr.) | "Bu kişi kim?"                              | Giriş ekranı: kullanıcı adı + parola        |
| **Authorization** (Yetkilendirme) | "Bu kişinin **bu işleme** hakkı var mı?"    | Faturayı görme, silme, düzenleme yetkisi    |

Çoğu uygulama **Authentication**'ı doğru yapar — kimsenin parolasız giremediği
bir login sayfaları vardır. Ama **Authorization**'ı çoğu uygulama **eksik**
yapar. IDOR tam olarak bu boşluktan doğar.

### IDOR'un anatomisi (3 adımda)

1. Uygulama, sana ait bir nesneye URL veya istek gövdesinde bir **kimlik
   numarası ile** (ID) referans verir.
   Örn: `GET /api/fatura/1023`, `DELETE /api/mesaj/55`, `POST /api/odeme/{id}/iade`
2. Saldırgan bu numarayı **başkasının numarasıyla** değiştirir
   (`1023` → `1024`).
3. Sunucu **"Bu nesne gerçekten bu kullanıcıya mı ait?"** sorusunu sormaz,
   nesneyi alır ve döndürür. **Veri sızar.**

### Gerçek hayattan analoji

Bir otele check-in yaptın, 203 numaralı oda anahtarını aldın. Lobinin yanındaki
asansörde **"Hangi katı tuşlarsanız o katın koridorlarına çıkarsınız, anahtar
kontrol etmiyoruz"** yazıyor. Sen 4. katı tuşlayıp Mehmet Bey'in 412 numaralı
odasının önüne gidip kapıyı tıklatabilirsin. Asansör seni içeri sokmamalıydı.
**Asansör, IDOR'lu bir API'dir.** Senin oda anahtarını gördü (Authentication)
ama o anahtarın hangi katlara çıkma yetkisi olduğunu sormadı (Authorization).

### Niye bu kadar sık?

- API'lar tipik olarak nesneye **sıralı tam sayı ID** verir (1, 2, 3...).
  Saldırgan tahmin etmek zorunda bile değil — bir önceki veya sonraki sayıyı dener.
- Backend geliştiricisi "Kullanıcı zaten giriş yapmış, gerisini güvenebiliriz"
  yanılgısına düşer.
- Login kontrolünü framework'ün dekoratörü hallederken (`@login_required`),
  **nesne sahipliği kontrolünü her endpoint'te elle yazmak gerekir**.
  Tek bir endpoint atlanır → tüm sistem patlar.

---

## 🌍 Gerçek hayatta nerede görülür?

IDOR, OWASP API Security Top 10 listesinde **uzun yıllardır 1. sıradadır**
(API1:2023 — Broken Object Level Authorization). Bilinen gerçek örnekler:

| Yıl    | Şirket / Servis  | Olay                                                                                       |
| ------ | ---------------- | ------------------------------------------------------------------------------------------ |
| 2021   | Facebook         | Sayfalardan rastgele kullanıcıların telefon numaralarına IDOR ile ulaşıldı (533M kayıt).   |
| 2022   | Optus (Avustralya) | Müşteri ID'sini iterate ederek 10M kullanıcının kimlik bilgileri sızdırıldı.             |
| 2022   | Uber             | UUID yerine sıralı ID kullanılan endpoint'lerle iç sistem erişimi.                         |
| 2023   | T-Mobile         | API üzerinden 37M müşteri kaydı sızdırıldı (BOLA).                                         |
| Birçok | Bankacılık & e-ticaret apps | Sipariş ID'sini değiştirip başka müşterinin siparişini görme/iptal etme.        |

**Pratikte gördüğün her** `GET /api/x/<id>` **endpoint'i potansiyel olarak IDOR adayıdır.**

---

## 🧪 Neyi gösteriyor bu uygulama?

- **Bir Flask web uygulaması** (Türkçe arayüz, koyu tema, sıfır kurulum):
  - `/login` — Giriş ekranı (demo kullanıcılarına tıkla, otomatik doldur)
  - `/dashboard` — "Faturalarım": **meşru** kullanım
  - `/attack-lab` — **Saldırı Laboratuvarı**: ID'yi değiştir, IDOR'u canlı dene
    *(adım-adım rehberli, sıfır bilgili kullanıcı bile yapabilir)*
  - `/admin` — Modu değiştir, istatistikleri ve **canlı güvenlik loglarını** izle
- **Aynı endpoint, iki davranış** — tek tıkla geçiş:
  - **VULNERABLE**: Sahiplik kontrolü yok → IDOR çalışır
  - **SECURE**: `check_object_ownership` aktif → 404 ile engellenir
- **Otomatik exploit script'i** (`exploit_demo.py`) — terminalden saldırı + savunma demosu
- **19 unit testi** (`test_cases.py`) — hem zafiyetli hem güvenli davranışı doğrular
- **Terminal log'ları**: her exploit `[IDOR EXPLOIT]`, her engelleme
  `YETKİSİZ ERİŞİM GİRİŞİMİ` olarak işaretlenir

---

## 🔧 Ön gereksinimler (ne kurulu olmalı?)

Tek bir şeye ihtiyacın var: **Python 3.10 veya üstü**.

### Python kurulu mu kontrol et

Terminali aç (Windows'ta **Komut İstemi** ya da **PowerShell**, Mac'te **Terminal**, Linux'ta favori terminalin) ve şunu yaz:

```bash
python3 --version
```

Windows'ta `python3` yerine `python` yazman gerekebilir:

```cmd
python --version
```

Şuna benzer bir çıktı görmen lazım: `Python 3.11.5`.

Eğer **"command not found"** ya da Windows'ta **"'python' is not recognized"** hatası alıyorsan
Python kurulu değil demektir.

### Python yoksa nasıl kurulur?

- **Windows**: <https://python.org/downloads> → "Download Python 3.x" → kurulum sırasında
  **mutlaka** "Add Python to PATH" kutucuğunu işaretle → Install Now → bilgisayarı yeniden başlat.
- **macOS**: <https://python.org/downloads> üzerinden yükleyici indir, veya Homebrew ile:
  `brew install python`
- **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install python3 python3-venv python3-pip`
- **Linux (Fedora)**: `sudo dnf install python3 python3-pip`

Başka hiçbir şeye ihtiyacın yok. Veritabanı yok, Node.js yok, Docker yok.

---

## 🚀 Hızlı başlangıç (5 dakikada çalıştır)

GitHub'dan projeyi indir ve çalıştır — toplam 4 komut:

### macOS / Linux:

```bash
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR
chmod +x run.sh
./run.sh
```

### Windows:

```cmd
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR
run.bat
```

> `git` kurulu değilse: GitHub sayfasında yeşil **"Code"** butonu → **"Download ZIP"** → indirilen ZIP'i bir klasöre çıkar → klasöre gir.

Script otomatik olarak şunları yapar:

1. Sanal Python ortamı (`.venv`) oluşturur
2. Flask gibi gerekli paketleri yükler
3. Sunucuyu başlatır

Çıktıda şu satırı görmelisin:

```
* Running on http://127.0.0.1:5000
```

Şimdi tarayıcını aç → **<http://localhost:5000>** adresine git.
Demo kullanıcı: `ahmet` / `ahmet123`. **Tamamdır.**

---

## 🛠 Adım adım kurulum

`run.sh` / `run.bat` script'lerini kullanmak istemiyorsan veya bir hata aldıysan,
manuel olarak da kurabilirsin. Aynı 3 adım, sadece komutları sen yazarsın.

### macOS / Linux (manuel)

```bash
# 1) Repoyu indir
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR

# 2) Sanal ortam oluştur ve aktive et
python3 -m venv .venv
source .venv/bin/activate

# 3) Bağımlılıkları yükle
pip install --upgrade pip
pip install -r requirements.txt

# 4) Çalıştır
python3 app.py
```

### Windows (manuel — Komut İstemi / cmd)

```cmd
:: 1) Repoyu indir
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR

:: 2) Sanal ortam oluştur ve aktive et
python -m venv .venv
.venv\Scripts\activate.bat

:: 3) Bağımlılıkları yükle
pip install --upgrade pip
pip install -r requirements.txt

:: 4) Çalıştır
python app.py
```

### Windows (PowerShell)

PowerShell'de sanal ortamı aktive etmek farklıdır:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

> PowerShell "execution policy" hatası verirse:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

### Sunucuyu durdurmak

Terminale geri dönüp **Ctrl+C** tuşlarına bas.

### Tekrar çalıştırırken

İlk kurulumdan sonra her seferinde sadece `./run.sh` (veya `run.bat`) çağırman yeterli — sanal ortam ve paketler zaten kurulu olduğu için bu sefer hemen başlar.

---

## 🎒 Uygulamayı ilk kez açtığında — gezi turu

<http://localhost:5000> adresini açtığında **Giriş** ekranı görürsün.

### 1. Giriş (Login)

- Demo kullanıcılar formun altında listelenir (`ahmet`, `mehmet`, `ayse`, `admin`).
- **`ahmet` kutucuğuna tıkla** — kullanıcı adı ve parola otomatik dolar.
- **"Giriş Yap"** butonuna bas.

### 2. Faturalarım (Dashboard)

- Ahmet olarak iki fatura görürsün: **#1001** ve **#1002**.
- Bu sayfa uygulamanın **meşru** yüzü — sunucu zaten "WHERE owner_id = senin_id"
  filtresi uyguladığı için yalnızca sana ait kayıtları gönderir.

### 3. Saldırı Laboratuvarı

- Üst menüden **"Saldırı Laboratuvarı"** sekmesine geç.
- Sayfa **6 adımlık** bir rehber halinde tasarlandı. Sırayla takip et:
  1. Hedef seç (başkasının fatura numarasına tıkla)
  2. URL anatomisini gör
  3. Sunucu yanıtını oku
  4. Sonucu yorumla (kırmızı = saldırı başarılı, mavi = engellendi, yeşil = meşru)
  5. SECURE moda geç ve aynı saldırıyı tekrarla
  6. Logları gör

### 4. Admin Paneli

- **Modu Değiştir** butonuyla VULNERABLE ↔ SECURE arası geçiş yap.
- **İstatistikler** kartı, başarılı exploit ve engellenen istek sayısını canlı gösterir.
- **Canlı Güvenlik Logları** her isteği işaretler:
  - 🔴 `[IDOR EXPLOIT]` — VULNERABLE modda başkasına ait veri çekildi
  - 🔵 `YETKİSİZ ERİŞİM GİRİŞİMİ` — SECURE modda saldırı engellendi

---

## 🎯 Saldırıyı **kendi başına** nasıl yaparsın

Bu kısmı dikkatli oku — sıfırdan bir IDOR saldırısı yapacaksın.

### Adım 1: Giriş yap

- `ahmet` / `ahmet123` ile giriş yap.
- Ahmet'in **kullanıcı ID**'si `1`. Faturaları: **1001, 1002**.

### Adım 2: Kendi verini gör (referans noktası)

- Dashboard'da iki fatura kartı görüyorsun — bunlar "doğru" durum.
- Sağ üstte sana ait kullanıcı ID'si yazar: `#1`.

### Adım 3: Saldırı Laboratuvarı'na geç

- Üst menüden tıkla. Sayfada şunları göreceksin:
  - Sistemdeki **tüm** fatura ID'leri (`1001, 1002, 2001, 2002, 3001, 3002`).
  - Senin olanlar **SENİN** rozetiyle yeşil işaretli.

### Adım 4: Başkasının ID'sine tıkla

- **#2001** (Mehmet'in faturası) butonuna tıkla.
- Tarayıcın arka planda şu isteği gönderir:

  ```
  GET http://localhost:5000/api/invoice/2001
  Cookie: session=<senin_oturum_çerezin>
  ```

- Yanıt geliyor. Sağ taraftaki "Sunucu Yanıtı" kutusuna bak:
  - **Kırmızı rozet** — `HTTP 200 • IDOR!` görüyorsan **saldırı başarılı**.
  - Fatura içeriği gözüküyor: ₺9.750, "Yazılım Geliştirme", sahibi: Mehmet Kaya.
  - Sen Ahmet'sin ama Mehmet'in faturasını okudun. **İşte zafiyet bu.**

### Adım 5: Terminalden de aynısını dene (bonus)

Saldırı Laboratuvarı sayfasında **"curl"** kutusunda hazır komut var. Görmek istersen:

```bash
# 1) Oturumu çerez dosyasına kaydet
curl -c cookies.txt -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"ahmet","password":"ahmet123"}'

# 2) Saldırı: başkasının fatura ID'siyle istek at
curl -b cookies.txt http://localhost:5000/api/invoice/2001
```

Yanıt JSON olarak Mehmet'in faturasını döner.

### Adım 6: Modu SECURE'a al

- Üst menüden **Admin Paneli**'ne git.
- **"Modu Değiştir"** butonuna bas.
- Sağ üstte rozet artık **SECURE — IDOR kapalı** olmalı.

### Adım 7: Aynı saldırıyı tekrarla

- Saldırı Laboratuvarı'na geri dön.
- Yine **#2001**'e tıkla.
- Bu sefer:
  - **Mavi rozet** — `HTTP 404` görmelisin.
  - "🛡 Erişim engellendi" mesajı.
  - **Saldırı engellendi.**

### Adım 8: Logları izle

- Admin Paneli'ne git.
- Canlı log akışında iki farklı satır görmelisin:
  - VULNERABLE'da yaptığın deneme: `WARNING [IDOR EXPLOIT] Kullanıcı #1 → Fatura #2001 ...`
  - SECURE'daki deneme: `WARNING YETKİSİZ ERİŞİM GİRİŞİMİ ...`

Tebrikler — kendi başına bir IDOR saldırısı yaptın, kapatıldığını gözledin ve loglardan izini sürdün. 🎉

---

## 🛡 Saldırı nasıl engellenir — kod seviyesinde fix

Tüm zafiyet `app.py` dosyasındaki **tek bir endpoint**'te:

```python
@app.route("/api/invoice/<int:invoice_id>", methods=["GET"])
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
        # ↑ Bilerek 403 değil 404 dönüyoruz.
        #   403, "ID gerçek ama erişimin yok" bilgisini sızdırır.

    # ❌ VULNERABLE mod buraya hiçbir kontrol olmadan düşer
    return jsonify(invoice), 200
```

`check_object_ownership` fonksiyonu basitçe şu kontrolü yapar:

```python
def check_object_ownership(obj, user_id):
    return obj.get("owner_id") == user_id
```

### Niye 403 değil 404?

403 ("Forbidden") sunucunun saldırgana **"Bu ID var, ama sen erişemezsin"**
dediği yanıttır. Saldırgan bunu okur ve şunu anlar: "ID 2001 gerçekten var,
demek ki sistemde bir Mehmet diye kullanıcı var, demek ki..." Bu **information
disclosure** sayılır. 404 dönerek "Sen olmayan bir şeye baktın" der gibi
yapmak saldırganın işini zorlaştırır.

### Doğru savunmanın 3 katmanı

1. **Object-level authorization** (bu projedeki tek satırlık fix). Her endpoint, her nesne.
2. **UUID kullan, sıralı integer değil**. `1023` yerine `c8a4...e9f1`. Tahmin edilmesi imkansız hale gelir. Ama UUID **savunma değildir**, sadece keşfi zorlaştırır.
3. **Logla**, **anomali tespit et**. Aynı kullanıcının dakikada 100 farklı ID denemesi → otomatik blokla.

---

## 🎬 Sunum senaryosu (5 dakikalık demo)

> Aşağıdaki akışı sunum sırasında tek tek geçersen 5 dakika içinde IDOR'u izleyiciye tam anlatırsın.

**0. Hazırlık (sunumdan önce):**
- `./run.sh` ile sunucuyu başlat. Tarayıcı sekmesini `localhost:5000` ile aç. VULNERABLE modda olduğundan emin ol.

**1. Tanıt (30 sn):**
> "Bu, bir muhasebe SaaS uygulamasının ufak bir kopyası. Login'i var, kullanıcılar var, faturalar var. Şimdi içine bakacağız — ama bir API güvenlik açığı var, beraber bulacağız."

**2. Giriş ve normal kullanım (45 sn):**
- `ahmet` ile giriş yap.
- "Faturalarım" sayfasını göster: "Burada her şey doğru. Sunucu sadece Ahmet'e ait faturaları gönderiyor."

**3. Saldırı Laboratuvarı (90 sn):**
- Üst menüden geç.
- Adım 1'i göster: "Sistemde başka kullanıcıların da faturaları var. Saldırgan bu numaraları biliyor (veya tahmin ediyor)."
- **#2001**'e (Mehmet'in faturası) tıkla.
- Yanıt geldi: "**Ahmet, Mehmet'in faturasını okudu**. Sunucu kimseyi durdurmadı."
- Curl satırını göster: "İsterseniz aynısını terminalden de yapabilirsiniz."

**4. Logları kanıt olarak göster (30 sn):**
- Admin Paneli → log akışı → kırmızı `[IDOR EXPLOIT]` satırını işaret et.
- "İstatistikler" kartında **Başarılı IDOR Exploit: 1** sayacını göster.

**5. Modu çevir, saldırıyı tekrarla (60 sn):**
- Aynı sayfada **"Modu Değiştir"**'e bas. Rozet mavi/yeşil oldu.
- Saldırı Laboratuvarı'na geri dön. **#2001**'e tekrar tıkla.
- "🛡 Erişim engellendi — HTTP 404" göründü.
- Loglara dön: bu sefer mavi `YETKİSİZ ERİŞİM GİRİŞİMİ` satırı + sayaç **Engellenen: 1**.

**6. Kod seviyesinde fark (45 sn):**
- Kod editöründen veya slayttan `app.py`'nin `get_invoice` fonksiyonunu aç.
- "Tek farkı **bu üç satır**" — `check_object_ownership` kontrolünü işaretle.
- "Authentication ≠ Authorization. `@login_required` 'Bu kim?' der, ama 'Bu kişinin bu nesneye erişme hakkı var mı?' sorusunu cevaplamaz. IDOR'u kapatan **nesne-seviyesi yetkilendirme** kontrolüdür."

**7. Kapanış (15 sn):**
- "OWASP API Security Top 10'da bu zafiyet **1. sıradadır**. Facebook, T-Mobile, Optus gibi devasa şirketler bu hata yüzünden milyonlarca kullanıcı verisi sızdırdı. Pratik tek savunması: **her endpoint, her nesne için sahiplik kontrolü.**"

---

## 👥 Demo kullanıcıları

| Kullanıcı | Parola      | Kullanıcı ID | Faturaları       | Rol   |
| --------- | ----------- | ------------ | ---------------- | ----- |
| `ahmet`   | `ahmet123`  | 1            | 1001, 1002       | user  |
| `mehmet`  | `mehmet123` | 2            | 2001, 2002       | user  |
| `ayse`    | `ayse123`   | 3            | 3001, 3002       | user  |
| `admin`   | `admin123`  | 99           | (hepsine erişir) | admin |

---

## 🔬 API referansı

| Yöntem | Endpoint                       | Açıklama                                                |
| ------ | ------------------------------ | ------------------------------------------------------- |
| POST   | `/api/login`                   | Giriş (`{username, password}` JSON)                     |
| POST   | `/api/logout`                  | Çıkış                                                   |
| GET    | `/api/me`                      | Mevcut oturumu döndürür                                 |
| GET    | `/api/my-invoices`             | Kullanıcının kendi faturaları (filtrelenmiş)            |
| GET    | `/api/invoice/<id>`            | **⚠ IDOR noktası** — mod'a göre kontrol yapılır/yapılmaz |
| POST   | `/admin/toggle-mode`           | VULNERABLE ↔ SECURE arası geçiş                         |
| GET    | `/admin/mode`                  | Mevcut modu döndürür                                    |
| GET    | `/admin/stats`                 | İstatistik sayaçları                                    |
| POST   | `/admin/reset-stats`           | Sayaçları sıfırla                                       |
| GET    | `/admin/logs`                  | Son 200 güvenlik logu (UI polling için)                 |
| POST   | `/admin/clear-logs`            | Log buffer'ı temizle                                    |

---

## 🧪 Testler

```bash
# Unit testler (sunucu çalışmasına gerek yok — Flask test client kullanır)
python3 test_cases.py

# Tam exploit demosu (önce sunucu çalışıyor olmalı: python3 app.py)
python3 exploit_demo.py
```

19/19 test geçmelidir. Test paketi hem VULNERABLE hem SECURE davranışını doğrular.

---

## 📁 Proje dosya yapısı

```
IDOR/
├── app.py                  # Flask uygulaması (web sayfaları + JSON API)
├── security_utils.py       # @login_required, check_object_ownership, loglama
├── exploit_demo.py         # Otomatik saldırı script'i (CLI)
├── test_cases.py           # 19 unit test
├── desktop.py              # Pywebview ile masaüstü uygulaması (opsiyonel)
├── main_gui.py             # Tkinter GUI (eski, opsiyonel)
├── requirements.txt        # Python bağımlılıkları
├── run.sh / run.bat        # Tek komutla başlatma (macOS+Linux / Windows)
├── desktop.sh / desktop.bat# Masaüstü uygulamasını başlatma
├── IDOR_Egitim.md          # Türkçe kavramsal rehber
├── README.md               # (bu dosya)
├── templates/              # Jinja2 HTML şablonları
│   ├── base.html           # Üst menü + ortak layout
│   ├── login.html          # Giriş ekranı (kendi başına çalışan tek sayfa)
│   ├── dashboard.html      # Faturalarım
│   ├── attack_lab.html     # ⚔ 6 adımlık saldırı rehberi
│   └── admin.html          # Mod, istatistik, canlı log
└── static/
    ├── css/style.css       # Koyu tema
    └── js/main.js          # Çıkış butonu, mod rozeti, fatura kartı renderer
```

---

## 🔥 Sıkça karşılaşılan sorunlar

### "Python bulunamadı / python: command not found"

- Python kurulu değil ya da PATH'e eklenmemiş.
- Windows'ta yeniden kur, **"Add Python to PATH"** kutucuğunu işaretle.
- macOS/Linux'ta `python3 --version` dene; sadece `python` Python 2 olabilir.

### "ModuleNotFoundError: No module named 'flask'"

- Sanal ortamı aktive etmeyi unuttun. Önce:
  - macOS/Linux: `source .venv/bin/activate`
  - Windows cmd: `.venv\Scripts\activate.bat`
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
- Sonra `pip install -r requirements.txt`.

### "Address already in use" / Port 5000 dolu

- macOS'ta AirPlay 5000 portunu kullanır.
- Çözüm: `PORT=5500 python3 app.py` ile farklı bir port kullan.

### "ERR_CONNECTION_REFUSED" tarayıcıda

- Sunucu çalışmıyor olabilir. Terminale bak: `Running on http://...` görmelisin.
- Sunucu çalışıyorsa adresi doğru yazdığından emin ol: `http://localhost:5000`
  (`https` değil).

### Sunucu çalışıyor ama tarayıcı açılmıyor

- Tarayıcıyı **kendin aç** ve `http://localhost:5000` yaz. `app.py` tarayıcı açmaz; bu sadece arka uçtur.

---

## ❓ SSS

**S: Bu zafiyetli kodu kendi projeme kopyalayabilir miyim?**
C: Hayır. Bu kod açıkça zafiyetlidir, parolaları açık metin saklar, secret key sabittir. Sadece eğitim içindir. Üretime almayın.

**S: VULNERABLE modu kapatıp uygulamayı yine de eğitim için kullanabilir miyim?**
C: Evet. Admin panelinden SECURE'a aldığında uygulama "doğru" davranır. Ama açıklarken VULNERABLE/SECURE karşılaştırması demonun değeridir.

**S: IDOR sadece GET endpoint'lerinde mi olur?**
C: Hayır. `POST /api/payment/<id>/refund` da IDOR olabilir — bir saldırgan başkasının ödemesini iade ettirebilir. `DELETE /api/message/<id>` da IDOR olabilir — başkasının mesajını siler. Her HTTP yönteminde, ID parametresi alan her endpoint'te kontrol edilmeli.

**S: UUID kullanırsam IDOR'dan korunur muyum?**
C: Hayır, sadece keşfi zorlaştırırsın. UUID **tahmin edilemez** ama bir saldırgan UUID'yi log'dan, e-posta'dan, sosyal mühendislik yoluyla elde edebilir. **Tek doğru savunma sahiplik kontrolüdür.**

**S: Flask yerine başka framework'le yazsam değişir mi?**
C: Hayır, IDOR framework'ten bağımsız bir kavramsal zafiyettir. Django, Express, Spring Boot, .NET — hepsinde aynı hatayı yapabilir, aynı çözümü uygulamak zorundasın.

**S: Bu projeyi Türkçe sunumda kullanabilir miyim?**
C: Tabii. Sunum senaryosunu yukarıda hazır verdik. README'nin bilgileri özetle sunum slaytlarına çevrilebilir.

---

## 📚 İleri okuma

- **OWASP API Security Top 10 — API1:2023 BOLA**:
  <https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/>
- **OWASP Cheat Sheet — Authorization**:
  <https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html>
- **PortSwigger Web Security Academy — Access Control**:
  <https://portswigger.net/web-security/access-control>
- `IDOR_Egitim.md` — bu projenin Türkçe kavramsal rehberi (daha kısa, slayt için uygun)

---

## ⚠ Yasal uyarı

Bu proje **yalnızca eğitim ve farkındalık amaçlıdır.** Açıkça zafiyetli kod yolu
içerir. Parolalar açık metin saklanır, `secret_key` sabittir, hata mesajları
saldırgan için bilgi sızdıracak şekilde tasarlanmamıştır.

**Bu kodun "VULNERABLE" sürümünü asla üretim ortamına almayın.** Kendi
sisteminizde IDOR taraması yapmak istiyorsanız: (a) sahibi olduğunuz sistemleri,
(b) açık yazılı izin aldığınız sistemleri test edebilirsiniz. Başkasının
sistemine izinsiz IDOR denemesi yapmak **suçtur** (TCK 243, Bilişim Suçları).

---

<p align="center">
  <em>Made with ⚡ for security education.</em><br>
  OWASP API1:2023 — Broken Object Level Authorization
</p>
