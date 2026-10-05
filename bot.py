import asyncio
import os
import shutil
import tempfile

from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InputMediaPhoto, InputMediaVideo, Message

import insta

load_dotenv()

API_ID = int(os.environ["API_ID", "20432885"])
API_HASH = os.environ["API_HASH", "4fdcfab1c7f5e24ae69f3ce6bb234dec"]
BOT_TOKEN = os.environ["BOT_TOKEN", "8719198691:AAGJuef3z2oHLgoehurOsn1SObTpVGA2rB0"]
INSTA_COOKIES = os.getenv("INSTA_COOKIES")  # bot owner ka ek server-side cookies.txt (sirf Stories/Highlights ke liye); users ko login nahi karna
MAX_PARALLEL = int(os.getenv("MAX_PARALLEL", "3"))

app = Client("insta_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
sem = asyncio.Semaphore(MAX_PARALLEL)

VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")


WELCOME_TEXT = """✨ INSTAGRAM DOWNLOADER ✨
━━━━━━━━━━━━━━━━━━

👋 Hey {name}, welcome!
Save any Instagram content straight into Telegram — fast, free & no login.

📦 What I can download
🎬 Reels & IGTV  ➜  Video
🖼 Posts & Carousels  ➜  All photos
📖 Stories  ➜  Video
👤 Profile link  ➜  HD Profile Picture

🚀 How to use
1️⃣ Copy an Instagram link
2️⃣ Paste it here
3️⃣ Get your media in seconds ⚡

🔗 Example
https://www.instagram.com/reel/XXXXXXXX/

🤖 Powered by @NexGen_SupportGC

👇 Just paste a link to begin!"""

HELP_TEXT = """📖 HOW TO USE
━━━━━━━━━━━━━━━━━━

Send me any public Instagram link — no commands needed.

✅ Supported links
🎬 Reels
📺 IGTV / Videos
🖼 Posts (single & multiple photos)
📖 Stories
👤 Profile links

📥 What you receive
Reel / Story  ➜  🎥 Video
Post  ➜  🖼 All photos
Profile  ➜  👤 HD Profile Picture

🔗 Example
https://www.instagram.com/reel/XXXXXXXX/

ℹ️ Private accounts can't be downloaded.
🤖 Powered by @NexGen_SupportGC"""


@app.on_message(filters.command("start") & filters.private)
async def start(_, m: Message):
    name = (m.from_user.first_name if m.from_user else None) or "there"
    await m.reply_text(WELCOME_TEXT.format(name=name), parse_mode=ParseMode.DISABLED)


@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, m: Message):
    await m.reply_text(HELP_TEXT, parse_mode=ParseMode.DISABLED)


async def _download_all(url: str, shortcode: str, workdir: str):
    """Returns list of (kind, filepath)."""
    files = []

    # Profile link -> HD profile picture (shortcode = username)
    if insta.is_profile_url(url):
        murl = await asyncio.to_thread(insta.fetch_profile_pic, shortcode)
        path = os.path.join(workdir, f"{shortcode}_dp.jpg")
        ok, err = await asyncio.to_thread(insta.download_file, murl, path)
        if not ok:
            raise ValueError(err)
        return [("photo", path)]

    # /share/ links -> asli post/reel URL
    if insta.is_share_url(url):
        resolved = await asyncio.to_thread(insta.resolve_share, url)
        if not resolved:
            raise ValueError("Share link resolve nahi hua.")
        url, shortcode = resolved

    # Stories / Highlights: Instagram login maangta hai -> owner ki server-side cookies use hoti hain
    if insta.is_story_url(url):
        url = insta.story_url_from(url)
        if not INSTA_COOKIES:
            raise ValueError("Stories abhi available nahi hain (bot owner ne Instagram session set nahi kiya).")
        paths = await asyncio.to_thread(insta.ytdlp_fallback, url, workdir, INSTA_COOKIES)
        if not paths:
            raise ValueError("Story nahi mili (expire ho gayi ya account private hai).")
        return [("video" if p.lower().endswith(VIDEO_EXT) else "photo", p) for p in paths]

    try:
        items = await asyncio.to_thread(insta.extract_media, url, shortcode)
        for i, (kind, murl) in enumerate(items, 1):
            path = os.path.join(workdir, f"{shortcode}_{i}.{'mp4' if kind == 'video' else 'jpg'}")
            ok, err = await asyncio.to_thread(insta.download_file, murl, path)
            if not ok:
                raise ValueError(err)
            files.append((kind, path))
        return files
    except ValueError:
        # scrape failed -> yt-dlp fallback
        paths = await asyncio.to_thread(insta.ytdlp_fallback, url, workdir, INSTA_COOKIES)
        if not paths:
            raise
        return [("video" if p.lower().endswith(VIDEO_EXT) else "photo", p) for p in paths]


@app.on_message(filters.text & filters.private & ~filters.command(["start", "help"]))
async def handle_link(client: Client, m: Message):
    url, shortcode = insta.find_insta_link(m.text)
    if not url:
        return await m.reply_text("❌ Valid Instagram link bhejo (post / reel / story / highlight / profile).")

    status = await m.reply_text("🔎 Link process ho raha hai...")
    workdir = tempfile.mkdtemp(prefix="igdl_")
    try:
        async with sem:
            files = await _download_all(url, shortcode, workdir)
            await status.edit_text(f"⬆️ Upload ho raha hai ({len(files)} item)...")

            if len(files) == 1:
                kind, path = files[0]
                if kind == "video":
                    await client.send_video(m.chat.id, path, supports_streaming=True,
                                            reply_to_message_id=m.id)
                else:
                    await client.send_photo(m.chat.id, path, reply_to_message_id=m.id)
            else:
                # Telegram albums take max 10 items per group
                for i in range(0, len(files), 10):
                    group = [
                        InputMediaVideo(p) if k == "video" else InputMediaPhoto(p)
                        for k, p in files[i:i + 10]
                    ]
                    await client.send_media_group(m.chat.id, group, reply_to_message_id=m.id)
        await status.delete()
    except Exception as e:
        await status.edit_text(
            f"❌ Download fail: {e}\n\nPost private ho sakti hai ya Instagram ne login wall laga di (private accounts support nahi hote)."
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    app.run()
