from urllib.parse import quote_plus
import httpx
import re
import orjson
import asyncio

from .Utils import format_views

# ─────────────────────────────
# UPSTASH REST REDIS (PERMANENT)
# ─────────────────────────────
UPSTASH_REDIS_REST_URL = "https://accepted-woodcock-22573.upstash.io"
UPSTASH_REDIS_REST_TOKEN = "AlgtAAIgcDJ6f5vhlO6Q9Af3w4dwAI4dvtMnh0IJCpKbAZDWe3Ac9w" 

REDIS_HEADERS = {
    "Authorization": f"Bearer {UPSTASH_REDIS_REST_TOKEN}"
}

# ─────────────────────────────
# CONSTANTS
# ─────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

YOUTUBE_SEARCH_URL = "https://www.youtube.com/results?search_query={}"
yt_data_regex = re.compile(r"ytInitialData\s*=\s*(\{.+?\});", re.DOTALL)

_client = httpx.AsyncClient(
    http2=True,
    timeout=6.0
)

# ─────────────────────────────
# RAM CACHE
# ─────────────────────────────
MEMORY_CACHE = {}
CACHE_LIMIT = 1000
_LOCKS = {}

def _normalize(q: str) -> str:
    return re.sub(r"\s+", " ", q.lower().strip())


# ─────────────────────────────
# REDIS REST HELPERS
# ─────────────────────────────
async def redis_get(key: str):
    url = f"{UPSTASH_REDIS_REST_URL}/get/{key}"
    r = await _client.get(url, headers=REDIS_HEADERS)
    if r.status_code == 200:
        data = r.json()
        return data.get("result")
    return None


async def redis_set(key: str, value: bytes):
    url = f"{UPSTASH_REDIS_REST_URL}/set/{key}"
    await _client.post(
        url,
        headers=REDIS_HEADERS,
        json={"value": value.decode()}
    )


# ─────────────────────────────
# MAIN SEARCH FUNCTION
# ─────────────────────────────
async def Search(query: str, limit: int = 1):
    if not query:
        return {"main_results": [], "suggested": []}

    qkey = _normalize(query)

    # 1️⃣ RAM CACHE
    if qkey in MEMORY_CACHE:
        return MEMORY_CACHE[qkey]

    # 2️⃣ REDIS (PERMANENT)
    try:
        cached = await redis_get(qkey)
        if cached:
            data = orjson.loads(cached.encode())
            MEMORY_CACHE[qkey] = data
            return data
    except Exception:
        pass

    lock = _LOCKS.setdefault(qkey, asyncio.Lock())

    async with lock:
        if qkey in MEMORY_CACHE:
            return MEMORY_CACHE[qkey]

        try:
            cached = await redis_get(qkey)
            if cached:
                data = orjson.loads(cached.encode())
                MEMORY_CACHE[qkey] = data
                return data
        except Exception:
            pass

        # 3️⃣ FETCH FROM YOUTUBE
        url = YOUTUBE_SEARCH_URL.format(quote_plus(query))
        resp = await _client.get(url, headers=HEADERS)

        match = yt_data_regex.search(resp.text)
        if not match:
            return {"main_results": [], "suggested": []}

        data = orjson.loads(match.group(1))
        contents = data["contents"]["twoColumnSearchResultsRenderer"][
            "primaryContents"]["sectionListRenderer"]["contents"
        ]

        results = []

        for section in contents:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                v = item.get("videoRenderer")
                if not v:
                    continue

                results.append({
                    "title": v["title"]["runs"][0]["text"],
                    "url": f"https://www.youtube.com/watch?v={v['videoId']}",
                    "duration": v.get("lengthText", {}).get("simpleText", "LIVE"),
                    "channel_name": v.get("ownerText", {}).get("runs", [{}])[0].get("text", "Unknown"),
                    "views": format_views(
                        v.get("viewCountText", {}).get("simpleText", "0 views")
                    ),
                    "thumbnail": v["thumbnail"]["thumbnails"][-1]["url"],
                })

                if len(results) >= limit + 5:
                    break

        output = {
            "main_results": results[:limit],
            "suggested": results[limit:limit + 5]
        }

        if len(MEMORY_CACHE) >= CACHE_LIMIT:
            MEMORY_CACHE.clear()

        MEMORY_CACHE[qkey] = output

        # 4️⃣ SAVE PERMANENTLY
        try:
            await redis_set(qkey, orjson.dumps(output))
        except Exception:
            pass

        return output
        
