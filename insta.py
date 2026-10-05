"""Instagram media extraction + download helpers (public posts / reels / carousels)."""
import glob
import os
import re
import time
from urllib.parse import unquote

import requests

INSTA_RE = re.compile(
    r"https?://(?:www\.)?(?:instagram\.com|instagr\.am)/(?:[A-Za-z0-9_.]+/)?"
    r"(?:p|reel|reels|tv)/([A-Za-z0-9_-]+)[^\s]*",
    re.IGNORECASE,
)

SHARE_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/share/(?:(?:p|reel|tv)/)?([A-Za-z0-9_-]+)[^\s]*",
    re.IGNORECASE,
)
STORY_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/"
    r"(?:stories/(?:highlights/\d+|[A-Za-z0-9_.]+(?:/\d+)?)|s/[A-Za-z0-9_=-]+"
    r"|[A-Za-z0-9_.]+/?\?[^\s]*stkn=[^\s]*)[^\s]*",
    re.IGNORECASE,
)

PROFILE_RE = re.compile(
    r"https?://(?:www\.)?instagram\.com/([A-Za-z0-9_.]{1,30})/?(?:\?[^\s]*)?",
    re.IGNORECASE,
)
RESERVED_PATHS = {"p", "reel", "reels", "tv", "stories", "explore", "share", "s",
                  "accounts", "direct", "about", "legal", "developer"}

FETCH_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}

VIDEO_URL_RE = re.compile(r'"video_url":"([^"]+)"')
OG_VIDEO_RE = re.compile(r'<meta property="og:video(?::secure_url)?" content="([^"]+)"', re.I)
OG_IMAGE_RE = re.compile(r'<meta property="og:image" content="([^"]+)"', re.I)


def find_insta_link(text: str):
    """Returns (url, shortcode_or_id) or (None, None). Handles post/reel/tv, share, story, highlight."""
    text = text or ""
    m = SHARE_RE.search(text)  # must come first: /share/reel/XYZ would also match INSTA_RE
    if m:
        return m.group(0), m.group(1)
    m = STORY_RE.search(text)
    if m:
        last = m.group(0).rstrip("/").split("?")[0].split("/")[-1]
        return m.group(0), re.sub(r"\W+", "_", last) or "story"
    m = INSTA_RE.search(text)
    if m:
        return m.group(0), m.group(1)
    for tok in text.split():  # profile link -> profile picture
        pm = PROFILE_RE.fullmatch(tok)
        if pm and pm.group(1).lower() not in RESERVED_PATHS:
            return pm.group(0), pm.group(1)
    return None, None


def is_profile_url(url: str) -> bool:
    pm = PROFILE_RE.fullmatch(url or "")
    return bool(pm) and pm.group(1).lower() not in RESERVED_PATHS


def fetch_profile_pic(username: str) -> str:
    """Returns direct URL of the (HD) profile picture. Raises ValueError."""
    headers = dict(FETCH_HEADERS)
    headers.update({"Accept": "*/*", "X-IG-App-ID": "936619743392459"})
    try:
        r = requests.get(
            "https://i.instagram.com/api/v1/users/web_profile_info/",
            params={"username": username}, headers=headers, timeout=30,
        )
        if r.ok:
            u = r.json()["data"]["user"]
            pic = u.get("profile_pic_url_hd") or u.get("profile_pic_url")
            if pic:
                return _unescape(pic)
    except Exception:
        pass
    try:  # fallback: og:image of the profile page
        r = requests.get(f"https://www.instagram.com/{username}/", headers=FETCH_HEADERS, timeout=30)
        im = OG_IMAGE_RE.search(r.text)
        if im:
            return _unescape(im.group(1))
    except Exception:
        pass
    raise ValueError("Profile picture nahi mili (account exist nahi karta ya Instagram ne block kiya).")


def story_url_from(url: str) -> str:
    """Profile link with ?stkn=... (shared story) -> standard stories URL."""
    if "stkn=" in url:
        pm = PROFILE_RE.match(url)
        if pm:
            return f"https://www.instagram.com/stories/{pm.group(1)}/"
    return url


def is_share_url(url: str) -> bool:
    return bool(SHARE_RE.match(url or ""))


def is_story_url(url: str) -> bool:
    return bool(STORY_RE.match(url or ""))


def resolve_share(url: str):
    """Follow a /share/ link to the real post/reel URL. Returns (url, shortcode) or None."""
    try:
        r = requests.get(url, headers=FETCH_HEADERS, allow_redirects=True, timeout=30)
    except Exception:
        return None
    m = INSTA_RE.search(unquote(r.url))
    return (m.group(0), m.group(1)) if m else None


def _unescape(u: str) -> str:
    return u.replace("\\u0026", "&").replace("\\/", "/").replace("&amp;", "&")


def _match_brace(s: str, i: int) -> int:
    depth = 0
    for k in range(i, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                return k
    return -1


def _carousel_items(html: str):
    idx = html.find('"edge_sidecar_to_children"')
    if idx == -1:
        return None
    e = html.find('"edges"', idx)
    a = html.find("[", e) if e != -1 else -1
    if a == -1:
        return None
    depth, end = 0, -1
    for k in range(a, len(html)):
        if html[k] == "[":
            depth += 1
        elif html[k] == "]":
            depth -= 1
            if depth == 0:
                end = k
                break
    if end == -1:
        return None
    blob = html[a:end + 1]
    items = []
    for nm in re.finditer(r'\{"node":\{', blob):
        s = nm.end() - 1
        t = _match_brace(blob, s)
        if t == -1:
            continue
        node = blob[s:t + 1]
        if '"is_video":true' in node:
            vm = re.search(r'"video_url":"([^"]+)"', node)
            if vm:
                items.append(("video", _unescape(vm.group(1))))
        else:
            dm = re.search(r'"display_url":"([^"]+)"', node)
            if dm:
                items.append(("photo", _unescape(dm.group(1))))
    return items or None


def _media_from_html(html: str):
    items = _carousel_items(html)
    if items:
        return items
    vm = VIDEO_URL_RE.search(html) or OG_VIDEO_RE.search(html)
    if vm:
        return [("video", _unescape(vm.group(1)))]
    im = OG_IMAGE_RE.search(html)
    if im:
        return [("photo", _unescape(im.group(1)))]
    return []


def extract_media(url: str, shortcode: str):
    """Returns [('video'|'photo', direct_url), ...]. Raises ValueError if nothing found."""
    try:
        r = requests.get(url, headers=FETCH_HEADERS, timeout=30)
        items = _media_from_html(r.text)
    except Exception as e:
        raise ValueError(f"Page fetch failed: {e}")

    if not items:
        # Embed page often still works for PUBLIC posts when the main page is login-walled.
        try:
            er = requests.get(
                f"https://www.instagram.com/p/{shortcode}/embed/captioned/",
                headers=FETCH_HEADERS, timeout=30,
            )
            items = _media_from_html(er.text)
        except Exception:
            pass

    if not items:
        raise ValueError("No media found (private post, or Instagram showed a login wall).")
    return items


def download_file(url: str, dest: str, progress_callback=None):
    """Returns (ok, error). Rejects HTML error pages saved as media.

    progress_callback(current_bytes, total_bytes, speed, eta) is optional (called from this thread).
    """
    try:
        r = requests.get(url, headers=FETCH_HEADERS, stream=True, timeout=60)
        r.raise_for_status()
    except Exception as e:
        return False, f"Request failed: {e}"

    if "text/html" in r.headers.get("Content-Type", "").lower():
        return False, "Got an HTML page instead of media (link expired / login wall)."

    written = 0
    try:
        total = int(r.headers.get("Content-Length") or 0)
    except ValueError:
        total = 0
    t0 = time.monotonic()
    try:
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=256 * 1024):
                if chunk:
                    f.write(chunk)
                    written += len(chunk)
                    if progress_callback:
                        el = max(time.monotonic() - t0, 0.1)
                        sp = written / el
                        progress_callback(written, total, sp, ((total - written) / sp) if total and sp else 0)
    except Exception as e:
        return False, f"Download interrupted: {e}"

    if written < 10 * 1024:
        try:
            os.remove(dest)
        except OSError:
            pass
        return False, f"File too small ({written} bytes) - probably an error page."
    return True, ""


def ytdlp_fallback(url: str, outdir: str, cookies_path=None):
    """Fallback: let yt-dlp try. Returns list of downloaded file paths."""
    import yt_dlp

    opts = {
        "outtmpl": os.path.join(outdir, "%(id)s_%(autonumber)s.%(ext)s"),
        "format": "best[ext=mp4]/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
    }
    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
    return sorted(glob.glob(os.path.join(outdir, "*")))


def fetch_info(url: str, cookies_path=None):
    """Fetch Instagram video metadata and available video heights using yt-dlp."""
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def available_qualities(info: dict):
    heights = set()
    for f in info.get("formats") or []:
        h = f.get("height")
        if h and f.get("vcodec") not in (None, "none"):
            try:
                heights.add(int(h))
            except Exception:
                pass
    # Keep useful Telegram-friendly choices and sort highest first.
    return sorted(heights, reverse=True)[:8]


def download_quality(url: str, outdir: str, quality="best", cookies_path=None, progress_callback=None):
    """Download a selected Instagram video quality with yt-dlp."""
    import yt_dlp

    if quality == "audio":
        fmt = "bestaudio/best"
    elif quality == "best":
        fmt = "best[ext=mp4]/best"
    else:
        q = int(quality)
        fmt = f"best[height<={q}][ext=mp4]/best[height<={q}]/best"

    opts = {
        "outtmpl": os.path.join(outdir, "%(id)s.%(ext)s"),
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [],
    }
    if cookies_path and os.path.exists(cookies_path):
        opts["cookiefile"] = cookies_path

    if progress_callback:
        def hook(d):
            if d.get("status") == "downloading":
                cur = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                progress_callback(cur, total, d.get("speed") or 0, d.get("eta") or 0)
        opts["progress_hooks"].append(hook)

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    candidates = []
    for p in glob.glob(os.path.join(outdir, "*")):
        if os.path.isfile(p) and os.path.getsize(p) > 10 * 1024:
            candidates.append(p)
    if not candidates:
        return None
    return max(candidates, key=os.path.getsize)
