import json
import subprocess
from pathlib import Path

QUERIES = {
    "reinflation": [
        "oil refinery aerial 4k documentary",
        "container shipping port cranes aerial 4k",
        "federal reserve building exterior b roll",
        "trading floor stock market b roll",
        "oil tanker sea aerial 4k",
    ],
    "takaichi": [
        "Japan election rally crowd Tokyo 4k",
        "Japanese parliament diet building b roll",
        "Tokyo crowd crossing 4k documentary",
        "Japan coast guard drill 4k",
        "Japan aging society elderly crowd 4k",
    ],
}

OUTROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")


def main() -> None:
    for slug, query_list in QUERIES.items():
        rows = []
        for query in query_list:
            cmd = ["yt-dlp", "--flat-playlist", "--dump-single-json", f"ytsearch5:{query}"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                rows.append({"query": query, "error": proc.stderr[:500]})
                continue

            data = json.loads(proc.stdout)
            for entry in data.get("entries", [])[:5]:
                video_id = entry.get("id")
                rows.append(
                    {
                        "query": query,
                        "id": video_id,
                        "title": entry.get("title"),
                        "url": f"https://www.youtube.com/watch?v={video_id}" if video_id else entry.get("url"),
                        "duration": entry.get("duration"),
                        "channel": entry.get("channel") or entry.get("uploader"),
                    }
                )

        target = OUTROOT / slug / "videos" / "web_search" / "youtube_candidates.json"
        target.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(target)


if __name__ == "__main__":
    main()
