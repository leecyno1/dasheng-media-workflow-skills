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


def resolve_publish_manifests(
    run_id: str | None,
    draft_manifest: str | None,
    publish_decision: str | None,
) -> tuple[str, str]:
    manifest = (
        Path(draft_manifest).expanduser().resolve()
        if draft_manifest
        else canonical_manifest_path("draft", run_id or "")
    )
    ensure_stage_manifest(manifest, "draft")
    ensure_final_structure_gate(manifest.parent / "final_structure_snapshot.json")
    decision_path = (
        Path(publish_decision).expanduser().resolve()
        if publish_decision
        else canonical_stage_dir("publish", run_id or "") / "publish_decision.json"
    )
    ensure_publish_decision_gate(decision_path)
    return str(manifest), str(decision_path)


def resolve_postmortem_manifest(run_id: str | None, publish_manifest: str | None) -> str:
    manifest = (
        Path(publish_manifest).expanduser().resolve()
        if publish_manifest
        else canonical_manifest_path("publish", run_id or "")
    )
    ensure_stage_manifest(manifest, "publish")
    return str(manifest)


def build_paradigm_command(args: argparse.Namespace) -> list[str]:
    if not args.run_id:
        raise WorkflowContractError("paradigm 阶段必须提供 --run-id。")
    if not args.samples:
        raise WorkflowContractError("paradigm 阶段必须至少提供一个样本文件。")
    command = [
        "python3",
        str(ROOT / "scripts/build_paradigm_profile.py"),
        *args.samples,
        "--run-id",
        args.run_id,
    ]
    if args.profile_name:
        command.extend(["--profile-name", args.profile_name])
    if args.sample_type:
        command.extend(["--sample-type", args.sample_type])
    for scenario in args.scenario:
        command.extend(["--scenario", scenario])
    for channel in args.channel:
        command.extend(["--channel", channel])
    if args.bind_style_dna:
        command.extend(["--bind-style-dna", args.bind_style_dna])
    if args.output_dir:
        command.extend(["--output-dir", args.output_dir])
    if args.no_ai:
        command.append("--no-ai")
    return command


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical 大圣 Daily mainline stage runner")
    subparsers = parser.add_subparsers(dest="stage", required=True)

    intake = subparsers.add_parser("intake")
    intake.add_argument("--run-id")

    paradigm = subparsers.add_parser("paradigm")
    paradigm.add_argument("samples", nargs="*")
    paradigm.add_argument("--run-id", required=True)
    paradigm.add_argument("--profile-name")
    paradigm.add_argument("--sample-type", default="standard_article")
    paradigm.add_argument("--scenario", action="append", default=[])
    paradigm.add_argument("--channel", action="append", default=[])
    paradigm.add_argument("--bind-style-dna", default="none")
    paradigm.add_argument("--output-dir")
    paradigm.add_argument("--no-ai", action="store_true")

    brief = subparsers.add_parser("brief")
    brief.add_argument("--run-id")
    brief.add_argument("--input-file")
    brief.add_argument("--manual-topic", action="append", default=[])
    brief.add_argument("--agent-cards-file")

    draft = subparsers.add_parser("draft")
    draft.add_argument("--run-id", required=True)
    draft.add_argument("--output-dir")

    publish = subparsers.add_parser("publish")
    publish.add_argument("--run-id")
    publish.add_argument("--draft-manifest")
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

    if args.stage == "paradigm":
        run_command(build_paradigm_command(args))
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
                *([] if not args.agent_cards_file else ["--agent-cards-file", args.agent_cards_file]),
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

    if args.stage == "publish":
        if not args.run_id and not (args.draft_manifest and args.publish_decision):
            raise WorkflowContractError("publish 阶段必须提供 --run-id，或同时提供 draft_manifest 与 publish_decision。")
        draft_manifest, publish_decision = resolve_publish_manifests(
            args.run_id,
            args.draft_manifest,
            args.publish_decision,
        )
        run_command(
            [
                "python3",
                str(ROOT / "scripts/publish_video_supplement.py"),
                "--draft-manifest",
                draft_manifest,
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
