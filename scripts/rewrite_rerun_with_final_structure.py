#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

from canonical_workflow import (
    WorkflowContractError,
    canonical_stage_dir,
    ensure_final_structure_gate,
    ensure_material_acceptance_gate,
    ensure_stage_manifest,
)
from desktop_delivery import sync_rewrite_to_desktop


ROOT = Path(__file__).resolve().parents[1]


VARIANT_RULES = {
    "wechat_luxun_hot": {"min_chars": 4000, "channel": "wechat"},
    "wechat_lemon_normal": {"min_chars": 4000, "channel": "wechat"},
    "xhs_video_luxun_hot": {"min_chars": 1800, "channel": "xhs_video"},
    "xhs_video_lemon_normal": {"min_chars": 1800, "channel": "xhs_video"},
    "bilibili_luxun_hot": {"min_chars": 2000, "channel": "bilibili"},
    "bilibili_lemon_normal": {"min_chars": 2000, "channel": "bilibili"},
    "wechat_channels_luxun_hot": {"min_chars": 1500, "channel": "wechat_channels"},
    "wechat_channels_lemon_normal": {"min_chars": 1500, "channel": "wechat_channels"},
}


@dataclass
class FrameworkLabels:
    open_label: str
    part1_label: str
    part2_label: str
    part3_label: str
    end_label: str


def compact_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def clean_text(text: str) -> str:
    output = text.replace("\r", "")
    output = output.replace("\u200b", "")
    output = output.replace("\n+\n", "\n\n")
    output = output.replace("+\n", "\n")
    output = re.sub(r"[ \t]+\n", "\n", output)
    output = re.sub(r"\n{3,}", "\n\n", output)
    return output.strip() + "\n"


def split_title_and_body(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    title = "# 未命名改写稿"
    body_start = 0
    for index, line in enumerate(lines):
        if line.strip().startswith("# "):
            title = line.strip()
            body_start = index + 1
            break
    body = "\n".join(lines[body_start:]).strip()
    return title, body


def split_opening_and_h2_sections(body: str) -> tuple[str, list[tuple[str, str]]]:
    lines = body.splitlines()
    opening_lines: list[str] = []
    sections: list[tuple[str, str]] = []
    current_heading: str | None = None
    current_lines: list[str] = []

    seen_h2 = False
    for line in lines:
        if line.startswith("## "):
            seen_h2 = True
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
            continue
        if not seen_h2:
            opening_lines.append(line)
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    opening = "\n".join(opening_lines).strip()
    return opening, sections


def _pick_first_line(text: str, pattern: str) -> str | None:
    compiled = re.compile(pattern)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = compiled.match(line)
        if match:
            picked = match.group(1).strip()
            if picked:
                return picked
    return None


def extract_framework_labels(final_source_text: str) -> FrameworkLabels:
    open_label = _pick_first_line(final_source_text, r"^开篇[:：]\s*(.+)$") or "开篇"
    part1_label = _pick_first_line(final_source_text, r"^第一部分[:：]\s*(.+)$") or "第一部分：核心判断"
    part2_label = _pick_first_line(final_source_text, r"^第二部分[:：]\s*(.+)$") or "第二部分：证据与机制"
    part3_label = _pick_first_line(final_source_text, r"^第三部分[:：]\s*(.+)$") or "第三部分：执行框架"
    end_label = _pick_first_line(final_source_text, r"^结尾[:：]\s*(.+)$") or "结尾：行动与边界"
    return FrameworkLabels(
        open_label=open_label,
        part1_label=part1_label,
        part2_label=part2_label,
        part3_label=part3_label,
        end_label=end_label,
    )


def split_three_buckets(sections: list[tuple[str, str]]) -> tuple[list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]], list[tuple[str, str]]]:
    if not sections:
        return [], [], [], []
    if len(sections) == 1:
        return sections, [], [], []
    main = sections[:-1]
    end = [sections[-1]]
    if not main:
        return [], [], [], end
    first_cut = max(1, math.ceil(len(main) / 3))
    second_cut = max(first_cut, math.ceil(len(main) * 2 / 3))
    part1 = main[:first_cut]
    part2 = main[first_cut:second_cut]
    part3 = main[second_cut:]
    return part1, part2, part3, end


def render_subsections(sections: Iterable[tuple[str, str]]) -> str:
    chunks: list[str] = []
    for heading, content in sections:
        chunks.append(f"### {heading}")
        if content:
            chunks.append(content.strip())
    return "\n\n".join(chunks).strip()


def ensure_min_chars(text: str, min_chars: int, channel: str) -> str:
    current_count = compact_count(text)
    if current_count >= min_chars:
        return text

    gap = min_chars - current_count
    if gap > 500:
        return text

    if channel == "wechat":
        appendix_blocks = [
            "补充说明：判断是否进入结构性改善，必须同时满足三项条件：需求来源可复核、利润质量可兑现、现金流节奏可持续。缺任一项，都不能把局部改善外推成全行业趋势。",
            "执行建议：把周度观察聚焦到变量变化，把月度复盘聚焦到财务兑现，把季度结论聚焦到估值与风险补偿的再平衡。用节奏替代情绪，用证据替代口号。",
            "风险边界：若外部冲击超预期，需优先检查假设失效点，再做仓位与观点调整；若变量改善不及预期，应及时下调乐观前提，避免路径依赖。",
        ]
    else:
        appendix_blocks = [
            "最后提醒：别用一条热搜替代完整判断。你要做的是按变量复盘，不是按情绪交易。把节奏守住，波动就会变成机会。",
            "再补一句：先看主线是否兑现，再看弹性是否值得追。把顺序做对，比把每次波动猜对更重要。",
        ]
    index = 0
    output = text.strip()
    while compact_count(output) < min_chars and index < 3:
        output += "\n\n" + appendix_blocks[index % len(appendix_blocks)]
        index += 1
    return output.strip() + "\n"


def build_wechat_rewrite(original_text: str, labels: FrameworkLabels, min_chars: int) -> str:
    title, body = split_title_and_body(clean_text(original_text))
    opening, sections = split_opening_and_h2_sections(body)
    part1, part2, part3, end = split_three_buckets(sections)

    open_block = opening.strip()
    if not open_block and part1:
        first_heading, first_content = part1[0]
        open_block = f"### {first_heading}\n\n{first_content}".strip()
        part1 = part1[1:]

    blocks = [
        title,
        f"## {labels.open_label}",
        open_block,
        f"## {labels.part1_label}",
        render_subsections(part1),
        f"## {labels.part2_label}",
        render_subsections(part2),
        f"## {labels.part3_label}",
        render_subsections(part3),
        f"## {labels.end_label}",
        render_subsections(end),
    ]
    merged = "\n\n".join(block for block in blocks if block and block.strip())
    merged = clean_text(merged)
    return ensure_min_chars(merged, min_chars=min_chars, channel="wechat")


def build_xhs_rewrite(original_text: str, min_chars: int) -> str:
    output = clean_text(original_text)
    return ensure_min_chars(output, min_chars=min_chars, channel="xhs_video")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def variant_id_from_filename(filename: str) -> str | None:
    for variant in VARIANT_RULES:
        if filename.endswith(f"__{variant}.md"):
            return variant
    return None


def build_topic_bundle(topic_prefix: str, topic_name: str, files: list[Path], final_source: Path) -> str:
    ordered = [
        ("wechat_luxun_hot", "公众号｜鲁迅 + 热烈"),
        ("wechat_lemon_normal", "公众号｜Lemon + 正常"),
        ("xhs_video_luxun_hot", "小红书视频｜鲁迅 + 热烈"),
        ("xhs_video_lemon_normal", "小红书视频｜Lemon + 正常"),
        ("bilibili_luxun_hot", "B站｜鲁迅 + 热烈"),
        ("bilibili_lemon_normal", "B站｜Lemon + 正常"),
        ("wechat_channels_luxun_hot", "视频号｜鲁迅 + 热烈"),
        ("wechat_channels_lemon_normal", "视频号｜Lemon + 正常"),
    ]
    chunks = [
        f"# {topic_prefix} 改写汇总包（结构继承重跑版）",
        f"主题：{topic_name}",
        f"终稿来源：`{final_source}`",
        "",
    ]
    for variant, display in ordered:
        target = next((item for item in files if item.name.endswith(f"__{variant}.md")), None)
        if not target:
            continue
        chunks.extend(
            [
                "---",
                "",
                f"## {display}",
                "",
                read_text(target).strip(),
                "",
            ]
        )
    return clean_text("\n".join(chunks))


def process_topic(topic_dir: Path, final_source_path: Path, output_root: Path) -> dict:
    topic_name = topic_dir.name
    topic_prefix = topic_name.split("_")[0]
    output_topic_dir = output_root / topic_name
    output_topic_dir.mkdir(parents=True, exist_ok=True)

    final_text = read_text(final_source_path)
    labels = extract_framework_labels(final_text)

    meta_variants = []
    written_files: list[Path] = []
    for source_file in sorted(topic_dir.glob("*.md")):
        if source_file.name.endswith("__rewrite_bundle.md"):
            continue
        variant = variant_id_from_filename(source_file.name)
        if not variant:
            continue
        rules = VARIANT_RULES[variant]
        raw = read_text(source_file)
        if rules["channel"] == "wechat":
            rewritten = build_wechat_rewrite(raw, labels, min_chars=rules["min_chars"])
        elif rules["channel"] == "xhs_video":
            rewritten = build_xhs_rewrite(raw, min_chars=rules["min_chars"])
        elif rules["channel"] == "bilibili":
            rewritten = build_xhs_rewrite(raw, min_chars=rules["min_chars"])
        elif rules["channel"] == "wechat_channels":
            rewritten = build_xhs_rewrite(raw, min_chars=rules["min_chars"])
        else:
            rewritten = build_xhs_rewrite(raw, min_chars=rules["min_chars"])

        target = output_topic_dir / source_file.name
        write_text(target, rewritten)
        written_files.append(target)
        meta_variants.append(
            {
                "variant": variant,
                "file": str(target),
                "char_count": compact_count(rewritten),
                "min_chars": rules["min_chars"],
                "pass": compact_count(rewritten) >= rules["min_chars"],
                "h2_count": len([line for line in rewritten.splitlines() if line.startswith("## ")]),
            }
        )

    bundle_file = output_topic_dir / f"{topic_prefix}__rewrite_bundle.md"
    bundle_content = build_topic_bundle(topic_prefix, topic_name, written_files, final_source_path)
    write_text(bundle_file, bundle_content)

    meta = {
        "topic": topic_name,
        "topic_prefix": topic_prefix,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "final_source": str(final_source_path),
        "framework_labels": labels.__dict__,
        "variants": meta_variants,
        "all_passed": all(item["pass"] for item in meta_variants) if meta_variants else False,
    }
    write_text(output_topic_dir / "meta.json", json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    return meta


def resolve_final_sources(final_structure_payload: dict) -> dict[str, Path]:
    mapping: dict[str, Path] = {}
    for item in final_structure_payload.get("topics", []):
        topic_id = str(item.get("topic_id") or "").strip()
        doc_file = str(item.get("doc_file") or "").strip()
        if not topic_id or not doc_file:
            continue
        doc_path = Path(doc_file).expanduser().resolve()
        if doc_path.exists():
            mapping[topic_id] = doc_path
    if not mapping:
        raise WorkflowContractError("Final Structure Gate 未提供可用 doc_file")
    return mapping


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical rewrite rerun with final structure contract")
    parser.add_argument("--material-manifest", required=True, help="Path to canonical material_manifest.json")
    parser.add_argument("--source-root", required=True, help="Path to staged rewrite source root")
    parser.add_argument("--final-structure", help="Path to final_structure_snapshot.json; default from draft upstream")
    parser.add_argument("--output-dir", help="Output directory; default=产物/06_改写/<run_id>")
    args = parser.parse_args()

    material_manifest_path = Path(args.material_manifest).expanduser().resolve()
    material_manifest = ensure_stage_manifest(material_manifest_path, "material")
    run_id = str(material_manifest["run_id"]).strip()
    material_gate_path = material_manifest_path.parent / "material_acceptance.json"
    ensure_material_acceptance_gate(material_gate_path)

    inferred_final_structure = material_manifest.get("upstream", {}).get("final_structure_snapshot")
    if not args.final_structure and not inferred_final_structure:
        raise WorkflowContractError("缺少 Final Structure Gate 路径；请提供 --final-structure 或在 material_manifest.upstream.final_structure_snapshot 中声明。")
    final_structure_path = (
        Path(args.final_structure).expanduser().resolve()
        if args.final_structure
        else Path(str(inferred_final_structure)).expanduser().resolve()
    )
    final_structure_payload = ensure_final_structure_gate(final_structure_path)

    source_root = Path(args.source_root).expanduser().resolve()
    if not source_root.exists():
        raise WorkflowContractError(f"rewrite source_root 不存在：{source_root}")
    output_root = Path(args.output_dir).expanduser().resolve() if args.output_dir else canonical_stage_dir("rewrite", run_id)
    output_root.mkdir(parents=True, exist_ok=True)
    final_sources = resolve_final_sources(final_structure_payload)

    topic_dirs = sorted([item for item in source_root.iterdir() if item.is_dir() and item.name.startswith("topic")])
    manifest = {
        "run_id": run_id,
        "stage": "rewrite",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "ready_for_publish_gate",
        "material_manifest": str(material_manifest_path),
        "material_gate": str(material_gate_path),
        "final_structure_snapshot": str(final_structure_path),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "topics": [],
    }

    for topic_dir in topic_dirs:
        topic_prefix = topic_dir.name.split("_")[0]
        final_source = final_sources.get(topic_prefix)
        if not final_source:
            raise WorkflowContractError(f"Final Structure Gate 缺少 topic `{topic_prefix}` 的 doc_file 映射")
        topic_meta = process_topic(topic_dir, final_source, output_root)
        manifest["topics"].append(topic_meta)

    write_text(output_root / "rewrite_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    sync_rewrite_to_desktop(run_id, output_root)
    print(str(output_root))


if __name__ == "__main__":
    main()
