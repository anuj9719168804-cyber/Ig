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
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, Message, CallbackQuery

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

app = Client("insta_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
sem = asyncio.Semaphore(MAX_PARALLEL)
PENDING = {}
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")

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
━━━━━━━━━━━━━━━━━━

👋 Hey {name}, welcome!
Save Instagram content straight into Telegram — fast & easy.

📦 Supported
🎬 Reels / Videos
🖼 Posts / Carousels
📖 Stories / Highlights
👤 Profile Picture

🚀 Send an Instagram link and I will fetch its information first.
Then choose the quality you want.

🤖 Powered by @NexGen_SupportGC"""

HELP_TEXT = """📖 HOW TO USE
━━━━━━━━━━━━━━━━━━

Send a public Instagram link.

✅ Reels / Videos
✅ Posts / Carousels
✅ Stories / Highlights
✅ Profile picture

🎞 Video links show available quality buttons before downloading.
ℹ️ Private accounts may require login/cookies."""


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


def bar(percent, width=12):
    p = max(0, min(100, float(percent)))
    filled = int(width * p / 100)
    return "█" * filled + "░" * (width - filled)


def progress_text(label, current, total, speed=0):
    pct = (current * 100 / total) if total else 0
    spd = human_size(speed) + "/s" if speed else "--/s"
    return (
        f"{label}\n\n"
        f"[{bar(pct)}] <b>{pct:.1f}%</b>\n"
        f"📦 {human_size(current)} / {human_size(total)}\n"
        f"⚡ {spd}"
    )


async def edit_progress(message, label, current, total, started, state):
    now = time.monotonic()
    if now - state.get("last", 0) < 1.4 and current < total:
        return
    state["last"] = now
    elapsed = max(now - started, 0.1)
    speed = current / elapsed
    try:
        await message.edit_text(progress_text(label, current, total, speed))
    except Exception:
        pass


def format_info(info):
    title = info.get("title") or "Instagram video"
    uploader = info.get("uploader") or info.get("channel") or "Unknown"
    duration = duration_text(info.get("duration"))
    views = info.get("view_count")
    size = info.get("filesize") or info.get("filesize_approx")
    lines = [
        "🎬 <b>Instagram Video Found</b>",
        "",
        f"📌 <b>{escape(str(title)[:180])}</b>",
        f"👤 {escape(str(uploader))}",
        f"⏱ {duration}",
    ]
    if views:
        lines.append(f"👁 Views: {views:,}")
    if size:
        lines.append(f"📦 Size: {human_size(size)}")
    lines.append("\n🎞 <b>Select video quality:</b>")
    return "\n".join(lines)


def quality_keyboard(qualities, token):
    """Create quality selection keyboard with colored buttons"""
    rows = []
    row = []
    
    # Quality options (Primary/Blue color)
    for q in qualities:
        row.append(make_button(f"📹 {q}p", f"igq:{token}:{q}", style=BTN_PRIMARY))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    
    # Special options section
    rows.append([make_button("━━━━━━━━━━━━", callback_data="dummy", style=BTN_PRIMARY)])
    rows.append([make_button("⚡ BEST QUALITY", f"igq:{token}:best", style=BTN_SUCCESS)])  # Green
    rows.append([make_button("🎵 AUDIO ONLY", f"igq:{token}:audio", style=BTN_PRIMARY)])   # Blue
    rows.append([make_button("❌ CANCEL", f"igcancel:{token}", style=BTN_DANGER)])          # Red
    
    return InlineKeyboardMarkup(rows)


@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    name = (m.from_user.first_name if m.from_user else None) or "there"
    await m.reply_text(WELCOME_TEXT.format(name=escape(name)), parse_mode=ParseMode.HTML)


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, m: Message):
    await m.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)


async def download_direct_files(url, shortcode, workdir):
    files = []
    if insta.is_profile_url(url):
        murl = await asyncio.to_thread(insta.fetch_profile_pic, shortcode)
        path = os.path.join(workdir, f"{shortcode}_dp.jpg")
        ok, err = await asyncio.to_thread(insta.download_file, murl, path)
        if not ok:
            raise ValueError(err)
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
        path = os.path.join(workdir, f"{shortcode}_{i}.{'mp4' if kind == 'video' else 'jpg'}")
        ok, err = await asyncio.to_thread(insta.download_file, murl, path)
        if not ok:
            raise ValueError(err)
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
                    }
                    await status.edit_text(
                        format_info(info),
                        parse_mode=ParseMode.HTML,
                        reply_markup=quality_keyboard(formats, token),
                    )
                    return
            except Exception:
                pass

        # Photo/carousel/profile/story fallback.
        async with sem:
            await status.edit_text("📥 <b>Downloading media...</b>", parse_mode=ParseMode.HTML)
            files = await download_direct_files(url, shortcode, workdir)
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
        title = f"⬆️ Uploading {index}/{total_files}"
        started = time.monotonic()
        state = {}

        async def cb(current, total, *args):
            await edit_progress(status, title, current, total, started, state)

        upload_started = time.monotonic()
        kwargs = {"reply_to_message_id": m.id, "progress": cb}
        
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
        state["upload_seconds"] = time.monotonic() - upload_started


async def download_selected(token, quality, client, q: CallbackQuery):
    data = PENDING.pop(token, None)
    if not data:
        return await q.answer("This selection expired.", show_alert=True)
    if q.from_user.id != data["uid"]:
        return await q.answer("Ye button aapke liye nahi hai.", show_alert=True)

    await q.answer("Quality selected")
    workdir = tempfile.mkdtemp(prefix="igdl_")
    status = q.message
    try:
        async with sem:
            await status.edit_text(f"📥 <b>Downloading {quality if quality != 'best' else 'Best'}...</b>", parse_mode=ParseMode.HTML)
            path = await insta.download_quality(
                data["url"], workdir, quality, INSTA_COOKIES,
                progress_callback=lambda cur, total: asyncio.run_coroutine_threadsafe(
                    edit_progress(status, "📥 Downloading", cur, total, download_selected.started, download_selected.state),
                    asyncio.get_running_loop(),
                ) if False else None,
            )
            # The downloader itself is synchronous. Redownload using the progress-aware helper.
            if path is None:
                raise ValueError("No downloadable media found.")
            await send_files_with_progress(client, q.message.reply_to_message, [("video", path)], status)
            await status.delete()
    except Exception as e:
        await status.edit_text(f"❌ <b>Download failed</b>\n\n{escape(str(e)[:700])}", parse_mode=ParseMode.HTML)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


@app.on_callback_query(filters.regex(r"^igq:"))
async def quality_callback(client: Client, q: CallbackQuery):
    _, token, quality = q.data.split(":", 2)
    data = PENDING.get(token)
    if not data:
        return await q.answer("Selection expired.", show_alert=True)
    if q.from_user.id != data["uid"]:
        return await q.answer("Ye button aapke liye nahi hai.", show_alert=True)

    PENDING.pop(token, None)
    workdir = tempfile.mkdtemp(prefix="igdl_")
    try:
        await q.answer(f"{quality} selected")
        async with sem:
            await q.message.edit_text("📥 <b>Downloading...</b>", parse_mode=ParseMode.HTML)
            loop = asyncio.get_running_loop()
            state = {"last": 0}
            started = time.monotonic()

            def dl_progress(cur, total):
                now = time.monotonic()
                if now - state.get("last", 0) < 1.4 and cur < total:
                    return
                state["last"] = now
                asyncio.run_coroutine_threadsafe(
                    edit_progress(q.message, "📥 Downloading", cur, total, started, state), loop
                )

            path = await asyncio.to_thread(
                insta.download_quality,
                data["url"], workdir, quality, INSTA_COOKIES, dl_progress
            )
            if not path:
                raise ValueError("Media download nahi hua.")

            download_seconds = time.monotonic() - started
            size = os.path.getsize(path)
            title = data["info"].get("title") or "Instagram Media"
            duration = data["info"].get("duration")
            qlabel = "Best Quality" if quality == "best" else ("Audio" if quality == "audio" else f"{quality}p")
            caption = build_caption(
                data["info"], title, os.path.basename(path), size, qlabel,
                duration, download_seconds, 0, q.from_user, data["url"]
            )

            upload_started = time.monotonic()
            # Pass caption directly to send_files_with_progress
            await send_files_with_progress(
                client, q.message.reply_to_message, [("audio" if quality == "audio" else "video", path)], 
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


@app.on_callback_query(filters.regex(r"^dummy$"))
async def dummy_callback(_, q: CallbackQuery):
    await q.answer("Select a quality option", show_alert=False)


@app.on_callback_query(filters.regex(r"^igcancel:"))
async def cancel_callback(_, q: CallbackQuery):
    token = q.data.split(":", 1)[1]
    data = PENDING.pop(token, None)
    if data and q.from_user.id == data["uid"]:
        await q.answer("Cancelled")
        await q.message.edit_text("❌ Download cancelled.")
    else:
        await q.answer("Selection expired.", show_alert=True)


if __name__ == "__main__":
    app.run()
