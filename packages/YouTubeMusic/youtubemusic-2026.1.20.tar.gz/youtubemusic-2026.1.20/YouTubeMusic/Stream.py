import subprocess
import json
import time
import os
import hashlib

__all__ = ["get_stream"]

# ==============================
# CONFIG
# ==============================

_TTL = 300  # seconds (5 min)
_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")

os.makedirs(_CACHE_DIR, exist_ok=True)

# RAM cache
_MEM_CACHE = {}


# ==============================
# INTERNAL HELPERS
# ==============================

def _key(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _cache_path(url: str) -> str:
    return os.path.join(_CACHE_DIR, _key(url) + ".json")


def _read_disk(url: str):
    path = _cache_path(url)
    if not os.path.exists(path):
        return None

    try:
        with open(path, "r") as f:
            data = json.load(f)

        if time.time() - data["ts"] < _TTL:
            return data["stream"]
    except Exception:
        pass

    return None


def _write_disk(url: str, stream: str):
    try:
        with open(_cache_path(url), "w") as f:
            json.dump({"stream": stream, "ts": time.time()}, f)
    except Exception:
        pass


def _extract_stream(url: str) -> str | None:
    cmd = [
        "yt-dlp",
        "-J",
        "-f", "ba/b",
        "--quiet",
        "--no-warnings",
        "--extractor-args", "youtube:player-client=android",
        url
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if p.returncode != 0:
        return None

    data = json.loads(p.stdout)

    for f in data.get("formats", []):
        if (
            f.get("acodec") not in (None, "none")
            and f.get("vcodec") in (None, "none")
            and f.get("url")
        ):
            return f["url"]

    for f in data.get("formats", []):
        if (
            f.get("acodec") not in (None, "none")
            and f.get("vcodec") not in (None, "none")
            and f.get("url")
        ):
            return f["url"]

    return None


# ==============================
# PUBLIC API
# ==============================

def get_stream(url: str) -> str | None:
    now = time.time()

    # 1️⃣ RAM cache
    cached = _MEM_CACHE.get(url)
    if cached:
        stream, ts = cached
        if now - ts < _TTL:
            return stream

    # 2️⃣ Disk cache
    stream = _read_disk(url)
    if stream:
        _MEM_CACHE[url] = (stream, now)
        return stream

    # 3️⃣ Fresh extract
    stream = _extract_stream(url)
    if stream:
        _MEM_CACHE[url] = (stream, now)
        _write_disk(url, stream)

    return stream
