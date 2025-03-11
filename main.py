import discord
import asyncio
import time
import json
import os
import sys
from discord.ext import commands
from pystyle import Colors, Colorate
from datetime import datetime
from typing import Optional
import aiohttp
from tqdm import tqdm
import datetime
from discord.ui import Select, View, Button

VERSION = "2.1.0"
CHANGELOG = """
v2.1.0 Güncellemeler:
• Düğme tabanlı CLI arayüzü
• Gelişmiş kullanıcı mentionları
• DM sonuç loglaması
• İlerleme çubuğu
• Embed yöneticisi iyileştirmeleri
"""

# Add helper functions at the top level
def has_sent_help_message() -> bool:
    """Check if help message has been sent before"""
    try:
        return os.path.exists("help_sent.dat")
    except:
        return False

def mark_help_sent() -> None:
    """Mark that help message has been sent"""
    try:
        with open("help_sent.dat", "w") as f:
            f.write("1")
    except Exception as e:
        print(Colorate.Color(Colors.yellow, f"Uyarı: Yardım gönderim durumu kaydedilemedi: {e}"))

class DMLogger:
    def __init__(self):
        self.log_file = f"dm_kayitlari_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    def log(self, message: str):
        with open(self.log_file, "a", encoding="utf-8") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {message}\n")

dm_logger = DMLogger()

if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)

def load_bot_settings():
    try:
        if os.path.exists("botinfo.dat"):
            with open("botinfo.dat", "r") as f:
                settings_data = f.read().strip()
                if settings_data:
                    settings = json.loads(settings_data)
                    return settings
    except Exception as e:
        print(Colorate.Color(Colors.yellow, f"Uyarı: Bot ayarları yüklenemedi: {e}"))
    return None

def save_bot_settings(bot_token, owner_id, second_owner_id="0"):
    try:
        settings = {
            "bot_token": bot_token,
            "owner_id": owner_id,
            "second_owner_id": second_owner_id
        }
        with open("botinfo.dat", "w") as f:
            f.write(json.dumps(settings))
        return True
    except Exception as e:
        print(Colorate.Color(Colors.yellow, f"Uyarı: Bot ayarları kaydedilemedi: {e}"))
        return False

async def send_dm(member, message_content):
    start_time = time.time()
    try:
        await member.send(content=message_content)
        end_time = time.time()
        duration = end_time - start_time
        print(Colorate.Color(Colors.green, f"[+] Mesaj gönderildi {member.name} ({member.id}) - Süre: {duration:.2f} saniye"))
        return True
    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] {member.name} ({member.id}) mesaj gönderilemedi: {e}"))
        return False

async def send_dm_with_rate_limit(member, message_content):
    start_time = time.time()
    max_retries = 3
    base_delay = 0.5
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                delay = base_delay * (2 ** attempt)
                print(Colorate.Color(Colors.yellow, f"[!] Rate limit hit, retrying in {delay:.2f}s for {member.name}"))
                await asyncio.sleep(delay)
            
            await member.send(content=message_content)
            end_time = time.time()
            duration = end_time - start_time
            print(Colorate.Color(Colors.green, f"[+] Mesaj gönderildi {member.name} ({member.id}) - Süre: {duration:.2f} saniye"))
            return True
        except discord.errors.HTTPException as e:
            if e.status == 429:
                if attempt == max_retries - 1:  
                    print(Colorate.Color(Colors.red, f"[-] {member.name} ({member.id}) mesaj gönderilemedi: Rate limit exceeded"))
                    return False
            else:
                print(Colorate.Color(Colors.red, f"[-] {member.name} ({member.id}) mesaj gönderilemedi: {e}"))
                return False
        except Exception as e:
            print(Colorate.Color(Colors.red, f"[-] {member.name} ({member.id}) mesaj gönderilemedi: {e}"))
            return False
    
    return False  

# Add rate limit handler
class RateLimitHandler:
    def __init__(self):
        self.reset_after = 0.02  # Reduced from 0.05 to 0.02 seconds
        self.last_send = 0
        self.concurrent_limit = 35  # Increased from 25 to 35
        self.semaphore = asyncio.Semaphore(35)  # Increased concurrency
        self._rate_limits = {}
        
    async def handle_ratelimit(self):
        now = time.time()
        # Only wait if we hit a rate limit in the last 0.5 seconds
        if now - self.last_send < 0.5:
            await asyncio.sleep(self.reset_after)
        self.last_send = now

rate_handler = RateLimitHandler()

# Modify dm_all function
async def dm_all(server_id, message_content, active_only=True, delay=0.02, batch_size=35):
    try:
        guild = bot.get_guild(int(server_id))
        if not guild:
            print(Colorate.Color(Colors.red, "[-] Sunucu bulunamadı."))
            return 0, 0

        start_time_total = time.time()
        
        # Get members with proper status filtering
        if active_only:
            valid_members = [
                member for member in guild.members 
                if not member.bot and str(member.status) in ['online', 'idle', 'dnd']
            ]
        else:
            valid_members = [member for member in guild.members if not member.bot]
        
        total_members = len(valid_members)
        if total_members == 0:
            print(Colorate.Color(Colors.yellow, "[!] Gönderilecek üye bulunamadı."))
            return 0, 0

        members_sent = 0
        members_fail = 0
        tasks = []
        progress = tqdm(total=total_members, desc="DM Gönderiliyor", unit="üye")

        async def send_dm_task(member):
            try:
                async with rate_handler.semaphore:
                    if isinstance(message_content, dict):
                        final_message = message_content.copy()
                        mention = f"<@{member.id}>"
                        
                        # Optimize message construction
                        if "content" in final_message:
                            final_message["content"] = f"{mention} {final_message['content']}"
                        if "embed" in final_message:
                            embed = final_message["embed"]
                            embed.description = f"{mention} {(embed.description or '')}"
                        
                        await member.send(**final_message)
                    else:
                        # Fast path for simple messages
                        await member.send(content=f"<@{member.id}> {message_content}")
                    return True
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limit
                    await asyncio.sleep(float(e.retry_after))
                    try:
                        await member.send(**final_message)
                        return True
                    except:
                        pass
                return False
            except Exception as e:
                return False
            finally:
                progress.update(1)

        # Process in larger chunks with minimal delays
        chunks = [valid_members[i:i + batch_size] for i in range(0, len(valid_members), batch_size)]
        for chunk in chunks:
            tasks = [send_dm_task(member) for member in chunk]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            members_sent += sum(1 for r in results if r is True)
            members_fail += sum(1 for r in results if r is False)
            
            if len(chunks) > 1:  # Only sleep between chunks if there are multiple
                await asyncio.sleep(delay)

        progress.close()
        end_time_total = time.time()
        elapsed = end_time_total - start_time_total
        
        print(Colorate.Color(Colors.green, f"\n✅ İşlem tamamlandı!"))
        print(Colorate.Color(Colors.blue, f"📊 İstatistikler:"))
        print(Colorate.Color(Colors.blue, f"• Başarılı: {members_sent}"))
        print(Colorate.Color(Colors.blue, f"• Başarısız: {members_fail}"))
        print(Colorate.Color(Colors.blue, f"• Süre: {elapsed:.2f} saniye"))
        print(Colorate.Color(Colors.blue, f"• Ortalama: {elapsed/total_members:.2f} saniye/mesaj"))
        
        return members_sent, members_fail

    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] Hata: {e}"))
        return 0, 0

def optimize_event_loop():
    loop = asyncio.get_event_loop()
    
    if sys.platform == 'win32':
        if hasattr(loop, 'slow_callback_duration'):
            loop.slow_callback_duration = 0.01
    return loop

TURKISH_BANNER = """
·▄▄▄▄  • ▌ ▄ ·.     • ▌ ▄ ·.  ▄▄▄·  ▐ ▄  ▄▄▄·  ▄▄ • ▄▄▄ .▄▄▄  
██▪ ██ ·██ ▐███▪    ·██ ▐███▪▐█ ▀█ •█▌▐█▐█ ▀█ ▐█ ▀ ▪▀▄.▀·▀▄ █·
▐█· ▐█▌▐█ ▌▐▌▐█·    ▐█ ▌▐▌▐█·▄█▀▀█ ▐█▐▐▌▄█▀▀█ ▄█ ▀█▄▐▀▀▪▄▐▀▀▄ 
██. ██ ██ ██▌▐█▌    ██ ██▌▐█▌▐█ ▪▐▌██▐█▌▐█ ▪▐▌▐█▄▪▐█▐█▄▄▌▐█•█▌
▀▀▀▀▀• ▀▀  █▪▀▀▀    ▀▀  █▪▀▀▀ ▀  ▀ ▀▀ █▪ ▀  ▀ ·▀▀▀▀  ▀▀▀ .▀  ▀

                    Krex Tarafından Geliştirildi
"""

class EmbedSettings:
    def __init__(self):
        self.settings = {}
        self.version = VERSION
    
    def save_preset(self, user_id: str, name: str, settings: dict):
        if user_id not in self.settings:
            self.settings[user_id] = {}
        self.settings[user_id][name] = settings
        self._save_to_file()
    
    def get_preset(self, user_id: str, name: str) -> Optional[dict]:
        return self.settings.get(user_id, {}).get(name)
    
    def delete_preset(self, user_id: str, name: str) -> bool:
        if user_id in self.settings and name in self.settings[user_id]:
            del self.settings[user_id][name]
            self._save_to_file()
            return True
        return False
    
    def get_user_presets(self, user_id: str) -> dict:
        return self.settings.get(user_id, {})
    
    def _save_to_file(self):
        with open("embed_presets.json", "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)
    
    def _load_from_file(self):
        try:
            with open("embed_presets.json", "r", encoding="utf-8") as f:
                self.settings = json.load(f)
        except:
            self.settings = {}

    def create_template(self, name: str) -> dict:
        return {
            "title": "Template Title",
            "description": "Template Description",
            "color": 0x00ff00,
            "footer": {"text": "Created with DM Manager"},
            "thumbnail": {"url": ""},
            "image": {"url": ""},
            "author": {"name": "", "icon_url": ""},
            "fields": []
        }
    
    def duplicate_preset(self, user_id: str, source: str, target: str) -> bool:
        if preset := self.get_preset(user_id, source):
            self.save_preset(user_id, target, preset.copy())
            return True
        return False

embed_manager = EmbedSettings()
embed_manager._load_from_file()

os.system('cls' if os.name == 'nt' else 'clear')
print(Colorate.Color(Colors.purple, """
·▄▄▄▄  • ▌ ▄ ·.     • ▌ ▄ ·.  ▄▄▄·  ▐ ▄  ▄▄▄·  ▄▄ • ▄▄▄ .▄▄▄  
██▪ ██ ·██ ▐███▪    ·██ ▐███▪▐█ ▀█ •█▌▐█▐█ ▀█ ▐█ ▀ ▪▀▄.▀·▀▄ █·
▐█· ▐█▌▐█ ▌▐▌▐█·    ▐█ ▌▐▌▐█·▄█▀▀█ ▐█▐▐▌▄█▀▀█ ▄█ ▀█▄▐▀▀▪▄▐▀▀▄ 
██. ██ ██ ██▌▐█▌    ██ ██▌▐█▌▐█ ▪▐▌██▐█▌▐█ ▪▐▌▐█▄▪▐█▐█▄▄▌▐█•█▌
▀▀▀▀▀• ▀▀  █▪▀▀▀    ▀▀  █▪▀▀▀ ▀  ▀ ▀▀ █▪ ▀  ▀ ·▀▀▀▀  ▀▀▀ .▀  ▀

                    Developed by Krex
"""))

print(Colorate.Color(Colors.green, "\n✅ DM Manager başlatılıyor..."))

saved_settings = load_bot_settings()
if saved_settings:
    print(Colorate.Color(Colors.purple, "\nKaydedilmiş bot ayarları bulundu:"))
    print(Colorate.Color(Colors.purple, f"Bot Token: {'*' * (len(saved_settings['bot_token']) - 5) + saved_settings['bot_token'][-5:]}"))
    print(Colorate.Color(Colors.purple, f"Owner ID: {saved_settings['owner_id']}"))
    print(Colorate.Color(Colors.purple, f"İkinci Owner ID: {saved_settings.get('second_owner_id', '0')}"))
    
    use_saved = input(Colorate.Color(Colors.purple, "Kaydedilmiş bot ayarlarını kullan? (E/h): ")).lower() != 'h'
    
    if use_saved:
        bot_token = saved_settings['bot_token']
        owner_id = saved_settings['owner_id']
        second_owner_id = saved_settings.get('second_owner_id', '0')
    else:
        bot_token = input(Colorate.Color(Colors.purple, "Bot tokeninizi girin: "))
        owner_id = input(Colorate.Color(Colors.purple, "Botun sahibi (owner) ID'sini girin: "))
        second_owner_id = input(Colorate.Color(Colors.purple, "İkinci Owner ID'si (isteğe bağlı): ") or "0")
        
        save_settings = input(Colorate.Color(Colors.purple, "Bu bot ayarlarını kaydetmek ister misiniz? (E/h): ")).lower() != 'h'
        if save_settings:
            save_bot_settings(bot_token, owner_id, second_owner_id)
            print(Colorate.Color(Colors.green, "✅ Bot ayarları kaydedildi!"))
else:
    bot_token = input(Colorate.Color(Colors.purple, "Bot tokeninizi girin: "))
    owner_id = input(Colorate.Color(Colors.purple, "Botun sahibi (owner) ID'sini girin: "))
    second_owner_id = input(Colorate.Color(Colors.purple, "İkinci Owner ID'si (isteğe bağlı): ") or "0")
    
    save_settings = input(Colorate.Color(Colors.purple, "Bu bot ayarlarını kaydetmek ister misiniz? (E/h): ")).lower() != 'h'
    if save_settings:
        save_bot_settings(bot_token, owner_id, second_owner_id)
        print(Colorate.Color(Colors.green, "✅ Bot ayarları kaydedildi!"))

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='/', intents=intents)

class EmbedMenuView(View):
    def __init__(self, owner_id):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @discord.ui.button(label="Embed Oluştur", style=discord.ButtonStyle.blurple, emoji="✨")
    async def embed_olustur(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message("Bu butonu kullanma izniniz yok!", ephemeral=True)
            return

        modal = EmbedOlusturModal()
        await interaction.response.send_modal(modal)

class EmbedOlusturModal(discord.ui.Modal, title="Embed Oluştur"):
    onayar_adi = discord.ui.TextInput(
        label="Önayar Adı",
        placeholder="örn: duyuru1",
        required=True,
        max_length=50
    )
    baslik = discord.ui.TextInput(
        label="Başlık",
        placeholder="Embed başlığı",
        required=True,
        max_length=256
    )
    aciklama = discord.ui.TextInput(
        label="Açıklama",
        placeholder="Embed açıklaması",
        required=True,
        style=discord.TextStyle.paragraph,
        max_length=4000
    )
    renk = discord.ui.TextInput(
        label="Renk (HEX)",
        placeholder="#ff0000",
        required=False,
        max_length=7
    )
    resim_url = discord.ui.TextInput(
        label="Resim URL",
        placeholder="https://example.com/image.png",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            ayarlar = {
                "title": self.baslik.value,
                "description": self.aciklama.value,
                "color": int(self.renk.value.replace("#", ""), 16) if self.renk.value else 0x00ff00
            }
            
            if self.resim_url.value:
                ayarlar["image"] = {"url": self.resim_url.value}

            embed_manager.save_preset(str(interaction.user.id), self.onayar_adi.value, ayarlar)
            
            onizleme = discord.Embed.from_dict(ayarlar)
            await interaction.response.send_message(
                f"✅ `{self.onayar_adi.value}` önayarı kaydedildi!\nÖnizleme:",
                embed=onizleme,
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Hata: {str(e)}", ephemeral=True)

@bot.tree.command(name="dmduyuru", description="Sunucudaki üyelere DM gönder")
async def dm_duyuru_slash(
    interaction: discord.Interaction,
    server_id: str,
    message: str = None,
    image: discord.Attachment = None,
    embed_preset: str = None,
    target: str = "aktif",
    delay: int = 4,  # Changed from float to int
    batch_size: int = 35
):
    try:
        await interaction.response.defer(ephemeral=True)

        # Convert delay to float after receiving it as int
        delay = float(delay) / 10  # Convert to seconds (e.g. 4 becomes 0.4)

        if str(interaction.user.id) != owner_id and str(interaction.user.id) != second_owner_id:
            await interaction.followup.send("Bu komutu kullanma izniniz yok.", ephemeral=True)
            return

        if not server_id:
            await interaction.followup.send("Sunucu ID'si belirtmelisiniz!", ephemeral=True)
            return

        try:
            server_id = int(server_id)
        except ValueError:
            await interaction.followup.send("Geçersiz sunucu ID'si!", ephemeral=True)
            return

        final_message = {}
        
        if message:
            final_message["content"] = message
            
        if embed_preset:
            preset = embed_manager.get_preset(str(interaction.user.id), embed_preset)
            if preset:
                embed = discord.Embed.from_dict(preset)
                final_message["embed"] = embed
            else:
                await interaction.followup.send(f"'{embed_preset}' isimli embed önayarı bulunamadı!", ephemeral=True)
                return
                
        if image:
            if "embed" not in final_message:
                final_message["embed"] = discord.Embed()
            final_message["embed"].set_image(url=image.url)

        if not final_message:
            await interaction.followup.send("En az bir mesaj içeriği belirtmelisiniz! (mesaj, embed veya resim)", ephemeral=True)
            return

        active_only = target.lower() != "tüm"
        status_msg = await interaction.followup.send(
            f"🚀 Mesajlar gönderiliyor... ({target} kullanıcılara)\n"
            f"Gecikme: {delay}s, Toplu Gönderim: {batch_size}", 
            ephemeral=True
        )
        
        sent, failed = await dm_all(
            server_id, 
            final_message, 
            active_only=active_only,
            delay=delay,
            batch_size=batch_size
        )
        
        await status_msg.edit(
            content=f"✅ Tamamlandı!\n"
                   f"✓ Başarılı: {sent}\n"
                   f"✗ Başarısız: {failed}\n"
                   f"🎯 Hedef: {target} kullanıcılar"
        )
        
    except Exception as e:
        await interaction.followup.send(f"❌ Hata oluştu: {str(e)}", ephemeral=True)

@bot.tree.command(name="embedayarla", description="Özel embed önayarı oluştur")
async def embed_ayarla_slash(
    interaction: discord.Interaction,
    onayar_adi: str,
    baslik: str = None,
    aciklama: str = None,
    renk: str = None,
    kucuk_resim: str = None,
    buyuk_resim: str = None,
    yazar_adi: str = None,
    yazar_resmi: str = None,
    alanlar: str = None
):
    # Check if user is owner
    if str(interaction.user.id) != owner_id and str(interaction.user.id) != second_owner_id:
        await interaction.response.send_message("Bu komutu kullanma izniniz yok.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    try:
        if not any([baslik, aciklama, renk, kucuk_resim, buyuk_resim, yazar_adi, alanlar]):
            embed = discord.Embed(
                title="Embed Ayarları Kullanımı",
                description="En az bir ayar belirtmelisiniz:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Parametreler",
                value=(
                    "• onayar_adi: Önayar ismi\n"
                    "• baslik: Başlık\n"
                    "• aciklama: Açıklama\n"
                    "• renk: Renk (Hex: #ff0000)\n"
                    "• kucuk_resim: Küçük resim URL\n"
                    "• buyuk_resim: Büyük resim URL\n"
                    "• yazar_adi: Yazar ismi\n"
                    "• yazar_resmi: Yazar icon URL\n"
                    "• alanlar: Alan başlıkları ve açıklamaları\n"
                    "   Format: 'başlık1|açıklama1,başlık2|açıklama2'"
                ),
                inline=False
            )
            
            view = EmbedMenuView(owner_id=str(interaction.user.id))
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            return

        ayarlar = {}
        
        if baslik: ayarlar["title"] = baslik
        if aciklama: ayarlar["description"] = aciklama
        if renk: 
            try:
                ayarlar["color"] = int(renk.replace("#", ""), 16)
            except ValueError:
                await interaction.followup.send("❌ Geçersiz renk kodu! Örnek: #ff0000", ephemeral=True)
                return

        if kucuk_resim: ayarlar["thumbnail"] = {"url": kucuk_resim}
        if buyuk_resim: ayarlar["image"] = {"url": buyuk_resim}
        if yazar_adi:
            ayarlar["author"] = {
                "name": yazar_adi,
                "icon_url": yazar_resmi if yazar_resmi else None
            }
        if alanlar:
            ayarlar["fields"] = []
            try:
                for alan in alanlar.split(","):
                    baslik, aciklama = alan.split("|")
                    ayarlar["fields"].append({"name": baslik.strip(), "value": aciklama.strip()})
            except ValueError:
                await interaction.followup.send("❌ Geçersiz alan formatı! Örnek: başlık1|açıklama1,başlık2|açıklama2", ephemeral=True)
                return

        embed_manager.save_preset(str(interaction.user.id), onayar_adi, ayarlar)
        
        onizleme = discord.Embed.from_dict(ayarlar)
        await interaction.followup.send(
            f"✅ `{onayar_adi}` önayarı kaydedildi!\nÖnizleme:",
            embed=onizleme,
            ephemeral=True
        )

    except Exception as e:
        if not interaction.response.is_done():
            await interaction.response.send_message(f"❌ Hata oluştu: {str(e)}", ephemeral=True)
        else:
            try:
                await interaction.followup.send(f"❌ Hata oluştu: {str(e)}", ephemeral=True)
            except:
                print(f"Kritik hata: {str(e)}")

@bot.tree.command(name="embedsil", description="Kayıtlı embed ayarını sil")
async def embed_sil_slash(interaction: discord.Interaction, preset_name: str):
    try:
        if embed_manager.delete_preset(str(interaction.user.id), preset_name):
            await interaction.followup.send(f"✅ `{preset_name}` isimli embed ayarları silindi!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ `{preset_name}` isimli embed ayarı bulunamadı!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Hata oluştu: {str(e)}", ephemeral=True)

@bot.tree.command(name="embedlerim", description="Kayıtlı embed ayarlarını listele")
async def embedlerim_slash(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        presets = embed_manager.get_user_presets(str(interaction.user.id))
        if not presets:
            await interaction.followup.send("Kayıtlı embed ayarınız bulunmuyor!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Kayıtlı Embed Ayarlarınız",
            color=discord.Color.blue()
        )

        for name, settings in presets.items():
            value = f"Başlık: {settings.get('title', 'Yok')}\n"
            value += f"Açıklama: {settings.get('description', 'Yok')[:100]}...\n"
            value += f"Alan Sayısı: {len(settings.get('fields', []))}"
            
            embed.add_field(
                name=f"📌 {name}",
                value=value,
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)
        
    except Exception as e:
        try:
            await interaction.followup.send(f"❌ Hata oluştu: {str(e)}", ephemeral=True)
        except:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Bir hata oluştu.", ephemeral=True)

@bot.tree.command(name="yardım", description="Bot komutları ve kullanım yardımı")
async def yardim(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        embed = discord.Embed(
            title="DM Manager - Komut Yardımı",
            description="Bot komutları ve kullanım rehberi:",
            color=discord.Color.blue()
        )
        
        view = CommandHelpView()
        
        embed.add_field(
            name="📬 DM Komutları",
            value=(
                "• `/dmduyuru` - DM mesajı gönderme\n"
                "• `/embedayarla` - Embed oluşturma\n"
                "• `/embedsil` - Embed silme\n"
                "• `/embedlerim` - Embedleri listeleme"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚡ Hızlı Kullanım",
            value=(
                "Aşağıdaki menüden istediğiniz işlemi seçebilir\n"
                "veya butonları kullanarak hızlıca işlem yapabilirsiniz."
            ),
            inline=False
        )
        
        embed.set_footer(text=f"DM Manager v{VERSION} | Krex")
        
        await interaction.followup.send(embed=embed, view=view)
    except Exception as e:
        try:
            await interaction.followup.send(f"❌ Hata oluştu: {str(e)}", ephemeral=True)
        except:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Bir hata oluştu.", ephemeral=True)

class CommandHelpView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        komut_sec = Select(
            placeholder="Komut seçin",
            options=[
                discord.SelectOption(
                    label="DM Duyuru",
                    description="Üyelere DM gönderme",
                    value="dmduyuru",
                    emoji="📬"
                ),
                discord.SelectOption(
                    label="Embed Ayarları",
                    description="Embed yönetimi",
                    value="embed",
                    emoji="🎨"
                ),
                discord.SelectOption(
                    label="Hızlı Ayarlar",
                    description="Hızlı komut kullanımı",
                    value="quick",
                    emoji="⚡"
                )
            ]
        )
        komut_sec.callback = self.select_callback
        self.add_item(komut_sec)
        
        # Hızlı işlem butonları
        self.add_item(Button(
            label="Aktif Üyelere DM",
            custom_id="dm_aktif",
            style=discord.ButtonStyle.green,
            emoji="🟢"
        ))
        self.add_item(Button(
            label="Tüm Üyelere DM",
            custom_id="dm_tum",
            style=discord.ButtonStyle.red,
            emoji="📢"
        ))
        self.add_item(Button(
            label="Embed Oluştur",
            custom_id="embed_olustur",
            style=discord.ButtonStyle.blurple,
            emoji="✨"
        ))

    async def button_callback(self, interaction: discord.Interaction):
        if interaction.custom_id == "embed_olustur":
            modal = EmbedOlusturModal()
            await interaction.response.send_modal(modal)
        elif interaction.custom_id in ["dm_aktif", "dm_tum"]:
            # Implement DM sending modal here
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send("Bu özellik yakında eklenecek!", ephemeral=True)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.data["values"][0] == "dmduyuru":
            embed = discord.Embed(
                title="DM Duyuru Komut Yardımı",
                description="Kullanıcılara DM gönderme komutları:",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Basit Kullanım",
                value="```/dmduyuru [sunucu_id] mesaj: Merhaba!```",
                inline=False
            )
            embed.add_field(
                name="Gelişmiş Kullanım",
                value=(
                    "• Aktif kullanıcılara:\n"
                    "```/dmduyuru [sunucu_id] hedef:aktif mesaj:Merhaba!```\n"
                    "• Resimli mesaj:\n"
                    "```/dmduyuru [sunucu_id] mesaj:Merhaba! [resim ekleyin]```\n"
                    "• Embed ile:\n"
                    "```/dmduyuru [sunucu_id] embed_preset:önayar_adı```"
                ),
                inline=False
            )
        elif interaction.data["values"][0] == "embed":
            embed = discord.Embed(
                title="Embed Komut Yardımı",
                description="Embed oluşturma ve yönetme komutları:",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Embed Oluşturma",
                value="```/embedayarla önayar_adı başlık:Test açıklama:Açıklama renk:#ff0000```",
                inline=False
            )
            embed.add_field(
                name="Embed Yönetimi",
                value=(
                    "• Embed silme:\n"
                    "```/embedsil [önayar_adı]```\n"
                    "• Embedleri listele:\n"
                    "```/embedlerim```"
                ),
                inline=False
            )
        else:
            embed = discord.Embed(
                title="Hızlı Komut Kullanımı",
                description="Butonları kullanarak hızlıca işlem yapabilirsiniz:",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="🟢 Aktif Kullanıcılara DM",
                value="Online, AFK veya DND durumundaki kullanıcılara mesaj gönderir",
                inline=False
            )
            embed.add_field(
                name="🔴 Tüm Kullanıcılara DM",
                value="Sunucudaki tüm kullanıcılara mesaj gönderir",
                inline=False
            )
            embed.add_field(
                name="🔵 Embed Oluştur",
                value="Hızlı embed oluşturma menüsünü açar",
                inline=False
            )
        
        embed.set_footer(text=f"DM Manager v{VERSION} | Krex")
        await interaction.response.edit_message(embed=embed, view=self)

async def send_help_message(user_id):
    try:
        user = await bot.fetch_user(int(user_id))
        if user:
            embed = discord.Embed(
                title="DM Manager - Komut Modu Aktif",
                description="Bot komut modunda çalışmaya başladı.\nKomut yardımı için aşağıdaki menüyü kullanabilirsiniz:",
                color=discord.Color.blue()
            )
            
            view = CommandHelpView()
            await user.send(embed=embed, view=view)
            return True
    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] Yardım mesajı gönderilemedi: {e}"))
        return False

@bot.event
async def on_ready():
    print(Colorate.Color(Colors.purple, f'[+] {bot.user.name} çevrimiçi! | Developed by Krex'))
    try:
        synced = await bot.tree.sync()
        print(Colorate.Color(Colors.green, f"Slash komutları senkronize edildi: {len(synced)} komut"))
    except Exception as e:
        print(Colorate.Color(Colors.red, f"Slash komut senkronizasyonu hatası: {e}"))
    
    optimize_event_loop()
    
    if not has_sent_help_message():
        owner_ids = [owner_id]
        if second_owner_id and second_owner_id != "0":
            owner_ids.append(second_owner_id)
        
        success_count = 0
        for user_id in owner_ids:
            if await send_help_message(user_id):
                success_count += 1
        
        if success_count > 0:
            mark_help_sent()
    
    dm_task = None
    
    while True:
        if dm_task is None or dm_task.done():
            os.system('cls' if os.name == 'nt' else 'clear')
            choice = input(Colorate.Color(Colors.purple, f"""{TURKISH_BANNER}
                    1. DM Duyuru Gönder
                    2. Embed DM Gönder
                    3. Komut Modunu Aç
                    4. Çıkış
Seçim: """))
            
            if choice == '1':
                saved_server_id = saved_settings.get('default_server_id', '') if saved_settings else ''
                if saved_server_id:
                    print(Colorate.Color(Colors.purple, f"Kaydedilmiş sunucu ID: {saved_server_id}"))
                    use_saved_server = input(Colorate.Color(Colors.purple, "Kaydedilmiş sunucu ID'yi kullan? (E/h): ")).lower() != 'h'
                    server_id = saved_server_id if use_saved_server else input(Colorate.Color(Colors.purple, "Sunucu ID'sini girin: "))
                else:
                    server_id = input(Colorate.Color(Colors.purple, "Sunucu ID'sini girin: "))
                
                if server_id != saved_server_id and saved_settings:
                    save_server = input(Colorate.Color(Colors.purple, "Bu sunucu ID'yi varsayılan olarak kaydetmek ister misiniz? (E/h): ")).lower() != 'h'
                    if save_server:
                        saved_settings['default_server_id'] = server_id
                        save_bot_settings(
                            saved_settings['bot_token'], 
                            saved_settings['owner_id'], 
                            saved_settings.get('second_owner_id', '0')
                        )
                        print(Colorate.Color(Colors.green, "✅ Varsayılan sunucu ID kaydedildi!"))
                
                filter_choice = input(Colorate.Color(Colors.purple, "Kimlere mesaj gönderilsin? (1: Sadece aktif kullanıcılar, 2: Tüm kullanıcılar): "))
                active_only = filter_choice != "2"
                
                message_content = input(Colorate.Color(Colors.purple, "Mesaj içeriğini girin: "))
                
                print(Colorate.Color(Colors.purple, "Mesajlar gönderiliyor, lütfen bekleyin..."))
                dm_task = asyncio.create_task(dm_all(server_id, message_content, active_only))
                
                await asyncio.sleep(1)
                
            elif choice == '2':
                server_id = input(Colorate.Color(Colors.purple, "Sunucu ID'sini girin: "))
                print(Colorate.Color(Colors.purple, "\nEmbed Ayarları:"))
                title = input("Başlık: ")
                description = input("Açıklama: ")
                color = input("Renk (Hex, örn: #ff0000): ")
                footer = input("Alt Yazı: ")
                image_url = input("Resim URL (isteğe bağlı): ")
                
                embed = {
                    "title": title,
                    "description": description,
                    "color": int(color.replace("#", ""), 16) if color else 0x000000
                }
                
                if footer:
                    embed["footer"] = {"text": footer}
                if image_url:
                    embed["image"] = {"url": image_url}
                
                final_message = {"embed": discord.Embed.from_dict(embed)}
                
                print(Colorate.Color(Colors.purple, "Embed mesajı gönderiliyor..."))
                dm_task = asyncio.create_task(dm_all(server_id, final_message, active_only=True))

            elif choice == '3':
                print(Colorate.Color(Colors.green, "Komut kullanımı aktif edilmiştir!"))
                
                if not has_sent_help_message():
                    embed = discord.Embed(
                        title="DM Manager - Komut Modu Aktif",
                        description="Bot komut modunda çalışmaya başladı. Aşağıdaki komutları kullanabilirsiniz:",
                        color=discord.Color.blue()
                    )
                    
                    embed.add_field(
                        name="DM Duyuru Komutu",
                        value="Sunucunuzdaki üyelere DM mesajı göndermek için:",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Kullanım", 
                        value="/dmduyuru [server_id] [mesaj]",
                        inline=False
                    )
                    
                    embed.add_field(
                        name="Örnekler", 
                        value="- Sadece aktif kullanıcılara:\n  `/dmduyuru 123456789 aktif: Merhaba!`\n\n- Tüm kullanıcılara:\n  `/dmduyuru 123456789 tüm: Merhaba!`",
                        inline=False
                    )
                    
                    embed.set_footer(text="DM Manager | Developed by Krex")
                    
                    owner_ids = [owner_id]
                    if second_owner_id and second_owner_id != "0":
                        owner_ids.append(second_owner_id)
                    
                    success_count = 0
                    for user_id in owner_ids:
                        try:
                            user = await bot.fetch_user(int(user_id))
                            if user:
                                await user.send(embed=embed)
                                print(Colorate.Color(Colors.green, f"[+] Komut bilgisi {user.name} kullanıcısına gönderildi"))
                                success_count += 1
                                await asyncio.sleep(0.5)  
                        except Exception as e:
                            print(Colorate.Color(Colors.red, f"[-] Komut bilgisi ID:{user_id} kullanıcısına gönderilemedi: {e}"))
                    
                    if success_count > 0:
                        mark_help_sent()
                    else:
                        print(Colorate.Color(Colors.yellow, "[!] Hiçbir kullanıcıya komut bilgisi gönderilemedi"))
                else:
                    print(Colorate.Color(Colors.blue, "[*] Komut bilgisi daha önce gönderildi, tekrar gönderilmiyor."))
                
                break
            
            elif choice == '4':
                print(Colorate.Color(Colors.purple, "Bot kapanıyor..."))
                await bot.close()  
                break
            
            else:
                print(Colorate.Color(Colors.red, "Geçersiz seçim. Lütfen geçerli bir seçenek girin."))
                await asyncio.sleep(2)  
        
        if dm_task is not None and dm_task.done():
            try:
                sent, failed = dm_task.result()
                print(Colorate.Color(Colors.green, f"İşlem tamamlandı! {sent} mesaj gönderildi, {failed} mesaj gönderilemedi."))
                input(Colorate.Color(Colors.purple, "Devam etmek için Enter tuşuna basın..."))
                dm_task = None
            except Exception as e:
                print(Colorate.Color(Colors.red, f"[-] DM görevi hatası: {e}"))
                dm_task = None

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.get_event_loop()
        loop.run_until_complete(bot.start(bot_token))
    except KeyboardInterrupt:
        loop.run_until_complete(bot.close())
    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] Bot başlatma hatası: {e}"))
        input(Colorate.Color(Colors.purple, "Devam etmek için Enter tuşuna basın..."))
        sys.exit(1)
    finally:
        loop.close()
