# 📸 Instagram Downloader Bot

> 🚀 A powerful Telegram bot for downloading Instagram media with metadata, quality selection, captions, and real-time download/upload progress.

## ✨ Features

- 🔗 Instagram link fetching
- 🎬 Video/Reel downloading
- 🖼️ Image/Photo downloading
- 📚 Carousel / multiple-media support
- 📊 Media metadata extraction
- 🎞️ Available quality selection
- ⚡ Best Quality option
- 🎵 Audio option where supported
- 📥 Real-time download progress
- 📤 Real-time Telegram upload progress
- 🚀 Speed, percentage and transferred-size display
- 📝 Professional media captions
- 👤 Uploader information when available
- 👁️ Views / likes / comments when available
- ⏱️ Duration information when available
- 🔗 Source URL in the final caption
- 📦 Multiple-file progress/count support
- 🛠️ Environment-variable configuration
- 📱 Termux compatible
- 🐍 Python based
- 🍪 Designed for public Instagram URLs without requiring cookies where the underlying extractor supports it

## 📋 Supported Content

| Content | Support |
|---|---|
| 🎬 Instagram Video/Reel | ✅ |
| 🖼️ Instagram Image | ✅ |
| 📚 Carousel | ✅ |
| 📊 Metadata | ✅ |
| 🎞️ Quality selection | ✅ |
| 📥 Download progress | ✅ |
| 📤 Upload progress | ✅ |
| 📝 Custom caption | ✅ |
| 👤 Profile information | Depends on source |
| 📖 Stories | Depends on current extractor/source access |

> ⚠️ Instagram can change its public endpoints and anti-bot protections. Availability may therefore vary by URL.

## 🎞️ Quality Selection

When multiple video qualities are available, the bot can present the available options before downloading.

Example:

```text
🎞️ Select Quality

🔹 144p
🔹 360p
🔹 480p
🔹 720p
🔹 1080p
⚡ Best Quality
🎵 Audio
```

Only qualities actually reported by the extractor should be offered.

## 📊 Download Progress

During downloading, the bot can show information such as:

```text
📥 Downloading...

━━━━━━━━━━━━━━
████████░░░░ 65%

📦 Size: 12.4 MB / 19.1 MB
⚡ Speed: 2.8 MB/s
⏳ ETA: 00:03
```

## 📤 Upload Progress

After the media is downloaded, Telegram upload progress can be displayed:

```text
📤 Uploading...

━━━━━━━━━━━━━━
██████████░░ 82%

📦 Size: 15.6 MB / 19.1 MB
⚡ Speed: 4.2 MB/s
⏳ ETA: 00:01
```

## 📝 Caption

The final media caption can contain useful metadata, for example:

```text
🎬 Title: Example Video
👤 Uploader: @username
🎞️ Quality: 720p
📦 Size: 19.1 MB
⏱️ Duration: 00:42
👁️ Views: 12.4K
❤️ Likes: 1.2K
💬 Comments: 86

🔗 Source: Instagram

⚡ Downloaded Successfully
```

Unavailable metadata is omitted rather than displaying fake values.

## 🔐 Configuration

Create environment variables for the Telegram credentials:

```env
API_ID=YOUR_API_ID
API_HASH=YOUR_API_HASH
BOT_TOKEN=YOUR_BOT_TOKEN
```

Example Python configuration:

```python
import os

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
```

### 🔒 Security

Never publish your:

- 🔑 `BOT_TOKEN`
- 🪪 `API_ID`
- 🔐 `API_HASH`
- 🍪 Cookies/session files
- 🗝️ Other private credentials

If a bot token is accidentally exposed, regenerate it through BotFather.

## 📱 Termux Installation

### 1️⃣ Update Termux

```bash
pkg update -y
pkg upgrade -y
```

### 2️⃣ Install required packages

```bash
pkg install git python ffmpeg -y
```

### 3️⃣ Clone the repository

```bash
git clone https://github.com/anuj9719168804-cyber/Ig.git
cd Ig
```

### 4️⃣ Create virtual environment

```bash
python -m venv venv
source venv/bin/activate
```

> ℹ️ Do not run `pip install -U pip` on Termux if Termux reports that upgrading the system pip package is forbidden.

### 5️⃣ Install Python dependencies

```bash
pip install -r requirements.txt
```

### 6️⃣ Configure credentials

Set the required environment variables:

```bash
export API_ID="YOUR_API_ID"
export API_HASH="YOUR_API_HASH"
export BOT_TOKEN="YOUR_BOT_TOKEN"
```

### 7️⃣ Start the bot

```bash
python bot.py
```

## 🔄 Updating the Bot

From the project directory:

```bash
cd ~/Ig
git pull
```

Then:

```bash
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## 📁 Project Structure

```text
Ig/
├── bot.py              # 🤖 Main Telegram bot
├── insta.py            # 📸 Instagram extraction/download logic
├── requirements.txt    # 📦 Python dependencies
├── README.md           # 📖 Documentation
├── venv/               # 🐍 Virtual environment (local only)
└── downloads/          # 📥 Temporary downloaded files
```

## 🛠️ Troubleshooting

### ❌ `venv/bin/activate: No such file`

Create the environment first:

```bash
python -m venv venv
source venv/bin/activate
```

### ❌ `Installing pip is forbidden`

Do not upgrade Termux's system pip with:

```bash
pip install -U pip
```

Use the Termux-provided pip or a virtual environment instead.

### ❌ `ModuleNotFoundError`

Run:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ Instagram returns an error

Instagram may temporarily block requests, require authentication for private/restricted content, or change its endpoints.

Try a public URL and make sure your dependencies are updated.

## 🍪 Cookies / Authentication

The bot is intended to work with public Instagram content without cookies when the extractor can access that content anonymously.

Private, login-required, age/restricted, or otherwise protected content may not be downloadable without appropriate authentication.

## ⚡ Performance

For better performance:

- 💾 Keep enough free storage for temporary files
- 🧹 Remove old downloads periodically
- 📶 Use a stable internet connection
- 🖥️ Use a reliable always-on host for 24/7 operation
- 📱 On Termux, keep the device/network available while the bot is running

## 🛡️ Responsible Use

Use the bot only with content you are permitted to download and process. Respect Instagram's terms, copyright, privacy, and the rights of content creators.

## ❤️ Credits

**Instagram Downloader Bot**

👨‍💻 Developer: `Anuj`

⭐ If you find the project useful, consider starring the repository.

---

### 🚀 Quick Start

```bash
git clone https://github.com/anuj9719168804-cyber/Ig.git
cd Ig
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python bot.py
```

**Made with ❤️ for Telegram & Instagram automation.**
