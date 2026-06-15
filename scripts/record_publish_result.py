#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_workflow import WorkflowContractError, ensure_runtime_output_dir, write_json


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def bool_from_text(value: str | None) -> bool | None:
    if value is None:
        return None
    lowered = value.strip().lower()
    if lowered in {"1", "true", "yes", "y", "ok", "success"}:
        return True
    if lowered in {"0", "false", "no", "n", "fail", "failed"}:
        return False
    raise WorkflowContractError(f"无法解析布尔值：{value}")


def normalize_status(
    status: str | None,
    success: bool | None,
    platform_url: str | None,
    draft_id: str | None,
    draft_url: str | None,
    error: str | None,
) -> str:
    if status:
        return status
    if success is False or error:
        return "failed"
    if draft_id or draft_url:
        return "draft"
    if platform_url:
        return "published"
    return "pending_verification"


def normalize_verification_status(
    *,
    status: str,
    success: bool,
) -> str:
    if not success or status in {"failed", "error"}:
        return "failed"
    return "needs_manual_verification"


def normalize_raw_verification_status(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    if normalized in {"verified", "failed", "needs_manual_verification"}:
        return normalized
    raise WorkflowContractError(f"无法解析验真状态：{value}")


def normalize_result(raw: dict[str, Any], *, channel_pack: dict[str, Any], source: str) -> dict[str, Any]:
    success = raw.get("success")
    if success is not None:
        success = bool(success)
    raw_status = str(raw.get("status") or "").strip()
    raw_url = raw.get("url")
    draft_url = raw.get("draft_url")
    platform_url = raw.get("platform_url") or raw_url
    if raw_status in {"draft", "scheduled"} and raw_url and not raw.get("platform_url"):
        draft_url = draft_url or raw_url
        platform_url = None
    draft_id = raw.get("draft_id") or raw.get("msg_id") or raw.get("draft_id_or_url")
    error = raw.get("error")
    status = normalize_status(raw.get("status"), success, platform_url, draft_id, draft_url, error)
    if success is None:
        success = status in {"draft", "published", "scheduled", "manual_uploaded"}
    verification_status = normalize_raw_verification_status(raw.get("verification_status")) or normalize_verification_status(
        status=status,
        success=success,
    )
    return {
        "schema_version": "1.0",
        "recorded_at": now_iso(),
        "source": source,
        "topic_id": channel_pack.get("topic_id"),
        "title": channel_pack.get("title"),
        "channel": channel_pack.get("channel"),
        "platform": raw.get("platform") or channel_pack.get("platform") or channel_pack.get("channel"),
        "success": success,
        "status": status,
        "platform_url": platform_url,
        "draft_url": draft_url,
        "platform_post_id": raw.get("platform_post_id") or raw.get("post_id") or raw.get("note_id"),
        "draft_id": draft_id,
        "account": raw.get("account") or raw.get("account_identifier"),
        "published_or_draft_at": raw.get("published_or_draft_at") or raw.get("published_at") or raw.get("draft_at") or now_iso(),
        "screenshot": raw.get("screenshot") or raw.get("screenshot_path"),
        "platform_response": raw.get("platform_response") or raw.get("response"),
        "error": error,
        "verification_status": verification_status,
        "notes": raw.get("notes"),
    }


def load_result(args: argparse.Namespace) -> dict[str, Any]:
    if args.result_file:
        return read_json(Path(args.result_file).expanduser().resolve())
    raw: dict[str, Any] = {
        "success": bool_from_text(args.success),
        "status": args.status,
        "platform": args.platform,
        "platform_url": args.platform_url,
        "platform_post_id": args.platform_post_id,
        "draft_id": args.draft_id,
        "draft_url": args.draft_url,
        "verification_status": args.verification_status,
        "account": args.account,
        "published_or_draft_at": args.published_or_draft_at,
        "screenshot": args.screenshot,
        "error": args.error,
        "notes": args.notes,
    }
    return {key: value for key, value in raw.items() if value is not None}


def publish_root_from_pack(pack_path: Path) -> Path:
    # channel_packs/<topic>/<channel>/channel_pack.json -> publish root
    try:
        return pack_path.parents[3]
    except IndexError as exc:
        raise WorkflowContractError(f"channel_pack 路径不符合 publish 输出结构：{pack_path}") from exc


def update_pack(pack_path: Path, result_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    pack = read_json(pack_path)
    pack["publish_result"] = str(result_path.resolve())
    pack["publish_status"] = result["status"]
    pack["verification_status"] = result["verification_status"]
    pack["platform_url"] = result.get("platform_url")
    pack["draft_url"] = result.get("draft_url")
    pack["draft_id"] = result.get("draft_id")
    pack["last_result_recorded_at"] = result["recorded_at"]
    write_json(pack_path, pack)
    return pack


def result_identity(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("topic_id") or "").strip(), str(row.get("channel") or "").strip())


def channel_targets_from_manifest(manifest: dict[str, Any], publish_root: Path) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for pack in manifest.get("channel_packs") or []:
        topic_id, channel = result_identity(pack)
        if not topic_id or not channel or (topic_id, channel) in seen:
            continue
        seen.add((topic_id, channel))
        targets.append({"topic_id": topic_id, "channel": channel, "title": pack.get("title"), "platform": pack.get("platform")})

    if targets:
        return targets

    packs_root = publish_root / "channel_packs"
    if not packs_root.exists():
        return []
    for pack_path in sorted(packs_root.glob("*/*/channel_pack.json")):
        try:
            pack = read_json(pack_path)
        except (OSError, json.JSONDecodeError):
            continue
        topic_id, channel = result_identity(pack)
        if not topic_id or not channel or (topic_id, channel) in seen:
            continue
        seen.add((topic_id, channel))
        targets.append({"topic_id": topic_id, "channel": channel, "title": pack.get("title"), "platform": pack.get("platform")})
    return targets


def result_is_failed(row: dict[str, Any]) -> bool:
    return row.get("success") is False or str(row.get("status") or "").strip() in {"failed", "error"}


def result_is_published(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("success"))
        and str(row.get("status") or "").strip() == "published"
        and row.get("verification_status") == "verified"
        and bool(row.get("platform_url"))
    )


def result_is_draft(row: dict[str, Any]) -> bool:
    return (
        bool(row.get("success"))
        and str(row.get("status") or "").strip() in {"draft", "scheduled"}
        and row.get("verification_status") == "verified"
        and bool(row.get("draft_id"))
    )


def aggregate_publish_state(publish_root: Path, records: list[dict[str, Any]], manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or {}
    targets = channel_targets_from_manifest(manifest, publish_root)
    target_keys = {result_identity(item) for item in targets}
    latest_records: dict[tuple[str, str], dict[str, Any]] = {}
    for record in records:
        key = result_identity(record)
        if key == ("", ""):
            continue
        latest_records[key] = record

    recorded_keys = set(latest_records)
    pending_keys = target_keys - recorded_keys if target_keys else set()
    failed_records = [item for item in latest_records.values() if result_is_failed(item)]
    published_records = [item for item in latest_records.values() if result_is_published(item)]
    draft_records = [item for item in latest_records.values() if result_is_draft(item)]
    verified_records = [item for item in latest_records.values() if item.get("verification_status") == "verified"]
    manual_verification_records = [
        item
        for item in latest_records.values()
        if item.get("verification_status") == "needs_manual_verification"
    ]
    total_channels = len(target_keys) if target_keys else len(recorded_keys)
    recorded_count = len(recorded_keys & target_keys) if target_keys else len(recorded_keys)
    pending_count = max(total_channels - recorded_count, 0) if target_keys else 0

    if failed_records:
        status = "failed"
    elif recorded_count == 0:
        status = "pending_execution"
    elif pending_count > 0:
        status = "partially_recorded"
    elif manual_verification_records:
        status = "needs_manual_verification"
    elif total_channels > 0 and len(published_records) == total_channels:
        status = "all_published"
    elif total_channels > 0 and len(draft_records) == total_channels:
        status = "all_drafted"
    elif total_channels > 0 and recorded_count == total_channels:
        status = "completed_with_mixed_status"
    else:
        status = "partially_recorded"

    pending_channels = [
        {"topic_id": topic_id, "channel": channel}
        for topic_id, channel in sorted(pending_keys)
    ]
    return {
        "status": status,
        "total_channels": total_channels,
        "recorded_count": recorded_count,
        "pending_count": pending_count,
        "failed_count": len(failed_records),
        "draft_count": len(draft_records),
        "published_count": len(published_records),
        "verified_count": len(verified_records),
        "needs_manual_verification_count": len(manual_verification_records),
        "pending_channels": pending_channels,
    }


def update_publish_manifest(publish_root: Path, result: dict[str, Any], result_path: Path) -> None:
    manifest_path = publish_root / "publish_manifest.json"
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    results = [item for item in manifest.get("publish_results") or [] if item.get("channel") != result["channel"] or item.get("topic_id") != result["topic_id"]]
    results.append({**result, "result_file": str(result_path.resolve())})
    summary = aggregate_publish_state(publish_root, results, manifest)
    manifest["publish_results"] = results
    manifest["publish_summary"] = summary
    manifest["status"] = summary["status"]
    manifest["last_result_recorded_at"] = now_iso()
    write_json(manifest_path, manifest)


def update_execution_manifest(publish_root: Path, result: dict[str, Any]) -> None:
    execution_path = publish_root / "channel_execution_manifest.json"
    if not execution_path.exists():
        return
    manifest = read_json(execution_path)
    for execution in manifest.get("executions") or []:
        if execution.get("topic_id") == result["topic_id"] and execution.get("channel") == result["channel"]:
            execution["status"] = result["status"]
            execution["result"] = {
                "success": result["success"],
                "platform_url": result.get("platform_url"),
                "draft_url": result.get("draft_url"),
                "draft_id": result.get("draft_id"),
                "verification_status": result.get("verification_status"),
            }
    write_json(execution_path, manifest)


def update_verification_report(publish_root: Path, result: dict[str, Any], result_path: Path) -> dict[str, Any]:
    verification_path = publish_root / "publish_verification_report.json"
    report = read_json(verification_path) if verification_path.exists() else {"stage": "publish", "published_links": []}
    records = [
        item
        for item in report.get("records") or []
        if item.get("topic_id") != result["topic_id"] or item.get("channel") != result["channel"]
    ]
    records.append({**result, "result_file": str(result_path.resolve())})
    report["records"] = records
    report["published_links"] = [
        {
            "topic_id": item.get("topic_id"),
            "channel": item.get("channel"),
            "platform": item.get("platform"),
            "url": item.get("platform_url"),
            "status": item.get("status"),
        }
        for item in records
        if result_is_published(item)
    ]
    report["draft_records"] = [
        {
            "topic_id": item.get("topic_id"),
            "channel": item.get("channel"),
            "platform": item.get("platform"),
            "draft_id": item.get("draft_id"),
            "draft_url": item.get("draft_url") or (item.get("platform_url") if item.get("status") == "draft" else None),
            "status": item.get("status"),
        }
        for item in records
        if result_is_draft(item)
    ]
    manifest_path = publish_root / "publish_manifest.json"
    publish_manifest = read_json(manifest_path) if manifest_path.exists() else {}
    summary = aggregate_publish_state(publish_root, records, publish_manifest)
    report["publish_summary"] = summary
    report["status"] = summary["status"]
    report["updated_at"] = now_iso()
    write_json(verification_path, report)
    return report


def render_result_markdown(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"# 发布结果｜{result.get('title') or result.get('topic_id')}｜{result.get('channel')}",
            "",
            f"- 状态：`{result['status']}`",
            f"- 成功：`{result['success']}`",
            f"- 验真：`{result['verification_status']}`",
            f"- 平台：`{result.get('platform')}`",
            f"- URL：`{result.get('platform_url') or ''}`",
            f"- 草稿 URL：`{result.get('draft_url') or ''}`",
            f"- 草稿 ID：`{result.get('draft_id') or ''}`",
            f"- 账号：`{result.get('account') or ''}`",
            f"- 截图：`{result.get('screenshot') or ''}`",
            f"- 错误：`{result.get('error') or ''}`",
        ]
    )


def record_result(channel_pack_path: Path, raw_result: dict[str, Any], *, source: str) -> dict[str, Any]:
    channel_pack_path = channel_pack_path.expanduser().resolve()
    channel_pack = read_json(channel_pack_path)
    publish_root = ensure_runtime_output_dir(publish_root_from_pack(channel_pack_path), label="publish result root")
    result = normalize_result(raw_result, channel_pack=channel_pack, source=source)
    result_dir = channel_pack_path.parent
    result_path = result_dir / "publish_result.json"
    result_md_path = result_dir / "publish_result.md"
    write_json(result_path, result)
    write_text(result_md_path, render_result_markdown(result))
    update_pack(channel_pack_path, result_path, result)
    update_publish_manifest(publish_root, result, result_path)
    update_execution_manifest(publish_root, result)
    verification = update_verification_report(publish_root, result, result_path)
    return {
        "status": "recorded",
        "will_not_publish": True,
        "channel_pack": str(channel_pack_path),
        "publish_result": str(result_path.resolve()),
        "publish_result_markdown": str(result_md_path.resolve()),
        "verification_status": result["verification_status"],
        "publish_verification_status": verification.get("status"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Record a platform publish/draft result back into a Dasheng channel pack.")
    parser.add_argument("--channel-pack", required=True)
    parser.add_argument("--result-file")
    parser.add_argument("--source", default="manual_or_executor")
    parser.add_argument("--success")
    parser.add_argument("--status")
    parser.add_argument("--platform")
    parser.add_argument("--platform-url")
    parser.add_argument("--platform-post-id")
    parser.add_argument("--draft-id")
    parser.add_argument("--draft-url")
    parser.add_argument("--verification-status")
    parser.add_argument("--account")
    parser.add_argument("--published-or-draft-at")
    parser.add_argument("--screenshot")
    parser.add_argument("--error")
    parser.add_argument("--notes")
    args = parser.parse_args()

    payload = record_result(Path(args.channel_pack), load_result(args), source=args.source)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
