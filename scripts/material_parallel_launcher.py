#!/usr/bin/env python3
"""
并行启动多个选题的 material 执行器。

示例：
  python3 scripts/material_parallel_launcher.py \
    --draft-manifest " + str(Path(__file__).resolve().parents[1]) + "/tmp/upgrade_validation/draft/draft_manifest.json \
    --max-workers 3 \
    --steps charts,image_search,video_search,ai_prep \
    --video-download-limit 2
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from canonical_workflow import canonical_manifest_path, ensure_stage_manifest
from material_execute_pack import (
    build_material_plan_from_draft_manifest,
    resolve_pack_root_from_material_manifest,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXECUTOR = PROJECT_ROOT / "scripts" / "material_execute_pack.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run material_execute_pack.py in parallel by topic")
    parser.add_argument("--draft-manifest", help="canonical draft_manifest.json path; auto-build or reuse material plan first")
    parser.add_argument("--material-manifest", help="canonical material_manifest.json path; will reuse upstream draft_manifest")
    parser.add_argument("--run-id", help="canonical run_id; resolve canonical material/draft manifests only")
    parser.add_argument("--topics", nargs="*", default=None, help="topic dir names, e.g. topic-6 topic-10")
    parser.add_argument("--max-workers", type=int, default=3, help="parallel workers")
    parser.add_argument("--steps", default="charts,image_search,video_search,ai_prep", help="steps passed to executor")
    parser.add_argument("--video-download-limit", type=int, default=2, help="video download limit per topic")
    parser.add_argument("--layer5-only", action="store_true", help="only run layer5-only mode")
    parser.add_argument("--rebuild-material-plan", action="store_true", help="force rerunning Node material planner when using --draft-manifest")
    return parser.parse_args()


def discover_topics(pack_root: Path, topics: list[str] | None) -> list[str]:
    candidates = sorted([p.name for p in pack_root.iterdir() if p.is_dir() and p.name.startswith("topic-")])
    if topics:
        allow = set(topics)
        return [name for name in candidates if name in allow]
    return candidates


def read_material_manifest(material_manifest: Path) -> dict:
    payload = ensure_stage_manifest(material_manifest, "material")
    if not isinstance(payload.get("upstream"), dict):
        raise SystemExit(f"material_manifest 缺少 upstream：{material_manifest}")
    return payload


def resolve_draft_manifest_from_material_manifest(material_manifest: Path) -> Path:
    payload = read_material_manifest(material_manifest)
    draft_manifest_value = str(payload["upstream"].get("draft_manifest") or "").strip()
    if not draft_manifest_value:
        raise SystemExit(f"material_manifest 缺少 upstream.draft_manifest：{material_manifest}")
    draft_manifest = Path(draft_manifest_value).expanduser().resolve()
    ensure_stage_manifest(draft_manifest, "draft")
    return draft_manifest


def resolve_execution_entry(args: argparse.Namespace) -> tuple[Path, Path | None, dict[str, str]]:
    provided = [bool(args.draft_manifest), bool(args.material_manifest), bool(args.run_id)]
    if sum(provided) != 1:
        raise SystemExit("必须且只能提供一个入口：--draft-manifest / --material-manifest / --run-id")

    metadata: dict[str, str] = {}
    if args.draft_manifest:
        draft_manifest = Path(args.draft_manifest).expanduser().resolve()
        pack_root, material_manifest = build_material_plan_from_draft_manifest(
            draft_manifest,
            force_rebuild=args.rebuild_material_plan,
        )
        metadata["draft_manifest"] = str(draft_manifest)
        metadata["material_manifest"] = str(material_manifest)
        metadata["pack_root"] = str(pack_root)
        return pack_root, draft_manifest, metadata

    if args.material_manifest:
        material_manifest = Path(args.material_manifest).expanduser().resolve()
        payload = read_material_manifest(material_manifest)
        pack_root = resolve_pack_root_from_material_manifest(material_manifest)
        if not pack_root:
            raise SystemExit(f"canonical material_manifest 未指向可用 pack_root：{material_manifest}")
        draft_manifest = resolve_draft_manifest_from_material_manifest(material_manifest)
        metadata["material_manifest"] = str(material_manifest)
        metadata["draft_manifest"] = str(draft_manifest)
        metadata["pack_root"] = str(pack_root)
        runtime_material_manifest = str(payload.get("runtime_material_manifest") or "").strip()
        if runtime_material_manifest:
            metadata["runtime_material_manifest"] = runtime_material_manifest
        return pack_root, draft_manifest, metadata

    run_id = str(args.run_id).strip()
    if not run_id:
        raise SystemExit("run_id 不能为空")
    material_manifest = canonical_manifest_path("material", run_id)
    if material_manifest.exists():
        pack_root = resolve_pack_root_from_material_manifest(material_manifest)
        if pack_root:
            draft_manifest = resolve_draft_manifest_from_material_manifest(material_manifest)
            metadata["run_id"] = run_id
            metadata["material_manifest"] = str(material_manifest)
            metadata["draft_manifest"] = str(draft_manifest)
            metadata["pack_root"] = str(pack_root)
            return pack_root, draft_manifest, metadata
    draft_manifest = canonical_manifest_path("draft", run_id)
    ensure_stage_manifest(draft_manifest, "draft")
    pack_root, runtime_material_manifest = build_material_plan_from_draft_manifest(
        draft_manifest,
        force_rebuild=args.rebuild_material_plan,
    )
    metadata["run_id"] = run_id
    metadata["draft_manifest"] = str(draft_manifest)
    metadata["material_manifest"] = str(canonical_manifest_path("material", run_id))
    metadata["runtime_material_manifest"] = str(runtime_material_manifest)
    metadata["pack_root"] = str(pack_root)
    return pack_root, draft_manifest, metadata


def atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        temp_name = handle.name
    os.replace(temp_name, path)


def run_topic(
    draft_manifest: Path,
    topic: str,
    steps: str,
    video_download_limit: int,
    layer5_only: bool,
) -> dict:
    started = time.time()
    cmd = [
        "python3",
        str(EXECUTOR),
        "--draft-manifest",
        str(draft_manifest),
        "--topic-dir",
        topic,
        "--video-download-limit",
        str(video_download_limit),
    ]
    if layer5_only:
        cmd.append("--layer5-only")
    else:
        cmd.extend(["--steps", steps])

    proc = subprocess.run(cmd, capture_output=True, text=True)
    duration = round(time.time() - started, 2)
    return {
        "topic": topic,
        "command": cmd,
        "returncode": proc.returncode,
        "duration_seconds": duration,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-2000:],
        "status": "ok" if proc.returncode == 0 else "failed",
    }


def main() -> int:
    args = parse_args()
    pack_root, draft_manifest, metadata = resolve_execution_entry(args)
    if not pack_root.exists():
        raise SystemExit(f"pack root not found: {pack_root}")
    if not EXECUTOR.exists():
        raise SystemExit(f"executor not found: {EXECUTOR}")
    if not draft_manifest:
        raise SystemExit("未解析到可执行的 draft_manifest")

    topics = discover_topics(pack_root, args.topics)
    if not topics:
        raise SystemExit("no topics found to run")

    started = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as pool:
        futures = {
            pool.submit(
                run_topic,
                draft_manifest,
                topic,
                args.steps,
                args.video_download_limit,
                args.layer5_only,
            ): topic
            for topic in topics
        }
        for future in as_completed(futures):
            results.append(future.result())

    results = sorted(results, key=lambda item: item["topic"])
    ok_count = sum(1 for item in results if item["status"] == "ok")
    payload = {
        "pack_root": str(pack_root),
        "topics": topics,
        "max_workers": args.max_workers,
        "steps": "charts" if args.layer5_only else args.steps,
        "layer5_only": bool(args.layer5_only),
        "video_download_limit": args.video_download_limit,
        "started_at_epoch": started,
        "duration_seconds": round(time.time() - started, 2),
        "ok_count": ok_count,
        "failed_count": len(results) - ok_count,
        "results": results,
    }
    payload.update(metadata)

    out_file = pack_root / "parallel_execution_report.json"
    atomic_write_json(out_file, payload)
    print(str(out_file))
    return 0 if ok_count == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
