import json
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import quote_plus, unquote, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/120.0"
    )
}

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()
YT_API_ENABLED = bool(YOUTUBE_API_KEY)
if not YT_API_ENABLED:
    print("[WARN] YOUTUBE_API_KEY is not set; 'Views Last 30 Days' will be empty for all channels.")

SEARCH_QUERIES: List[str] = [
    "авто",
    "автомобиль",
    "автомобили",
    "машины",
    "автоканал",
    "авто канал",
    "автоблог",
    "авто блог",
    "автомобильный блог",
    "автошоу",
    "авто шоу",

    # Обзоры и тест-драйвы
    "обзор авто",
    "обзоры авто",
    "обзор автомобиля",
    "обзоры автомобилей",
    "автообзор",
    "авто обзоры",
    "тест драйв",
    "тест-драйв",
    "тест драйв авто",
    "тест-драйв автомобиля",
    "тест-драйв новых автомобилей",
    "новые авто обзор",
    "обзор новых автомобилей",
    "обзор подержанных авто",
    "обзор б/у авто",
    "обзор бюджетных авто",
    "обзор китайских авто",
    "китайские авто обзор",
    "китайские автомобили обзор",
    "обзор корейских авто",
    "обзор немецких авто",
    "обзор японских авто",
    "обзор электромобилей",

    # Покупка, продажа, подбор
    "автоподбор",
    "подбор авто",
    "подбор автомобиля",
    "подбор б/у авто",
    "автоподбор россия",
    "автоподбор москва",
    "автоподбор спб",
    "автоподбор питер",
    "автоподбор екатеринбург",
    "автоподбор новосибирск",
    "автоподбор казахстан",
    "автоподбор алматы",
    "авто рынок",
    "рынок б/у авто",
    "авто из японии",
    "авто из кореи",
    "авто из китая",
    "авто из европы",

    # Ремонт, сервис, DIY
    "ремонт авто",
    "ремонт автомобиля",
    "ремонт машины",
    "автосервис",
    "автосервис канал",
    "гараж ремонт авто",
    "ремонт авто своими руками",
    "машина своими руками",
    "авто своими руками",
    "авто лайфхаки",
    "диагностика авто",
    "авто диагностика",
    "автоэлектрика",
    "авто электрика",
    "кузовной ремонт",
    "покраска авто",
    "покраска автомобиля",
    "рихтовка авто",
    "переборка двигателя",
    "ремонт двигателя авто",
    "ремонт подвески",
    "ремонт коробки передач",
    "автослесарь",

    # Тюнинг, стайлинг, спорт
    "тюнинг авто",
    "авто тюнинг",
    "тюнинг автомобилей",
    "стайлинг авто",
    "автозвук",
    "авто звук",
    "чип тюнинг",
    "дрифт",
    "drift авто",
    "дрифт машины",
    "drag racing",
    "гонки авто",
    "street racing",
    "stance авто",
    "стенс авто",
    "offroad 4x4",
    "внедорожник оффроуд",
    "джип трофи",
    "ралли авто",
    "автоспорт",

    # Конкретные бренды (обзоры, тест-драйвы)
    "обзор ваз",
    "обзор lada",
    "обзор лада",
    "обзор гранта",
    "обзор лада веста",
    "обзор уаз",
    "обзор bmw",
    "обзор mercedes",
    "обзор mercedes-benz",
    "обзор audi",
    "обзор volkswagen",
    "обзор vw",
    "обзор skoda",
    "обзор toyota",
    "обзор nissan",
    "обзор honda",
    "обзор mazda",
    "обзор kia",
    "обзор hyundai",
    "обзор renault",
    "обзор peugeot",
    "обзор citroen",
    "обзор porsche",
    "обзор tesla",

    # Региональные/гео-запросы
    "авто москва",
    "авто спб",
    "авто питер",
    "авто ростов",
    "авто краснодар",
    "авто екатеринбург",
    "авто новосибирск",
    "авто казахстан",
    "авто алматы",
    "авто астана",
    "авто минск",
    "авто киев",
    "авто одесса",

    # Лайфстайл и автожизнь
    "жизнь с авто",
    "авто путешествия",
    "дальняк на машине",
    "жизнь в тачке",
    "авто будни",
    "такси на личном авто",
    "жизнь таксиста",
    "грузовики блог",
    "грузовой авто блог",
]

# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------


def sleep_briefly() -> None:
    """Pause a short time between network calls."""
    time.sleep(random.uniform(1.0, 2.0))


def fetch_html(url: str) -> Optional[str]:
    """GET a URL and return HTML text; log and return None on failure."""
    try:
        print(f"[GET] {url}")
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        print(f"[WARN] Request failed for {url}: {exc}")
        return None
    finally:
        sleep_briefly()


def extract_ytinitialdata(html: str) -> Optional[Dict[str, Any]]:
    """Extract ytInitialData JSON from HTML."""
    patterns = [
        r'ytInitialData"\s*:\s*({.*?})\s*;',
        r"var ytInitialData\s*=\s*({.*?});",
        r"ytInitialData\s*=\s*({.*?});",
        r'window\["ytInitialData"\]\s*=\s*({.*?});',
    ]
    for pat in patterns:
        m = re.search(pat, html, re.S)
        if not m:
            continue
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
    return None


def text_from_runs(obj: Any) -> str:
    """Extract text from YouTube's simpleText/runs formats."""
    if not obj:
        return ""
    if isinstance(obj, dict):
        if "simpleText" in obj:
            return obj.get("simpleText", "")
        if "runs" in obj and obj.get("runs"):
            return "".join(run.get("text", "") for run in obj["runs"])
    return ""


def walk_for_key(node: Any, key: str) -> Iterable[Any]:
    """Yield values for all occurrences of key in nested structures."""
    if isinstance(node, dict):
        if key in node:
            yield node[key]
        for v in node.values():
            yield from walk_for_key(v, key)
    elif isinstance(node, list):
        for item in node:
            yield from walk_for_key(item, key)


# ------------------------------------------------------------
# Search helpers
# ------------------------------------------------------------


def iter_channel_renderers(data: Any) -> Iterable[Dict[str, Any]]:
    """Yield channelRenderer objects from ytInitialData."""
    if isinstance(data, dict):
        if "channelRenderer" in data:
            yield data["channelRenderer"]
        for v in data.values():
            yield from iter_channel_renderers(v)
    elif isinstance(data, list):
        for item in data:
            yield from iter_channel_renderers(item)


def channel_url_from_renderer(renderer: Dict[str, Any]) -> Optional[str]:
    """Construct channel URL from channelRenderer."""
    endpoint = renderer.get("navigationEndpoint", {}).get("browseEndpoint", {})
    canonical = endpoint.get("canonicalBaseUrl")
    browse_id = endpoint.get("browseId")
    if canonical:
        return f"https://www.youtube.com{canonical}"
    if browse_id:
        return f"https://www.youtube.com/channel/{browse_id}"
    return None


def search_channels(query: str) -> Set[str]:
    """Search YouTube for channels for a given query."""
    url = f"https://www.youtube.com/results?search_query={quote_plus(query)}&sp=EgIQAg%253D%253D"
    html = fetch_html(url)
    if not html:
        return set()
    data = extract_ytinitialdata(html)
    if not data:
        print(f"[WARN] ytInitialData missing for search query {query!r}")
        return set()
    channels: Set[str] = set()
    for renderer in iter_channel_renderers(data):
        ch_url = channel_url_from_renderer(renderer)
        if ch_url:
            channels.add(ch_url)
    print(f"[INFO] Found {len(channels)} channels for query {query!r}")
    return channels

# ------------------------------------------------------------
# Parsing helpers
# ------------------------------------------------------------


def clean_subscriber_text(raw_text: str) -> str:
    """Normalize subscriber count text, keep numeric + unit."""
    if not raw_text:
        return ""
    t = raw_text.lower().replace("\xa0", " ").replace(",", ".")
    t = re.sub(r"подпис\w+", "", t)
    t = t.replace("subscribers", "").replace("subscriber", "").replace("жазылушы", "")
    t = t.replace(" ", "")
    multiplier = ""
    if re.search(r"(млн\.?|million|mln|\bm\b|\bм\b)", t):
        multiplier = "млн"
        t = re.sub(r"(млн\.?|million|mln|\bm\b|\bм\b)", "", t)
    elif re.search(r"(тыс\.?|тысяч|k|\bк\b|мың|\bk\b)", t):
        multiplier = "тыс."
        t = re.sub(r"(тыс\.?|тысяч|k|\bк\b|мың|\bk\b)", "", t)
    num_match = re.search(r"([\d.]+)", t)
    if not num_match:
        return ""
    num = num_match.group(1).strip(".")
    return f"{num} {multiplier}".strip() if multiplier else num


def first_email_in_text(text: str) -> str:
    """Return first email in text if present."""
    if not text:
        return ""
    emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return emails[0] if emails else ""


def extract_links_from_json(data: Any) -> List[str]:
    """Collect URL-like strings from ytInitialData."""
    links: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("url", "href"):
                if isinstance(node.get(key), str):
                    links.append(node[key])
            if "navigationEndpoint" in node:
                url_ep = node["navigationEndpoint"].get("urlEndpoint", {}).get("url")
                if isinstance(url_ep, str):
                    links.append(url_ep)
            if "webCommandMetadata" in node and isinstance(node.get("webCommandMetadata"), dict):
                meta = node["webCommandMetadata"]
                if isinstance(meta.get("url"), str):
                    links.append(meta["url"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return links


def extract_external_links(soup: BeautifulSoup, data: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Return first Telegram/Website/social links from both HTML and JSON."""
    telegram_link = ""
    website_link = ""
    instagram_link = ""
    vk_link = ""
    facebook_link = ""

    link_candidates: List[str] = []
    for a in soup.find_all("a", href=True):
        link_candidates.append(a["href"])
    if isinstance(data, dict):
        link_candidates.extend(extract_links_from_json(data))
        meta_links = (
            data.get("metadata", {})
            .get("channelMetadataRenderer", {})
            .get("externalLinks", [])
        )
        if isinstance(meta_links, list):
            for el in meta_links:
                if isinstance(el, dict):
                    for key in ("url", "href"):
                        if isinstance(el.get(key), str):
                            link_candidates.append(el[key])

    bad_domains = (
        "youtube.com",
        "youtu.be",
        "ytimg.com",
        "googlevideo.com",
        "gstatic.com",
        "developers.google.com",
        "googleusercontent.com",
        "ggpht.com",
        "yt3.ggpht.com",
        "yt3.googleusercontent.com",
    )

    def is_bad(link: str) -> bool:
        low = link.lower()
        return any(dom in low for dom in bad_domains) or "google.com/url" in low

    for href in link_candidates:
        if not isinstance(href, str) or not href:
            continue
        if href.startswith("//"):
            href = "https:" + href
        low = href.lower()
        if "youtube.com/redirect" in low or "youtube.com/attribution_link" in low:
            try:
                q = urlparse(href).query
                params = dict([kv.split("=", 1) for kv in q.split("&") if "=" in kv])
                real = params.get("q")
                if real:
                    href = unquote(real)
                    low = href.lower()
            except Exception:
                pass
        if is_bad(href):
            continue

        if not telegram_link and ("t.me" in low or "telegram.me" in low or "telegram.org" in low):
            telegram_link = href
            continue
        if not instagram_link and "instagram.com" in low:
            instagram_link = href
            continue
        if not vk_link and "vk.com" in low:
            vk_link = href
            continue
        if not facebook_link and ("facebook.com" in low or "fb.com" in low):
            facebook_link = href
            continue
        if (
            href.startswith("http")
            and not website_link
            and "t.me" not in low
            and "telegram.me" not in low
            and "telegram.org" not in low
            and "instagram.com" not in low
            and "vk.com" not in low
            and "facebook.com" not in low
            and "fb.com" not in low
            and not is_bad(href)
        ):
            website_link = href

    return {
        "Telegram": telegram_link or "",
        "Website": website_link or "",
        "Instagram": instagram_link or "",
        "VK": vk_link or "",
        "Facebook": facebook_link or "",
    }


def parse_about_page(channel_url: str) -> Dict[str, str]:
    """Parse a channel's About page to collect metadata."""
    url = channel_url.rstrip("/") + "/about"
    html = fetch_html(url)
    if not html:
        return {
            "Channel URL": channel_url,
            "Name": "",
            "Subscribers": "",
            "Description": "",
            "Email": "",
            "Telegram": "",
            "Website": "",
            "Instagram": "",
            "VK": "",
            "Facebook": "",
        }

    soup = BeautifulSoup(html, "html.parser")
    data = extract_ytinitialdata(html)

    title_meta = soup.find("meta", {"property": "og:title"})
    name = title_meta.get("content", "") if title_meta else ""
    if not name and isinstance(data, dict):
        name = (
            data.get("metadata", {})
            .get("channelMetadataRenderer", {})
            .get("title", "")
        ) or (
            data.get("header", {})
            .get("c4TabbedHeaderRenderer", {})
            .get("title", "")
        )

    desc_meta = soup.find("meta", {"name": "description"})
    description = desc_meta.get("content", "") if desc_meta else ""
    if not description and isinstance(data, dict):
        description = (
            data.get("metadata", {})
            .get("channelMetadataRenderer", {})
            .get("description", "")
        )
    if not description and isinstance(data, dict):
        description = (
            data.get("microformat", {})
            .get("microformatDataRenderer", {})
            .get("description", "")
        )

    subscribers = ""
    if isinstance(data, dict):
        subs_candidates = []
        meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
        header = data.get("header", {}).get("c4TabbedHeaderRenderer", {})
        page_header = (
            data.get("header", {})
            .get("pageHeaderRenderer", {})
            .get("content", {})
            .get("pageHeaderViewModel", {})
            .get("metadata", {})
            .get("contentMetadataViewModel", {})
        )
        micro = data.get("microformat", {}).get("microformatDataRenderer", {})
        for cand in (
            header.get("subscriberCountText") if isinstance(header, dict) else None,
            page_header.get("subscriberCountText") if isinstance(page_header, dict) else None,
            meta.get("subscriberCountText") if isinstance(meta, dict) else None,
            micro.get("subscriberCountText") if isinstance(micro, dict) else None,
        ):
            if cand:
                subs_candidates.append(cand)
        subs_candidates.extend(list(walk_for_key(data, "subscriberCountText")))
        for cand in subs_candidates:
            subs_text = cand if isinstance(cand, str) else text_from_runs(cand)
            if subs_text:
                subscribers = clean_subscriber_text(subs_text)
                break

    combined_text = " ".join(
        [
            description or "",
            soup.get_text(" ", strip=True),
            json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else "",
        ]
    )
    email = first_email_in_text(combined_text)
    links = extract_external_links(soup, data if isinstance(data, dict) else None)

    return {
        "Channel URL": channel_url,
        "Name": name,
        "Subscribers": subscribers,
        "Description": description,
        "Email": email,
        "Telegram": links["Telegram"],
        "Website": links["Website"],
        "Instagram": links.get("Instagram", ""),
        "VK": links.get("VK", ""),
        "Facebook": links.get("Facebook", ""),
    }


# ------------------------------------------------------------
# YouTube Data API helpers
# ------------------------------------------------------------


def yt_api_get(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Minimal YouTube Data API GET wrapper."""
    if not YT_API_ENABLED:
        return {}
    try:
        base = f"https://www.googleapis.com/youtube/v3/{endpoint}"
        params = dict(params)
        params["key"] = YOUTUBE_API_KEY
        resp = requests.get(base, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            print(f"[WARN] YouTube API {endpoint} returned non-dict response")
            return {}
        if "error" in data:
            print(f"[WARN] YouTube API {endpoint} returned error: {data.get('error')}")
        return data
    except Exception as exc:
        print(f"[WARN] YouTube API {endpoint} request failed: {exc}")
        return {}


def resolve_channel_id(channel_url: str) -> Optional[str]:
    """Resolve UC channelId from URL using API when possible, else HTML fallback."""
    try:
        def _items(obj: Any) -> List[Any]:
            if not isinstance(obj, dict):
                return []
            val = obj.get("items", [])
            return val if isinstance(val, list) else []

        def _first_channel_id_from_items(items: List[Any]) -> Optional[str]:
            for item in items:
                if not isinstance(item, dict):
                    continue
                cid = item.get("id", {}).get("channelId") if isinstance(item.get("id"), dict) else None
                if not cid and "channelId" in item and isinstance(item["channelId"], str):
                    cid = item["channelId"]
                if cid and isinstance(cid, str) and cid.startswith("UC"):
                    return cid
            return None

        parsed = urlparse(channel_url)
        path = parsed.path or ""

        # Step 1: explicit /channel/UC...
        m = re.search(r"/channel/([A-Za-z0-9_-]+)", path)
        if m and m.group(1).startswith("UC"):
            return m.group(1)

        # Step 2: handle-based via API
        handle_match = re.search(r"/@([^/?#]+)", path)
        if handle_match and YT_API_ENABLED:
            handle = unquote(handle_match.group(1))
            for candidate in (handle, f"@{handle}"):
                data = yt_api_get(
                    "channels",
                    {
                        "part": "id",
                        "forHandle": candidate,
                    },
                )
                cid = _first_channel_id_from_items(_items(data))
                if cid:
                    return cid

        # Step 3: legacy /user/<name>
        user_match = re.search(r"/user/([^/?#]+)", path)
        if user_match and YT_API_ENABLED:
            username = unquote(user_match.group(1))
            data = yt_api_get(
                "channels",
                {
                    "part": "id",
                    "forUsername": username,
                },
            )
            cid = _first_channel_id_from_items(_items(data))
            if cid:
                return cid

        # Step 4: custom /c/<name> via search
        custom_match = re.search(r"/c/([^/?#]+)", path)
        if custom_match and YT_API_ENABLED:
            query = unquote(custom_match.group(1))
            data = yt_api_get(
                "search",
                {
                    "part": "id",
                    "type": "channel",
                    "q": query,
                    "maxResults": 3,
                },
            )
            cid = _first_channel_id_from_items(_items(data))
            if cid:
                return cid

        # Step 5: HTML fallback (main and about)
        for candidate_url in (channel_url, channel_url.rstrip("/") + "/about"):
            html = fetch_html(candidate_url)
            if not html:
                continue
            data = extract_ytinitialdata(html)
            meta = (
                data.get("metadata", {}).get("channelMetadataRenderer", {})
                if isinstance(data, dict)
                else {}
            )
            if isinstance(meta, dict):
                ext_id = meta.get("externalId")
                if isinstance(ext_id, str) and ext_id.startswith("UC"):
                    return ext_id
                chan_url = meta.get("channelUrl")
                if isinstance(chan_url, str):
                    m = re.search(r"/channel/(UC[\w-]+)", chan_url)
                    if m:
                        return m.group(1)
            if isinstance(data, dict):
                for value in walk_for_key(data, "externalId"):
                    if isinstance(value, str) and value.startswith("UC"):
                        return value
                for value in walk_for_key(data, "channelId"):
                    if isinstance(value, str) and value.startswith("UC"):
                        return value

            m = re.search(r'"externalId":"(UC[\w-]+)"', html)
            if m:
                return m.group(1)
            m = re.search(r'"channelId":"(UC[\w-]+)"', html)
            if m:
                return m.group(1)

    except Exception as exc:
        print(f"[WARN] Could not resolve channelId for {channel_url}: {exc}")
        return None

    print(f"[WARN] No channelId for {channel_url}, cannot get 30-day views.")
    return None


def get_views_last_30_days_api(channel_url: str) -> str:
    """Fetch 30-day views via YouTube Data API; return '' on failure."""
    if not YT_API_ENABLED:
        return ""
    channel_id = resolve_channel_id(channel_url)
    if not channel_id:
        return ""

    def _items(obj: Any) -> List[Any]:
        if not isinstance(obj, dict):
            return []
        val = obj.get("items", [])
        return val if isinstance(val, list) else []

    published_after = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    video_ids: List[str] = []
    page_token = None
    attempts = 0
    while attempts < 3:
        params = {
            "part": "id",
            "channelId": channel_id,
            "publishedAfter": published_after,
            "type": "video",
            "order": "date",
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        data = yt_api_get("search", params)
        if not isinstance(data, dict):
            break
        items = _items(data)
        for item in items:
            if not isinstance(item, dict):
                continue
            vid = item.get("id", {}).get("videoId")
            if vid:
                video_ids.append(vid)
        page_token = data.get("nextPageToken")
        attempts += 1
        if not page_token or len(video_ids) >= 100:
            break

    if not video_ids:
        print(f"[INFO] No recent videos (30d) for {channel_url}")
        return ""

    total_views = 0
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        stats = yt_api_get(
            "videos",
            {
                "part": "statistics",
                "id": ",".join(batch),
            },
        )
        if not isinstance(stats, dict):
            continue
        for item in _items(stats):
            if not isinstance(item, dict):
                continue
            vc = item.get("statistics", {}).get("viewCount")
            if vc:
                try:
                    total_views += int(vc)
                except ValueError:
                    continue

    return str(total_views) if total_views > 0 else ""


def views_last_30_days(channel_url: str, max_videos: int = 120) -> str:
    """Return total views for last ~30 days (API only)."""
    if not YT_API_ENABLED:
        return ""
    return get_views_last_30_days_api(channel_url)


# ------------------------------------------------------------
# Video recency helpers (used only in HTML fallback if ever needed)
# ------------------------------------------------------------


def is_within_30_days(published_text: str) -> bool:
    """Check if published text is within ~30 days."""
    if not published_text:
        return False
    t = published_text.lower()
    if any(word in t for word in ["year", "years", "год", "лет"]):
        return False
    if "только что" in t or "just now" in t:
        return True
    if any(word in t for word in ["мин", "минут", "сек", "секунд", "minute", "minutes", "min", "sec", "hour", "hours", "час"]):
        return True
    num_match = re.search(r"(\d+)", t)
    num = int(num_match.group(1)) if num_match else 0
    if any(word in t for word in ["день", "дня", "дней", "day", "days", "дн"]):
        return 0 < num <= 30
    if "недел" in t or "week" in t:
        return 0 < num <= 4
    if "месяц" in t or "месяца" in t or "месяцев" in t or "month" in t or "months" in t:
        return 0 < num <= 1
    return False


def parse_view_count(view_text: str) -> Optional[int]:
    """Parse a view count text into an integer, handling тыс/млн."""
    if not view_text:
        return None
    text = view_text.replace("\xa0", " ").lower().strip()
    for word in ["просмотров", "просмотра", "просмотры", "просмотр", "views", "view", "қаралым"]:
        text = text.replace(word, "")
    m = re.search(r"([\d\s.,]+)", text)
    if not m:
        return None
    num_str = m.group(1).replace(" ", "").replace(",", ".")
    multiplier = 1
    if re.search(r"(млн|million|mln|\bm\b|\bм\b)", text):
        multiplier = 1_000_000
    elif re.search(r"(тыс|тысяч|\bk\b|\bк\b|мың)", text):
        multiplier = 1_000
    try:
        value = float(num_str) if "." in num_str else int(num_str)
        return int(value * multiplier)
    except ValueError:
        return None


# ------------------------------------------------------------
# Video renderer iterator (used if ever needed)
# ------------------------------------------------------------


def iter_video_renderers(data: Any) -> Iterable[Dict[str, Any]]:
    """Yield video renderer shapes from ytInitialData."""
    if isinstance(data, dict):
        if "gridVideoRenderer" in data:
            yield data["gridVideoRenderer"]
        if "videoRenderer" in data:
            yield data["videoRenderer"]
        if "compactVideoRenderer" in data:
            yield data["compactVideoRenderer"]
        if "richItemRenderer" in data:
            content = data["richItemRenderer"].get("content", {})
            if isinstance(content, dict) and "videoRenderer" in content:
                yield content["videoRenderer"]
        if "reelItemRenderer" in data:
            reel = data["reelItemRenderer"]
            if isinstance(reel, dict) and "videoRenderer" in reel:
                yield reel["videoRenderer"]
        if "richGridRenderer" in data:
            contents = data["richGridRenderer"].get("contents", [])
            if isinstance(contents, list):
                for item in contents:
                    if isinstance(item, dict):
                        rich = item.get("richItemRenderer", {})
                        if isinstance(rich, dict):
                            content = rich.get("content", {})
                            if isinstance(content, dict) and "videoRenderer" in content:
                                yield content["videoRenderer"]
        for v in data.values():
            yield from iter_video_renderers(v)
    elif isinstance(data, list):
        for item in data:
            yield from iter_video_renderers(item)


# ------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------


def collect_all_channels() -> Set[str]:
    """Run searches across all queries and return deduplicated channel URLs."""
    all_channels: Set[str] = set()
    for query in SEARCH_QUERIES:
        print(f"\n=== Searching for query: {query!r} ===")
        found = search_channels(query)
        before = len(all_channels)
        all_channels.update(found)
        after = len(all_channels)
        print(f"[INFO] Total unique channels so far: {after} (+{after - before})")
    return all_channels


def process_channels(channels: Set[str]) -> List[Dict[str, str]]:
    """Fetch metadata for each channel and prepare rows for export."""
    rows: List[Dict[str, str]] = []
    total = len(channels)
    for idx, channel_url in enumerate(sorted(channels), start=1):
        print(f"\n[{idx}/{total}] Processing channel: {channel_url}")
        try:
            about_info = parse_about_page(channel_url)
            about_info["Views Last 30 Days"] = views_last_30_days(channel_url)
            rows.append(about_info)
        except Exception as exc:
            print(f"[WARN] Skipping {channel_url} due to error: {exc}")
    return rows


def export_results(rows: List[Dict[str, str]]) -> None:
    """Write collected data to CSV and Excel files."""
    if not rows:
        print("[WARN] No data collected; nothing to export.")
        return

    csv_filename = "channels_auto_ru.csv"
    xlsx_filename = "channels_auto_ru.xlsx"

    df = pd.DataFrame(rows)[
        [
            "Channel URL",
            "Name",
            "Subscribers",
            "Views Last 30 Days",
            "Description",
            "Email",
            "Telegram",
            "Website",
            "Instagram",
            "VK",
            "Facebook",
        ]
    ]

    df.to_csv(csv_filename, sep=";", index=False, encoding="utf-8")
    print(f"[INFO] CSV saved to {csv_filename}")

    df.to_excel(xlsx_filename, index=False)
    print(f"[INFO] Excel saved to {xlsx_filename}")


def main() -> None:
    print("[START] Collecting Russian auto-related YouTube channels...")
    channels = collect_all_channels()
    print(f"\n[SUMMARY] Total unique channels discovered: {len(channels)}\n")
    rows = process_channels(channels)
    export_results(rows)
    print("[DONE] Completed scraping.")


if __name__ == "__main__":
    main()
