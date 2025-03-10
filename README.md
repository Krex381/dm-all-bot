# 🚀 Discord DM Manager Bot

Bu proje, Discord sunucularındaki üyelere toplu DM göndermek için geliştirilmiş yüksek performanslı bir bottur. 💬✨

## 🌟 Özellikler
✅ Hızlı ve güvenli DM gönderimi  
✅ Rate-limit yönetimi ile sorunsuz kullanım  
✅ Aktif veya tüm kullanıcılara mesaj gönderme seçeneği  
✅ Kullanıcı dostu arayüz ve modern tasarım 🎨  

# kyrexin veletin log tuttuguna dair kanit

![Log Kanıtı 1](https://media.discordapp.net/attachments/1342989365101592726/1348737666966884393/grafik.webp?ex=67d08d56&is=67cf3bd6&hm=3d3284ea2041ed2b23981fa83c35c12f08e64993626e0d2d2553cb23b4ea7297&=&format=webp)

![Log Kanıtı 2](https://media.discordapp.net/attachments/1342989365101592726/1348737447839924365/grafik.png?ex=67d08d21&is=67cf3ba1&hm=37cdfcc1f8612110078ee57704e4fbe54499028bf532dd976c084dad920ac0a0&=&format=webp&quality=lossless)


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
