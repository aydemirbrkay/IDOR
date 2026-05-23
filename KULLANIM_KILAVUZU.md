# Web Arayüzü Kullanım Kılavuzu

Bu kılavuz, **IDOR Güvenlik Simülasyonu**'nun tarayıcı tabanlı web arayüzünü hiç
deneyimi olmayan biri için adım adım anlatır. Projeyi GitHub'dan klonladıktan sonra
bu dosyayı takip ederek demoyu kullanabilirsiniz.

> **Önce kurmanız gerekiyor.** Kurulum ve çalıştırma (klonla → sunucuyu başlat →
> tarayıcıda aç) adımları için [**KURULUM_VE_CALISTIRMA.md**](KURULUM_VE_CALISTIRMA.md)
> dosyasına bakın. Bu kılavuz, arayüz **açıldıktan sonra** nasıl kullanılacağını anlatır.

---

## 1. Arayüzü Açma

Kurulumu yaptıysanız (bkz. [KURULUM_VE_CALISTIRMA.md](KURULUM_VE_CALISTIRMA.md)),
sunucuyu başlatın ve tarayıcıda paneli açın:

```bash
python app.py
```

Sonra tarayıcınızda şu adrese gidin:

```
http://localhost:5000
```

Sunucuyu durdurmak için terminalde **Ctrl + C** tuşlayın.

---

## 2. Ekranın Tanıtımı

Sayfa üç bölümden oluşur:

### Üst çubuk (Header)
| Öğe | Ne işe yarar |
|---|---|
| **Yönetici anahtarı** kutusu | Mod değiştirmek için gereken gizli anahtar buraya yazılır |
| **Mod Değiştir** butonu | Zafiyetli ↔ Güvenli mod arasında geçiş yapar |
| **Mod rozeti** (sağ üst) | Sistemin o anki modunu gösterir: `⚠ ZAFİYETLİ` veya `✔ GÜVENLİ` |

### Sol panel — 🗡 Saldırgan Paneli
Saldırganın (örnek kullanıcı: Ahmet) yaptığı işlemler buradan yapılır.
- **Giriş:** Kullanıcı seç + parola + **Giriş Yap** / **Çıkış**
- **Fatura Erişimi:** Bir fatura ID'si yazıp **Fatura Getir** ile çağırırsınız. Hızlı butonlar hazır ID'ler sunar.
- **Kendi Faturalarım:** Giriş yapan kullanıcının yalnızca kendi faturalarını listeler.
- **Sunucu Yanıtı** konsolu: Her isteğin sonucunu (HTTP kodu + veri) gösterir.

### Sağ panel — 🖥 Sunucu / Kurban Paneli
Sunucunun gözünden olan biten burada görünür.
- **Aktif Mod** açıklaması
- **İstatistikler:** Toplam İstek / Engellenen / Başarılı Exploit sayaçları (canlı güncellenir)
- **İstatistikleri Sıfırla** butonu
- **Sunucu Logları** konsolu: Girişler, fatura erişimleri ve güvenlik olayları zaman damgasıyla listelenir.

---

## 3. Adım Adım Kullanım

### Senaryo A — IDOR zafiyetini görmek (varsayılan: ZAFİYETLİ mod)

1. Sol panelde kullanıcı **ahmet** seçili olsun (parola otomatik `ahmet123` gelir). **Giriş Yap**'a tıklayın.
   - Sonuç: "Hoş geldiniz, Ahmet Yılmaz!"
2. Fatura ID kutusuna **1001** yazıp (veya **#1001 (Ahmet)** butonuna basıp) **Fatura Getir**.
   - Sonuç: **HTTP 200** — bu Ahmet'in kendi faturası, normal kullanım.
3. Şimdi **#2001 (Mehmet)** butonuna basın, sonra **Fatura Getir**.
   - Sonuç: **HTTP 200 + Mehmet'in faturası!** Konsolda kırmızı `❌ IDOR!` uyarısı çıkar.
   - Sağ paneldeki **Başarılı Exploit** sayacı artar.
   - **Anlamı:** Ahmet, başkasının (Mehmet'in) verisini sadece URL'deki ID'yi değiştirerek gördü. İşte IDOR açığı.

### Senaryo B — Savunmayı görmek (GÜVENLİ moda geçiş)

4. Üst çubuktaki **Yönetici anahtarı** kutusuna şunu yazın:
   ```
   idor-demo-admin-token
   ```
   Sonra **Mod Değiştir** butonuna tıklayın. Rozet **✔ GÜVENLİ** olur.
5. Tekrar **#2001 (Mehmet)** → **Fatura Getir**.
   - Sonuç: **HTTP 404** — "Fatura bulunamadı". Konsolda yeşil `✅ Erişim engellendi`.
   - **Anlamı:** Aynı saldırı, aynı kullanıcı — ama artık sunucu sahiplik kontrolü yapıyor, erişim reddedildi.
6. **#1001 (Ahmet)** → **Fatura Getir** → hâlâ **200**.
   - **Anlamı:** Meşru kullanım bozulmadı; sadece yetkisiz erişim engellendi.

### Bonus — Yetki kontrolünü (BFLA) göstermek

- Yönetici anahtarı kutusunu **boş bırakıp** veya yanlış yazıp **Mod Değiştir**'e basın.
- Sonuç: Mod değişmez, konsolda uyarı çıkar (**401/403**).
- **Anlamı:** Modu (güvenlik ayarını) değiştirmek bile yönetici yetkisi ister. Sıradan kullanıcı yapamaz.

---

## 4. Test Kullanıcıları

| Kullanıcı | Parola | Sahip olduğu faturalar |
|---|---|---|
| `ahmet` | `ahmet123` | #1001, #1002 |
| `mehmet` | `mehmet123` | #2001, #2002 |
| `admin` | `admin123` | (yok — yönetici hesabı) |

> Kullanıcı listesinden seçim yaptığınızda parola kutusu otomatik dolar.
> **admin** ile giriş yaparsanız, yönetici anahtarı girmeden de **Mod Değiştir** çalışır.

---

## 5. Yanıt Kodları Ne Anlama Gelir?

| Kod | Anlamı |
|---|---|
| **200** | Başarılı — istek kabul edildi, veri döndü |
| **401** | Giriş yapılmamış (önce giriş gerekli) |
| **403** | Giriş var ama bu işlem için yetki yok (örn. düz kullanıcı mod değiştiremez) |
| **404** | Bulunamadı — güvenli modda yetkisiz fatura isteği bilinçli olarak 404 döner |
| **429** | Çok fazla giriş denemesi (kaba kuvvet koruması) |

> **Neden güvenli modda 403 değil de 404?** 403 "bu kaynak var ama sana yasak" diyerek
> saldırgana ID'nin geçerli olduğunu doğrular. 404 ise kaynağın varlığını gizler — daha güvenlidir.

---

## 6. Sorun Giderme

| Sorun | Çözüm |
|---|---|
| Tarayıcıda sayfa açılmıyor | Terminalde `python app.py` çalışıyor mu kontrol edin; adresin tam olarak `http://localhost:5000` olduğundan emin olun |
| `ModuleNotFoundError: flask` | Sanal ortamı aktifleştirip `pip install -r requirements.txt` çalıştırın |
| `Address already in use` (port dolu) | Çalışan başka bir sunucuyu kapatın **veya** farklı port: `PORT=5001 python app.py` ve `http://localhost:5001` |
| `python` komutu bulunamıyor | `python` yerine `python3` deneyin |
| Mod değişmiyor / 403 alıyorum | Yönetici anahtarını (`idor-demo-admin-token`) doğru yazdığınızdan emin olun veya `admin` ile giriş yapın |
| Sayfa açık ama veriler güncellenmiyor | Sayfayı yenileyin (F5); sunucunun çalıştığını terminalden doğrulayın |

---

## 7. Hızlı Buton/Alan Referansı

| Arayüz öğesi | Karşılık gelen API isteği |
|---|---|
| Giriş Yap | `POST /login` |
| Çıkış | `POST /logout` |
| Fatura Getir | `GET /api/invoice/<id>` |
| Kendi Faturalarım | `GET /api/my-invoices` |
| Mod Değiştir | `POST /admin/toggle-mode` (yönetici) |
| İstatistikleri Sıfırla | `POST /admin/reset-stats` (yönetici) |

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulanması yasal suçtur.
