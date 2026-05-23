# Localhost'a Bağlanma Adımları

Bu kısa rehber, projeyi kendi bilgisayarınızda (localhost) çalıştırıp tarayıcıdan
bağlanmanın adımlarını anlatır.

> **Localhost nedir?** "localhost" ve `127.0.0.1`, "kendi bilgisayarın" anlamına gelir.
> Sunucuyu kendi makinenizde başlatır, yine kendi tarayıcınızdan ona bağlanırsınız.
> İnternete açık değildir; yalnızca sizde çalışır.

---

## Adım 1 — Proje klasörüne girin ve ortamı hazırlayın

```bash
git clone https://github.com/aydemirbrkay/IDOR.git
cd IDOR

python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows (PowerShell / CMD)

pip install -r requirements.txt
```

> Bu adımları daha önce yaptıysanız, sadece klasöre girip ortamı aktifleştirmeniz yeter:
> `cd IDOR` → `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).

## Adım 2 — Sunucuyu başlatın

```bash
python app.py
```

Terminalde şu satırı görürseniz sunucu çalışıyor demektir:

```
[IDOR Sunucu] http://localhost:5000 — Mod: ZAFİYETLİ
 * Running on http://127.0.0.1:5000
```

> Terminali **kapatmayın** — kapatırsanız sunucu durur. Açık kalsın.

## Adım 3 — Tarayıcıdan bağlanın

Tarayıcınızı (Chrome, Edge, Firefox...) açın ve adres çubuğuna şunu yazın:

```
http://localhost:5000
```

İnteraktif IDOR demo paneli açılır. Kullanım için
[KULLANIM_KILAVUZU.md](KULLANIM_KILAVUZU.md) dosyasına bakın.

## Adım 4 — Sunucuyu durdurma

Sunucunun çalıştığı terminale gelin ve **Ctrl + C** tuşlayın.

---

## Farklı port kullanma

5000 portu doluysa (başka bir program kullanıyorsa) farklı bir port verin:

```bash
# Linux / macOS
PORT=5001 python app.py

# Windows (PowerShell)
$env:PORT=5001; python app.py

# Windows (CMD)
set PORT=5001 && python app.py
```

Ardından tarayıcıda: `http://localhost:5001`

---

## Aynı ağdaki başka bir cihazdan bağlanma (isteğe bağlı)

Sunucu `0.0.0.0` üzerinde dinlediği için, **aynı Wi-Fi/ağdaki** başka bir cihaz
(telefon, arkadaşınızın bilgisayarı) sizin makinenize bağlanabilir. Sunum sırasında
işe yarayabilir.

1. Sunucuyu çalıştıran bilgisayarın **yerel IP adresini** öğrenin:
   - **Windows:** `ipconfig` → "IPv4 Address" (örn. `192.168.1.25`)
   - **Linux / macOS:** `ifconfig` veya `ip addr` → `192.168.x.x` ile başlayan adres
2. Diğer cihazın tarayıcısında şunu açın (IP'yi kendi adresinizle değiştirin):
   ```
   http://192.168.1.25:5000
   ```

> Bağlanamıyorsanız: iki cihaz da **aynı ağda** olmalı; bilgisayarınızın
> **güvenlik duvarı** 5000 portuna izin vermelidir.

---

## Sorun Giderme

| Sorun | Çözüm |
|---|---|
| Tarayıcıda "bağlanılamadı" / sayfa açılmıyor | Terminalde `python app.py` çalışıyor mu kontrol edin; terminal kapanmamış olmalı |
| `Address already in use` | Port dolu — `PORT=5001 python app.py` ile farklı port kullanın |
| `ModuleNotFoundError: flask` | Sanal ortamı aktifleştirip `pip install -r requirements.txt` çalıştırın |
| `python` bulunamadı | `python` yerine `python3` deneyin |
| `git` bulunamadı | [git-scm.com](https://git-scm.com/downloads) adresinden Git kurun |

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
