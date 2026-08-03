#!/usr/bin/env python3
"""Quality gate for Dasheng video scene plans.

This catches the failure mode where a video technically renders, but the
director plan is too coarse, repetitive, or evidence-light to be production
grade.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scene_start(scene: dict[str, Any]) -> float:
    return float(scene.get("start_sec", scene.get("start", 0.0)) or 0.0)


def scene_end(scene: dict[str, Any]) -> float:
    if scene.get("end_sec") is not None:
        return float(scene["end_sec"])
    if scene.get("end") is not None:
        return float(scene["end"])
    return scene_start(scene) + scene_duration(scene)


def scene_duration(scene: dict[str, Any]) -> float:
    if scene.get("duration_sec") is not None:
        return float(scene["duration_sec"])
    if scene.get("duration") is not None:
        return float(scene["duration"])
    return max(0.0, scene_end(scene) - scene_start(scene))


def composition_key(scene: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(scene.get("speaker_state") or "unknown"),
        str(scene.get("material_state") or "unknown"),
        str(scene.get("pip_shape") or "unknown"),
    )


def scene_micro_shots(scene: dict[str, Any]) -> list[dict[str, Any]]:
    direct = scene.get("micro_shots")
    if isinstance(direct, list):
        return [item for item in direct if isinstance(item, dict)]
    nested = (scene.get("variables") or {}).get("micro_shots")
    if isinstance(nested, list):
        return [item for item in nested if isinstance(item, dict)]
    return []


def is_evidence_scene(scene: dict[str, Any]) -> bool:
    beat = str(scene.get("beat_class") or "")
    material = str(scene.get("material_state") or "")
    shot = str(scene.get("shot") or "")
    return (
        beat in {"evidence_data", "evidence_document"}
        or "evidence" in material
        or "chart" in material
        or "document" in material
        or shot in {"chart_card", "document_zoom"}
    )


def run_lengths(keys: list[tuple[str, str, str]]) -> list[tuple[tuple[str, str, str], int]]:
    if not keys:
        return []
    out: list[tuple[tuple[str, str, str], int]] = []
    current = keys[0]
    count = 1
    for key in keys[1:]:
        if key == current:
            count += 1
            continue
        out.append((current, count))
        current = key
        count = 1
    out.append((current, count))
    return out


def audit_scene_plan(plan: dict[str, Any]) -> dict[str, Any]:
    scenes = plan.get("scenes") or plan.get("segments") or plan.get("timeline") or []
    durations = [scene_duration(scene) for scene in scenes]
    total_duration = max((scene_end(scene) for scene in scenes), default=0.0)
    if not total_duration and durations:
        total_duration = sum(durations)
    cuts_per_min = (len(scenes) / total_duration * 60.0) if total_duration else 0.0
    effective_visual_count = sum(max(1, len(scene_micro_shots(scene))) for scene in scenes)
    effective_visual_changes_per_min = (
        effective_visual_count / total_duration * 60.0 if total_duration else 0.0
    )
    median_duration = statistics.median(durations) if durations else 0.0
    avg_duration = statistics.mean(durations) if durations else 0.0

    failures: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    lane = str(plan.get("lane") or "")
    schema_version = str(plan.get("schema_version") or "")
    if not lane and schema_version.startswith("dasheng.html_anything_video_timeline."):
        lane = "explainer_html_video"
    is_talking_head = lane == "talking_head_video" or plan.get("schema_version") == "dasheng.talking_head_timeline.v1"
    is_explainer = lane == "explainer_html_video"
    is_bound_evidence_plan = "real_evidence" in schema_version or bool(plan.get("evidence_policy"))

    timeline_alignment = plan.get("timeline_alignment") or {}
    if timeline_alignment.get("mode") == "global_scale":
        failures.append(
            {
                "code": "global_time_scale_after_roughcut",
                "message": "离散粗剪不能用全局 timeScale 压缩分镜时间轴，必须按 EDL 分段映射或在粗剪成片上重新转录。",
                "time_scale": timeline_alignment.get("time_scale"),
            }
        )

    if is_talking_head:
        if cuts_per_min < 14:
            failures.append(
                {
                    "code": "visual_density_too_low",
                    "message": "真人精简分镜太粗，未达到小林说类 17-25 次/分钟的可接受下限。",
                    "actual_cuts_per_min": round(cuts_per_min, 2),
                    "minimum": 14,
                }
            )
        if median_duration > 4.5:
            failures.append(
                {
                    "code": "median_scene_too_long",
                    "message": "中位分镜时长过长，会形成PPT感。",
                    "actual_median_sec": round(median_duration, 2),
                    "maximum": 4.5,
                }
            )
        long_static = [
            scene.get("id") or index + 1
            for index, scene in enumerate(scenes)
            if scene_duration(scene) > 8 and not scene.get("micro_shots")
        ]
        if long_static:
            failures.append(
                {
                    "code": "long_scene_without_micro_shots",
                    "message": "超过 8 秒的大分镜必须拆成微镜头或写明镜头内动作。",
                    "scene_ids": long_static[:20],
                    "count": len(long_static),
                }
            )

    if is_explainer:
        rewrite_framing = re.compile(r"原文(?:提到|指出|认为|表示)?|原文章|文章(?:提到|指出|认为|表示)|作者(?:提到|指出|认为|表示)|根据原文章")
        framed_scenes = []
        duplicate_chart_scenes = []
        for index, scene in enumerate(scenes):
            narration = str(scene.get("narration_tts") or scene.get("narration") or "")
            match = rewrite_framing.search(narration)
            if match:
                framed_scenes.append(
                    {
                        "id": scene.get("id") or index + 1,
                        "term": match.group(0),
                    }
                )
            render_mode = str(scene.get("chart_render_mode") or (scene.get("variables") or {}).get("chart_render_mode") or "")
            source_visible = bool(scene.get("source_chart_image_visible") or (scene.get("variables") or {}).get("source_chart_image_visible"))
            if render_mode == "dynamic_reconstruction" and source_visible:
                duplicate_chart_scenes.append(scene.get("id") or index + 1)
        if framed_scenes:
            failures.append(
                {
                    "code": "third_party_rewrite_framing",
                    "message": "无头口播必须以创作者本人视角直接表达，禁止把输入文章当第三方原文反复转述。",
                    "scenes": framed_scenes[:20],
                }
            )
        if duplicate_chart_scenes:
            failures.append(
                {
                    "code": "duplicate_source_chart_after_reconstruction",
                    "message": "动态图表已完整重建时，不得再次并排或相邻展示原图。",
                    "scene_ids": duplicate_chart_scenes[:20],
                }
            )
        if effective_visual_changes_per_min < 7:
            failures.append(
                {
                    "code": "explainer_visual_density_too_low",
                    "message": "无头科普镜头密度过低，容易退化成PPT翻页。",
                    "actual_cuts_per_min": round(cuts_per_min, 2),
                    "effective_visual_changes_per_min": round(effective_visual_changes_per_min, 2),
                    "minimum": 7,
                }
            )
        long_without_motion = []
        for index, scene in enumerate(scenes):
            policy = scene.get("motion_policy") or {}
            has_motion = bool(scene.get("html_animation_behavior") or scene.get("motion") or policy.get("animation"))
            if scene_duration(scene) > 14 and not has_motion:
                long_without_motion.append(scene.get("id") or index + 1)
        if long_without_motion:
            failures.append(
                {
                    "code": "explainer_long_scene_without_motion",
                    "message": "无头科普超过14秒的镜头必须有明确的内部动画行为。",
                    "scene_ids": long_without_motion[:20],
                }
            )

    composition_keys = [composition_key(scene) for scene in scenes]
    repeated = [] if is_explainer else [(key, count) for key, count in run_lengths(composition_keys) if count > 2]
    if repeated:
        failures.append(
            {
                "code": "composition_repetition",
                "message": "同一 speaker/material/PIP 构图连续重复超过 2 个分镜。",
                "runs": [{"composition": list(key), "count": count} for key, count in repeated],
            }
        )

    forbidden_motion = ["scanline", "yellow", "sweep", "扫描线", "黄线", "扫光", "横扫"]
    bad_motion = []
    for scene in scenes:
        motion = str(scene.get("html_animation_behavior") or scene.get("motion") or "")
        if any(token in motion for token in forbidden_motion):
            bad_motion.append({"id": scene.get("id"), "motion": motion})
    if bad_motion:
        failures.append(
            {
                "code": "forbidden_scan_motion",
                "message": "出现已被否定的扫描线/黄线/扫光动效。",
                "scenes": bad_motion[:20],
            }
        )

    evidence_scenes = [scene for scene in scenes if is_evidence_scene(scene)]
    if scenes and is_talking_head and len(evidence_scenes) / len(scenes) < 0.35:
        warnings.append(
            {
                "code": "evidence_ratio_low",
                "message": "证据镜头占比偏低，金融口播容易显得空。",
                "actual_ratio": round(len(evidence_scenes) / len(scenes), 3),
                "target_min": 0.45,
            }
        )
    if scenes and is_explainer and len(evidence_scenes) / len(scenes) < 0.35:
        warnings.append(
            {
                "code": "explainer_evidence_ratio_low",
                "message": "无头金融科普的证据/数据镜头占比偏低。",
                "actual_ratio": round(len(evidence_scenes) / len(scenes), 3),
                "target_min": 0.35,
            }
        )

    missing_authenticity = [
        scene.get("id") or index + 1
        for index, scene in enumerate(evidence_scenes)
        if not scene.get("evidence_authenticity")
    ]
    if missing_authenticity:
        warnings.append(
            {
                "code": "evidence_authenticity_missing",
                "message": "证据镜头应标注 real_data / source_screenshot / user_claim_card / schematic，避免伪证据。",
                "scene_ids": missing_authenticity[:20],
                "count": len(missing_authenticity),
            }
        )

    asset_claims: dict[str, set[str]] = {}
    incomplete_bindings: list[dict[str, Any]] = []
    if is_bound_evidence_plan:
        for scene in evidence_scenes:
            authenticity = str(scene.get("evidence_authenticity") or "")
            asset_ids = [str(item) for item in scene.get("evidence_asset_ids") or [] if item]
            binding = scene.get("evidence_binding") or {}
            claim_id = str(binding.get("claim_id") or scene.get("id") or "")
            relation = str(binding.get("relation") or "")
            source_locator = binding.get("source_locator")
            if authenticity in {"real_data", "source_screenshot"} and (
                not asset_ids or not claim_id or relation != "direct" or not source_locator
            ):
                incomplete_bindings.append(
                    {
                        "id": scene.get("id"),
                        "authenticity": authenticity,
                        "asset_ids": asset_ids,
                        "relation": relation or None,
                        "source_locator": source_locator,
                    }
                )
            if relation == "direct":
                for asset_id in asset_ids:
                    asset_claims.setdefault(asset_id, set()).add(claim_id)
        if incomplete_bindings:
            failures.append(
                {
                    "code": "evidence_binding_incomplete",
                    "message": "强证据镜头必须绑定具体命题、direct 关系和可复核的来源定位。",
                    "scenes": incomplete_bindings[:20],
                    "count": len(incomplete_bindings),
                }
            )
        overused_assets = [
            {"asset_id": asset_id, "distinct_claim_count": len(claim_ids), "claim_ids": sorted(claim_ids)[:12]}
            for asset_id, claim_ids in asset_claims.items()
            if len(claim_ids) > 4
        ]
        if overused_assets:
            failures.append(
                {
                    "code": "evidence_asset_overused",
                    "message": "同一素材被当作过多不同命题的直接证据，需拆分数据、截图区域或降级为背景/情境素材。",
                    "assets": overused_assets,
                }
            )

    layout_counts = Counter(composition_key(scene) for scene in scenes)
    return {
        "schema_version": "dasheng.video_scene_plan_quality_gate.v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "pass" if not failures else "fail",
        "lane": lane,
        "metrics": {
            "scene_count": len(scenes),
            "duration_sec": round(total_duration, 3),
            "cuts_per_min": round(cuts_per_min, 2),
            "effective_visual_count": effective_visual_count,
            "effective_visual_changes_per_min": round(effective_visual_changes_per_min, 2),
            "avg_scene_duration_sec": round(avg_duration, 2),
            "median_scene_duration_sec": round(median_duration, 2),
            "evidence_scene_count": len(evidence_scenes),
            "evidence_ratio": round(len(evidence_scenes) / len(scenes), 3) if scenes else 0.0,
            "unique_evidence_asset_count": len(asset_claims),
            "max_distinct_claims_per_asset": max((len(value) for value in asset_claims.values()), default=0),
            "composition_unique_count": len(layout_counts),
            "top_compositions": [
                {"composition": list(key), "count": count}
                for key, count in layout_counts.most_common(8)
            ],
        },
        "failures": failures,
        "warnings": warnings,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit a Dasheng video scene plan for production-grade director quality.")
    parser.add_argument("scene_plan")
    parser.add_argument("--output", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.scene_plan).expanduser().resolve()
    report = audit_scene_plan(load_json(path))
    report["scene_plan"] = str(path)
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
