import json
import subprocess
from pathlib import Path

ROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")
CONFIG = ROOT / "shared" / "config" / "selected_videos.json"


def download(entry: dict, category: str) -> dict:
    topic = entry["topic"]
    target_dir = ROOT / topic / "videos" / category
    target_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(target_dir / f"{entry['anchor']}__{entry['label']}.%(ext)s")
    cmd = [
        "yt-dlp",
        "-f",
        "mp4/bestvideo*+bestaudio/best",
        "--merge-output-format",
        "mp4",
        "--output",
        outtmpl,
        "--no-playlist",
        entry["url"],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    result = {
        "topic": topic,
        "anchor": entry["anchor"],
        "label": entry["label"],
        "url": entry["url"],
        "category": category,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-1000:],
        "stderr": proc.stderr[-1000:],
    }
    return result


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    results = []
    for entry in payload["source_link_videos"]:
        results.append(download(entry, "source_links"))
    for entry in payload["web_search_videos"]:
        results.append(download(entry, "web_search"))
    (ROOT / "shared" / "config" / "video_download_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(ROOT / "shared" / "config" / "video_download_results.json")


if __name__ == "__main__":
    main()
