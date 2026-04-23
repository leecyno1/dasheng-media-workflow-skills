#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = ROOT / "scripts" / "material_execute_pack.sh"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def discover_topic_roots(pack_root: Path) -> list[Path]:
    roots: list[Path] = []
    for config in sorted(pack_root.glob("*/config/topic_config.json")):
        roots.append(config.parent.parent)
    return roots


def run_topic_video_search(pack_root: Path, topic_dir_name: str, download_limit: int) -> dict[str, Any]:
    cmd = [
        str(EXECUTOR),
        "--pack-root",
        str(pack_root),
        "--topic-dir",
        topic_dir_name,
        "--steps",
        "video_search",
        "--video-download-limit",
        str(download_limit),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "topic_dir": topic_dir_name,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-500:],
        "stderr": proc.stderr[-500:],
        "command": " ".join(cmd),
    }


def load_topic_audit(topic_root: Path) -> dict[str, Any]:
    report_path = topic_root / "videos" / "web_search" / "video_quality_audit_report.json"
    if not report_path.exists():
        return {
            "topic_dir": topic_root.name,
            "topic_slug": "",
            "report_path": str(report_path),
            "report_exists": False,
        }
    report = read_json(report_path)
    summary = report.get("summary", {})
    return {
        "topic_dir": topic_root.name,
        "topic_slug": report.get("topic", ""),
        "report_path": str(report_path),
        "report_exists": True,
        "candidate_total": summary.get("candidate_total", 0),
        "candidate_qualified": summary.get("candidate_qualified", 0),
        "candidate_rejected": summary.get("candidate_rejected", 0),
        "download_attempts": summary.get("download_attempts", 0),
        "download_passed": summary.get("download_passed", 0),
        "download_failed": summary.get("download_failed", 0),
        "candidate_reject_reason_counts": summary.get("candidate_reject_reason_counts", {}),
        "download_fail_reason_counts": summary.get("download_fail_reason_counts", {}),
    }


def merge_reason_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    merged: dict[str, int] = {}
    for row in rows:
        counts = row.get(field, {})
        if not isinstance(counts, dict):
            continue
        for reason, count in counts.items():
            merged[str(reason)] = merged.get(str(reason), 0) + int(count)
    return merged


def render_markdown(pack_root: Path, executed: list[dict[str, Any]], topics: list[dict[str, Any]], overall: dict[str, Any]) -> str:
    lines = [
        "# 视频质量回归报告",
        "",
        f"- pack_root: `{pack_root}`",
        "",
        "## 执行状态",
        "",
    ]
    if executed:
        for item in executed:
            status = "OK" if item.get("returncode") == 0 else "FAIL"
            lines.append(f"- `{item.get('topic_dir')}`: {status}")
    else:
        lines.append("- 本次未执行下载与检索（--skip-execute）")

    lines.extend(
        [
            "",
            "## 主题汇总",
            "",
            "| topic_dir | topic_slug | candidates | qualified | rejected | download_attempts | download_passed | download_failed |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in topics:
        lines.append(
            "| {topic_dir} | {topic_slug} | {candidate_total} | {candidate_qualified} | {candidate_rejected} | {download_attempts} | {download_passed} | {download_failed} |".format(
                topic_dir=row.get("topic_dir", ""),
                topic_slug=row.get("topic_slug", ""),
                candidate_total=row.get("candidate_total", 0),
                candidate_qualified=row.get("candidate_qualified", 0),
                candidate_rejected=row.get("candidate_rejected", 0),
                download_attempts=row.get("download_attempts", 0),
                download_passed=row.get("download_passed", 0),
                download_failed=row.get("download_failed", 0),
            )
        )

    lines.extend(
        [
            "",
            "## 全局统计",
            "",
            f"- 主题数: {overall['topic_count']}",
            f"- 候选总数: {overall['candidate_total']}",
            f"- 合格候选: {overall['candidate_qualified']}",
            f"- 下载尝试: {overall['download_attempts']}",
            f"- 下载通过: {overall['download_passed']}",
            f"- 下载失败: {overall['download_failed']}",
            "",
            "### 候选拒绝原因 Top",
            "",
        ]
    )
    for reason, count in sorted(overall["candidate_reject_reason_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"- {reason}: {count}")

    lines.extend(["", "### 下载失败原因 Top", ""])
    for reason, count in sorted(overall["download_fail_reason_counts"].items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"- {reason}: {count}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and summarize video quality regression")
    parser.add_argument("--pack-root", required=True, help="Path to pack_assets root")
    parser.add_argument("--topics", nargs="*", help="Optional topic dir names under pack_root")
    parser.add_argument("--video-download-limit", type=int, default=1)
    parser.add_argument("--skip-execute", action="store_true", help="Only summarize existing audit reports")
    args = parser.parse_args()

    pack_root = Path(args.pack_root).expanduser().resolve()
    if not pack_root.exists():
        raise RuntimeError(f"pack_root not found: {pack_root}")

    topic_roots = discover_topic_roots(pack_root)
    if args.topics:
        wanted = set(args.topics)
        topic_roots = [topic for topic in topic_roots if topic.name in wanted]
    if not topic_roots:
        raise RuntimeError("No topic directories matched")

    executed: list[dict[str, Any]] = []
    if not args.skip_execute:
        for topic_root in topic_roots:
            executed.append(run_topic_video_search(pack_root, topic_root.name, args.video_download_limit))

    topic_reports = [load_topic_audit(topic_root) for topic_root in topic_roots]
    overall = {
        "topic_count": len(topic_reports),
        "candidate_total": sum(int(row.get("candidate_total", 0)) for row in topic_reports),
        "candidate_qualified": sum(int(row.get("candidate_qualified", 0)) for row in topic_reports),
        "candidate_rejected": sum(int(row.get("candidate_rejected", 0)) for row in topic_reports),
        "download_attempts": sum(int(row.get("download_attempts", 0)) for row in topic_reports),
        "download_passed": sum(int(row.get("download_passed", 0)) for row in topic_reports),
        "download_failed": sum(int(row.get("download_failed", 0)) for row in topic_reports),
        "candidate_reject_reason_counts": merge_reason_counts(topic_reports, "candidate_reject_reason_counts"),
        "download_fail_reason_counts": merge_reason_counts(topic_reports, "download_fail_reason_counts"),
    }
    out = {
        "pack_root": str(pack_root),
        "executed": executed,
        "topics": topic_reports,
        "overall": overall,
    }

    json_out = pack_root / "video_quality_regression_summary.json"
    md_out = pack_root / "video_quality_regression_summary.md"
    write_json(json_out, out)
    write_text(md_out, render_markdown(pack_root, executed, topic_reports, overall))
    print(json_out)
    print(md_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

