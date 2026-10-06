import asyncio
import glob
import os
import shutil
import tempfile
import time
from html import escape

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, LinkPreviewOptions, Message, CallbackQuery

# reply_to_message_id is deprecated -> reply_parameters (older builds fall back to the old kwarg)
try:
    from pyrogram.types import ReplyParameters
except ImportError:
    ReplyParameters = None

# Try to import ButtonStyle for colored buttons (only in newer pyrogram builds)
try:
    from pyrogram.enums import ButtonStyle
    BUTTON_STYLE_SUPPORTED = True
except ImportError:
    BUTTON_STYLE_SUPPORTED = False

import insta

load_dotenv()

API_ID = int(os.getenv("API_ID", "20432885"))
API_HASH = os.getenv("API_HASH", "4fdcfab1c7f5e24ae69f3ce6bb234dec")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8719198691:AAGJuef3z2oHLgoehurOsn1SObTpVGA2rB0")
INSTA_COOKIES = os.getenv("INSTA_COOKIES")
MAX_PARALLEL = int(os.getenv("MAX_PARALLEL", "3"))
# seconds between progress-card edits (Telegram flood-limits faster edits)
EDIT_INTERVAL = max(3.0, float(os.getenv("PROGRESS_EDIT_INTERVAL", "5") or 5))
POWERED_BY_URL = "https://t.me/NexGen_SupportGC"
WELCOME_PHOTO_URL = "https://t.me/log_ak_bot/201"

app = Client("insta_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
sem = asyncio.Semaphore(MAX_PARALLEL)
PENDING = {}
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")
PENDING_TIMEOUT = 300  # 5 minutes timeout for quality selection

# ═══════════════════════════════════════════════════════════════
# Button Styles (Colors)
# ═══════════════════════════════════════════════════════════════
BTN_PRIMARY = ButtonStyle.PRIMARY if BUTTON_STYLE_SUPPORTED else None      # 🔵 Blue
BTN_DANGER = ButtonStyle.DANGER if BUTTON_STYLE_SUPPORTED else None        # 🔴 Red
BTN_SUCCESS = getattr(ButtonStyle, "SUCCESS", BTN_PRIMARY) if BUTTON_STYLE_SUPPORTED else None  # 🟢 Green


def make_button(text, callback_data=None, url=None, style=None):
    """Create an inline keyboard button with optional color styling"""
    kw = {"text": text}
    if callback_data:
        kw["callback_data"] = callback_data
    if url:
        kw["url"] = url
    if BUTTON_STYLE_SUPPORTED and style is not None:
        kw["style"] = style
    try:
        return InlineKeyboardButton(**kw)
    except TypeError:
        # Fallback if style is not supported
        kw.pop("style", None)
        return InlineKeyboardButton(**kw)

WELCOME_TEXT = """✨ INSTAGRAM DOWNLOADER ✨
━━━━━━━━━━━━━━━━━━━━
👋 Hey {name}, Welcome to NEXGEN!
💜
📸 Download Instagram content directly into Telegram — fast, simple & high quality.

📦 Supported Content
🎬 Reels & Videos
🖼️ Posts & Carousels
📖 Stories & Highlights
👤 Profile Pictures

🚀 How It Works
🔗 Send any supported Instagram link
🔍 NEXGEN fetches the available information
⚙️ Choose your preferred quality
📥 Get your media directly in Telegram

⚡ Fast Download • 🔒 Secure • 💎 High Quality

🤖 Powered by NEXGEN
📢 Support: @NexGen_SupportGC
━━━━━━━━━━━━━━━━━━━━
💙 NEXGEN — Your Instagram, Made Downloadable."""

HELP_TEXT = """🆘 HELP TEXT
🤖 NEXGEN Instagram Downloader — Help
📸 Instagram Photos — Download instantly
🎬 Reels & Videos — High-quality downloads
📖 Stories — Easy story downloading
🎵 Media Support — Save supported Instagram content
⚡ Fast & Simple — Just paste your link

🔗 How to use:
1️⃣ Copy your Instagram link
2️⃣ Send it to the bot
3️⃣ Wait for NEXGEN to process it
4️⃣ Enjoy your downloaded media! 🚀

💙 NEXGEN — Fast. Secure. Simple."""

ABOUT_TEXT = """<blockquote>✨ ABOUT NEXGEN INSTAGRAM DOWNLOADER ✨
━━━━━━━━━━━━━━━━━━━━
🤖 Meet NEXGEN — Your Instagram Download Assistant! 💜
📸 Download supported Instagram content directly into Telegram — fast, simple & high quality.</blockquote>

<blockquote>📦 What NEXGEN Supports
🎬 Reels & Videos
🖼️ Posts & Carousels
📖 Stories & Highlights
👤 Profile Pictures</blockquote>

<blockquote>⚡ Powerful Features
🚀 Fast Media Processing
💎 High-Quality Downloads
🔗 Easy Link-Based Download
📥 Direct Telegram Delivery
🛡️ Simple & Secure Experience</blockquote>

<blockquote>📞 Support & Community
🍀 Support: @NexGen_SupportGC
⁉️ HelpDesk: @NexGenxHelpbot
💌 More Bots: @NexGen_BotList
🤖 Powered by: @NexGen_Bots
🔧 Version: Nex v5.08.05</blockquote>

<blockquote>━━━━━━━━━━━━━━━━━━━━
💙 NEXGEN — Fast. Simple. Made for Instagram.</blockquote>"""


async def generate_referral_text(user_id, app=None, referral_count=0):
    """Generate referral dashboard text with user-specific referral link"""
    # Try to get bot username from app
    bot_username = "log_ak_bot"  # fallback
    try:
        if app and hasattr(app, 'me'):
            me = await app.get_me() if callable(app.get_me) else app.me
            if hasattr(me, 'username') and me.username:
                bot_username = me.username
    except Exception:
        pass
    
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    progress = min(referral_count, 2)
    remaining = max(2 - referral_count, 0)
    
    progress_bar = "🟢" * progress + "⚪" * remaining
    
    return f"""<blockquote>🎁 Referral Dashboard
━━━━━━━━━━━━━━━━━━</blockquote>

<blockquote>📊 Your Progress
🎯 Current Progress: {progress}/2
📈 Progress Bar: {progress_bar}
🌱 Total Referrals: {referral_count}
⚡ Need {remaining} more referral(s)</blockquote>

<blockquote>🎉 Your Rewards
┌ 🔗 Referral Link → 3 Days
│   Referral Welcome Premium for new user
└ 🎁 2/2 Complete → 5 Days
    Referral Premium for you</blockquote>

<blockquote>💡 How It Works
1️⃣ Share your referral link with friends
2️⃣ Friend joins via your link → gets 3 Days Welcome Premium
3️⃣ You collect referrals
4️⃣ Complete 2/2 → unlock 5 Days Referral Premium!</blockquote>

<blockquote>🔗 Your Referral Link:
<code>{referral_link}</code></blockquote>"""


def human_size(n):
    try:
        n = float(n or 0)
    except Exception:
        return "Unknown"
    units = ["B", "KB", "MB", "GB"]
    for u in units:
        if n < 1024 or u == units[-1]:
            return f"{n:.1f} {u}"
        n /= 1024
    return "Unknown"


def duration_text(seconds):
    try:
        seconds = int(seconds or 0)
    except Exception:
        return "Unknown"
    h, r = divmod(seconds, 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def human_speed(n):
    n = float(n or 0)
    for unit in ("B/s", "KB/s", "MB/s", "GB/s"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB/s"


def human_time(seconds):
    seconds = max(0, int(seconds or 0))
    h, rem = divmod(seconds, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {sec}s"
    if m:
        return f"{m}m {sec}s"
    return f"{sec}s"


def hex_bar(pct, width=10):
    filled = min(width, int(width * pct / 100))
    return "⬢" * filled + "⬡" * (width - filled)


def progress_text(is_download, title, label, current, total, speed, elapsed, eta, tag=""):
    """Same progress card as the YouTube bot (⬢⬡ bar + ╭━❰Progress❱━➣ box)."""
    pct = min(100.0, (current / total * 100)) if total else 0
    emoji = "📥" if is_download else "📤"
    verb = "Downloading" if is_download else "Uploading"
    word = "download" if is_download else "upload"
    return (
        f"{emoji} <b>Fast {verb}{tag} via Main Engine</b>\n\n"
        "╭━━━━❰Progress❱━➣\n"
        f"┣⪼ 🎬 File: <code>{escape(str(title)[:60])}</code>\n"
        f"┣⪼ 🎞 Quality: {escape(str(label))}\n"
        f"┣⪼ [{hex_bar(pct)}]\n"
        f"┣⪼ ✅ {pct:.1f}%\n"
        f"┣⪼ 💾 {human_size(current)} / {human_size(total) if total else '?'}\n"
        f"┣⪼ ⚡ {human_speed(speed)}\n"
        f"┣⪼ 🕐 Elapsed: {human_time(elapsed)}\n"
        f"┣⪼ ⏳ ETA: {human_time(eta)}\n"
        "╰━━━━━━━━━━━━━━━➣\n\n"
        f"⚡ Hyper {word} connections active"
    )


async def safe_edit(msg, text, markup=None):
    try:
        await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=markup,
                            link_preview_options=LinkPreviewOptions(is_disabled=True))
    except (MessageNotModified, FloodWait):
        pass
    except Exception:  # message deleted etc.
        pass


class Progress:
    """Throttled progress card for one download or upload."""

    def __init__(self, message, is_download, title, label, tag=""):
        self.msg, self.is_download, self.title, self.label, self.tag = message, is_download, title, label, tag
        self.t0 = time.monotonic()
        self.last = 0.0

    def ready(self, cur, total):
        now = time.monotonic()
        final = bool(total) and cur >= total
        if not final and now - self.last < EDIT_INTERVAL:
            return False
        self.last = now
        return True

    async def update(self, cur, total, speed=0, eta=0, force=False):
        if not force and not self.ready(cur, total):
            return
        el = max(time.monotonic() - self.t0, 0.1)
        speed = speed or (cur / el)
        eta = eta or ((total - cur) / speed if speed > 0 and total else 0)
        await safe_edit(self.msg, progress_text(self.is_download, self.title, self.label,
                                                cur, total, speed, el, eta, self.tag))

    def push(self, loop, cur, total, speed=0, eta=0):
        """Thread-safe: call from yt-dlp / requests worker threads."""
        if self.ready(cur, total):
            asyncio.run_coroutine_threadsafe(self.update(cur, total, speed, eta, force=True), loop)


def reply_kw(m):
    """kwargs that make a send_* call reply to message m (no deprecated reply_to_message_id)."""
    mid = getattr(m, "id", None)
    if not mid:
        return {}
    if ReplyParameters is not None:
        return {"reply_parameters": ReplyParameters(message_id=mid)}
    return {"reply_to_message_id": mid}


def format_info(info, qualities=None):
    title = info.get("title") or "Instagram video"
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    duration = duration_text(info.get("duration"))
    views = info.get("view_count")
    upload_date = info.get("upload_date")
    
    # Format main title
    lines = [
        f"<b>🎬 {escape(str(title)[:200])}</b>",
        "",
    ]
    
    # Create a clean info section with better formatting
    info_section = [
        f"<b>👤 BY:</b> <code>{escape(str(uploader))}</code>",
        f"<b>⏱️ DURATION:</b> <code>{duration}</code>",
    ]
    
    if views:
        info_section.append(f"<b>👁️ VIEWS:</b> <code>{views:,}</code>")
    
    info_section.append("🏷️ <b>CATEGORY:</b> <code>MUSIC</code>")
    
    # Format upload date nicely
    if upload_date and len(str(upload_date)) == 8:
        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
        info_section.append(f"📅 <b>UPLOADED:</b> <code>{formatted_date}</code>")
    
    lines.extend(info_section)
    lines.append("")
    lines.append("<b>AVAILABLE QUALITIES:</b>")
    
    # Show available qualities with better formatting
    if qualities:
        quality_names = {2160: "4K", 1440: "2K"}
        quality_list = []
        for q in sorted(qualities, reverse=True):
            name = quality_names.get(q, f"{q}p")
            quality_list.append(f"✅ <code>{name}</code>")
        lines.extend(quality_list)
    
    # Add audio option
    lines.append("🎵 <code>MP3 (audio)</code>")
    
    lines.append("")
    lines.append("<b>👇 TAP A QUALITY BELOW TO DOWNLOAD:</b>")
    
    return "\n".join(lines)


def start_keyboard():
    return InlineKeyboardMarkup([
        [make_button("📖 How to use", "ig_help", style=BTN_PRIMARY),
         make_button("ℹ️ About", "ig_about", style=BTN_SUCCESS)],
        [make_button("🎁 Refer & Earn", "ig_referral", style=BTN_SUCCESS)],
        [make_button("📢 Updates", url=POWERED_BY_URL, style=BTN_SUCCESS)],
        [make_button("❌ Close", "ig_close", style=BTN_DANGER)],
    ])


def help_keyboard():
    return InlineKeyboardMarkup([
        [make_button("⬅️ Back", "ig_back", style=BTN_PRIMARY),
         make_button("❌ Close", "ig_close", style=BTN_DANGER)],
    ])


def about_keyboard():
    return InlineKeyboardMarkup([
        [make_button("⬅️ Back", "ig_back", style=BTN_PRIMARY),
         make_button("❌ Close", "ig_close", style=BTN_DANGER)],
    ])


def referral_keyboard():
    return InlineKeyboardMarkup([
        [make_button("📋 Copy Link", "ig_copy_ref", style=BTN_SUCCESS)],
        [make_button("⬅️ Back", "ig_back", style=BTN_PRIMARY),
         make_button("❌ Close", "ig_close", style=BTN_DANGER)],
    ])


def quality_keyboard(qualities, token):
    """Create quality selection keyboard with 2-column grid layout"""
    rows = []
    row = []
    
    # Quality options in 2-column grid (Primary/Blue color)
    quality_names = {2160: "4K", 1440: "2K"}
    
    # Filter and sort qualities in descending order
    quality_list = sorted(qualities, reverse=True)
    
    # Add quality buttons in 2-column format
    for q in quality_list:
        name = quality_names.get(q, f"{q}p")
        row.append(make_button(f"🎬 {name}", f"igq:{token}:{q}", style=BTN_PRIMARY))
        if len(row) == 2:
            rows.append(row)
            row = []
    
    # Add remaining button if odd number
    if row:
        rows.append(row)
    
    # Add special options as full-width buttons
    rows.append([make_button("⚡ BEST QUALITY", f"igq:{token}:best", style=BTN_SUCCESS)])
    rows.append([make_button("🎵 AUDIO ONLY", f"igq:{token}:audio", style=BTN_PRIMARY)])
    rows.append([make_button("❌ CANCEL", f"igcancel:{token}", style=BTN_DANGER)])
    
    return InlineKeyboardMarkup(rows)


@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    name = (m.from_user.first_name if m.from_user else None) or "there"
    
    # Handle referral parameter
    args = m.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = args[1].replace("ref_", "")
        # You can log referral here if using database
        pass
    
    try:
        await m.reply_photo(
            WELCOME_PHOTO_URL,
            caption=WELCOME_TEXT.format(name=escape(name)),
            parse_mode=ParseMode.HTML,
            reply_markup=start_keyboard()
        )
    except Exception:
        # Fallback to text if photo fails
        await m.reply_text(WELCOME_TEXT.format(name=escape(name)), parse_mode=ParseMode.HTML,
                           reply_markup=start_keyboard())


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, m: Message):
    await m.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML, reply_markup=help_keyboard())


@app.on_message(filters.command("about") & filters.private)
async def about_cmd(_, m: Message):
    await m.reply_text(ABOUT_TEXT, parse_mode=ParseMode.HTML, reply_markup=about_keyboard())


@app.on_message(filters.command("referral") & filters.private)
async def referral_cmd(client: Client, m: Message):
    user_id = m.from_user.id
    referral_text = await generate_referral_text(user_id, app=client, referral_count=0)
    await m.reply_text(referral_text, parse_mode=ParseMode.HTML, reply_markup=referral_keyboard())


@app.on_message(filters.command("menu") & filters.private)
async def menu_cmd(_, m: Message):
    name = (m.from_user.first_name if m.from_user else None) or "there"
    await m.reply_text(WELCOME_TEXT.format(name=escape(name)), parse_mode=ParseMode.HTML, reply_markup=start_keyboard())


async def download_direct_files(url, shortcode, workdir, status=None):
    files = []
    loop = asyncio.get_running_loop()

    async def fetch(murl, path, title, label, tag=""):
        prog = Progress(status, True, title, label, tag) if status else None
        cb = (lambda cur, total, sp=0, eta=0: prog.push(loop, cur, total, sp, eta)) if prog else None
        ok, err = await asyncio.to_thread(insta.download_file, murl, path, cb)
        if not ok:
            raise ValueError(err)

    if insta.is_profile_url(url):
        murl = await asyncio.to_thread(insta.fetch_profile_pic, shortcode)
        path = os.path.join(workdir, f"{shortcode}_dp.jpg")
        await fetch(murl, path, f"{shortcode}_dp.jpg", "Profile Picture")
        return [("photo", path)]

    if insta.is_share_url(url):
        resolved = await asyncio.to_thread(insta.resolve_share, url)
        if not resolved:
            raise ValueError("Share link resolve nahi hua.")
        url, shortcode = resolved

    if insta.is_story_url(url):
        url = insta.story_url_from(url)
        if not INSTA_COOKIES:
            raise ValueError("Stories ke liye INSTA_COOKIES set nahi hai.")
        paths = await asyncio.to_thread(insta.ytdlp_fallback, url, workdir, INSTA_COOKIES)
        if not paths:
            raise ValueError("Story nahi mili.")
        return [("video" if p.lower().endswith(VIDEO_EXT) else "photo", p) for p in paths]

    items = await asyncio.to_thread(insta.extract_media, url, shortcode)
    for i, (kind, murl) in enumerate(items, 1):
        name = f"{shortcode}_{i}.{'mp4' if kind == 'video' else 'jpg'}"
        path = os.path.join(workdir, name)
        await fetch(murl, path, name, "Video" if kind == "video" else "Photo",
                    tag=f" {i}/{len(items)}" if len(items) > 1 else "")
        files.append((kind, path))
    return files


async def fetch_video_info(url):
    return await asyncio.to_thread(insta.fetch_info, url, INSTA_COOKIES)


@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_link(client: Client, m: Message):
    url, shortcode = insta.find_insta_link(m.text)
    if not url:
        return await m.reply_text("❌ Valid Instagram link bhejo.")

    status = await m.reply_text("🔎 <b>Fetching link information...</b>", parse_mode=ParseMode.HTML)
    workdir = tempfile.mkdtemp(prefix="igdl_")
    try:
        # Resolve share URL before metadata lookup.
        if insta.is_share_url(url):
            resolved = await asyncio.to_thread(insta.resolve_share, url)
            if resolved:
                url, shortcode = resolved

        # Video/reel: fetch metadata and expose available qualities first.
        if not insta.is_profile_url(url) and not insta.is_story_url(url):
            try:
                info = await fetch_video_info(url)
                formats = insta.available_qualities(info)
                if formats:
                    token = os.urandom(6).hex()
                    PENDING[token] = {
                        "uid": m.from_user.id,
                        "url": url,
                        "shortcode": shortcode,
                        "info": info,
                        "created_at": time.monotonic(),
                    }
                    # Send quality selection message with proper buttons
                    quality_text = format_info(info, formats)
                    thumbnail = info.get("thumbnail")
                    
                    try:
                        # Delete old status message
                        await status.delete()
                        
                        # Send new message with thumbnail and quality buttons
                        if thumbnail:
                            try:
                                await m.reply_photo(
                                    thumbnail,
                                    caption=quality_text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=quality_keyboard(formats, token)
                                )
                            except Exception:
                                # Fallback to text if thumbnail fails
                                await m.reply_text(
                                    quality_text,
                                    parse_mode=ParseMode.HTML,
                                    reply_markup=quality_keyboard(formats, token)
                                )
                        else:
                            await m.reply_text(
                                quality_text,
                                parse_mode=ParseMode.HTML,
                                reply_markup=quality_keyboard(formats, token)
                            )
                    except Exception as e:
                        # Fallback: show quality options as text
                        await status.edit_text(
                            quality_text,
                            parse_mode=ParseMode.HTML,
                            reply_markup=quality_keyboard(formats, token),
                        )
                    return
            except Exception:
                pass

        # Photo/carousel/profile/story fallback.
        async with sem:
            await status.edit_text("📥 <b>Downloading media...</b>", parse_mode=ParseMode.HTML)
            files = await download_direct_files(url, shortcode, workdir, status)
            # Try to fetch info for caption, but proceed even if it fails
            info = None
            try:
                info = await fetch_video_info(url)
            except Exception:
                pass
            await send_files_with_progress(client, m, files, status, info=info, source_url=url)
        await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ <b>Failed</b>\n\n{escape(str(e)[:700])}", parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def build_caption(info, title, filename, size_bytes, quality_label, duration,
                  download_seconds, upload_seconds, user, source_url):
    info = info or {}
    uploader = info.get("uploader") or info.get("channel")
    lines = [
        f"🎬 <b>{escape(str(title or 'Instagram Media')[:180])}</b>",
        "",
        "<blockquote>",
        f"📄 <b>File Name</b>: {escape(str(filename))}",
        f"📦 <b>Size</b>: {human_size(size_bytes)}",
        f"🎞️ <b>Quality</b>: {escape(str(quality_label or 'Original'))}",
        f"⏱️ <b>Duration</b>: {duration_text(duration) if duration else 'Unknown'}",
    ]
    if uploader:
        lines.append(f"👤 <b>By</b>: {escape(str(uploader))}")
    if info.get("view_count"):
        lines.append(f"👁️ <b>Views</b>: {info['view_count']:,}")
    if info.get("like_count"):
        lines.append(f"👍 <b>Likes</b>: {info['like_count']:,}")
    if info.get("comment_count"):
        lines.append(f"💬 <b>Comments</b>: {info['comment_count']:,}")
    ud = str(info.get("upload_date") or "")
    if len(ud) == 8 and ud.isdigit():
        lines.append(f"📅 <b>Uploaded</b>: {ud[:4]}-{ud[4:6]}-{ud[6:]}")
    lines.extend([
        f"⬇️ <b>Downloaded in</b>: {download_seconds:.1f} sec",
        f"⬆️ <b>Uploaded in</b>: {upload_seconds:.1f} sec",
    ])
    if user:
        name = escape(user.first_name or "User")
        uid = user.id
        lines.append(f"🙋 <b>Downloaded by</b>: <a href=\"tg://user?id={uid}\">{name}</a>")
    if source_url:
        lines.append(f"🔗 <b>Source</b>: <a href=\"{escape(source_url, quote=True)}\">Instagram Link</a>")
    lines.append("</blockquote>")
    lines.extend(["", "⚡ <b>Powered by</b> <a href=\"https://t.me/NexGen_SupportGC\">NexGen</a>"])
    return "\n".join(lines)


async def send_files_with_progress(client, m, files, status, caption=None, info=None, quality_label=None, source_url=None):
    total_files = len(files)
    download_started = time.monotonic()  # For tracking total download time

    for index, (kind, path) in enumerate(files, 1):
        tag = f" {index}/{total_files}" if total_files > 1 else ""
        label = quality_label or ("Audio" if kind == "audio" else "Original")
        prog = Progress(status, False, os.path.basename(path), label, tag)

        async def cb(current, total, *args):
            await prog.update(current, total)

        # show the card right away (0%) instead of waiting for Telegram's first callback
        await prog.update(0, os.path.getsize(path), force=True)

        upload_started = time.monotonic()
        kwargs = {"progress": cb, **reply_kw(m)}

        # Build caption if not provided but info is available
        if caption is None and info and index == 1:
            download_seconds = time.monotonic() - download_started
            upload_seconds = time.monotonic() - upload_started
            size_bytes = os.path.getsize(path)
            title_text = info.get("title") or "Instagram Media"
            caption = build_caption(
                info, title_text, os.path.basename(path), size_bytes,
                quality_label or "Original", info.get("duration"),
                download_seconds, upload_seconds, m.from_user, source_url
            )

        if caption and index == 1:
            kwargs["caption"] = caption
            kwargs["parse_mode"] = ParseMode.HTML

        if kind == "audio":
            await client.send_audio(m.chat.id, path, **kwargs)
        elif kind == "video":
            kwargs["supports_streaming"] = True
            await client.send_video(m.chat.id, path, **kwargs)
        else:
            await client.send_photo(m.chat.id, path, **kwargs)


@app.on_callback_query(filters.regex(r"^igq:"))
async def quality_callback(client: Client, q: CallbackQuery):
    _, token, quality = q.data.split(":", 2)
    data = PENDING.get(token)
    if not data:
        return await q.answer("Selection expired.", show_alert=True)
    
    # Check if selection has timed out
    if time.monotonic() - data.get("created_at", 0) > PENDING_TIMEOUT:
        PENDING.pop(token, None)
        return await q.answer("❌ Selection expired. Please send the link again.", show_alert=True)
    
    if q.from_user.id != data["uid"]:
        return await q.answer("Ye button aapke liye nahi hai.", show_alert=True)

    PENDING.pop(token, None)
    workdir = tempfile.mkdtemp(prefix="igdl_")
    try:
        await q.answer(f"{quality} selected")
        async with sem:
            await q.message.edit_text("📥 <b>Downloading...</b>", parse_mode=ParseMode.HTML)
            loop = asyncio.get_running_loop()
            started = time.monotonic()
            qlabel = "Best Quality" if quality == "best" else ("Audio" if quality == "audio" else f"{quality}p")
            prog = Progress(q.message, True, data["info"].get("title") or "Instagram Media", qlabel)
            await prog.update(0, 0, force=True)

            path = await asyncio.to_thread(
                insta.download_quality,
                data["url"], workdir, quality, INSTA_COOKIES,
                lambda cur, total, sp=0, eta=0: prog.push(loop, cur, total, sp, eta),
            )
            if not path:
                raise ValueError("Media download nahi hua.")

            download_seconds = time.monotonic() - started
            size = os.path.getsize(path)
            title = data["info"].get("title") or "Instagram Media"
            duration = data["info"].get("duration")
            caption = build_caption(
                data["info"], title, os.path.basename(path), size, qlabel,
                duration, download_seconds, 0, q.from_user, data["url"]
            )

            upload_started = time.monotonic()
            # Pass caption directly to send_files_with_progress
            await send_files_with_progress(
                client, q.message.reply_to_message or q.message, [("audio" if quality == "audio" else "video", path)], 
                q.message, caption=caption, info=data["info"], quality_label=qlabel, source_url=data["url"]
            )
            upload_seconds = time.monotonic() - upload_started
            await q.message.delete()
    except Exception as e:
        try:
            await q.message.edit_text(f"❌ <b>Failed</b>\n\n{escape(str(e)[:700])}", parse_mode=ParseMode.HTML)
        except Exception:
            pass
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@app.on_callback_query(filters.regex(r"^ig_help$"))
async def help_callback(_, q: CallbackQuery):
    await q.answer()
    await safe_edit(q.message, HELP_TEXT, help_keyboard())


@app.on_callback_query(filters.regex(r"^ig_about$"))
async def about_callback(_, q: CallbackQuery):
    await q.answer()
    await safe_edit(q.message, ABOUT_TEXT, about_keyboard())


@app.on_callback_query(filters.regex(r"^ig_referral$"))
async def referral_callback(client: Client, q: CallbackQuery):
    await q.answer()
    user_id = q.from_user.id
    referral_text = await generate_referral_text(user_id, app=client, referral_count=0)
    await safe_edit(q.message, referral_text, referral_keyboard())


@app.on_callback_query(filters.regex(r"^ig_copy_ref$"))
async def copy_ref_callback(client: Client, q: CallbackQuery):
    user_id = q.from_user.id
    bot_username = "log_ak_bot"  # fallback
    try:
        me = await client.get_me()
        if hasattr(me, 'username') and me.username:
            bot_username = me.username
    except Exception:
        pass
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    await q.answer(f"Link copied: {referral_link}", show_alert=False)


@app.on_callback_query(filters.regex(r"^ig_back$"))
async def back_callback(_, q: CallbackQuery):
    await q.answer()
    name = q.from_user.first_name or "there"
    await safe_edit(q.message, WELCOME_TEXT.format(name=escape(name)), start_keyboard())


@app.on_callback_query(filters.regex(r"^ig_close$"))
async def close_callback(_, q: CallbackQuery):
    await q.answer()
    try:
        await q.message.delete()
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^dummy$"))
async def dummy_callback(_, q: CallbackQuery):
    await q.answer("Select a quality option", show_alert=False)


@app.on_callback_query(filters.regex(r"^igcancel:"))
async def cancel_callback(_, q: CallbackQuery):
    token = q.data.split(":", 1)[1]
    data = PENDING.pop(token, None)
    if data and q.from_user.id == data["uid"]:
        await q.answer("Cancelled")
        try:
            await q.message.edit_text("❌ Download cancelled.")
        except Exception:
            pass
    else:
        await q.answer("Selection expired.", show_alert=True)


if __name__ == "__main__":
    app.run()
