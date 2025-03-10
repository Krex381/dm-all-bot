import discord
import asyncio
import time
import json
import os
import sys
from discord.ext import commands
from pystyle import Colors, Colorate
from datetime import datetime

# Check if running as exe or script
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

# Set working directory to application path
os.chdir(application_path)

def load_bot_settings():
    """Load saved bot settings from botinfo.dat"""
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
    """Save bot settings to botinfo.dat"""
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
    """Ultra-optimized DM sending function for maximum performance"""
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
    """DM sending function with rate limit handling"""
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

async def dm_all(server_id, message_content, active_only=True):
    try:
        guild = bot.get_guild(int(server_id))
        if guild:
            start_time_total = time.time()  
            
            if active_only:
                valid_members = [
                    member for member in guild.members 
                    if not member.bot and member.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]
                ]
                filter_mode = "ACTIVE_ONLY"
            else:
                valid_members = [member for member in guild.members if not member.bot]
                filter_mode = "ALL_USERS"
            
            total_active = len([m for m in guild.members if not m.bot and m.status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]])
            total_offline = len([m for m in guild.members if not m.bot and m.status == discord.Status.offline])
            total_all = total_active + total_offline
            
            if active_only:
                print(Colorate.Color(Colors.blue, f"[*] Filtreleme: {total_active} aktif kullanıcı bulundu, {total_offline} çevrimdışı kullanıcı atlandı"))
            else:
                print(Colorate.Color(Colors.blue, f"[*] Filtreleme: Tüm kullanıcılara mesaj gönderiliyor ({total_all} kullanıcı)"))
            
            message_times = []
            
            async def tracked_send_dm(member, message_content):
                start_time = time.time()
                result = await send_dm_with_rate_limit(member, message_content)
                if result:
                    message_times.append(time.time() - start_time)
                return result
            
            members_sent = 0
            members_fail = 0
            batch_size = 35  
            
            for i in range(0, len(valid_members), batch_size):
                batch = valid_members[i:i+batch_size]
                
                tasks = [tracked_send_dm(member, message_content) for member in batch]
                results = await asyncio.gather(*tasks, return_exceptions=False)
                
                batch_sent = sum(1 for result in results if result)
                batch_fail = len(results) - batch_sent
                
                members_sent += batch_sent
                members_fail += batch_fail
                
                if i + batch_size < len(valid_members):
                    await asyncio.sleep(0.5)  
                
                if len(valid_members) > 10:
                    progress = int(((i + batch_size) / len(valid_members)) * 100)
                    print(Colorate.Color(Colors.blue, f"[*] İlerleme: %{min(progress, 100)} ({min(i + batch_size, len(valid_members))}/{len(valid_members)})"))
            
            end_time_total = time.time()
            elapsed = end_time_total - start_time_total
            
            await asyncio.sleep(0.5)
            
            total_message_time = sum(message_times) if message_times else 0
            
            filter_status = "aktif kullanıcılara" if active_only else "tüm kullanıcılara"
            print(Colorate.Color(Colors.purple, f"[!] Komut Kullanıldı: DM Tüm - {members_sent} mesaj gönderildi, {members_fail} mesaj gönderilemedi - Toplam Süre: {elapsed:.2f} saniye ({filter_status})"))
            
            if active_only:
                print(Colorate.Color(Colors.purple, f"[!] Aktif Kullanıcı Filtreleme: {total_active} aktif, {total_offline} çevrimdışı"))
            else:
                print(Colorate.Color(Colors.purple, f"[!] Tüm Kullanıcılar: {total_all} ({total_active} aktif, {total_offline} çevrimdışı)"))
            
            return members_sent, members_fail
        else:
            print(Colorate.Color(Colors.red, "[-] Sunucu bulunamadı."))
            return 0, 0
    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] Hata: {e}"))
        return 0, 0

def optimize_event_loop():
    loop = asyncio.get_event_loop()
    
    if sys.platform == 'win32':
        if hasattr(loop, 'slow_callback_duration'):
            loop.slow_callback_duration = 0.01
    return loop

# Show application header
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

# Load or get bot settings
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

@bot.command(name="dmduyuru", help="Belirtilen sunucudaki tüm üyelere DM gönderir.")
async def dm_duyuru(ctx, server_id: str = None, *, message: str = None):
    """
    DM duyuru komutu
    
    Kullanım:
    /dmduyuru [server_id] [mesaj]
    
    Örnek:
    /dmduyuru 123456789 Merhaba, bu bir test mesajıdır!
    """
    if str(ctx.author.id) != owner_id and str(ctx.author.id) != second_owner_id:
        await ctx.send("Bu komutu kullanma izniniz yok.")
        return
    
    if not server_id or not message:
        embed = discord.Embed(
            title="DM Duyuru - Eksik Parametreler",
            description="Aşağıdaki parametreleri sağlamanız gerekiyor:",
            color=discord.Color.red()
        )
        embed.add_field(name="Kullanım", value="/dmduyuru [server_id] [mesaj]", inline=False)
        embed.add_field(name="Örnek", value="/dmduyuru 123456789 Merhaba, bu bir test mesajıdır!", inline=False)
        embed.set_footer(text="Developed by Krex")
        await ctx.send(embed=embed)
        return

    try:
        int(server_id)  
    except ValueError:
        await ctx.send(f"Hata: Sunucu ID'si bir sayı olmalıdır, '{server_id}' geçerli değil.")
        return

    filter_option = "aktif"  
    if "tüm:" in message.lower():
        filter_option = "tüm"
        message = message.replace("tüm:", "", 1).strip()
    elif "aktif:" in message.lower():
        filter_option = "aktif"
        message = message.replace("aktif:", "", 1).strip()
    
    active_only = filter_option.lower() != "tüm"
    filter_text = "Sadece aktif kullanıcılar" if active_only else "Tüm kullanıcılar"
    
    status_msg = await ctx.send(f"🚀 Mesajlar gönderiliyor... ({filter_text})")
    
    sent, failed = await dm_all(server_id, message, active_only)
    
    await status_msg.edit(content=f"✅ Tamamlandı! {sent} gönderildi, {failed} başarısız ({filter_text})")

def has_sent_help_message():
    """Check if help message has been sent before"""
    try:
        return os.path.exists("help_sent.dat")
    except:
        return False

def mark_help_sent():
    """Mark that help message has been sent"""
    try:
        with open("help_sent.dat", "w") as f:
            f.write("1")
    except Exception as e:
        print(Colorate.Color(Colors.yellow, f"Uyarı: Yardım gönderim durumu kaydedilemedi: {e}"))

@bot.event
async def on_ready():
    print(Colorate.Color(Colors.purple, f'[+] {bot.user.name} çevrimiçi! | Developed by Krex'))
    
    optimize_event_loop()
    
    dm_task = None
    
    while True:
        if dm_task is None or dm_task.done():
            os.system('cls' if os.name == 'nt' else 'clear')
            choice = input(Colorate.Color(Colors.purple, """
·▄▄▄▄  • ▌ ▄ ·.     • ▌ ▄ ·.  ▄▄▄·  ▐ ▄  ▄▄▄·  ▄▄ • ▄▄▄ .▄▄▄  
██▪ ██ ·██ ▐███▪    ·██ ▐███▪▐█ ▀█ •█▌▐█▐█ ▀█ ▐█ ▀ ▪▀▄.▀·▀▄ █·
▐█· ▐█▌▐█ ▌▐▌▐█·    ▐█ ▌▐▌▐█·▄█▀▀█ ▐█▐▐▌▄█▀▀█ ▄█ ▀█▄▐▀▀▪▄▐▀▀▄ 
██. ██ ██ ██▌▐█▌    ██ ██▌▐█▌▐█ ▪▐▌██▐█▌▐█ ▪▐▌▐█▄▪▐█▐█▄▄▌▐█•█▌
▀▀▀▀▀• ▀▀  █▪▀▀▀    ▀▀  █▪▀▀▀ ▀  ▀ ▀▀ █▪ ▀  ▀ ·▀▀▀▀  ▀▀▀ .▀  ▀

                        Developed by Krex

                    1. DM'ye Duyuru Yap
                    2. Komut Kullanımı Aktif Et
                    3. Çıkış
Seçim : """))
            
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
            
            elif choice == '3':
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
                print(Colorate.Color(Colors.red, f"DM gönderme işlemi hata ile sonuçlandı: {e}"))
                input(Colorate.Color(Colors.purple, "Devam etmek için Enter tuşuna basın..."))
                dm_task = None
        
        await asyncio.sleep(0.1)

@bot.event
async def on_command_error(ctx, error):
    print(Colorate.Color(Colors.red, f"[-] Command error: {error}"))

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        bot.run(bot_token)
    except Exception as e:
        print(Colorate.Color(Colors.red, f"[-] Bot startup error: {e}"))
        input(Colorate.Color(Colors.purple, "Press Enter to exit..."))
        sys.exit(1)