#!/usr/bin/env python3
"""Dasheng video director entrypoint.

This script turns article HTML or talking-head captions into a governed
scene_plan package before material generation/rendering.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from build_storyboard_template_review_table import build_html as build_review_html
from project_run_manifest import add_artifact, is_safe_output_root, load_manifest, save_manifest, set_stage_status, validate_manifest
from video_director_timeline import (
    build_talking_head_timeline,
    load_captions_json,
    load_srt,
    remap_captions_to_roughcut,
    run_ffprobe_duration,
)
from video_explainer_storyboard import build_explainer_storyboard, load_router, parse_html_article, write_preview_html
from video_pipeline_governance import build_checkpoint, load_pipeline, validate_artifact
from video_director_tool_router import apply_routes_to_scene_plan
from video_scene_plan_quality_gate import audit_scene_plan


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def scene_end(scene: dict[str, Any]) -> float:
    if "end_sec" in scene:
        return float(scene["end_sec"])
    if "end" in scene:
        return float(scene["end"])
    start = float(scene.get("start_sec", scene.get("start", 0.0)) or 0.0)
    duration = float(scene.get("duration_sec", scene.get("duration", 0.0)) or 0.0)
    return start + duration


def motion_text(scene: dict[str, Any]) -> str:
    explicit = str(scene.get("html_animation_behavior") or "").strip()
    if explicit:
        return explicit
    motion = scene.get("motion") or {}
    if isinstance(motion, dict):
        parts = [str(motion.get(key) or "").strip() for key in ["entrance", "focus_change", "exit"]]
        return " -> ".join(part for part in parts if part)
    return str(motion or "").strip()


def normalize_explainer_scene_plan(storyboard: dict[str, Any]) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for index, scene in enumerate(storyboard.get("scenes") or [], 1):
        start = float(scene.get("start_sec", 0.0) or 0.0)
        duration = float(scene.get("duration_sec", 0.0) or 0.0)
        evidence_refs: list[str] = []
        if scene.get("evidence_required"):
            evidence_refs.append(str((scene.get("variables") or {}).get("source") or scene.get("content_part") or "article_html"))
        scenes.append(
            {
                **scene,
                "id": str(scene.get("id") or f"scene_{index:03d}"),
                "title": str(scene.get("title") or f"分镜 {index}"),
                "start_sec": round(start, 3),
                "end_sec": round(scene_end(scene), 3),
                "duration_sec": round(duration, 3),
                "beat_class": str(scene.get("beat_class") or "claim"),
                "template_id": str(scene.get("template_id") or "deck-swiss-international"),
                "evidence_refs": scene.get("evidence_refs") or evidence_refs,
                "html_animation_behavior": motion_text(scene) or "live_html_motion_required",
                "risk_notes": scene.get("risk_notes")
                or [
                    "Verify template is rendered as live HTML motion, not a static screenshot.",
                    "Check subtitle and chart/table safe zones before render.",
                ],
            }
        )
    return {
        "schema_version": "dasheng.video.scene_plan.v1",
        "lane": "explainer_html_video",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "title": storyboard.get("title") or "无真人科普视频",
        "source_storyboard_schema": storyboard.get("schema_version"),
        "source_html": storyboard.get("source_html"),
        "aspect": storyboard.get("aspect") or "9:16",
        "renderer": storyboard.get("renderer") or "html-video",
        "duration_estimate_sec": storyboard.get("duration_estimate_sec"),
        "director_state_machine": storyboard.get("director_state_machine"),
        "style": storyboard.get("style"),
        "scenes": scenes,
    }


def segment_index(segment: dict[str, Any]) -> int:
    raw = str(segment.get("id") or "")
    digits = "".join(ch for ch in raw if ch.isdigit())
    if digits:
        return max(1, int(digits))
    return 1


def pick_template(pool: list[str], index: int) -> str:
    if not pool:
        return "frame-electric-studio"
    return pool[(index - 1) % len(pool)]


def template_for_talking_head_shot(segment: dict[str, Any]) -> str:
    index = segment_index(segment)
    shot = str(segment.get("shot") or "")
    beat_class = str(segment.get("beat_class") or "")
    if shot == "chart_card":
        return pick_template(["frame-data-chart-nyt", "frame-nyt-graph", "frame-data-rollup", "frame-pentagram-stat"], index)
    if shot == "document_zoom":
        return pick_template(["doc-kami-parchment", "frame-macos-notification", "social-x-post-card", "article-magazine"], index)
    if shot == "html_logic_overlay":
        return pick_template(["frame-decision-tree", "frame-build-minimal", "frame-swiss-grid", "deck-blueprint"], index)
    if shot == "broll_with_pip":
        return pick_template(
            [
                "frame-light-leak-cinema",
                "frame-liquid-bg-hero",
                "frame-creative-voltage",
                "frame-takram-organic",
                "frame-warm-grain",
                "frame-product-promo",
                "deck-guizang-editorial",
                "deck-swiss-international",
            ],
            index,
        )
    if beat_class == "hook":
        return pick_template(["frame-glitch-title", "vfx-text-cursor", "frame-liquid-bg-hero"], index)
    if beat_class == "recap":
        return pick_template(["frame-logo-outro", "frame-bold-signal", "frame-bold-poster"], index)
    if shot in {"claim_closeup", "talking_head_punch_in"}:
        return pick_template(["frame-electric-studio", "frame-kinetic-type", "frame-bold-signal", "frame-play-mode"], index)
    return pick_template(["frame-electric-studio", "frame-kinetic-type", "frame-swiss-grid", "frame-vignelli", "frame-warm-grain"], index)


def evidence_authenticity_for_segment(segment: dict[str, Any]) -> str | None:
    overlay = segment.get("overlay") or {}
    overlay_type = str(overlay.get("type") or "")
    beat_class = str(segment.get("beat_class") or "")
    shot = str(segment.get("shot") or "")
    if overlay_type == "real_data_chart_or_table":
        return "real_data"
    if overlay_type == "source_document_or_news_card":
        return "source_screenshot"
    if overlay_type in {"logic_chain_overlay", "broll_or_html_sticker"}:
        return "schematic"
    if beat_class in {"evidence_data", "evidence_document"} or shot in {"chart_card", "document_zoom"}:
        return "user_claim_card"
    return None


def normalize_talking_head_scene_plan(timeline: dict[str, Any]) -> dict[str, Any]:
    scenes: list[dict[str, Any]] = []
    for index, segment in enumerate(timeline.get("segments") or [], 1):
        start = float(segment.get("start", 0.0) or 0.0)
        end = float(segment.get("end", start) or start)
        overlay = segment.get("overlay") or {}
        evidence_refs: list[str] = []
        if overlay.get("required"):
            evidence_refs.append(str(overlay.get("source_hint") or overlay.get("type") or "speaker_caption"))
        scenes.append(
            {
                "id": str(segment.get("id") or f"scene_{index:03d}"),
                "title": str(segment.get("caption") or f"口播分镜 {index}")[:42],
                "start_sec": round(start, 3),
                "end_sec": round(end, 3),
                "duration_sec": round(float(segment.get("duration", end - start) or end - start), 3),
                "beat_class": str(segment.get("beat_class") or "claim"),
                "template_id": template_for_talking_head_shot(segment),
                "content_part": str(overlay.get("type") or segment.get("shot") or "talking_head"),
                "narration": segment.get("caption"),
                "evidence_refs": evidence_refs,
                **({"evidence_authenticity": evidence_authenticity_for_segment(segment)} if evidence_authenticity_for_segment(segment) else {}),
                "speaker_state": segment.get("speaker_state"),
                "material_state": segment.get("material_state"),
                "pip_shape": segment.get("pip_shape"),
                "shot": segment.get("shot"),
                "driver_scores": segment.get("driver_scores"),
                "html_animation_behavior": segment.get("html_animation_behavior") or "live_overlay_motion_required",
                "transition_in": segment.get("transition_in"),
                "transition_out": segment.get("transition_out"),
                "transition_to_next": segment.get("transition_out") or segment.get("transition"),
                "audio": segment.get("audio"),
                "collision_policy": segment.get("collision_policy"),
                "risk_notes": [segment.get("qc_risk") or "Verify roughcut gate and subtitle sync before render."],
            }
        )
    return {
        "schema_version": "dasheng.video.scene_plan.v1",
        "lane": "talking_head_video",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "title": timeline.get("title") or "真人口播视频",
        "source_timeline_schema": timeline.get("schema_version"),
        "source_video": timeline.get("source_video"),
        "duration_estimate_sec": timeline.get("duration_sec"),
        "aspect": timeline.get("aspect") or "9:16",
        "roughcut_gate": timeline.get("roughcut_gate"),
        "style_reference": timeline.get("style_reference"),
        "director_state_machine": timeline.get("director_state_machine"),
        "safe_areas": timeline.get("safe_areas"),
        "qc_targets": timeline.get("qc_targets"),
        "timeline_alignment": timeline.get("timeline_alignment"),
        "scenes": scenes,
    }


def register_outputs_to_project_manifest(project_manifest: Path, outputs: dict[str, Path], *, stage_status: str) -> None:
    manifest = load_manifest(project_manifest)
    set_stage_status(
        manifest,
        stage_name="scene_plan",
        status=stage_status,
        checkpoint_path=str(outputs.get("checkpoint", "")),
        review_path=str(outputs.get("review_html", "")),
    )
    for artifact_type, path in outputs.items():
        if path.exists():
            add_artifact(manifest, stage_name="scene_plan", artifact_type=artifact_type, path=str(path.resolve()))
    errors = validate_manifest(manifest)
    if errors:
        raise RuntimeError(f"project_run_manifest invalid: {json.dumps(errors, ensure_ascii=False)}")
    save_manifest(manifest, project_manifest)


def build_explainer_package(args: argparse.Namespace, output_dir: Path) -> dict[str, Path]:
    article_html = Path(args.article_html).expanduser().resolve()
    router = load_router(Path(args.template_router).expanduser().resolve() if args.template_router else None)
    storyboard = build_explainer_storyboard(
        parse_html_article(article_html),
        source_html=str(article_html),
        duration_target_sec=args.duration_target_sec,
        router=router,
    )
    raw_storyboard_path = output_dir / "explainer_storyboard.raw.json"
    scene_plan_path = output_dir / "scene_plan.json"
    quality_gate_path = output_dir / "scene_plan_quality_gate.json"
    preview_path = output_dir / "storyboard_preview.html"
    review_path = output_dir / "storyboard_template_review.html"
    checkpoint_path = output_dir / "director_checkpoint.json"
    routing_plan_path = output_dir / "tool_routing_plan.json"

    scene_plan = normalize_explainer_scene_plan(storyboard)
    disable_tool_routing = bool(getattr(args, "disable_tool_routing", False))
    if not disable_tool_routing:
        tool_registry = getattr(args, "tool_registry", str(PROJECT_ROOT / "configs/video/tool_registry.json"))
        project_registry = getattr(args, "project_registry", str(PROJECT_ROOT / "configs/external/reserved_projects.json"))
        scene_plan, routing_plan = apply_routes_to_scene_plan(
            scene_plan,
            tool_registry_path=Path(tool_registry).expanduser().resolve(),
            project_registry_path=Path(project_registry).expanduser().resolve(),
        )
        write_json(routing_plan_path, routing_plan)
    errors = validate_artifact("scene_plan", scene_plan)
    if errors:
        raise RuntimeError(f"scene_plan invalid: {json.dumps(errors, ensure_ascii=False)}")
    write_json(raw_storyboard_path, storyboard)
    write_json(scene_plan_path, scene_plan)
    write_json(quality_gate_path, audit_scene_plan(scene_plan))
    write_preview_html(preview_path, scene_plan)
    review_path.write_text(
        build_review_html(scene_plan, output=review_path, preview_roots=[Path(item).expanduser().resolve() for item in args.template_preview_root], source_storyboard=scene_plan_path),
        encoding="utf-8",
    )
    checkpoint = build_checkpoint(
        load_pipeline("explainer_html"),
        "scene_plan",
        artifact_paths={
            "scene_plan": str(scene_plan_path),
            "quality_gate": str(quality_gate_path),
            "review": str(review_path),
            **({"tool_routing_plan": str(routing_plan_path)} if not disable_tool_routing else {}),
        },
        status="pending_review",
        notes="Review storyboard_template_review.html before material generation.",
    )
    write_json(checkpoint_path, checkpoint)
    return {
        "raw_storyboard": raw_storyboard_path,
        "scene_plan": scene_plan_path,
        "scene_plan_quality_gate": quality_gate_path,
        "preview_html": preview_path,
        "review_html": review_path,
        "checkpoint": checkpoint_path,
        **({"tool_routing_plan": routing_plan_path} if not disable_tool_routing else {}),
    }


def build_talking_head_package(args: argparse.Namespace, output_dir: Path) -> dict[str, Path]:
    if args.captions_json:
        captions = load_captions_json(Path(args.captions_json).expanduser().resolve())
    else:
        captions = load_srt(Path(args.srt).expanduser().resolve())
    timeline_alignment = None
    roughcut_edl = getattr(args, "roughcut_edl", "")
    if roughcut_edl:
        captions, timeline_alignment = remap_captions_to_roughcut(
            captions,
            Path(roughcut_edl).expanduser().resolve(),
        )
    source_video = str(Path(args.source_video).expanduser().resolve()) if args.source_video else None
    duration = args.duration
    if duration is None and source_video:
        duration = run_ffprobe_duration(Path(source_video))
    if duration is None and timeline_alignment:
        duration = float(timeline_alignment["output_duration_sec"])
    timeline = build_talking_head_timeline(
        captions,
        title=args.title,
        source_video=source_video,
        duration=duration,
        roughcut_gate=str(Path(args.roughcut_gate).expanduser().resolve()) if args.roughcut_gate else None,
        timeline_alignment=timeline_alignment,
    )
    raw_timeline_path = output_dir / "talking_head_timeline.raw.json"
    scene_plan_path = output_dir / "scene_plan.json"
    quality_gate_path = output_dir / "scene_plan_quality_gate.json"
    review_path = output_dir / "storyboard_template_review.html"
    checkpoint_path = output_dir / "director_checkpoint.json"
    routing_plan_path = output_dir / "tool_routing_plan.json"

    scene_plan = normalize_talking_head_scene_plan(timeline)
    disable_tool_routing = bool(getattr(args, "disable_tool_routing", False))
    if not disable_tool_routing:
        tool_registry = getattr(args, "tool_registry", str(PROJECT_ROOT / "configs/video/tool_registry.json"))
        project_registry = getattr(args, "project_registry", str(PROJECT_ROOT / "configs/external/reserved_projects.json"))
        scene_plan, routing_plan = apply_routes_to_scene_plan(
            scene_plan,
            tool_registry_path=Path(tool_registry).expanduser().resolve(),
            project_registry_path=Path(project_registry).expanduser().resolve(),
        )
        write_json(routing_plan_path, routing_plan)
    errors = validate_artifact("scene_plan", scene_plan)
    if errors:
        raise RuntimeError(f"scene_plan invalid: {json.dumps(errors, ensure_ascii=False)}")
    write_json(raw_timeline_path, timeline)
    write_json(scene_plan_path, scene_plan)
    write_json(quality_gate_path, audit_scene_plan(scene_plan))
    review_path.write_text(
        build_review_html(scene_plan, output=review_path, preview_roots=[Path(item).expanduser().resolve() for item in args.template_preview_root], source_storyboard=scene_plan_path),
        encoding="utf-8",
    )
    checkpoint = build_checkpoint(
        load_pipeline("talking_head"),
        "scene_plan",
        artifact_paths={
            "scene_plan": str(scene_plan_path),
            "quality_gate": str(quality_gate_path),
            "review": str(review_path),
            **({"tool_routing_plan": str(routing_plan_path)} if not disable_tool_routing else {}),
        },
        status="pending_review",
        notes="Review director composition and roughcut gate before material generation.",
    )
    write_json(checkpoint_path, checkpoint)
    return {
        "raw_timeline": raw_timeline_path,
        "scene_plan": scene_plan_path,
        "scene_plan_quality_gate": quality_gate_path,
        "review_html": review_path,
        "checkpoint": checkpoint_path,
        **({"tool_routing_plan": routing_plan_path} if not disable_tool_routing else {}),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a governed Dasheng video director scene_plan package.")
    parser.add_argument("--lane", choices=["explainer_html_video", "talking_head_video"], required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--project-manifest", default="")
    parser.add_argument("--title", default="未命名视频")
    parser.add_argument("--template-preview-root", action="append", default=[])
    parser.add_argument("--tool-registry", default=str(PROJECT_ROOT / "configs" / "video" / "tool_registry.json"))
    parser.add_argument("--project-registry", default=str(PROJECT_ROOT / "configs" / "external" / "reserved_projects.json"))
    parser.add_argument("--disable-tool-routing", action="store_true", help="Build a scene plan without director tool routing annotations.")

    parser.add_argument("--article-html", help="Required for explainer_html_video.")
    parser.add_argument("--duration-target-sec", type=int, default=180)
    parser.add_argument("--template-router", default=str(PROJECT_ROOT / "configs" / "video" / "html_anything_template_router.json"))

    caption_group = parser.add_mutually_exclusive_group()
    caption_group.add_argument("--captions-json")
    caption_group.add_argument("--srt")
    parser.add_argument("--source-video")
    parser.add_argument("--duration", type=float)
    parser.add_argument("--roughcut-gate")
    parser.add_argument("--roughcut-edl", help="Discrete keep-segment EDL from the rough-cut stage.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not is_safe_output_root(output_dir):
        raise SystemExit(f"Unsafe output-dir: {output_dir}. Use ~/Desktop/自媒体创作 or another creator output root.")
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.lane == "explainer_html_video":
        if not args.article_html:
            raise SystemExit("--article-html is required for explainer_html_video")
        outputs = build_explainer_package(args, output_dir)
    else:
        if not args.captions_json and not args.srt:
            raise SystemExit("--captions-json or --srt is required for talking_head_video")
        outputs = build_talking_head_package(args, output_dir)

    if args.project_manifest:
        register_outputs_to_project_manifest(Path(args.project_manifest).expanduser().resolve(), outputs, stage_status="pending_review")

    result = {
        "status": "pending_review",
        "lane": args.lane,
        "output_dir": str(output_dir),
        "outputs": {key: str(path) for key, path in outputs.items()},
        "next_step": "Open storyboard_template_review.html, export storyboard_review_decision.json, then validate the review gate.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
