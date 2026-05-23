# Kurulum ve Çalıştırma — Nasıl Kurulur, Localhost'a Nasıl Bağlanılır?

Bu dosya, projeyi **sıfırdan** kurup tarayıcıda (localhost) çalıştırmanın tüm
adımlarını anlatır. Hiç deneyimi olmayan biri bile sırayla takip ederek
çalıştırabilir.

> **Sadece 3 şey yapacaksınız:** (1) projeyi indir, (2) ortamı kur, (3) sunucuyu
> başlatıp tarayıcıda `http://localhost:5000` adresini aç.

---

## 0. Önce Bunlar Kurulu Olmalı

| Gereksinim | Nereden | Notu |
|---|---|---|
| **Python 3.8+** | [python.org/downloads](https://www.python.org/downloads/) | Windows'ta kurarken **"Add Python to PATH"** kutusunu işaretleyin |
| **Git** | [git-scm.com/downloads](https://git-scm.com/downloads) | Projeyi indirmek için (ZIP ile de indirebilirsiniz, bkz. Adım 1) |

Kurulu mu kontrol edin (terminal/komut istemi açıp yazın):

```bash
python --version      # veya: python3 --version
git --version
```

---

## 1. Projeyi İndirin (Klonlayın)

Bir terminal / komut istemi açın:

```bash
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR
```

> **Git kullanmak istemiyorsanız:** GitHub sayfasında yeşil **Code → Download ZIP**
> ile indirin, klasörü açın (extract), sonra o klasörün içinde terminal açın.

---

## 2. Sanal Ortam Kurun ve Bağımlılıkları Yükleyin

```bash
# Sanal ortam oluştur
python -m venv .venv

# Aktifleştir
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows (PowerShell / CMD)

# Gerekli paketleri yükle (Flask, requests)
pip install -r requirements.txt
```

> Aktifleştirme başarılıysa satır başında `(.venv)` yazısını görürsünüz.

---

## 3. Sunucuyu Başlatın (Web'de Çalıştırma)

```bash
python app.py
```

Terminalde şu satırları görürseniz **hazırsınız**:

```
[IDOR Sunucu] http://localhost:5000 — Mod: ZAFİYETLİ
 * Running on http://127.0.0.1:5000
```

> Bu terminali **kapatmayın** — kapatırsanız sunucu durur. Açık kalmalı.

---

## 4. Tarayıcıdan Bağlanın

Tarayıcınızı açın (Chrome, Edge, Firefox...) ve adres çubuğuna yazın:

```
http://localhost:5000
```

İnteraktif IDOR demo paneli açılır. Nasıl kullanılacağını öğrenmek için
[**KULLANIM_KILAVUZU.md**](KULLANIM_KILAVUZU.md) dosyasına bakın.

---

## 5. Sunucuyu Durdurma

Sunucunun çalıştığı terminale gelin ve **Ctrl + C** tuşlayın.

---

## Tekrar Çalıştırmak İçin (kurulumdan sonra)

Bir kez kurduktan sonra her seferinde sadece şunları yapın:

```bash
cd IDOR
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python app.py
```

---

## Alternatif Çalıştırma Yolları

```bash
./run.sh                  # Linux/macOS: tek tıkla (masaüstü GUI açar)
run.bat                   # Windows: çift tıkla (masaüstü GUI açar)

python main_gui.py        # Masaüstü Tkinter arayüzü (ekran/display gerektirir)
python exploit_demo.py    # Terminal saldırı demosu (app.py çalışırken, ayrı terminalde)
python test_cases.py      # Testleri çalıştır (31 test → OK görmelisiniz)
```

---

## Farklı Port Kullanma

5000 portu başka bir program tarafından kullanılıyorsa:

```bash
PORT=5001 python app.py                 # Linux / macOS
$env:PORT=5001; python app.py           # Windows PowerShell
set PORT=5001 && python app.py          # Windows CMD
```

Sonra tarayıcıda: `http://localhost:5001`

---

## Aynı Ağdaki Başka Cihazdan Bağlanma (sunum için, isteğe bağlı)

Sunucu `0.0.0.0` üzerinde dinlediği için **aynı Wi-Fi/ağdaki** başka bir cihaz
(telefon, arkadaşınızın bilgisayarı) sizin makinenize bağlanabilir.

1. Sunucuyu çalıştıran bilgisayarın **yerel IP adresini** bulun:
   - **Windows:** `ipconfig` → "IPv4 Address" (örn. `192.168.1.25`)
   - **Linux / macOS:** `ip addr` veya `ifconfig` → `192.168.x.x`
2. Diğer cihazın tarayıcısında açın (IP'yi kendinizinkiyle değiştirin):
   ```
   http://192.168.1.25:5000
   ```

> Bağlanamıyorsanız: iki cihaz da **aynı ağda** olmalı ve bilgisayarınızın
> **güvenlik duvarı** 5000 portuna izin vermelidir.

---

## Sorun Giderme

| Sorun | Çözüm |
|---|---|
| Tarayıcıda "bağlanılamadı" / sayfa açılmıyor | `python app.py` çalışıyor mu? Terminal kapanmamış olmalı |
| `Address already in use` (port dolu) | `PORT=5001 python app.py` ile farklı port kullanın |
| `ModuleNotFoundError: flask` | Sanal ortamı aktifleştirip `pip install -r requirements.txt` çalıştırın |
| `python` bulunamadı | `python` yerine `python3` deneyin |
| `git` bulunamadı | [git-scm.com](https://git-scm.com/downloads) adresinden Git kurun veya ZIP indirin |
| `(.venv)` görünmüyor | Aktifleştirme komutunu tekrar çalıştırın (işletim sisteminize uygun olanı) |

---

## Ortam Değişkenleri (ileri seviye, opsiyonel)

| Değişken | Varsayılan | Açıklama |
|---|---|---|
| `PORT` | `5000` | Sunucu portu |
| `FLASK_SECRET_KEY` | rastgele | Oturum imzalama anahtarı (üretimde sabit verin) |
| `FLASK_ENV` | — | `production` ise çerezler `Secure` (HTTPS) olur |
| `ADMIN_API_TOKEN` | `idor-demo-admin-token` | Web panelinde mod değiştirme için yönetici anahtarı |

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
