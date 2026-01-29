import subprocess
import json


def get_stream_url(
    video_url: str,
    cookies_path: str = None,
    mode: str = "audio"   # "audio" | "video"
) -> str | None:
    try:
        if mode == "video":
            fmt = "bv*+ba/b"
        else:
            fmt = "ba/b"

        cmd = [
            "yt-dlp",
            "-j",
            "-f", fmt,
            "--no-playlist",
            "--quiet",
            "--no-warnings",
            "--merge-output-format", "mp4"
        ]

        # 🔥 MOST IMPORTANT (n-challenge bypass)
        cmd += ["--extractor-args", "youtube:player-client=android"]

        if cookies_path:
            cmd += ["--cookies", cookies_path]

        cmd.append(video_url)

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print("❌ yt-dlp error:", result.stderr)
            return None

        data = json.loads(result.stdout)

        # 🎯 CORRECT STREAM URL
        if mode == "audio":
            for f in data.get("formats", []):
                if f.get("acodec") != "none" and f.get("vcodec") == "none":
                    return f.get("url")
        else:
            for f in data.get("formats", []):
                if f.get("acodec") != "none" and f.get("vcodec") != "none":
                    return f.get("url")

        return None

    except Exception as e:
        print(f"❌ Error extracting stream URL: {e}")
        return None
