from __future__ import annotations

import json
import shutil
from pathlib import Path

from path_config import get_desktop_root


DESKTOP_ROOT = get_desktop_root()


def ensure_run_root(run_id: str) -> Path:
    target = DESKTOP_ROOT / run_id
    target.mkdir(parents=True, exist_ok=True)
    return target


def _copy_file(src: Path, dst: Path) -> None:
    if not src.exists() or not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _copy_dir(src: Path, dst: Path) -> None:
    if not src.exists() or not src.is_dir():
        return
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def _write_manifest(run_root: Path, stage: str, exported: list[str]) -> None:
    manifest_path = run_root / f"{stage}__desktop_export_manifest.json"
    manifest_path.write_text(
        json.dumps({"stage": stage, "desktop_root": str(run_root), "exported": exported}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _remove_existing(run_root: Path, patterns: list[str]) -> None:
    for pattern in patterns:
        for target in run_root.glob(pattern):
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()


def sync_intake_to_desktop(run_id: str, stage_dir: Path) -> Path:
    run_root = ensure_run_root(run_id)
    exported: list[str] = []
    for name in [
        "notes/01_内容采集_报告.md",
        "notes/01_内容采集_底稿.md",
        "channel_top10.json",
        "event_clusters.json",
        "brief_input.json",
        "intake_manifest.json",
    ]:
        src = stage_dir / name
        if src.exists():
            dst = run_root / f"{run_id}__{src.name}"
            _copy_file(src, dst)
            exported.append(str(dst))
    _write_manifest(run_root, "intake", exported)
    return run_root


def sync_brief_to_desktop(run_id: str, stage_dir: Path) -> Path:
    run_root = ensure_run_root(run_id)
    exported: list[str] = []
    for name in [
        "02_编辑Brief库.md",
        "02_研究Brief库.md",
        "02_编辑Brief_报告.md",
        "topic_cards.json",
        "selected_topics.template.json",
        "selected_topics.json",
        "brief_manifest.json",
    ]:
        src = stage_dir / name
        if src.exists():
            dst = run_root / f"{run_id}__{src.name}"
            _copy_file(src, dst)
            exported.append(str(dst))
    _write_manifest(run_root, "brief", exported)
    return run_root


def sync_draft_to_desktop(run_id: str, stage_dir: Path) -> Path:
    run_root = ensure_run_root(run_id)
    exported: list[str] = []
    patterns = [
        "03_初稿_报告.md",
        "draft_manifest.json",
        "final_structure_snapshot.json",
        "selected_topics_for_draft.json",
        "03_标准初稿_*.md",
        "03_ReasoningSheet_*.md",
        "03_ReasoningSheet_*.json",
    ]
    for pattern in patterns:
        for src in sorted(stage_dir.glob(pattern)):
            dst = run_root / f"{run_id}__{src.name}"
            _copy_file(src, dst)
            exported.append(str(dst))
    _write_manifest(run_root, "draft", exported)
    return run_root


def sync_rewrite_to_desktop(run_id: str, stage_dir: Path) -> Path:
    run_root = ensure_run_root(run_id)
    exported: list[str] = []
    manifest = stage_dir / "rewrite_manifest.json"
    if manifest.exists():
        dst = run_root / f"{run_id}__rewrite_manifest.json"
        _copy_file(manifest, dst)
        exported.append(str(dst))
    for topic_dir in sorted([item for item in stage_dir.iterdir() if item.is_dir()]):
        for src in sorted(topic_dir.glob("*.md")):
            dst = run_root / f"{run_id}__{topic_dir.name}__{src.name}"
            _copy_file(src, dst)
            exported.append(str(dst))
        meta_file = topic_dir / "meta.json"
        if meta_file.exists():
            dst = run_root / f"{run_id}__{topic_dir.name}__meta.json"
            _copy_file(meta_file, dst)
            exported.append(str(dst))
    _write_manifest(run_root, "rewrite", exported)
    return run_root


def sync_material_to_desktop(run_id: str, canonical_stage_dir: Path, runtime_material_dir: Path, pack_root: Path) -> Path:
    run_root = ensure_run_root(run_id)
    _remove_existing(
        run_root,
        [
            f"{run_id}__04_Material*",
            f"{run_id}__05_Material*",
            f"{run_id}__material*",
            "material__desktop_export_manifest.json",
        ],
    )
    exported: list[str] = []
    for src in [
        canonical_stage_dir / "material_manifest.json",
        canonical_stage_dir / "material_acceptance.json",
        runtime_material_dir / "04_MaterialPack.md",
        runtime_material_dir / "04_Material_报告.md",
        runtime_material_dir / "material-packs.json",
        runtime_material_dir / "material_ai_inputs.json",
        runtime_material_dir / "material_ai_decisions.json",
    ]:
        if src.exists():
            dst = run_root / f"{run_id}__{src.name}"
            _copy_file(src, dst)
            exported.append(str(dst))
    for topic_dir in sorted([item for item in pack_root.iterdir() if item.is_dir()]):
        dst = run_root / f"{run_id}__material__{topic_dir.name}"
        _copy_dir(topic_dir, dst)
        exported.append(str(dst))
    _write_manifest(run_root, "material", exported)
    return run_root
