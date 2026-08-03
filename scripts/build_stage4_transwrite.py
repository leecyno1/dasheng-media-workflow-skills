#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_workflow import (
    WorkflowContractError,
    canonical_stage_dir,
    ensure_final_structure_gate,
    ensure_stage_manifest,
    ensure_transwrite_decision_gate,
    ensure_runtime_output_dir,
    write_json,
)
from dasheng_video_director import build_explainer_package, build_talking_head_package


DEFAULT_LANES = ["wechat_article"]
SUPPORTED_LANES = {"wechat_article", "talking_head_video", "podcast"}
LANE_STATUS_LIFECYCLE = [
    "planned",
    "pending_director_review",
    "ready_for_agent_execution",
    "ready_for_skill_execution",
    "rendered",
    "packageable",
    "completed",
    "blocked_missing_provider",
    "blocked_missing_director_source",
    "blocked_missing_human_media",
    "failed_qc",
]
LANE_COMPLETION_STATUSES = ["completed", "packageable"]
LANE_PUBLISH_BLOCKING_STATUSES = [
    "planned",
    "pending_director_review",
    "ready_for_agent_execution",
    "ready_for_skill_execution",
    "waiting_for_human_media",
    "blocked_missing_provider",
    "blocked_missing_director_source",
    "blocked_missing_audio_provider",
    "blocked_missing_human_media",
    "failed_qc",
]
PODCAST_PROVIDER_ENVS = {
    "coze": ["COZE_API_KEY", "COZE_WORKFLOW_ID", "COZE_BOT_ID"],
}
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HTML_VIDEO_ROOT = os.environ.get("HTML_VIDEO_ROOT", str(ROOT / "vendor/reserved/render/html-video"))
DEFAULT_HTML_VIDEO_CLI = os.environ.get(
    "HTML_VIDEO_CLI",
    str(Path(DEFAULT_HTML_VIDEO_ROOT) / "packages/cli/dist/bin.js"),
)
DEFAULT_HTML_ANYTHING_ROOT = os.environ.get(
    "HTML_ANYTHING_ROOT",
    str(ROOT / "vendor/reserved/render/html-anything"),
)
DEFAULT_TEMPLATE_ROUTER = ROOT / "configs" / "video" / "html_anything_template_router.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def safe_slug(value: str, fallback: str = "topic") -> str:
    cleaned = re.sub(r"[^0-9A-Za-z._-]+", "-", value.strip()).strip("-._").lower()
    return cleaned or fallback


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def path_exists(path: str | None) -> bool:
    return bool(path and Path(path).expanduser().exists())


def short_text(text: str, limit: int = 180) -> str:
    collapsed = re.sub(r"\s+", " ", text).strip()
    return collapsed[: limit - 1] + "…" if len(collapsed) > limit else collapsed


def read_optional_text(path: str | None) -> str:
    if not path:
        return ""
    candidate = Path(path).expanduser()
    if not candidate.exists():
        return ""
    return candidate.read_text(encoding="utf-8", errors="ignore")


def extract_markdown_beats(markdown: str, title: str) -> list[dict[str, Any]]:
    beats: list[dict[str, Any]] = []
    current = {"heading": title, "body": []}
    for line in markdown.splitlines():
        h2 = re.match(r"^##+\s+(.+?)\s*$", line)
        if h2:
            if current["body"]:
                beats.append(
                    {
                        "heading": current["heading"],
                        "summary": short_text("\n".join(current["body"]), 220),
                    }
                )
            current = {"heading": h2.group(1).strip(), "body": []}
            continue
        if line.strip() and not line.lstrip().startswith("#"):
            current["body"].append(line.strip())
    if current["body"]:
        beats.append(
            {
                "heading": current["heading"],
                "summary": short_text("\n".join(current["body"]), 220),
            }
        )
    if not beats:
        beats.append({"heading": title, "summary": short_text(markdown, 220)})
    return beats[:8]


def build_html_video_vars(title: str, beats: list[dict[str, Any]], duration_sec: float = 8) -> dict[str, Any]:
    lead = beats[0]["summary"] if beats else title
    return {
        "headline": short_text(title, 110),
        "subheadline": short_text(lead, 180),
        "cta": "继续看完整分析",
        "duration_sec": max(4, min(12, duration_sec)),
    }


def build_execution_contract(
    *,
    lane: str,
    owner: str,
    required_steps: list[str],
    final_artifacts: dict[str, str | None],
    qc_report: str,
) -> dict[str, Any]:
    return {
        "lane": lane,
        "execution_owner": owner,
        "policy": "Python builds the task package; Agent/skills execute production and update this manifest.",
        "required_steps": required_steps,
        "final_artifacts": final_artifacts,
        "qc": {
            "required": True,
            "status": "pending",
            "report": qc_report,
        },
        "status_lifecycle": LANE_STATUS_LIFECYCLE,
        "completion_statuses": LANE_COMPLETION_STATUSES,
        "publish_blocking_statuses": LANE_PUBLISH_BLOCKING_STATUSES,
    }


def build_html_video_plan(
    *,
    title: str,
    topic_id: str | None,
    lane_dir: Path,
    beats: list[dict[str, Any]],
    render: dict[str, Any],
    audio_mode: str,
    alignment_mode: str,
    base_video: str | None,
    human_audio: str | None,
) -> dict[str, Any]:
    html_video_root = str(render.get("html_video_root") or os.getenv("HTML_VIDEO_ROOT") or DEFAULT_HTML_VIDEO_ROOT)
    html_video_cli = str(render.get("html_video_cli") or os.getenv("HTML_VIDEO_CLI") or DEFAULT_HTML_VIDEO_CLI)
    aspect = str((render.get("aspect_ratios") or ["9:16"])[0])
    template_id = str(render.get("template_id") or "frame-liquid-bg-hero")
    vars_path = lane_dir / "html_video_project_vars.json"
    project_name = f"dasheng-{safe_slug(topic_id or title)}"
    output_mp4 = lane_dir / "renders" / f"{safe_slug(topic_id or title)}.mp4"
    vars_payload = build_html_video_vars(title, beats, duration_sec=float(render.get("duration_sec") or 8))
    write_json(vars_path, vars_payload)
    commands = [
        f"node {html_video_cli} doctor --cwd {html_video_root}",
        f"node {html_video_cli} project-create --name {json.dumps(project_name, ensure_ascii=False)} --intent {json.dumps(title, ensure_ascii=False)} --aspect {aspect} --cwd {html_video_root}",
        f"node {html_video_cli} project-set-template <project_id> --template {template_id} --cwd {html_video_root}",
        f"node {html_video_cli} project-set-vars <project_id> --vars-file {vars_path.resolve()} --cwd {html_video_root}",
        f"node {html_video_cli} project-preview <project_id> --cwd {html_video_root}",
        f"node {html_video_cli} project-render <project_id> --output {output_mp4.resolve()} --cwd {html_video_root}",
    ]
    command_path = lane_dir / "html_video_commands.sh"
    write_text(command_path, "#!/usr/bin/env bash\nset -euo pipefail\n\n" + "\n".join(commands))
    plan = {
        "renderer": "html-video",
        "status": "ready_for_bridge",
        "topic_id": topic_id,
        "title": title,
        "html_video_root": html_video_root,
        "html_video_cli": html_video_cli,
        "template_id": template_id,
        "aspect": aspect,
        "project_name": project_name,
        "vars_file": str(vars_path.resolve()),
        "commands_file": str(command_path.resolve()),
        "expected_output": str(output_mp4.resolve()),
        "audio_mode": audio_mode,
        "alignment_mode": alignment_mode,
        "human_media": {
            "base_video": base_video,
            "human_audio": human_audio,
        },
        "template_references": [
            {
                "source": "html-video",
                "template_id": template_id,
                "path": f"{html_video_root}/templates/{template_id}/SKILL.md",
            },
            {
                "source": "html-anything",
                "template_id": "video-hyperframes",
                "path": f"{DEFAULT_HTML_ANYTHING_ROOT}/next/src/lib/templates/skills/video-hyperframes/SKILL.md",
            },
        ],
        "bridge_command": [
            "python3",
            "scripts/transwrite_html_video_bridge.py",
            "--video-manifest",
            str((lane_dir / "talking_head_video_manifest.json").resolve()),
        ],
        "render_command": [
            "python3",
            "scripts/transwrite_html_video_bridge.py",
            "--video-manifest",
            str((lane_dir / "talking_head_video_manifest.json").resolve()),
            "--execute",
            "render",
        ],
    }
    plan_path = lane_dir / "html_video_project_plan.json"
    write_json(plan_path, plan)
    return {**plan, "plan_file": str(plan_path.resolve())}


def build_director_package_for_video_lane(
    *,
    topic: dict[str, Any],
    decision: dict[str, Any],
    lane_dir: Path,
    title: str,
    base_video: str | None,
) -> dict[str, Any]:
    director_dir = lane_dir / "director_scene_plan"
    srt = decision.get("srt") or decision.get("agent_proofread_srt") or decision.get("subtitle_srt")
    captions_json = decision.get("captions_json") or decision.get("captions")
    roughcut_gate = decision.get("roughcut_gate") or decision.get("roughcut_gate_report")
    template_preview_roots = decision.get("template_preview_roots") or []
    if isinstance(template_preview_roots, str):
        template_preview_roots = [template_preview_roots]

    if path_exists(captions_json) or path_exists(srt):
        args = Namespace(
            captions_json=captions_json if path_exists(captions_json) else None,
            srt=srt if path_exists(srt) else None,
            source_video=base_video,
            duration=decision.get("duration"),
            title=title,
            roughcut_gate=roughcut_gate if path_exists(roughcut_gate) else None,
            template_preview_root=template_preview_roots,
        )
        outputs = build_talking_head_package(args, director_dir)
        mode = "talking_head_video"
    elif path_exists(topic.get("html_file")):
        args = Namespace(
            article_html=topic.get("html_file"),
            duration_target_sec=int((decision.get("director") or {}).get("duration_target_sec") or decision.get("duration_target_sec") or 180),
            template_router=str((decision.get("director") or {}).get("template_router") or DEFAULT_TEMPLATE_ROUTER),
            template_preview_root=template_preview_roots,
        )
        outputs = build_explainer_package(args, director_dir)
        mode = "explainer_html_video"
    else:
        return {
            "status": "blocked_missing_director_source",
            "mode": "unavailable",
            "reason": "Need agent_proofread_srt/captions_json for talking-head director, or Draft html_file for no-human director.",
            "output_dir": str(director_dir.resolve()),
        }

    return {
        "status": "pending_review",
        "mode": mode,
        "output_dir": str(director_dir.resolve()),
        "scene_plan": str(outputs["scene_plan"].resolve()),
        "review_html": str(outputs["review_html"].resolve()),
        "checkpoint": str(outputs["checkpoint"].resolve()),
        "raw_storyboard": str(outputs["raw_storyboard"].resolve()) if "raw_storyboard" in outputs else None,
        "raw_timeline": str(outputs["raw_timeline"].resolve()) if "raw_timeline" in outputs else None,
        "preview_html": str(outputs["preview_html"].resolve()) if "preview_html" in outputs else None,
        "next_step": "Review storyboard_template_review.html and export storyboard_review_decision.json before material generation.",
    }


def normalize_topic_rows(decision: dict[str, Any]) -> list[dict[str, Any]]:
    rows = decision.get("topics") or []
    if not isinstance(rows, list) or not rows:
        raise WorkflowContractError("transwrite_decision.json 必须包含非空 topics 列表")
    normalized = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        lanes = row.get("lanes") or row.get("channels") or DEFAULT_LANES
        if isinstance(lanes, str):
            lanes = [lanes]
        selected_lanes = [lane for lane in lanes if lane in SUPPORTED_LANES]
        if not selected_lanes:
            selected_lanes = list(DEFAULT_LANES)
        normalized.append({**row, "lanes": selected_lanes})
    return normalized


def topic_lookup(draft_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    topics: dict[str, dict[str, Any]] = {}
    for item in draft_manifest.get("drafts") or draft_manifest.get("topics") or []:
        if not isinstance(item, dict):
            continue
        topic_id = str(item.get("topic_id") or item.get("id") or "").strip()
        if topic_id:
            topics[topic_id] = item
    return topics


def resolve_topic(draft_topics: dict[str, dict[str, Any]], decision_row: dict[str, Any]) -> dict[str, Any]:
    topic_id = str(decision_row.get("topic_id") or "").strip()
    if topic_id and topic_id in draft_topics:
        return {**draft_topics[topic_id], **decision_row}
    if len(draft_topics) == 1:
        only = next(iter(draft_topics.values()))
        return {**only, **decision_row, "topic_id": only.get("topic_id") or topic_id}
    raise WorkflowContractError(f"transwrite_decision 中的 topic_id 未命中 draft_manifest：{topic_id or '<empty>'}")


def copy_if_exists(src: str | None, dst: Path) -> str | None:
    if not src:
        return None
    source = Path(src).expanduser()
    if not source.exists():
        return None
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dst)
    return str(dst.resolve())


def build_illustration_contract(topic: dict[str, Any], lane_dir: Path) -> dict[str, Any]:
    intents = topic.get("illustration_intents") if isinstance(topic.get("illustration_intents"), list) else []
    specs = topic.get("illustration_specs") if isinstance(topic.get("illustration_specs"), list) else []
    unresolved = []
    asset_specs_path = topic.get("asset_specs_file")
    if asset_specs_path and Path(asset_specs_path).expanduser().exists():
        asset_specs = read_json(Path(asset_specs_path).expanduser())
        intents = intents or (asset_specs.get("illustration_intents") or [])
        specs = specs or (asset_specs.get("illustration_specs") or [])
        unresolved = asset_specs.get("unresolved_illustration_intents") or []
    if not unresolved:
        resolved_ids = {
            str(spec.get("intent_id"))
            for spec in specs
            if isinstance(spec, dict) and spec.get("intent_id")
        }
        unresolved = [
            intent
            for intent in intents
            if isinstance(intent, dict)
            and intent.get("required")
            and str(intent.get("intent_id")) not in resolved_ids
        ]
    contract_path = lane_dir / "illustration_intents.json"
    payload = {
        "schema_version": "dasheng.lemon_illustration_intents.v1",
        "topic_id": topic.get("topic_id"),
        "skill": "dasheng-lemon-illustrations",
        "status": "pending_agent_generation" if unresolved else "ready",
        "intents": intents,
        "specs": specs,
        "unresolved": unresolved,
        "output_dir": str((lane_dir / "lemon_illustrations").resolve()),
    }
    write_json(contract_path, payload)
    return {**payload, "file": str(contract_path.resolve())}


def build_wechat_lane(topic: dict[str, Any], decision: dict[str, Any], topic_dir: Path) -> dict[str, Any]:
    lane_dir = topic_dir / "wechat_article"
    title = str(topic.get("title") or topic.get("topic_name") or topic.get("topic_id"))
    source_md = copy_if_exists(topic.get("draft_file"), lane_dir / "source_draft.md")
    source_html = copy_if_exists(topic.get("html_file"), lane_dir / "source_draft.html")
    wechat_md = copy_if_exists(topic.get("draft_file"), lane_dir / "wechat_article.base.md")
    if not wechat_md:
        write_text(lane_dir / "wechat_article.base.md", f"# {title}\n\n待 Agent 基于 Draft 完成公众号转写。")
        wechat_md = str((lane_dir / "wechat_article.base.md").resolve())
    illustration_contract = build_illustration_contract(topic, lane_dir)

    cover_enabled = bool((decision.get("cover_generation") or {}).get("enabled", True))
    humanize_enabled = bool(decision.get("humanize", True))
    dna_profile = decision.get("dna_profile") or decision.get("style_dna") or "project_or_user_default"
    prompt_path = lane_dir / "agent_rewrite_prompt.md"
    cover_prompt_path = lane_dir / "cover_prompt.md"
    write_text(
        prompt_path,
        f"""# 公众号转写 Agent Prompt

## 目标

基于 `source_draft.md` / `source_draft.html` 生成微信公众号版本。事实、数据、图表和结论以 Draft 为准，不新增未经核验的论据。

## 必做动作

- 继承 Style DNA：`{dna_profile}`；如缺少画像，优先调用 `dasheng-style-profiler` 或 `wechat-style-profiler` 从用户历史稿提取。
- 执行 humanize 清洗：减少模板句、口号句和“不是...而是...”这类机械对偶句。
- 保留 Draft 中已嵌入的图表、表格和图片；不得把图表计划留给下游。
- 读取 `{illustration_contract["file"]}`。原文中的比喻、举例、类比、拟人或抽象机制如被列为 illustration intent，调用 `dasheng-lemon-illustrations` 生成柠檬人漫画，并紧跟对应段落插入；不得统一堆到文末。
- 如果 humanize 新增了一个重要比喻或举例，也必须补充 illustration intent；只有能增加理解的场景才生成，不把每段都画成卡通。
- 漫画属于概念解释，不得替代真实图表、网页、表格、文档或来源证据。
- 公众号排版遵守 `configs/publish/wechat_layout_rules.json`：H2 使用阿拉伯数字大标题并左对齐；不要居中块状标题；表格内文字压到 12px 左右，减小 padding，避免手机端换行挤压。
- 需要封面时调用 `baoyu-cover-image` / `baoyu-imagine`，产物写入 `cover/`。
- 输出 `wechat_article.final.md` 与 `wechat_article.final.html`，再更新 `wechat_article_manifest.json`。

## 输入

- Markdown：`{source_md or wechat_md}`
- HTML：`{source_html or "无，使用 Markdown 转换"}`
""",
    )
    write_text(
        cover_prompt_path,
        f"""# 封面生成 Prompt

标题：{title}

请生成适合微信公众号头图的封面，优先 16:9，财经/时政宏观内容保持清晰、克制、有记忆点。不要堆字，不要做傻大粗逻辑图。

建议调用：

```bash
/baoyu-cover-image {wechat_md} --quick --aspect 16:9 --type conceptual --text title-only
```
""",
    )
    execution_contract = build_execution_contract(
        lane="wechat_article",
        owner="agent+skills",
        required_steps=[
            "Load source Draft and preserve all embedded facts, charts, tables, images, and conclusions.",
            "Apply Style DNA / humanize through dasheng-style-profiler or wechat-style-profiler when requested.",
            "Generate final Markdown and WeChat-compatible HTML through baoyu-markdown-to-html when needed.",
            "Apply WeChat layout hard rules from configs/publish/wechat_layout_rules.json before packaging.",
            "Consume illustration_intents.json and generate/place lemon-person comics after the matching metaphor or example paragraph.",
            "Generate cover assets through baoyu-cover-image / baoyu-imagine when requested.",
            "Run article QC before marking this lane packageable or completed.",
        ],
        final_artifacts={
            "markdown": str((lane_dir / "wechat_article.final.md").resolve()),
            "html": str((lane_dir / "wechat_article.final.html").resolve()),
            "cover": str((lane_dir / "cover").resolve()) if cover_enabled else None,
            "illustrations": illustration_contract["output_dir"],
        },
        qc_report=str((lane_dir / "wechat_article_qc_report.json").resolve()),
    )
    manifest = {
        "lane": "wechat_article",
        "status": "ready_for_agent_execution" if humanize_enabled or cover_enabled else "packageable",
        "topic_id": topic.get("topic_id"),
        "title": title,
        "source_md": source_md,
        "source_html": source_html,
        "base_markdown": wechat_md,
        "final_markdown": str((lane_dir / "wechat_article.final.md").resolve()),
        "final_html": str((lane_dir / "wechat_article.final.html").resolve()),
        "cover": {
            "enabled": cover_enabled,
            "prompt_file": str(cover_prompt_path.resolve()),
            "output_dir": str((lane_dir / "cover").resolve()),
            "skill": "baoyu-cover-image",
        },
        "skill_invocations": [
            {"skill": "dasheng-style-profiler", "purpose": "提取或加载作者 Style DNA", "required": dna_profile == "project_or_user_default"},
            {"skill": "wechat-style-profiler", "purpose": "公众号风格画像补充", "required": False},
            {"skill": "baoyu-markdown-to-html", "purpose": "将最终 Markdown 转微信兼容 HTML", "required": not bool(source_html)},
            {"skill": "baoyu-cover-image", "purpose": "生成封面", "required": cover_enabled},
            {
                "skill": "dasheng-lemon-illustrations",
                "purpose": "将原文比喻、举例和抽象机制转成柠檬人正文漫画",
                "required": bool(illustration_contract["unresolved"]),
            },
        ],
        "illustration_contract": illustration_contract,
        "agent_prompt": str(prompt_path.resolve()),
        "humanize_rules": {
            "enabled": humanize_enabled,
            "avoid_patterns": ["不是...而是...", "一方面...另一方面...", "可以说", "本质上"],
        },
        "layout_rules": {
            "config": str((ROOT / "configs" / "publish" / "wechat_layout_rules.json").resolve()),
            "default_variant": "editorial_blue_left",
            "preview_script": str((ROOT / "scripts" / "wechat_layout_variants.py").resolve()),
            "hard_requirements": [
                "H2 使用 01/02/03 这类阿拉伯数字标题并左对齐，不使用居中块状标题。",
                "表格文字约 12px，单元格紧凑，优先手机端可读性。",
                "正文不得全篇蓝色或全篇加粗；仅重点词和关键数据做局部强调。",
            ],
        },
        "final_artifacts": execution_contract["final_artifacts"],
        "qc": execution_contract["qc"],
        "execution_contract": execution_contract,
    }
    manifest_path = lane_dir / "wechat_article_manifest.json"
    write_json(manifest_path, manifest)
    return {**manifest, "manifest": str(manifest_path.resolve())}


def render_overlay_html(title: str, beats: list[dict[str, Any]], transparent: bool) -> str:
    bg = "transparent" if transparent else "#07111f"
    cards = "\n".join(
        f"""<section class="frame" data-index="{idx}" data-duration="3600">
  <p class="eyebrow">镜头 {idx:02d}</p>
  <h2>{html.escape(beat["heading"])}</h2>
  <p>{html.escape(beat["summary"])}</p>
</section>"""
        for idx, beat in enumerate(beats, 1)
    )
    meta = json.dumps(
        [{"index": idx, "duration": 3600, "sceneSummary": beat["heading"]} for idx, beat in enumerate(beats, 1)],
        ensure_ascii=False,
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}｜口播视觉层</title>
<style>
html,body{{margin:0;width:100%;height:100%;background:{bg};font-family:"LXGW WenKai","Noto Serif SC",serif;overflow:hidden;}}
.stage{{position:relative;width:1920px;height:1080px;box-sizing:border-box;padding:92px;color:#f7fbff;}}
.frame{{position:absolute;inset:92px;display:grid;align-content:center;max-width:1180px;opacity:0;transform:translateY(24px);transition:opacity .45s ease,transform .45s ease;}}
.frame.active{{opacity:1;transform:translateY(0);}}
.eyebrow{{font-size:30px;letter-spacing:.18em;color:#6fb7ff;text-transform:uppercase;margin:0 0 28px;}}
h1{{position:absolute;left:92px;top:54px;font-size:42px;margin:0;color:#ffffff;}}
h2{{font-size:92px;line-height:1.04;margin:0 0 34px;color:#ffffff;max-width:1120px;}}
p{{font-size:36px;line-height:1.55;margin:0;color:#d8e8ff;}}
.accent{{position:absolute;right:120px;bottom:120px;width:420px;height:420px;border:2px solid rgba(65,148,255,.55);border-radius:50%;animation:spin 18s linear infinite;}}
.accent:before{{content:"";position:absolute;inset:54px;border:1px solid rgba(255,68,68,.5);border-radius:50%;}}
.progress{{position:absolute;left:92px;right:92px;bottom:54px;height:8px;background:rgba(255,255,255,.18);border-radius:99px;overflow:hidden;}}
.bar{{height:100%;width:0;background:#e43737;transition:width .4s ease;}}
@keyframes spin{{to{{transform:rotate(360deg);}}}}
</style>
</head>
<body>
<main class="stage">
  <h1>{html.escape(title)}</h1>
  <div class="accent"></div>
  {cards}
  <div class="progress"><div class="bar"></div></div>
</main>
<script>
var frames = Array.prototype.slice.call(document.querySelectorAll('.frame'));
var bar = document.querySelector('.bar');
var current = 0;
function showFrame(index) {{
  current = (index + frames.length) % frames.length;
  frames.forEach(function(frame, idx) {{ frame.classList.toggle('active', idx === current); }});
  if (bar) {{ bar.style.width = (((current + 1) / frames.length) * 100) + '%'; }}
}}
showFrame(0);
setInterval(function() {{ showFrame(current + 1); }}, 3600);
document.addEventListener('keydown', function(event) {{
  if (event.key === 'ArrowRight') showFrame(current + 1);
  if (event.key === 'ArrowLeft') showFrame(current - 1);
}});
</script>
<!-- HYPERFRAMES_META: {meta} -->
</body>
</html>"""


def build_video_lane(topic: dict[str, Any], decision: dict[str, Any], topic_dir: Path) -> dict[str, Any]:
    lane_dir = topic_dir / "talking_head_video"
    title = str(topic.get("title") or topic.get("topic_name") or topic.get("topic_id"))
    markdown = read_optional_text(topic.get("draft_file"))
    beats = extract_markdown_beats(markdown, title)
    visual = decision.get("visual_layer") or {}
    audio = decision.get("audio") or {}
    alignment = decision.get("alignment") or {}
    render = decision.get("render") or {}
    base_video = decision.get("base_video") or decision.get("human_video")
    human_audio = audio.get("file") or decision.get("human_audio")
    has_human_media = path_exists(base_video) or path_exists(human_audio)
    audio_mode = audio.get("mode") or ("human_audio" if has_human_media else "synthetic_audio")
    alignment_mode = alignment.get("mode") or ("active_to_existing_audio" if audio_mode == "human_audio" else "passive_to_generated_audio")
    transparent = str(visual.get("background") or "transparent").lower() == "transparent"
    illustration_contract = build_illustration_contract(topic, lane_dir)

    storyboard = {
        "topic_id": topic.get("topic_id"),
        "title": title,
        "beats": beats,
        "source_draft": topic.get("draft_file"),
        "illustration_intents": illustration_contract["intents"],
    }
    storyboard_path = lane_dir / "video_storyboard.json"
    write_json(storyboard_path, storyboard)
    script_path = lane_dir / "talking_head_script.md"
    write_text(
        script_path,
        "# " + title + "\n\n"
        + "\n\n".join(f"## {beat['heading']}\n\n{beat['summary']}" for beat in beats)
        + "\n\n> 说明：这是口播基线稿。Agent 可继续压缩成 60 秒、3 分钟或 8 分钟版本。",
    )
    overlay_path = lane_dir / "html_overlay.html"
    write_text(overlay_path, render_overlay_html(title, beats, transparent))
    render_plan = {
        "engine": render.get("engine") or "html-video",
        "fallback_engine": "remotion",
        "aspect_ratios": render.get("aspect_ratios") or ["9:16", "16:9"],
        "transparent_overlay": transparent,
        "composition": {
            "base_video": base_video,
            "human_audio": human_audio,
            "html_overlay": str(overlay_path.resolve()),
            "output_dir": str((lane_dir / "renders").resolve()),
        },
        "commands": [
            {
                "name": "transcribe_human_audio",
                "when": "audio.mode == human_audio",
                "tool": alignment.get("engine") or "whisperx",
                "status": "ready" if has_human_media else "waiting_for_human_media",
            },
            {
                "name": "render_overlay",
                "tool": render.get("engine") or "remotion",
                "status": "planned",
            },
            {
                "name": "compose_final_video",
                "tool": "ffmpeg",
                "status": "planned",
            },
        ],
    }
    render_plan_path = lane_dir / "render_plan.json"
    write_json(render_plan_path, render_plan)
    html_video_plan = build_html_video_plan(
        title=title,
        topic_id=topic.get("topic_id"),
        lane_dir=lane_dir,
        beats=beats,
        render=render_plan | render,
        audio_mode=audio_mode,
        alignment_mode=alignment_mode,
        base_video=base_video,
        human_audio=human_audio,
    )
    director_package = build_director_package_for_video_lane(
        topic=topic,
        decision=decision,
        lane_dir=lane_dir,
        title=title,
        base_video=base_video,
    )
    if director_package["status"] == "pending_review":
        lane_status = "pending_director_review"
    elif director_package["status"].startswith("blocked"):
        lane_status = director_package["status"]
    else:
        lane_status = "ready_for_skill_execution" if has_human_media or audio_mode == "synthetic_audio" else "blocked_missing_human_media"
    execution_contract = build_execution_contract(
        lane="talking_head_video",
        owner="agent+video-skills",
        required_steps=[
            "Choose talking-head or no-human mode from decision inputs.",
            "Review director scene_plan through storyboard_template_review.html before TTS, material generation, or final render.",
            "Use human footage/audio when supplied; otherwise generate voiceover with MiniMax CLI.",
            "Build timeline, HTML visual layer, subtitles, and data-backed charts/stickers through video skills.",
            "Route source metaphors and examples from illustration_intents.json to lemon-person full-canvas or transparent-overlay scenes, then animate setup, action, and result as separate beats.",
            "Render preview/final video through html-video, HTML Anything bridge, Remotion, or FFmpeg as selected.",
            "Run video QC for duration, audio loudness, subtitle alignment, missing media, and final render existence.",
        ],
        final_artifacts={
            "video": str((lane_dir / "renders" / f"{safe_slug(topic.get('topic_id') or title)}.mp4").resolve()),
            "srt": str((lane_dir / "renders" / f"{safe_slug(topic.get('topic_id') or title)}.srt").resolve()),
            "timeline": str((lane_dir / "render_plan.json").resolve()),
            "scene_plan": director_package.get("scene_plan"),
            "storyboard_review": director_package.get("review_html"),
            "illustrations": illustration_contract["output_dir"],
        },
        qc_report=str((lane_dir / "video_qc_report.json").resolve()),
    )
    manifest = {
        "lane": "talking_head_video",
        "status": lane_status,
        "topic_id": topic.get("topic_id"),
        "title": title,
        "storyboard": str(storyboard_path.resolve()),
        "script": str(script_path.resolve()),
        "html_overlay": str(overlay_path.resolve()),
        "render_plan": str(render_plan_path.resolve()),
        "director_package": director_package,
        "html_video_project_plan": html_video_plan["plan_file"],
        "html_video_project_vars": html_video_plan["vars_file"],
        "html_video_commands": html_video_plan["commands_file"],
        "workflow_modes": {
            "human_media_present": has_human_media,
            "audio_mode": audio_mode,
            "alignment_mode": alignment_mode,
            "visual_background": "transparent" if transparent else "opaque",
        },
        "renderer": {
            "default": "html-video",
            "html_video_root": html_video_plan["html_video_root"],
            "template_id": html_video_plan["template_id"],
            "aspect": html_video_plan["aspect"],
            "expected_output": html_video_plan["expected_output"],
        },
        "template_references": html_video_plan["template_references"],
        "skill_invocations": [
            {"skill": "dasheng-html-video-bridge", "purpose": "调用本地 html-video 创建、预览和渲染口播视频", "required": True},
            {"skill": "dasheng-html-anything-bridge", "purpose": "参考 HTML Anything 的 video-hyperframes / motion-frames 视觉语言", "required": False},
            {"skill": "remotion-best-practices", "purpose": "复杂自定义透明合成兜底", "required": render_plan["engine"] == "remotion"},
            {"skill": "dasheng-stage-publish-video", "purpose": "兼容旧 motion 视频补充能力", "required": False},
            {
                "skill": "dasheng-lemon-illustrations",
                "purpose": "将原文比喻、举例和抽象机制转成柠檬人分镜素材",
                "required": bool(illustration_contract["intents"]),
            },
        ],
        "illustration_contract": illustration_contract,
        "final_artifacts": execution_contract["final_artifacts"],
        "qc": execution_contract["qc"],
        "execution_contract": execution_contract,
    }
    manifest_path = lane_dir / "talking_head_video_manifest.json"
    write_json(manifest_path, manifest)
    return {**manifest, "manifest": str(manifest_path.resolve())}


def podcast_provider_status(provider: str) -> dict[str, Any]:
    if provider in {"minimax", "mmx"}:
        mmx_path = shutil.which("mmx")
        auth_config = Path.home() / ".mmx" / "config.json"
        missing = []
        if not mmx_path:
            missing.append("mmx_cli")
        if not auth_config.exists():
            missing.append("mmx_auth_config")
        return {
            "provider": "mmx",
            "method": "cli",
            "required": ["mmx_cli", "mmx_auth_config"],
            "present": {
                "mmx_cli": bool(mmx_path),
                "mmx_auth_config": auth_config.exists(),
            },
            "missing_required": missing,
            "default_command": 'mmx speech synthesize --text-file <script.txt> --out <audio.wav> --model speech-2.8-hd --voice "Chinese (Mandarin)_Radio_Host"',
        }
    env_names = PODCAST_PROVIDER_ENVS.get(provider, [])
    present = [name for name in env_names if os.getenv(name)]
    required = env_names[:1]
    missing_required = [name for name in required if not os.getenv(name)]
    return {
        "provider": provider,
        "method": "api_or_workflow",
        "required_env": required,
        "optional_env": env_names[1:],
        "present_env_count": len(present),
        "missing_required": missing_required,
    }


def build_podcast_lane(topic: dict[str, Any], decision: dict[str, Any], topic_dir: Path) -> dict[str, Any]:
    lane_dir = topic_dir / "podcast"
    title = str(topic.get("title") or topic.get("topic_name") or topic.get("topic_id"))
    markdown = read_optional_text(topic.get("draft_file"))
    beats = extract_markdown_beats(markdown, title)
    provider = str(decision.get("provider") or "minimax").lower()
    mode = decision.get("mode") or "solo"
    provider_status = podcast_provider_status(provider)
    script_path = lane_dir / "podcast_script.md"
    write_text(
        script_path,
        f"""# {title}｜播客脚本

模式：{mode}

开场：今天聊一个容易被标题带偏、但值得拆开看的问题：{title}

"""
        + "\n\n".join(f"## {idx}. {beat['heading']}\n\n{beat['summary']}" for idx, beat in enumerate(beats, 1))
        + "\n\n收束：如果后续要发布成播客，请先人工确认事实口径、敏感表述和节目标题。",
    )
    request = {
        "provider": provider,
        "mode": mode,
        "title": title,
        "script_file": str(script_path.resolve()),
        "output_dir": str((lane_dir / "audio").resolve()),
        "provider_status": provider_status,
        "execution_policy": "dry_run_until_audio_provider_ready",
    }
    request_path = lane_dir / "provider_request.json"
    write_json(request_path, request)
    status = "ready_for_skill_execution" if not provider_status["missing_required"] else "blocked_missing_audio_provider"
    execution_contract = build_execution_contract(
        lane="podcast",
        owner="agent+audio-skills",
        required_steps=[
            "Review and polish podcast script without adding unverified facts.",
            "Generate audio through MiniMax CLI or Coze workflow.",
            "Export audio, optional transcript/subtitles, and provider metadata.",
            "Run audio QC before marking this lane packageable or completed.",
        ],
        final_artifacts={
            "audio": str((lane_dir / "audio" / "podcast.wav").resolve()),
            "transcript": str((lane_dir / "audio" / "podcast_transcript.txt").resolve()),
        },
        qc_report=str((lane_dir / "podcast_qc_report.json").resolve()),
    )
    manifest = {
        "lane": "podcast",
        "status": status,
        "topic_id": topic.get("topic_id"),
        "title": title,
        "provider": provider,
        "mode": mode,
        "script": str(script_path.resolve()),
        "provider_request": str(request_path.resolve()),
        "provider_status": provider_status,
        "skill_invocations": [
            {"skill": "coze_api", "purpose": "扣子播客/声音工作流", "required": provider == "coze"},
            {"skill": "mmx_cli", "purpose": "MiniMax CLI 语音生成", "required": provider in {"minimax", "mmx"}},
        ],
        "final_artifacts": execution_contract["final_artifacts"],
        "qc": execution_contract["qc"],
        "execution_contract": execution_contract,
    }
    manifest_path = lane_dir / "podcast_manifest.json"
    write_json(manifest_path, manifest)
    return {**manifest, "manifest": str(manifest_path.resolve())}


def build_topic_lanes(topic: dict[str, Any], decision_row: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    topic_id = str(topic.get("topic_id") or decision_row.get("topic_id") or "")
    title = str(topic.get("title") or decision_row.get("topic_name") or topic_id)
    topic_dir = output_dir / safe_slug(topic_id, safe_slug(title, "topic"))
    lanes: dict[str, Any] = {}
    if "wechat_article" in decision_row["lanes"]:
        lanes["wechat_article"] = build_wechat_lane(topic, decision_row.get("wechat_article") or decision_row, topic_dir)
    if "talking_head_video" in decision_row["lanes"]:
        lanes["talking_head_video"] = build_video_lane(topic, decision_row.get("talking_head_video") or decision_row, topic_dir)
    if "podcast" in decision_row["lanes"]:
        lanes["podcast"] = build_podcast_lane(topic, decision_row.get("podcast") or decision_row, topic_dir)
    return {
        "topic_id": topic_id,
        "title": title,
        "topic_dir": str(topic_dir.resolve()),
        "lanes": lanes,
    }


def render_report(run_id: str, topics: list[dict[str, Any]]) -> str:
    lines = [
        f"# 04 转写生产计划｜{run_id}",
        "",
        "本阶段把 Draft 终稿转为可发布前验收的渠道材料。Draft 仍是事实、图表和 HTML 的源头；本阶段只做表达、封面、口播/播客和渠道形态转换。",
        "",
    ]
    for topic in topics:
        lines.extend([f"## {topic['title']}", "", f"- topic_id：`{topic['topic_id']}`", f"- 目录：`{topic['topic_dir']}`"])
        for lane_name, lane in topic["lanes"].items():
            lines.append(f"- {lane_name}：{lane['status']}，manifest：`{lane['manifest']}`")
        lines.append("")
    return "\n".join(lines)


def build_transwrite_outputs(
    *,
    draft_manifest_path: Path,
    transwrite_decision_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    draft_manifest = ensure_stage_manifest(draft_manifest_path, "draft")
    ensure_final_structure_gate(draft_manifest_path.parent / "final_structure_snapshot.json")
    transwrite_decision = ensure_transwrite_decision_gate(transwrite_decision_path)
    run_id = str(draft_manifest.get("run_id") or transwrite_decision.get("run_id") or "").strip()
    if not run_id:
        raise WorkflowContractError("无法从 draft_manifest 或 transwrite_decision 推断 run_id")
    out_dir = ensure_runtime_output_dir(output_dir or canonical_stage_dir("transwrite", run_id), label="transwrite output_dir")
    out_dir.mkdir(parents=True, exist_ok=True)

    draft_topics = topic_lookup(draft_manifest)
    topic_rows = normalize_topic_rows(transwrite_decision)
    topics = [
        build_topic_lanes(resolve_topic(draft_topics, row), row, out_dir)
        for row in topic_rows
    ]
    report_path = out_dir / "04_转写计划.md"
    write_text(report_path, render_report(run_id, topics))
    manifest = {
        "run_id": run_id,
        "stage": "transwrite",
        "status": "prepared_for_skill_execution",
        "created_at": now_iso(),
        "source_draft_manifest": str(draft_manifest_path.resolve()),
        "transwrite_decision": str(transwrite_decision_path.resolve()),
        "report": str(report_path.resolve()),
        "topics": topics,
        "lane_contract": {
            "wechat_article": "DNA/humanize/封面/公众号 HTML 转写",
            "talking_head_video": "真人口播可选 + 视觉层 + 音频 + 主动/被动对齐 + 渲染计划",
            "podcast": "MiniMax CLI / Coze 工作流请求包，不重复造轮子",
        },
        "execution_model": {
            "policy": "lightweight_manifest_builder",
            "script_role": "build task packages, prompts, request bodies, artifact slots, and QC contracts",
            "agent_skill_role": "produce final channel artifacts and update lane manifests",
            "publish_requires": LANE_COMPLETION_STATUSES,
            "publish_blocks": LANE_PUBLISH_BLOCKING_STATUSES,
        },
        "next_stage": "publish",
    }
    manifest_path = out_dir / "transwrite_manifest.json"
    write_json(manifest_path, manifest)
    return {**manifest, "manifest_file": str(manifest_path.resolve()), "out_dir": str(out_dir.resolve())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Dasheng Stage 4 Transwrite builder")
    parser.add_argument("--draft-manifest", required=True)
    parser.add_argument("--transwrite-decision", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args()

    result = build_transwrite_outputs(
        draft_manifest_path=Path(args.draft_manifest).expanduser().resolve(),
        transwrite_decision_path=Path(args.transwrite_decision).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve() if args.output_dir else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
