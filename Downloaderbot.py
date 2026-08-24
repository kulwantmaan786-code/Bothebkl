import re
import os
import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import KeyboardButtonCallback
from yt_dlp import YoutubeDL

# ========== 🔴 APNA CREDENTIALS YAHAN DALO 🔴 ==========
API_ID = 23548472
API_HASH = '72ee7f991ff1c712268fabcbc289cd56'
BOT_TOKEN = '8868625614:AAFastFy5oSK29ioeFavKGCvahWvUpGXiPY'

# Download folder
if not os.path.exists('downloads'):
    os.mkdir('downloads')

# Store user's selected platform
user_platform = {}

# Platforms with emojis
PLATFORMS = {
    'instagram': '📸 Instagram',
    'youtube': '🎬 YouTube',
    'tiktok': '⏰ TikTok',
    'twitter': '🐦 Twitter/X',
    'facebook': '📘 Facebook',
    'pinterest': '📌 Pinterest',
    'snapchat': '👻 Snapchat'
}

# Platform-specific URL patterns
PLATFORM_PATTERNS = {
    'instagram': r'(instagram\.com|instagr\.am)',
    'youtube': r'(youtube\.com|youtu\.be)',
    'tiktok': r'tiktok\.com',
    'twitter': r'(twitter\.com|x\.com)',
    'facebook': r'(facebook\.com|fb\.watch)',
    'pinterest': r'pinterest\.com',
    'snapchat': r'snapchat\.com'
}

# Delete old session if exists
if os.path.exists('download_bot.session'):
    os.remove('download_bot.session')

bot = TelegramClient('download_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

def download_with_ytdlp(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'no_check_certificate': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_path = ydl.prepare_filename(info)
        return file_path, info.get('title', 'file')

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    # Create buttons (2 per row)
    buttons = []
    row = []
    for i, (platform, name) in enumerate(PLATFORMS.items(), 1):
        row.append(KeyboardButtonCallback(text=name, data=f"platform_{platform}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    await event.reply(
        "🎯 **FREE MULTI-PLATFORM DOWNLOADER BOT**\n\n"
        "⚡ **100% FREE - No Limits!** ⚡\n\n"
        "1️⃣ Choose a platform from buttons below\n"
        "2️⃣ Send me the link\n"
        "3️⃣ I'll download & send you the file\n\n"
        "✨ **Supported Platforms:**\n"
        "📸 Instagram | 🎬 YouTube | ⏰ TikTok | 🐦 Twitter/X\n"
        "📘 Facebook | 📌 Pinterest | 👻 Snapchat\n\n"
        "🔄 Send /start anytime to see this menu",
        buttons=buttons
    )

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode('utf-8')
    if data.startswith('platform_'):
        platform = data.replace('platform_', '')
        user_platform[event.chat_id] = platform
        
        await event.edit(
            f"✅ **Platform selected:** {PLATFORMS[platform]}\n\n"
            f"📤 Now send me the link\n"
            f"📝 Example: https://{platform}.com/...\n\n"
            f"⚡ **Tip:** You can also send multiple links!\n\n"
            f"🔄 Send /start to change platform"
        )

@bot.on(events.NewMessage)
async def handle_link(event):
    if event.text.startswith('/'):
        return
    
    text = event.raw_text
    chat_id = event.chat_id
    
    # Check if user selected a platform
    if chat_id not in user_platform:
        await event.reply(
            "❌ **Please select a platform first!**\n\n"
            "Send /start to see platform buttons."
        )
        return
    
    platform = user_platform[chat_id]
    
    # Validate URL matches selected platform
    pattern = PLATFORM_PATTERNS.get(platform, '')
    if pattern and not re.search(pattern, text, re.IGNORECASE):
        await event.reply(
            f"❌ **Invalid link for {PLATFORMS[platform]}!**\n\n"
            f"Send correct {PLATFORMS[platform]} link or /start to change platform"
        )
        return
    
    msg = await event.reply(f"⏳ **Downloading from {PLATFORMS[platform]}...**\n\nPlease wait, this may take a few seconds...")
    
    # Extract URLs from message
    urls = re.findall(r'https?://[^\s]+', text)
    
    if not urls:
        await msg.edit("❌ No valid URL found!")
        return
    
    success_count = 0
    fail_count = 0
    
    for url in urls[:5]:  # Max 5 links at once
        try:
            file_path, title = await asyncio.get_event_loop().run_in_executor(None, download_with_ytdlp, url)
            
            if os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                
                # Send based on file type
                if ext in ['.mp4', '.mkv', '.webm', '.mov']:
                    await bot.send_file(event.chat_id, file_path, caption=f"✅ **{title[:50]}**\n📥 Downloaded from {PLATFORMS[platform]}\n⚡ FREE BOT")
                elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    await bot.send_file(event.chat_id, file_path, caption=f"🖼️ **{title[:50]}**\n📥 Downloaded from {PLATFORMS[platform]}\n⚡ FREE BOT")
                else:
                    await bot.send_file(event.chat_id, file_path)
                
                os.remove(file_path)
                success_count += 1
            else:
                fail_count += 1
                
        except Exception as e:
            fail_count += 1
            await event.reply(f"❌ **Failed for:** {url[:50]}...\nError: {str(e)[:80]}")
    
    # Clear user's platform selection after download
    if chat_id in user_platform:
        del user_platform[chat_id]
    
    # Send summary
    if success_count > 0:
        await msg.edit(f"✅ **Download Complete!**\n\n📥 Successfully downloaded: {success_count} file(s)\n❌ Failed: {fail_count}\n\n🔄 Send /start to download more!")
    else:
        await msg.edit(f"❌ **Download Failed!**\n\nNo files could be downloaded.\n\n🔄 Send /start to try again!")

@bot.on(events.NewMessage(pattern='/cancel'))
async def cancel(event):
    chat_id = event.chat_id
    if chat_id in user_platform:
        del user_platform[chat_id]
        await event.reply("✅ **Cancelled!** Send /start to begin again.")
    else:
        await event.reply("Nothing to cancel. Send /start")

@bot.on(events.NewMessage(pattern='/help'))
async def help_cmd(event):
    await event.reply(
        "📖 **HELP MENU**\n\n"
        "**How to use:**\n"
        "1️⃣ Send /start\n"
        "2️⃣ Click on platform button\n"
        "3️⃣ Send your link\n"
        "4️⃣ Get your file!\n\n"
        "**Commands:**\n"
        "/start - Show platform menu\n"
        "/cancel - Reset selection\n"
        "/help - Show this help\n"
        "/about - About this bot\n\n"
        "**Supported Links:**\n"
        "• Instagram: Reels, Posts, Stories\n"
        "• YouTube: Videos, Shorts\n"
        "• TikTok: Videos (No Watermark)\n"
        "• Twitter/X: Videos, GIFs\n"
        "• Facebook: Videos\n"
        "• Pinterest: Images, Videos\n"
        "• Snapchat: Stories\n\n"
        "⚡ **100% FREE - Unlimited Downloads!**"
    )

@bot.on(events.NewMessage(pattern='/about'))
async def about_cmd(event):
    await event.reply(
        "🤖 **About This Bot**\n\n"
        "**Multi-Platform Downloader Bot**\n\n"
        "✨ Features:\n"
        "• Download from 7+ platforms\n"
        "• 100% FREE\n"
        "• No daily limits\n"
        "• High quality downloads\n"
        "• Fast processing\n\n"
        "📢 **Join our channel:** @GLITCH_ARMY\n\n"
        "👨‍💻 **Developer:** @usjacker\n\n"
        "💡 **Tip:** Send /start to begin downloading!"
    )

print("🤖 FREE MULTI-PLATFORM DOWNLOADER BOT")
print("=" * 40)
print("✅ Bot is running...")
print("📱 Supported platforms:", ', '.join(PLATFORMS.keys()))
print("⚡ 100% FREE - No premium required!")
print("=" * 40)
bot.run_until_disconnected()
