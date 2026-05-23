# 10 Dakikalık Sunum Planı

Bu dosya, projeyi **10 dakikalık** bir sunumda nasıl anlatacağınızı dakika dakika,
slayt slayt planlar. Her slayt için **slaytta ne yazacağınız** ve **ne söyleyeceğiniz**
(konuşmacı notu) ayrı ayrı verilmiştir.

> Projenin anlatım metni ve genel rehber için: [SUNUM_VE_PROJE_ANLATIMI.md](SUNUM_VE_PROJE_ANLATIMI.md)
> Demoyu çalıştırmak için: [KURULUM_VE_CALISTIRMA.md](KURULUM_VE_CALISTIRMA.md)

---

## Sunum Künyesi

| Özellik | Değer |
|---|---|
| **Konu** | IDOR (Güvensiz Doğrudan Nesne Referansı) ve API güvenliği |
| **Süre** | 10 dakika (+ 2 dk soru) |
| **Hedef kitle** | Yazılım/güvenlik dersi sınıfı, jüri |
| **Amaç** | IDOR'u canlı göstermek + nasıl kapatıldığını öğretmek |
| **Format** | ~9 slayt + 1 canlı demo |
| **Anahtar mesaj** | "Giriş yapmış olmak ≠ her şeye erişim hakkı" |

> **İki kişiyseniz rol dağılımı:** Kişi A slaytları anlatır (teori), Kişi B canlı
> demoyu yapar (bilgisayar başında). Demo slaytında rol değişir.

---

## Zaman Çizelgesi (özet)

| Süre | Slayt | Başlık |
|---|---|---|
| 0:00–0:30 | 1 | Kapak ve tanıtım |
| 0:30–1:30 | 2 | Problem: IDOR nedir? |
| 1:30–2:30 | 3 | Otel analojisi + Authentication vs Authorization |
| 2:30–3:00 | 4 | Projemiz: fatura sistemi senaryosu |
| 3:00–6:30 | 5 | **CANLI DEMO** (zafiyet → savunma) |
| 6:30–8:00 | 6 | Çözüm: tek satırlık savunma + neden 404? |
| 8:00–9:00 | 7 | Ek API güvenliği önlemleri |
| 9:00–9:30 | 8 | 3 temel çıkarım |
| 9:30–10:00 | 9 | Kapanış + sorular |

---

## Slayt Slayt Plan

### 🟦 Slayt 1 — Kapak (0:00–0:30)

**Slaytta:**
- Başlık: "IDOR Güvenlik Açığı — Bir Veri Sızıntısı Nasıl Oluşur?"
- Alt başlık: OWASP API Top 10 — #1: Broken Object Level Authorization
- Sunan kişi(ler), ders/tarih

**Ne söylenir:**
> "Merhaba, bugün web ve API uygulamalarında en sık görülen açıklardan biri olan
> IDOR'u anlatacağız. Hem açığın nasıl sömürüldüğünü canlı göstereceğiz, hem de
> nasıl kapatıldığını."

---

### 🟦 Slayt 2 — Problem: IDOR Nedir? (0:30–1:30)

**Slaytta:**
- Tanım: "Uygulamanın, kullanıcının giriş yaptığını kontrol edip kaynağın **sahibi mi**
  olduğunu kontrol etmemesi."
- Görsel:
  ```
  GET /api/invoice/1001  → kendi faturam ✓
  GET /api/invoice/2001  → BAŞKASININ faturası... açılır mı?
  ```

**Ne söylenir:**
> "IDOR şöyle oluşur: Sisteme giriş yaptım, kendi faturam 1001 numara. Peki URL'deki
> numarayı 2001 yaparsam? Eğer sunucu 'bu fatura bu kişiye mi ait?' diye sormuyorsa,
> başkasının faturasını görürüm. İşte tüm açık bu kadar basit — ve tam da bu yüzden çok yaygın."

---

### 🟦 Slayt 3 — Otel Analojisi + Auth vs Auth (1:30–2:30)

**Slaytta:**
- Otel görseli: Giriş kartı her kapıyı açar mı?
- Tablo:
  | Authentication | Authorization |
  |---|---|
  | "Sen kimsin?" | "Bunu yapmaya hakkın var mı?" |
  | Giriş kartı | Oda tahsisi |

**Ne söylenir:**
> "Bunu otele benzetelim. Resepsiyondan giriş kartı aldınız — bu *kimlik doğrulama*.
> Ama o kart her odayı açmamalı; sadece sizin odanızı açmalı — bu da *yetkilendirme*.
> IDOR, bu ikisinin karıştırılmasıdır: giriş kartını her kapıya geçerli saymak."

---

### 🟦 Slayt 4 — Projemiz: Fatura Sistemi (2:30–3:00)

**Slaytta:**
- 2 kullanıcı: Ahmet (#1001, #1002) ve Mehmet (#2001, #2002)
- Uygulama iki modda çalışır: **ZAFİYETLİ** ↔ **GÜVENLİ** (tek tıkla)

**Ne söylenir:**
> "Bunu göstermek için bir fatura sistemi yaptık. İki kullanıcı var: Ahmet ve Mehmet.
> Uygulamamızın özel yanı: tek tıkla zafiyetli ve güvenli mod arasında geçebiliyoruz.
> Şimdi saldırıyı canlı görelim."

---

### 🟥 Slayt 5 — CANLI DEMO (3:00–6:30) ★ en kritik bölüm

> Tarayıcıda `http://localhost:5000` açık olmalı. Mod: **ZAFİYETLİ** ile başlayın.

**A) Zafiyeti göster (3:00–4:45):**
1. **ahmet** ile **Giriş Yap** → *"Meşru kullanıcı olarak girdim."*
2. Fatura **1001** → **Fatura Getir** → 200 → *"Kendi faturam, sorun yok."*
3. **#2001 (Mehmet)** → **Fatura Getir** → **200 + Mehmet'in verisi!**
   > "Dikkat edin — sadece numarayı değiştirdim ve Mehmet'in 9.750 TL'lik faturasını
   > gördüm. Bu bir veri sızıntısı. Sağda 'Başarılı Exploit' sayacı arttı."

**B) Savunmayı göster (4:45–6:30):**
4. Üstte **Yönetici anahtarı** kutusuna `idor-demo-admin-token` → **Mod Değiştir** → **GÜVENLİ**.
   > "Şimdi güvenli moda geçiyorum. (Not: modu değiştirmek bile yönetici yetkisi ister —
   > sıradan kullanıcı yapamaz, bu da ayrı bir koruma.)"
5. Tekrar **#2001** → **Fatura Getir** → **404**.
   > "Aynı saldırı, aynı kullanıcı — ama artık sunucu sahiplik kontrolü yaptı ve
   > engelledi. '403 yasak' yerine '404 bulunamadı' döndük; nedenini birazdan açıklayacağız."
6. **#1001** → 200 → *"Kendi faturam hâlâ açılıyor; meşru kullanım bozulmadı."*

> **Yedek plan:** Demo çalışmazsa, ekran görüntüleri/GIF hazır bulundurun.

---

### 🟦 Slayt 6 — Çözüm: Tek Satırlık Savunma (6:30–8:00)

**Slaytta:**
```python
def check_object_ownership(resource, current_user_id):
    return resource["owner_id"] == current_user_id
```
- Kural: **Her** kaynak isteğinde çağrılır.
- Neden 404? 403 "kaynak var ama yasak" der → saldırgana ID'yi doğrular. 404 gizler.

**Ne söylenir:**
> "Açığı kapatan kod aslında tek satır: erişilen faturanın sahibi, giriş yapan kullanıcı
> mı? Değilse reddet. Önemli detay: 403 yerine 404 döndük. Çünkü 403 'bu ID gerçek ama
> sana yasak' diyerek saldırgana ipucu verir; 404 ise kaynağın varlığını bile gizler."

---

### 🟦 Slayt 7 — Ek API Güvenliği Önlemleri (8:00–9:00)

**Slaytta (tablo):**
| Önlem | OWASP |
|---|---|
| Parola hash'leme | API2 |
| Yönetim uçları sadece admin (BFLA) | API5 |
| Giriş rate-limit (brute-force) | API4 |
| Güvenlik başlıkları (CSP vb.) | Genel |

**Ne söylenir:**
> "IDOR'u kapatmakla kalmadık; projede gerçek dünya güvenlik önlemleri de var:
> parolalar düz metin değil hash'li; yönetim fonksiyonları sadece admin'e açık;
> giriş denemeleri sınırlı, yani kaba kuvvet engelleniyor; ve tarayıcı saldırılarına
> karşı güvenlik başlıkları ekli."

---

### 🟦 Slayt 8 — 3 Temel Çıkarım (9:00–9:30)

**Slaytta:**
1. Authentication ≠ Authorization
2. Her nesne isteğinde sahiplik kontrolü zorunlu
3. UUID açığı kapatmaz, sahiplik kontrolü kapatır

**Ne söylenir:**
> "Üç şey aklınızda kalsın: Giriş yapmak yetki vermez. Her veri isteğinde sahiplik
> kontrol edilmeli. Ve tahmin edilemez ID kullanmak tek başına yeterli değil — asıl
> çözüm sahiplik kontrolüdür."

---

### 🟦 Slayt 9 — Kapanış + Sorular (9:30–10:00)

**Slaytta:**
- "Giriş yapmış olmak, her veriye erişim hakkı vermez."
- GitHub repo linki + teşekkür
- "Sorular?"

**Ne söylenir:**
> "Özetle: IDOR çok basit bir hatadan doğar ama sonuçları ağırdır — Facebook'tan USPS'e
> kadar büyük platformları etkiledi. Çözümü de basit: her istekte sahiplik kontrolü.
> Teşekkürler, sorularınızı alabiliriz."

---

## Olası Sorular ve Kısa Cevaplar

- **"UUID kullansak yeter mi?"** → Hayır; ID'yi ele geçiren yine erişir. Asıl çözüm sahiplik kontrolü.
- **"Neden 404, 403 değil?"** → 403 geçerli ID'yi doğrular; 404 varlığı gizler.
- **"Parolalar nasıl saklanıyor?"** → Hash + sabit-zamanlı doğrulama, düz metin değil.
- **"Gerçek hayatta görüldü mü?"** → Evet: Facebook, Instagram, USPS, Parler (bkz. IDOR_Egitim.md).
- **"Performansı etkiler mi?"** → Hayır; tek bir karşılaştırma, ihmal edilebilir maliyet.

---

## Sunum Öncesi Hazırlık Listesi

- [ ] Sunum bilgisayarında `python app.py` çalışıyor, `http://localhost:5000` açık.
- [ ] Mod **ZAFİYETLİ** ile başlıyor (demoya buradan girilecek).
- [ ] Yönetici anahtarı (`idor-demo-admin-token`) bir yere not edildi / kopyalandı.
- [ ] Tarayıcı yazı tipi büyütüldü (Ctrl + ile zoom), arka koltuktan görünsün.
- [ ] Demo bir kez prova edildi; yedek ekran görüntüleri/GIF hazır.
- [ ] İnternet yoksa demo yerelde çalışıyor (localhost — internet gerekmez).
- [ ] Slaytlar + bu plan açık; rol dağılımı netleşti.

---

## Materyal Kontrol Listesi

- Slaytlar (9 slayt)
- Çalışan demo (bilgisayar + tarayıcı)
- Yedek: demo ekran görüntüleri / kısa video
- GitHub repo linki (paylaşmak için)

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
