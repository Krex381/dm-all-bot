# DM Manager v2.0 - Krex

Gelişmiş Discord DM yönetim aracı

## 🚀 Özellikler

### Temel Özellikler
- Özelleştirilebilir DM mesaj gönderimi
- Aktif ve tüm kullanıcılara gönderim desteği
- Gelişmiş rate limit koruması
- Büyük sunucu desteği (100K+ üye)
- Kişiselleştirilmiş kullanıcı mentionları
- İlerleme takibi ve istatistikler

### Mesaj Türleri
- Düz metin mesajları
- Tam özelleştirilebilir embedler
- Resim eklentileri
- Kombine mesajlar (metin + embed + resim)

### Embed Sistemi
- Embed önayarlarını kaydetme ve yönetme
- Tam embed özelleştirme:
  - Başlık ve açıklama
  - Özel renkler (HEX)
  - Yazar bilgileri
  - Alt yazı
  - Küçük ve büyük resimler
  - Çoklu alanlar
  - Kullanıcı etiket entegrasyonu

### Komut Sistemi
- CLI ve slash komut desteği
- Sadece sunucularda komut kullanımı
- Gizli yanıtlar (ephemeral)
- Sadece yetkililere özel erişim

## 📋 Komutlar

### Slash Komutları
```
/dmduyuru [sunucu_id] [seçenekler]
Seçenekler:
  - mesaj: Mesaj içeriği
  - resim: Direkt resim yükleme
  - embed_önayar: Kayıtlı embed kullanımı
  - hedef: "aktif" veya "tüm"
  - gecikme: Toplu gönderimler arası bekleme (saniye)
  - paket_boyutu: Toplu gönderim miktarı

/embedayarla [önayar_adı] [seçenekler]
  - başlık: Embed başlığı
  - açıklama: Ana metin
  - renk: HEX renk kodu
  - küçük_resim: Küçük resim URL
  - büyük_resim: Büyük resim URL
  - yazar_adı: Yazar adı
  - yazar_resmi: Yazar icon URL
  - alanlar: "başlık1|açıklama1,başlık2|açıklama2"

/embedsil [önayar_adı]
/embedlerim
```

### CLI Arayüzü
1. DM Duyuru Gönder
   - Düz metin mesajları
   - Kullanıcı mention entegrasyonu
   - Aktif/Tüm kullanıcı filtresi

2. Embed DM Gönder
   - Tam embed özelleştirme
   - Resim desteği
   - Kayıtlı sunucu ID'leri

3. Komut Modu
   - Slash komutları aktifleştirme
   - DM üzerinden komut yardımı

## ⚙️ Yapılandırma

### Bot Ayarları
- Bot token kaydı
- Owner ID yapılandırması
- İkincil owner desteği
- Varsayılan sunucu ID kaydı

### Performans Ayarları
- Toplu gönderim boyutu özelleştirme (varsayılan: 35)
- Gecikme kontrolü
- Rate limit yönetimi
- Event loop optimizasyonu

## 🔧 Kurulum

1. Gereksinimler:
```
discord.py
pystyle
aiohttp
```

2. Yapılandırma:
- Bot tokeninizi girin
- Owner ID'lerini ayarlayın
- Varsayılan sunucu ID'sini ayarlayın (isteğe bağlı)

3. Çalıştırma:
```bash
python main.py
```

## 🛠️ Gelişmiş Kullanım

### Embed Önayarları
Karmaşık embed tasarımlarını kaydedin:
```
/embedayarla test_preset title:"Test" description:"Açıklama" color:#ff0000
```

### Mesaj Filtreleme
Belirli kullanıcıları hedefleyin:
```
/dmduyuru 123456789 target:aktif message:"Merhaba!"
```

### Performans Ayarı
Toplu gönderim ayarlarını düzenleyin:
```
/dmduyuru 123456789 batch_size:50 delay:2 message:"Merhaba!"
```

## 📝 Notlar

- Mesajlara kullanıcı mentionları eklenir: `<@userid>`
- Rate limitler otomatik yönetilir
- Tüm yanıtlar gizlidir (ephemeral)
- Hatalar loglanır ama kullanıcılardan gizlenir
- Ayarlar oturumlar arasında kaydedilir

## ⚠️ Güncellemeler (v2.0)
- Kullanıcı mention entegrasyonu eklendi
- Embed önayar sistemi geliştirildi
- Rate limit yönetimi iyileştirildi
- Büyük sunucu desteği geliştirildi
- Toplu gönderim boyutu kontrolü eklendi
- Hata yönetimi iyileştirildi

---
Krex tarafından geliştirildi | DM Manager v2.0
