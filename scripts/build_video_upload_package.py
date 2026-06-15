#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VIDEO_CHANNELS = {
    "xiaohongshu_video": "xiaohongshu",
    "douyin_video": "douyin",
    "bilibili_video": "bilibili",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def existing_path(value: Any) -> str | None:
    if not value:
        return None
    candidate = Path(str(value)).expanduser()
    return str(candidate.resolve()) if candidate.exists() else str(candidate)


def validate_video_pack(pack: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    channel = pack.get("channel")
    if channel not in VIDEO_CHANNELS:
        errors.append(f"unsupported_video_channel:{channel}")
    video = ((pack.get("artifact_hint") or {}).get("video"))
    if not video:
        errors.append("missing_video_artifact")
    elif not Path(str(video)).expanduser().exists():
        errors.append("video_artifact_not_found")
    if not ((pack.get("publish_metadata") or {}).get("title") or pack.get("title")):
        errors.append("missing_title")
    return errors


def common_payload(pack: dict[str, Any], channel_pack_path: Path) -> dict[str, Any]:
    artifacts = pack.get("artifact_hint") or {}
    metadata = pack.get("publish_metadata") or {}
    title = metadata.get("title") or pack.get("title")
    description = metadata.get("summary") or metadata.get("description") or ""
    tags = metadata.get("tags") or []
    return {
        "topic_id": pack.get("topic_id"),
        "title": title,
        "description": description,
        "tags": tags,
        "cover": existing_path(metadata.get("cover")),
        "video": existing_path(artifacts.get("video")),
        "subtitle": existing_path(artifacts.get("video_srt")),
        "source_channel_pack": str(channel_pack_path.resolve()),
        "requires_user_confirmation": True,
        "auto_publish": False,
    }


def build_social_auto_upload_request(pack: dict[str, Any], channel_pack_path: Path) -> dict[str, Any]:
    payload = common_payload(pack, channel_pack_path)
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "adapter": "social-auto-upload",
        "platform": VIDEO_CHANNELS.get(pack.get("channel")),
        "status": "ready_for_external_dry_run",
        "upload": payload,
        "safety": {
            "will_not_publish_without_confirmation": True,
            "credentials_handling": "external_tool_session_only",
            "runtime_output_root": "same_channel_pack_directory",
        },
    }


def build_bilibili_submission(pack: dict[str, Any], channel_pack_path: Path) -> dict[str, Any]:
    payload = common_payload(pack, channel_pack_path)
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "adapter": "bilibili-upload-bridge",
        "platform": "bilibili",
        "status": "ready_for_external_dry_run",
        "submission": {
            "title": payload["title"],
            "desc": payload["description"],
            "tags": payload["tags"],
            "cover": payload["cover"],
            "video": payload["video"],
            "subtitle": payload["subtitle"],
            "source_channel_pack": payload["source_channel_pack"],
            "copyright": "original_or_user_confirmed",
        },
        "preferred_tools": ["biliup-rs", "social-auto-upload", "manual-package"],
        "safety": {
            "will_not_publish_without_confirmation": True,
            "credentials_handling": "external_tool_session_only",
            "runtime_output_root": "same_channel_pack_directory",
        },
    }


def build_package(channel_pack_path: Path) -> dict[str, Any]:
    pack = read_json(channel_pack_path)
    errors = validate_video_pack(pack)
    pack_dir = channel_pack_path.parent
    social_path = pack_dir / "social_auto_upload_request.json"
    bilibili_path = pack_dir / "bilibili_submission.json"

    outputs: dict[str, str] = {}
    if not errors:
        social_request = build_social_auto_upload_request(pack, channel_pack_path)
        write_json(social_path, social_request)
        outputs["social_auto_upload_request"] = str(social_path.resolve())
        if pack.get("channel") == "bilibili_video":
            bilibili_submission = build_bilibili_submission(pack, channel_pack_path)
            write_json(bilibili_path, bilibili_submission)
            outputs["bilibili_submission"] = str(bilibili_path.resolve())

    status = "ready" if not errors else "blocked"
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "status": status,
        "channel_pack": str(channel_pack_path.resolve()),
        "channel": pack.get("channel"),
        "platform": VIDEO_CHANNELS.get(pack.get("channel")),
        "errors": errors,
        "outputs": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build external video upload package from Dasheng channel_pack.json.")
    parser.add_argument("--channel-pack", required=True)
    parser.add_argument("--output", help="Optional conversion report path.")
    args = parser.parse_args()

    channel_pack = Path(args.channel_pack).expanduser().resolve()
    report = build_package(channel_pack)
    if args.output:
        write_json(Path(args.output).expanduser().resolve(), report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
