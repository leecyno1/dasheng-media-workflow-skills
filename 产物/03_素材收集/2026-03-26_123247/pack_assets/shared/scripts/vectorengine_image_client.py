import argparse
import json
import os
from pathlib import Path

import requests

ROOT = Path("/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets")
STATUS_FILE = ROOT / "shared" / "config" / "image_generation_status.json"
ENV_FILE = ROOT / "shared" / "config" / "vectorengine_gemini_image.env"


def load_env() -> dict[str, str]:
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.strip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="VectorEngine Gemini image compatibility client")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output-json", required=True)
    args = parser.parse_args()

    status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    if status.get("status") != "ok":
        raise SystemExit(f"provider unavailable: {status.get('status')} / {status.get('message')}")

    env = load_env()
    response = requests.post(
        f"{env['VECTORENGINE_BASE_URL']}/chat/completions",
        headers={
            "Authorization": f"Bearer {env['VECTORENGINE_API_KEY']}",
            "Content-Type": "application/json",
        },
        json={
            "model": env["VECTORENGINE_MODEL"],
            "messages": [{"role": "user", "content": args.prompt}],
            "temperature": 0.2,
        },
        timeout=120,
    )
    Path(args.output_json).write_text(response.text, encoding="utf-8")
    print(args.output_json)


if __name__ == "__main__":
    main()
