# ✨ NEXGEN Instagram Downloader Bot 💜

> 🚀 A powerful Telegram bot for downloading Instagram media with metadata, quality selection, captions, real-time progress, referral system, and professional UI.

## ✨ Features

### 📥 Download Features
- 🔗 Instagram link fetching
- 🎬 Video/Reel downloading
- 🖼️ Image/Photo downloading
- 📚 Carousel / multiple-media support
- 📊 Media metadata extraction
- 🎞️ Available quality selection (2x2 grid layout)
- ⚡ Best Quality option
- 🎵 Audio option where supported
- 📥 Real-time download progress
- 📤 Real-time Telegram upload progress
- 🚀 Speed, percentage and transferred-size display
- 📝 Professional media captions with blockquote styling
- 👤 Uploader information when available
- 👁️ Views / likes / comments when available
- ⏱️ Duration information when available
- 🔗 Source URL in the final caption
- 📦 Multiple-file progress/count support

### 🎁 Referral System
- 🎁 Referral Dashboard with progress tracking
- 🔗 Dynamic referral links (auto-detects bot username)
- 👥 Track referral count (0/2)
- 🎉 Rewards system (3 Days + 5 Days Premium)
- 📋 Copy referral link functionality
- 📊 Progress visualization with progress bar

### 💻 User Interface & Commands
- 🎬 Welcome message with photo thumbnail
- 📖 Professional help text
- ℹ️ About NEXGEN information (blockquote formatted)
- 🎁 Referral Dashboard
- 📋 Main menu with inline buttons
- 🎨 Colored button layout (Primary/Success/Danger)
- 📱 Mobile-friendly design
- ⏱️ 5-minute timeout for quality selections

### 🛠️ Technical Features
- 🛠️ Environment-variable configuration
- 📱 Termux compatible
- 🐍 Python based
- 🍪 Designed for public Instagram URLs without requiring cookies
- 🤖 Dynamic bot username detection
- 🔐 Referral parameter handling (?start=ref_)

### 📋 Available Commands
- `/start` - Welcome with photo
- `/help` - How to use guide
- `/about` - About NEXGEN information
- `/referral` - Referral dashboard
- `/menu` - Main menu without photo

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

## 🎨 User Interface & Menus

### Welcome Screen
- 📸 Photo thumbnail display
- 🎬 Personalized welcome message (uses user's first name)
- 📖 Quick access buttons:
  - 📖 How to use
  - ℹ️ About NEXGEN
  - 🎁 Refer & Earn
  - 📢 Updates
  - ❌ Close

### Referral Dashboard
```text
🎁 Referral Dashboard
━━━━━━━━━━━━━━━━━━

📊 Your Progress
🎯 Current Progress: 0/2
📈 Progress Bar: ⚪⚪
🌱 Total Referrals: 0
⚡ Need 2 more referral(s)

🎉 Your Rewards
[Rewards details...]

💡 How It Works
[4-step referral process]

🔗 Your Referral Link:
https://t.me/YourBotUsername?start=ref_123456789
```

### Meta Information Card
- 🎬 Title (bold)
- 👤 Creator/Uploader
- ⏱️ Duration
- 👁️ Views (when available)
- 🏷️ Category
- 📅 Upload date
- ✅ Available qualities list

## 🎞️ Quality Selection

When multiple video qualities are available, the bot presents options in a professional 2-column grid layout with metadata card.

Example:

```text
🎬 Video Title

👤 BY: channel_name
⏱️ DURATION: 53:07
👁️ VIEWS: 7,777
🏷️ CATEGORY: MUSIC
📅 UPLOADED: 2026-10-01

AVAILABLE QUALITIES:
✅ 1920p
✅ 1280p
✅ 960p
✅ 640p
🎵 MP3 (audio)

👇 TAP A QUALITY BELOW TO DOWNLOAD:
```

**Button Layout (2x2 Grid):**
```text
🎬 1920p    🎬 1280p
🎬 960p     🎬 640p
⚡ BEST QUALITY (full-width)
🎵 AUDIO ONLY (full-width)
❌ CANCEL (full-width)
```

Only qualities actually reported by the extractor are offered. Quality selections have a 5-minute timeout for security.

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

## 🔄 Dynamic Features

### Auto-Detecting Bot Username
The referral system automatically detects your bot's username at runtime:

```python
# Bot automatically fetches its own username
me = await client.get_me()
bot_username = me.username  # e.g., "NEXGEN_Bot"

# Referral links are generated dynamically
referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
```

This means:
- ✅ No hardcoding of bot username needed
- ✅ Works with any bot username
- ✅ Referral links always point to the correct bot
- ✅ Safe fallback to default username if detection fails

### Quality Selection Timeout
- ⏱️ 5-minute timeout for quality button selections
- 🔒 Security against stale quality buttons
- ⚠️ User gets notified when selection expires

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

## ℹ️ About NEXGEN

**NEXGEN Instagram Downloader** is a modern, feature-rich Telegram bot that combines powerful Instagram media downloading with an engaging user experience. Built with:

- ✨ Professional UI with blockquote styling
- 🎁 Referral system for user engagement
- 🎨 Responsive button layouts (2x2 grid)
- 🤖 Auto-detecting bot username
- 💜 NEXGEN branding throughout
- 🔐 Secure quality selection with timeout

## ❤️ Credits

**NEXGEN Instagram Downloader Bot**

👨‍💻 Developer: `Anuj`
🎨 Enhanced by: NEXGEN Team
💜 Branding & UI: NEXGEN v5.08.05

⭐ If you find the project useful, consider starring the repository.

---

### 📞 Support & Community

🍀 Support: @NexGen_SupportGC
⁉️ HelpDesk: @NexGenxHelpbot
💌 More Bots: @NexGen_BotList
🤖 Powered by: @NexGen_Bots

---

### 🚀 Quick Start

```bash
git clone https://github.com/anuj9719168804-cyber/Ig.git
cd Ig
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your credentials
export API_ID="YOUR_API_ID"
export API_HASH="YOUR_API_HASH"
export BOT_TOKEN="YOUR_BOT_TOKEN"

python bot.py
```

### 🎯 First Steps After Deploying

1. **Start the bot**: Send `/start` to see the welcome screen
2. **Learn how to use**: Send `/help` for instructions
3. **Share referral link**: Send `/referral` to get your referral dashboard
4. **Invite friends**: Use your dynamic referral link to earn rewards
5. **Download media**: Send any Instagram link to the bot

---

**Made with 💜 for Telegram & Instagram automation by NEXGEN.**
