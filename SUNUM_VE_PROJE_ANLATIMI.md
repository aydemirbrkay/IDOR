# Sunum ve Proje Anlatımı

Bu dosya iki şey içindir:
1. **Projeyi anlatan metin** — projenin ne olduğunu, neyi gösterdiğini ve nasıl
   çalıştığını başlıklarla, ayrıntılı biçimde anlatır.
2. **Sunum rehberi** — bir sunumda adım adım ne söyleyeceğinizi ve hangi düğmeye
   tıklayacağınızı gösterir.

> Teorinin tamamı (analoji, gerçek dünya vakaları, OWASP referansları) için ayrıca
> [IDOR_Egitim.md](IDOR_Egitim.md) dosyasına bakın.
>
> **Dakika dakika, slayt slayt 10 dakikalık sunum planı** için:
> [SUNUM_PLANI.md](SUNUM_PLANI.md).

---

# BÖLÜM 1 — PROJEYİ ANLATAN METİN

## 1.1 Proje Nedir?

Bu proje, bir **dijital fatura sistemi** üzerinden **IDOR** adlı güvenlik açığını
*canlı* olarak gösteren eğitim amaçlı bir uygulamadır. Aynı API iki modda çalışır:

- **ZAFİYETLİ mod:** Açık aktiftir; bir kullanıcı başkasının faturasını görebilir.
- **GÜVENLİ mod:** Açık kapatılmıştır; yetkisiz erişim engellenir.

Tek bir butonla iki mod arasında geçip "öncesi / sonrası" karşılaştırması yaparsınız.

## 1.2 IDOR Nedir?

**IDOR (Insecure Direct Object Reference — Güvensiz Doğrudan Nesne Referansı)**,
bir uygulamanın bir kaynağa (fatura, profil, dosya) erişim verirken yalnızca
kullanıcının **giriş yapıp yapmadığını** kontrol etmesi, ancak o kaynağın
**isteyen kişiye ait olup olmadığını** kontrol etmemesiyle oluşan açıktır.

> Tek cümleyle: **"URL'deki ID'yi değiştirmek, başkasının verisine erişmeye yetmemeli."**

Bu, OWASP API Güvenlik Top 10 listesinde **API1:2023 — Broken Object Level
Authorization** olarak 1. sıradadır.

## 1.3 Otel Odası Analojisi

- **Güvensiz otel (IDOR var):** Giriş kartınız sadece "bu kişi misafirimizdir" der.
  Herhangi bir oda numarasını denerseniz kapı açılır.
- **Güvenli otel (IDOR yok):** Kart "bu kişi yalnızca 304 numaralı odaya girebilir"
  bilgisini taşır. Başka odayı denerseniz "Bu oda size tahsis edilmemiş" yanıtı alırsınız.

| Otel | API karşılığı |
|---|---|
| Giriş kartı | Oturum (session) |
| Oda numarası | URL'deki ID (`/api/invoice/1001`) |
| Oda tahsis kontrolü | Sahiplik kontrolü (`fatura.owner_id == oturum.user_id`) |

## 1.4 Sistem Nasıl Çalışıyor? (Mimari)

```
Tarayıcı (web paneli)  ──HTTP──>  Flask API (app.py)  ──>  security_utils.py
   templates/index.html               /login                  sahiplik kontrolü
                                       /api/invoice/<id>        admin yetki kontrolü
                                       /admin/toggle-mode       rate-limit, loglama
```

- **app.py** — REST API + web sayfasını sunar. IDOR noktası `/api/invoice/<id>`'dir.
- **security_utils.py** — Asıl savunma burada: `check_object_ownership()`, yetki
  dekoratörleri, rate limiter ve güvenlik loglaması.
- **templates/index.html** — Tarayıcıda çalışan saldırgan + sunucu panelleri.

## 1.5 Tek Satırlık Savunma

IDOR'u kapatan asıl mantık tek bir karşılaştırmadır:

```python
def check_object_ownership(resource, current_user_id):
    return resource.get("owner_id") == current_user_id
```

Her kaynak erişiminde bu çağrılır. `False` dönerse erişim reddedilir.

## 1.6 Neden 403 Değil de 404?

Yetkisiz erişimde **404 (Bulunamadı)** döndürürüz, 403 (Yasak) değil:
- **403** "bu kaynak var ama sana yasak" diyerek saldırgana ID'nin geçerli olduğunu *doğrular*.
- **404** kaynağın varlığını *gizler* — saldırgan hangi ID'lerin gerçek olduğunu anlayamaz.

## 1.7 Projedeki Ek API Güvenliği Önlemleri

IDOR'a ek olarak, gerçek dünya en iyi pratikleri uygulanmıştır:

| Alan | OWASP | Önlem |
|---|---|---|
| Parola saklama | API2 | `werkzeug` ile hash + sabit-zamanlı doğrulama |
| Yönetim fonksiyonları | API5 (BFLA) | `/admin` durum değiştiren uçlar yalnızca admin |
| Kaba kuvvet | API4 | `/login` IP başına dakikada 5 deneme (sonra 429) |
| Tarayıcı saldırıları | Genel | Güvenlik başlıkları (CSP, X-Frame-Options, vb.) |
| Bilgi sızıntısı | Genel | Genel hata mesajları, JSON hata yanıtları |

---

# BÖLÜM 2 — SUNUM REHBERİ

## 2.1 Sunumun Amacı (tek cümle)

> "Sisteme giriş yapmış olmak her veriye erişim hakkı vermez; her istekte
> **kaynağın sahibi mi?** kontrolü yapılmalı — yapılmazsa IDOR oluşur."

## 2.2 Önerilen Akış (~10 dakika)

| Süre | Bölüm | Ne anlatılır |
|---|---|---|
| 1 dk | IDOR nedir | Tanım + "URL'deki ID'yi değiştir" cümlesi (1.2) |
| 1 dk | Otel analojisi | Giriş kartı ≠ her odanın anahtarı (1.3) |
| 4 dk | **Canlı demo** | Aşağıdaki senaryo: önce zafiyet, sonra savunma |
| 2 dk | Kod: tek savunma satırı | `check_object_ownership()` ve 404 tercihi (1.5–1.6) |
| 2 dk | Ek API güvenliği | Hash, BFLA, rate-limit, header'lar (1.7) |

## 2.3 Canlı Demo Senaryosu (adım adım)

Önce sunucuyu başlatın (`python app.py`) ve `http://localhost:5000`'i açın.
Kurulum için [KURULUM_VE_CALISTIRMA.md](KURULUM_VE_CALISTIRMA.md).

**A) Zafiyeti göster (varsayılan: ZAFİYETLİ mod)**
1. Kullanıcı **ahmet** seçili → **Giriş Yap** → "Hoş geldiniz, Ahmet Yılmaz".
2. Fatura ID **1001** → **Fatura Getir** → **200**, kendi faturası. *"Normal kullanım."*
3. **#2001 (Mehmet)** → **Fatura Getir** → **200 + Mehmet'in verisi!**
   - *"Sadece URL'deki ID'yi değiştirdim ve başkasının faturasını gördüm. İşte IDOR."*
   - Sağ panelde **Başarılı Exploit** sayacı artar.

**B) Savunmayı göster (GÜVENLİ moda geç)**
4. Sağ üstte **Yönetici anahtarı** kutusuna `idor-demo-admin-token` yazın → **Mod Değiştir** → mod **GÜVENLİ**.
   - *Bonus:* Önce kutuyu boş bırakıp denerseniz **403** alırsınız → "Modu değiştirmek bile yönetici yetkisi ister (BFLA)."
5. Tekrar **#2001** → **Fatura Getir** → **404** "Fatura bulunamadı".
   - *"Aynı saldırı, aynı kullanıcı — ama artık sahiplik kontrolü var. 403 değil 404 döndü ki ID'nin varlığı bile gizlensin."*
6. **#1001** (kendi faturası) → hâlâ **200**. *"Meşru kullanım bozulmadı."*

## 2.4 Olası Sorular ve Cevaplar

- **UUID kullansak IDOR biter mi?** Hayır. UUID kaba kuvveti zorlaştırır ama
  sahiplik kontrolü yoksa ID'yi ele geçiren yine erişir. Asıl çözüm sahiplik kontrolü.
- **Neden 404 döndürdünüz?** Bkz. 1.6 — 403 saldırgana geçerli ID'yi doğrular.
- **Parolalar nasıl saklanıyor?** Düz metin değil; hash + sabit-zamanlı doğrulama.
- **Brute-force'a karşı?** `/login` IP başına dakikada 5 denemeyle sınırlı (429).
- **Bu gerçek bir açık mı?** Evet — Facebook, Instagram, USPS gibi büyük platformlarda
  görüldü (ayrıntı: IDOR_Egitim.md).

## 2.5 Sunum Öncesi Kontrol Listesi

- [ ] `python app.py` çalışıyor, `http://localhost:5000` açılıyor.
- [ ] Sağ panelde mod **ZAFİYETLİ** görünüyor (demoya buradan başlanır).
- [ ] Yönetici anahtarı (`idor-demo-admin-token`) elinizin altında.
- [ ] `python test_cases.py` → **31 test OK** (kod sağlığını göstermek isterseniz).
- [ ] İnternet/yansıtma çalışıyorsa, telefondan da `http://<IP>:5000` ile gösterebilirsiniz.

---

> **Yasal Uyarı:** Bu proje yalnızca eğitim ve akademik amaçlıdır.
> Gerçek sistemlere izinsiz uygulanması yasal suçtur.
