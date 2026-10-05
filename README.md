# Instagram Downloader Bot

Public Instagram posts, reels, photos aur carousels download karke Telegram par bhejta hai.

## Setup
1. `pip install -r requirements.txt`
2. `.env.example` ko `.env` naam se copy karo aur API_ID, API_HASH, BOT_TOKEN bharo.
3. `python bot.py`

## Kaise kaam karta hai
- Pehle post page + `/embed/captioned/` page se direct media URLs nikalta hai (carousel ke photo/video alag-alag).
- Fail ho to `yt-dlp` fallback.
- Carousel album ke roop mein (10-10 ke group) bhejta hai; temp files bhejne ke baad delete.

## Notes
- Posts / reels / IGTV / carousels / `/share/` links / profile picture: cookies ke bina chalte hain.
- Stories/Highlights: Instagram login maangta hai, isliye bot owner ek baar server par `cookies.txt` (Netscape format) rakhta hai aur `.env` mein `INSTA_COOKIES=path/to/cookies.txt` set karta hai. Users ko kuch nahi karna padta. Alag (dummy) account use karo, apna main nahi.
- Profile link (`instagram.com/username`) bhejne par HD profile picture milti hai (best-effort, Instagram kabhi block kar sakta hai).
- Instagram Live ka replay post/reel/IGTV ban jaata hai - wo link normal tarah se chalta hai. Chalti hui live download nahi hoti.
- Instagram anti-bot rules badalta rehta hai; login wall aaye to wo post download nahi hogi.
- Sirf wahi content download karo jiska aapko haq/permission ho.
