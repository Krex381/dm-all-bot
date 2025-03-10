# 🚀 Discord DM Manager Bot

Bu proje, Discord sunucularındaki üyelere toplu DM göndermek için geliştirilmiş yüksek performanslı bir bottur. 💬✨

## 🌟 Özellikler
✅ Hızlı ve güvenli DM gönderimi  
✅ Rate-limit yönetimi ile sorunsuz kullanım  
✅ Aktif veya tüm kullanıcılara mesaj gönderme seçeneği  
✅ Kullanıcı dostu arayüz ve modern tasarım 🎨  

## 🔧 Gereksinimler
📌 **Python 3.8+**  
📌 **Discord.py**  
📌 **Pystyle** (Renkli terminal çıktıları için)  

## ⚙️ Kurulum
1️⃣ **Bağımlılıkları yükleyin:**
   ```sh
   pip install discord pystyle requests
   ```
2️⃣ **Botu başlatın:**
   ```sh
   python main.py
   ```

## 🎮 Kullanım
Bot, iki farklı modda çalıştırılabilir:
1️⃣ **CLI Modu** (Başlatıldığında interaktif menü ile gelir)  
2️⃣ **Komut Modu** (Discord üzerinden komutlarla kontrol edilir)  

### 📝 Komutlar
🔹 **`/dmduyuru [server_id] [mesaj]`** – Belirtilen sunucudaki üyelere DM gönderir.  
💡 `aktif:` ile başlarsa, sadece aktif kullanıcılara gönderir.  
💡 `tüm:` ile başlarsa, tüm kullanıcılara gönderir.  

**Örnekler:**  
```sh
/dmduyuru 123456789 aktif: Merhaba! 👋
/dmduyuru 123456789 tüm: Önemli duyuru! 📢
```

## ⚠️ Önemli Notlar
⚠️ **Discord API**, büyük toplu mesaj gönderimlerinde rate-limit uygulayabilir. Bot, gecikmeleri otomatik olarak yönetir.  
🔒 Lisans anahtarınızı güvende tutun, aksi takdirde bot çalışmaz!  

## 👨‍💻 Geliştirici
Bu proje **Krex** tarafından geliştirilmiştir ve Leaklenmistir. Iyi kullanimlar :]. 🚀

📩 **İletişim:** [discord.gg/waylay](#)