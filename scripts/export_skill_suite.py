#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_ROOT = ROOT / "openclaw-skill-exports"
FORMAL_SKILLS = [
    "dasheng-media-sop",
    "dasheng-stage-publish",
    "dasheng-daily-intake",
    "dasheng-daily-phase2",
    "dasheng-daily-material",
    "dasheng-daily-postmortem",
    "dasheng-style-profiler",
    "feishu-doc-creator",
]
DOC_FILES = [
    ROOT / "README_自媒体工作台.md",
    ROOT / "引擎/03_全链路SOP工作流/STAGE_INTERFACES.md",
]


def export_suite(target_dir: Path) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    (target_dir / "skills").mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    for skill_name in FORMAL_SKILLS:
        src = ROOT / "skills" / skill_name
        dst = target_dir / "skills" / skill_name
        shutil.copytree(src, dst)
        exported.append(str(dst))
    docs_dir = target_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for doc in DOC_FILES:
        shutil.copy2(doc, docs_dir / doc.name)
        exported.append(str(docs_dir / doc.name))
    manifest = {
        "source_repo": str(ROOT),
        "formal_skills": FORMAL_SKILLS,
        "docs": [path.name for path in DOC_FILES],
        "exported": exported,
    }
    (target_dir / "EXPORT_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="导出当前正式 Dasheng skill 套件")
    parser.add_argument("--target-dir", help="目标目录；默认 openclaw-skill-exports/dasheng-media-workflow-skills-current")
    args = parser.parse_args()

    target_dir = (
        Path(args.target_dir).expanduser().resolve()
        if args.target_dir
        else (DEFAULT_EXPORT_ROOT / "dasheng-media-workflow-skills-current")
    )
    exported_dir = export_suite(target_dir)
    print(str(exported_dir))


if __name__ == "__main__":
    main()
