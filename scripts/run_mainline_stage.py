#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from canonical_workflow import (
    WorkflowContractError,
    canonical_manifest_path,
    canonical_stage_dir,
    ensure_final_structure_gate,
    ensure_material_acceptance_gate,
    ensure_publish_decision_gate,
    ensure_selected_topics_gate,
    ensure_stage_manifest,
)


ROOT = Path(__file__).resolve().parents[1]


def run_command(args: list[str]) -> None:
    subprocess.run(args, cwd=str(ROOT), check=True)


def resolve_intake_inputs(run_id: str | None, intake_file: str | None) -> tuple[str, str]:
    if intake_file:
        resolved = Path(intake_file).expanduser().resolve()
        if not resolved.exists():
            raise WorkflowContractError(f"intake 文件不存在：{resolved}")
        if run_id:
            return str(resolved), run_id
        if resolved.parent.name == "raw":
            return str(resolved), resolved.parent.parent.name
        raise WorkflowContractError("提供 --input-file 时必须同时提供 --run-id，或使用 canonical raw/intake_records.json 路径。")
    if not run_id:
        raise WorkflowContractError("brief 阶段必须提供 --run-id 或 --input-file；不再允许猜最新目录。")
    intake_manifest = canonical_manifest_path("intake", run_id)
    ensure_stage_manifest(intake_manifest, "intake")
    intake_path = canonical_stage_dir("intake", run_id) / "raw" / "intake_records.json"
    if not intake_path.exists():
        raise WorkflowContractError(f"缺少 canonical intake_records.json：{intake_path}")
    return str(intake_path), run_id


def resolve_draft_inputs(run_id: str) -> tuple[str, str]:
    brief_manifest = canonical_manifest_path("brief", run_id)
    ensure_stage_manifest(brief_manifest, "brief")
    brief_dir = canonical_stage_dir("brief", run_id)
    selected_topics = brief_dir / "selected_topics.json"
    topic_cards = brief_dir / "topic_cards.json"
    ensure_selected_topics_gate(selected_topics)
    if not topic_cards.exists():
        raise WorkflowContractError(f"缺少 topic_cards.json：{topic_cards}")
    return str(selected_topics), str(topic_cards)


def resolve_material_manifest(run_id: str | None, draft_manifest: str | None) -> str:
    manifest = (
        Path(draft_manifest).expanduser().resolve()
        if draft_manifest
        else canonical_manifest_path("draft", run_id or "")
    )
    ensure_stage_manifest(manifest, "draft")
    ensure_final_structure_gate(manifest.parent / "final_structure_snapshot.json")
    return str(manifest)


def resolve_rewrite_manifest(run_id: str | None, material_manifest: str | None) -> str:
    manifest = (
        Path(material_manifest).expanduser().resolve()
        if material_manifest
        else canonical_manifest_path("material", run_id or "")
    )
    ensure_stage_manifest(manifest, "material")
    ensure_material_acceptance_gate(manifest.parent / "material_acceptance.json")
    return str(manifest)


def resolve_publish_manifests(
    run_id: str | None,
    rewrite_manifest: str | None,
    material_manifest: str | None,
    publish_decision: str | None,
) -> tuple[str, str, str]:
    rewrite_path = (
        Path(rewrite_manifest).expanduser().resolve()
        if rewrite_manifest
        else canonical_manifest_path("rewrite", run_id or "")
    )
    material_path = (
        Path(material_manifest).expanduser().resolve()
        if material_manifest
        else canonical_manifest_path("material", run_id or "")
    )
    decision_path = (
        Path(publish_decision).expanduser().resolve()
        if publish_decision
        else canonical_stage_dir("publish", run_id or "") / "publish_decision.json"
    )
    ensure_stage_manifest(rewrite_path, "rewrite")
    ensure_stage_manifest(material_path, "material")
    ensure_publish_decision_gate(decision_path)
    return str(rewrite_path), str(material_path), str(decision_path)


def resolve_postmortem_manifest(run_id: str | None, publish_manifest: str | None) -> str:
    manifest = (
        Path(publish_manifest).expanduser().resolve()
        if publish_manifest
        else canonical_manifest_path("publish", run_id or "")
    )
    ensure_stage_manifest(manifest, "publish")
    return str(manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical 大圣 Daily mainline stage runner")
    subparsers = parser.add_subparsers(dest="stage", required=True)

    intake = subparsers.add_parser("intake")
    intake.add_argument("--run-id")

    brief = subparsers.add_parser("brief")
    brief.add_argument("--run-id")
    brief.add_argument("--input-file")
    brief.add_argument("--manual-topic", action="append", default=[])

    draft = subparsers.add_parser("draft")
    draft.add_argument("--run-id", required=True)
    draft.add_argument("--output-dir")

    material = subparsers.add_parser("material")
    material.add_argument("--run-id")
    material.add_argument("--draft-manifest")

    rewrite = subparsers.add_parser("rewrite")
    rewrite.add_argument("--run-id")
    rewrite.add_argument("--material-manifest")
    rewrite.add_argument("--source-root", required=True)
    rewrite.add_argument("--final-structure")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--run-id")
    publish.add_argument("--rewrite-manifest")
    publish.add_argument("--material-manifest")
    publish.add_argument("--publish-decision")
    publish.add_argument("--reuse-existing-video-supplement", action="store_true")

    postmortem = subparsers.add_parser("postmortem")
    postmortem.add_argument("--run-id")
    postmortem.add_argument("--publish-manifest")

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--run-id")
    doctor.add_argument("--latest", action="store_true")
    doctor.add_argument("--strict", action="store_true")

    args = parser.parse_args()

    if args.stage == "intake":
        command = ["python3", str(ROOT / "scripts/run_stage1_intake.py")]
        if args.run_id:
            command.extend(["--run-id", args.run_id])
        run_command(command)
        return

    if args.stage == "brief":
        intake_file, run_id = resolve_intake_inputs(args.run_id, args.input_file)
        run_command(
            [
                "python3",
                str(ROOT / "scripts/phase2_rebuilder.py"),
                intake_file,
                str(canonical_stage_dir("brief", run_id)),
                "--run-id",
                run_id,
                *sum([["--manual-topic", topic] for topic in args.manual_topic], []),
            ]
        )
        return

    if args.stage == "draft":
        selected_topics, topic_cards = resolve_draft_inputs(args.run_id)
        command = [
            "python3",
            str(ROOT / "scripts/build_stage3_draft.py"),
            selected_topics,
            topic_cards,
        ]
        if args.output_dir:
            command.extend(["--output-dir", args.output_dir])
        run_command(command)
        return

    if args.stage == "material":
        if not args.run_id and not args.draft_manifest:
            raise WorkflowContractError("material 阶段必须提供 --run-id 或 --draft-manifest。")
        draft_manifest = resolve_material_manifest(args.run_id, args.draft_manifest)
        run_command(["python3", str(ROOT / "scripts/material_execute_pack.py"), "--draft-manifest", draft_manifest])
        return

    if args.stage == "rewrite":
        if not args.run_id and not args.material_manifest:
            raise WorkflowContractError("rewrite 阶段必须提供 --run-id 或 --material-manifest。")
        material_manifest = resolve_rewrite_manifest(args.run_id, args.material_manifest)
        run_command(
            [
                "python3",
                str(ROOT / "scripts/rewrite_rerun_with_final_structure.py"),
                "--material-manifest",
                material_manifest,
                "--source-root",
                args.source_root,
                *([] if not args.final_structure else ["--final-structure", args.final_structure]),
            ]
        )
        return

    if args.stage == "publish":
        if not args.run_id and not (args.rewrite_manifest and args.material_manifest and args.publish_decision):
            raise WorkflowContractError("publish 阶段必须提供 --run-id，或同时提供 rewrite/material manifest 与 publish_decision。")
        rewrite_manifest, material_manifest, publish_decision = resolve_publish_manifests(
            args.run_id,
            args.rewrite_manifest,
            args.material_manifest,
            args.publish_decision,
        )
        run_command(
            [
                "python3",
                str(ROOT / "scripts/publish_video_supplement.py"),
                "--rewrite-manifest",
                rewrite_manifest,
                "--material-manifest",
                material_manifest,
                "--publish-decision",
                publish_decision,
                *(["--reuse-existing-video-supplement"] if args.reuse_existing_video_supplement else []),
            ]
        )
        return

    if args.stage == "postmortem":
        if not args.run_id and not args.publish_manifest:
            raise WorkflowContractError("postmortem 阶段必须提供 --run-id 或 --publish-manifest。")
        publish_manifest = resolve_postmortem_manifest(args.run_id, args.publish_manifest)
        run_command(
            [
                "python3",
                str(ROOT / "scripts/postmortem_writeback.py"),
                "--publish-manifest",
                publish_manifest,
            ]
        )
        return

    if args.stage == "doctor":
        command = ["python3", str(ROOT / "scripts/workflow_doctor.py")]
        if args.run_id:
            command.extend(["--run-id", args.run_id])
        if args.latest:
            command.append("--latest")
        if args.strict:
            command.append("--strict")
        run_command(command)
        return


if __name__ == "__main__":
    main()
