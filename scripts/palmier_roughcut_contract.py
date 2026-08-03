#!/usr/bin/env python3
"""Validate the guarded Palmier rough-cut route and its exported result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "dasheng.palmier_roughcut.v1"
ALLOWED_OPERATIONS = {
    "create_project",
    "import_media",
    "create_timeline",
    "ripple_delete_ranges",
    "apply_color",
    "export_video",
}
BLOCKED_OPERATIONS = {
    "remove_words",
    "undo",
    "remove_silence",
    "denoise_audio_per_fragment",
    "close_project_as_persistence_proof",
}


def _is_desktop_media_path(path: Path) -> bool:
    expected = (Path.home() / "Desktop" / "自媒体创作").resolve()
    try:
        path.expanduser().resolve().relative_to(expected)
    except ValueError:
        return False
    return True


def normalized_ranges(ranges: list[dict[str, Any]]) -> list[tuple[float, float]]:
    normalized: list[tuple[float, float]] = []
    for item in ranges:
        start = float(item["start_seconds"])
        end = float(item["end_seconds"])
        if start < 0 or end <= start:
            raise ValueError(f"invalid delete range: {start}-{end}")
        normalized.append((start, end))
    normalized.sort()
    for previous, current in zip(normalized, normalized[1:]):
        if current[0] < previous[1]:
            raise ValueError(f"overlapping delete ranges: {previous} and {current}")
    return normalized


def removed_frame_count(ranges: list[dict[str, Any]], fps: float) -> int:
    if fps <= 0:
        raise ValueError("fps must be positive")
    return sum(round((end - start) * fps) for start, end in normalized_ranges(ranges))


def validate_plan(plan: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    operations = [str(item.get("tool") or "") for item in plan.get("operations", [])]
    unknown = sorted(set(operations) - ALLOWED_OPERATIONS)
    blocked = sorted(set(operations) & BLOCKED_OPERATIONS)
    if unknown:
        errors.append(f"operations outside allowlist: {', '.join(unknown)}")
    if blocked:
        errors.append(f"blocked operations requested: {', '.join(blocked)}")

    output_path = Path(str(plan.get("output_path") or ""))
    if not _is_desktop_media_path(output_path):
        errors.append("output_path must be under ~/Desktop/自媒体创作")

    ranges = plan.get("delete_ranges") or []
    try:
        frames = removed_frame_count(ranges, float(plan.get("fps") or 0))
    except (KeyError, TypeError, ValueError) as exc:
        errors.append(str(exc))
        frames = 0

    for index, item in enumerate(ranges):
        if not item.get("reason"):
            errors.append(f"delete_ranges[{index}] is missing reason")
        if item.get("reviewed") is not True:
            errors.append(f"delete_ranges[{index}] is not reviewed")

    return {
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "errors": errors,
        "operation_count": len(operations),
        "delete_range_count": len(ranges),
        "requested_removed_frames": frames,
    }


def validate_result(plan: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    plan_report = validate_plan(plan)
    errors = list(plan_report["errors"])
    expected = int(plan_report["requested_removed_frames"])
    actual = int(result.get("actual_removed_frames") or -1)
    tolerance = int(result.get("frame_tolerance") or 1)
    if actual < 0 or abs(actual - expected) > tolerance:
        errors.append(f"removed frame mismatch: expected {expected}, actual {actual}, tolerance {tolerance}")

    output_path = Path(str(result.get("output_path") or plan.get("output_path") or ""))
    if not _is_desktop_media_path(output_path):
        errors.append("result output_path must be under ~/Desktop/自媒体创作")
    if result.get("output_exists") is not True:
        errors.append("output file was not verified")
    if result.get("video_stream_ok") is not True or result.get("audio_stream_ok") is not True:
        errors.append("video/audio stream verification failed")
    if result.get("audio_continuity_ok") is not True:
        errors.append("audio continuity verification failed")
    if result.get("export_timeout") is True:
        errors.append("Palmier export timed out")

    project_reusable = result.get("project_reopen_ok") is True
    warnings = [] if project_reusable else ["Palmier project persistence was not verified; treat the MP4 as the deliverable"]

    return {
        "schema_version": SCHEMA_VERSION,
        "valid": not errors,
        "errors": errors,
        "requested_removed_frames": expected,
        "actual_removed_frames": actual,
        "editable_project_ready": project_reusable,
        "warnings": warnings,
        "route_status": "experimental_pass" if not errors else "blocked",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True)
    parser.add_argument("--result")
    parser.add_argument("--output")
    args = parser.parse_args()

    plan = json.loads(Path(args.plan).expanduser().read_text(encoding="utf-8"))
    if args.result:
        result = json.loads(Path(args.result).expanduser().read_text(encoding="utf-8"))
        report = validate_result(plan, result)
    else:
        report = validate_plan(plan)

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        target = Path(args.output).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if report["valid"] else 2)


if __name__ == "__main__":
    main()
