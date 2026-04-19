import json
from pathlib import Path

import requests

ROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")
CONFIG = ROOT / "shared" / "config" / "wikipedia_images.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MediaPackBot/1.0; +https://example.com/bot)"}


def fetch_image_url(title: str) -> str | None:
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageimages",
        "format": "json",
        "piprop": "original",
    }
    response = requests.get("https://en.wikipedia.org/w/api.php", params=params, headers=HEADERS, timeout=60)
    try:
        data = response.json()
    except Exception:
        summary = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}",
            headers=HEADERS,
            timeout=60,
        )
        try:
            summary_json = summary.json()
            original = summary_json.get("originalimage") or summary_json.get("thumbnail")
            if original and original.get("source"):
                return original["source"]
        except Exception:
            return None
        return None
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        original = page.get("original")
        if original and original.get("source"):
            return original["source"]
    return None


def main() -> None:
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    results = []
    for item in payload["images"]:
        image_url = fetch_image_url(item["title"])
        result = {**item, "image_url": image_url}
        if image_url:
            response = requests.get(image_url, headers=HEADERS, timeout=120)
            response.raise_for_status()
            suffix = Path(image_url).suffix or ".jpg"
            target = ROOT / item["topic"] / "images" / "web_search" / f"{item['anchor']}__{item['slug']}{suffix}"
            target.write_bytes(response.content)
            result["saved_to"] = str(target)
        results.append(result)
    (ROOT / "shared" / "config" / "image_download_results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(ROOT / "shared" / "config" / "image_download_results.json")


if __name__ == "__main__":
    main()
