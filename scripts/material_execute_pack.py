#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import textwrap
import time
import signal
from html import unescape
from io import StringIO
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urlparse

import requests

os.environ.setdefault("MPLBACKEND", "Agg")

WORLDMONITOR_ROOT = Path(os.getenv("DASHENG_WORLDMONITOR_ROOT", ""))
FINANCE_MOTION_ROOT = Path(os.getenv("DASHENG_FINANCE_MOTION_ROOT", ""))

from canonical_workflow import (
    WorkflowContractError,
    canonical_stage_dir,
    ensure_final_structure_gate,
    ensure_pending_gate_file,
    ensure_stage_manifest,
)
from desktop_delivery import sync_material_to_desktop
from provider_registry import resolve_chat_provider, resolve_material_image_provider_snapshot, extract_chat_content
from path_config import get_project_root


ROOT = get_project_root()
TUSHARE_TOKEN_FILE = ROOT / ".tushare_token"
USER_AGENT = "Mozilla/5.0 (compatible; MaterialPackExecutor/1.0; +https://example.com)"
IMAGE_CONFIG_DIR = ROOT / "configs" / "image_generation"
IMAGE_ENV_FILE = IMAGE_CONFIG_DIR / "providers.local.env"
LEGACY_IMAGE_ENV_FILE = ROOT / "产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/vectorengine_gemini_image.env"

VIDEO_MIN_HEIGHT = 0
VIDEO_MIN_DURATION_SECONDS = 8
VIDEO_MIN_SCENE_CHANGES = 2
VIDEO_MIN_SCENE_CHANGE_RATE = 0.08
IMAGE_MIN_SHORT_EDGE = 1024
DEFAULT_PERSON_DOWNLOAD_BOOST = 2
DEFAULT_NEWS_SCREENSHOT_PER_QUERY = 1
DEFAULT_NEWS_SCREENSHOT_TOTAL_LIMIT = 4
DEFAULT_NEWS_SEARCH_LIMIT = 3
DEFAULT_IMAGE_SEARCH_TIMEOUT = 20
DEFAULT_IMAGE_DOWNLOAD_TIMEOUT = 30
DEFAULT_NEWS_SEARCH_TIMEOUT = 20
DEFAULT_NEWS_SCREENSHOT_TIMEOUT = 45
DEFAULT_IMAGE_DOWNLOAD_TOTAL_LIMIT = 6
DEFAULT_IMAGE_MAX_BYTES = 12 * 1024 * 1024
DEFAULT_WIKIMEDIA_THUMB_WIDTH = 1600
DEFAULT_YTDLP_SOCKET_TIMEOUT = 20
DEFAULT_YTDLP_COMMAND_TIMEOUT = 180

SELF_MEDIA_TALKING_HEAD_PATTERNS = [
    r"口播",
    r"自媒体",
    r"主播",
    r"up主",
    r"个人频道",
    r"vlog",
    r"reaction",
    r"talking\s*head",
    r"时评",
    r"解读",
    r"播客",
    r"podcast",
]

NEWS_LIVE_INTERVIEW_PATTERNS = [
    r"news",
    r"breaking",
    r"live",
    r"livestream",
    r"直播",
    r"采访",
    r"interview",
    r"press\s*conference",
    r"briefing",
]

TRUSTED_NEWSROOM_PATTERNS = [
    r"央视",
    r"新华社",
    r"人民网",
    r"澎湃",
    r"bbc",
    r"cnn",
    r"reuters",
    r"associated\s+press",
    r"ap\s+news",
    r"bloomberg",
    r"al\s*jazeera",
    r"sky\s*news",
    r"wsj",
    r"financial\s+times",
    r"cnbc",
]

MATERIAL_SKILL_STACK = {
    "evidence_search": [
        {"skill": "news-radar", "role": "global_news_signal", "source": "openclaw-default"},
        {"skill": "web-search", "role": "general_web_search", "source": "openclaw-default"},
        {"skill": "multi-search-engine", "role": "multi_engine_recall", "source": "openclaw-default"},
        {"skill": "tavily-search", "role": "llm_search_fallback", "source": "openclaw-default"},
        {"skill": "reddit", "role": "overseas_social_signal", "source": "openclaw-default"},
        {"skill": "twitter", "role": "x_signal_lookup", "source": "openclaw-default"},
        {"skill": "google-trends", "role": "trend_heat_signal", "source": "openclaw-default"},
        {"skill": "wechat-search", "role": "wechat_article_search", "source": "openclaw-default"},
        {"skill": "wechat-article-extractor-skill", "role": "wechat_article_extract", "source": "openclaw-default"},
        {"skill": "xiaohongshu-extract", "role": "xhs_note_extract", "source": "openclaw-default"},
    ],
    "visual_generation": [
        {"skill": "baoyu-article-illustrator", "role": "structure_aware_illustration", "source": "openclaw-default"},
        {"skill": "baoyu-comic", "role": "comic_generation", "source": "openclaw-default"},
        {"skill": "baoyu-cover-image", "role": "cover_generation", "source": "openclaw-default"},
        {"skill": "baoyu-infographic", "role": "infographic_generation", "source": "openclaw-default"},
        {"skill": "baoyu-xhs-images", "role": "xhs_image_series", "source": "openclaw-default"},
        {"skill": "baoyu-image-gen", "role": "primary_image_generator", "source": "openclaw-default"},
        {"skill": "ai-image-generation", "role": "secondary_image_generator", "source": "openclaw-default"},
    ],
    "video_and_media": [
        {"skill": "media-downloader", "role": "media_search_and_download", "source": "openclaw-default"},
        {"skill": "video-download", "role": "video_download", "source": "openclaw-default"},
        {"skill": "video-frames", "role": "frame_extraction", "source": "openclaw-default"},
        {"skill": "video-subtitles", "role": "subtitle_and_transcript", "source": "openclaw-default"},
        {"skill": "bilibili-youtube-watcher", "role": "long_video_transcript", "source": "openclaw-default"},
    ],
    "motion_helpers": [
        {"skill": "remotion", "role": "motion_best_practice", "source": "openclaw-default"},
        {"skill": "remotion-video", "role": "motion_execution_reference", "source": "openclaw-default"},
        {"skill": "remotion-video-toolkit", "role": "motion_toolkit", "source": "openclaw-default"},
    ],
}


def maybe_reexec_preferred_python() -> None:
    preferred = ROOT / ".venv_media" / "bin" / "python"
    current_prefix = Path(sys.prefix).resolve()
    preferred_prefix = (ROOT / ".venv_media").resolve()
    if preferred.exists() and current_prefix != preferred_prefix:
        os.execv(str(preferred), [str(preferred), str(Path(__file__).resolve()), *sys.argv[1:]])


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def load_image_env() -> tuple[dict[str, str], str | None]:
    for candidate in [IMAGE_ENV_FILE, LEGACY_IMAGE_ENV_FILE]:
        if candidate.exists():
            return load_env_file(candidate), str(candidate)
    return {}, None


def normalize_openai_images_base_url(base_url: str) -> str:
    value = (base_url or "").strip().rstrip("/")
    if not value:
        return value
    for suffix in [
        "/v1/images/generations",
        "/v1/chat/completions",
        "/images/generations",
        "/chat/completions",
        "/v1",
    ]:
        if value.endswith(suffix):
            value = value[: -len(suffix)]
            break
    return value.rstrip("/")


def normalize_gemini_base_url(base_url: str) -> str:
    value = (base_url or "").strip().rstrip("/")
    if not value:
        return value
    for suffix in [
        "/v1beta/models",
        "/v1/chat/completions",
        "/v1/images/generations",
        "/v1",
    ]:
        if value.endswith(suffix):
            value = value[: -len(suffix)]
            break
    return value.rstrip("/")


def normalize_chat_base_url(base_url: str) -> str:
    value = (base_url or "").strip().rstrip("/")
    if not value:
        return value
    if value.endswith("/chat/completions") or value.endswith("/v1/chat/completions"):
        return value
    if value.endswith("/v1"):
        return f"{value}/chat/completions"
    return f"{value}/v1/chat/completions"


def read_tushare_token() -> str:
    token = (os.environ.get("TUSHARE_TOKEN") or os.environ.get("TS_TOKEN") or "").strip()
    if token:
        return token
    if TUSHARE_TOKEN_FILE.exists():
        return TUSHARE_TOKEN_FILE.read_text(encoding="utf-8").strip()
    return ""


def resolve_material_ai_config() -> dict[str, str] | None:
    return resolve_chat_provider(
        custom_env_var="DASHENG_MATERIAL_PROVIDER_ENV",
        base_url_keys=["MATERIAL_AI_BASE_URL", "QHAIGC_BASE_URL"],
        api_key_keys=["MATERIAL_AI_API_KEY", "QHAIGC_API_KEY"],
        model_keys=["MATERIAL_AI_MODEL", "PHASE4_AI_MODEL", "PHASE3_AI_MODEL", "DRAFT_AI_MODEL", "PHASE2_AI_MODEL"],
        timeout_keys=["MATERIAL_AI_TIMEOUT_SECONDS", "PHASE3_AI_TIMEOUT_SECONDS", "DRAFT_AI_TIMEOUT_SECONDS"],
        default_model="gpt-4.1-mini",
        default_timeout_seconds="180",
    )


def strip_code_fence(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def parse_json_object_from_text(text: str) -> dict[str, Any] | None:
    cleaned = strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.S)
    if not match:
        return None
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def request_material_ai_json(system_prompt: str, user_prompt: str, *, max_tokens: int = 5000) -> dict[str, Any]:
    config = resolve_material_ai_config()
    if not config:
        raise RuntimeError("未找到 Material AI 配置：缺少 MATERIAL_AI/QHAIGC base_url 或 api_key")

    body = {
        "model": config["model"],
        "temperature": 0.55,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.post(
                config["base_url"],
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {config['api_key']}",
                    "Connection": "close",
                },
                json=body,
                timeout=float(config["timeout_seconds"]),
            )
            response.raise_for_status()
            payload = response.json()
            content = extract_chat_content(payload)
            parsed = parse_json_object_from_text(content)
            if not parsed:
                raise RuntimeError("Material AI 返回的 JSON 为空或格式无效")
            return parsed
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= 2:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Material AI 调用失败：{last_error}")


def strip_markdown_frontmatter(text: str) -> str:
    raw = text.lstrip()
    if not raw.startswith("---"):
        return text
    parts = raw.split("\n")
    if len(parts) < 3:
        return text
    end_index = None
    for index in range(1, len(parts)):
        if parts[index].strip() == "---":
            end_index = index
            break
    if end_index is None:
        return text
    return "\n".join(parts[end_index + 1 :]).lstrip()


def parse_markdown_sections(markdown_text: str) -> list[dict[str, str]]:
    cleaned = strip_markdown_frontmatter(markdown_text)
    lines = cleaned.splitlines()
    sections: list[dict[str, str]] = []
    current_heading = "开篇"
    current_body: list[str] = []

    def flush_section() -> None:
        body = "\n".join(current_body).strip()
        if not body:
            return
        section_id = f"section-{len(sections) + 1:02d}"
        sections.append({"section_id": section_id, "heading": current_heading.strip(), "body": body})

    for line in lines:
        match = re.match(r"^(#{1,2})\s+(.+?)\s*$", line)
        if match:
            flush_section()
            current_heading = match.group(2).strip()
            current_body = []
            continue
        current_body.append(line)
    flush_section()
    if sections:
        return sections

    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", cleaned) if chunk.strip()]
    for index, paragraph in enumerate(paragraphs[:6], start=1):
        sections.append({"section_id": f"section-{index:02d}", "heading": f"段落 {index}", "body": paragraph})
    return sections


def material_ai_runtime_paths(run_id: str) -> tuple[Path, Path, Path]:
    material_dir, _ = material_runtime_paths(run_id)
    return material_dir, material_dir / "material_ai_inputs.json", material_dir / "material_ai_decisions.json"


def resolve_topic_article_source(topic_row: dict[str, Any], draft_row: dict[str, Any]) -> tuple[str, Path]:
    candidates = [
        topic_row.get("final_doc"),
        topic_row.get("doc_file"),
        topic_row.get("final_doc_file"),
        draft_row.get("final_doc"),
        draft_row.get("draft_file"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        if str(candidate).startswith(("http://", "https://")):
            raise RuntimeError(f"当前 run 的终稿正文仍是远程链接，material 暂不支持直接读取远程文档：{candidate}")
        path = Path(candidate).expanduser().resolve()
        if path.exists() and path.is_file():
            return "local_markdown", path
    raise RuntimeError(f"未找到可读取的终稿正文源：topic={topic_row.get('topic_id') or topic_row.get('title')}")


def read_topic_reasoning_payload(draft_row: dict[str, Any]) -> dict[str, Any]:
    candidate = draft_row.get("reasoning_sheet_json")
    if not candidate:
        return {}
    path = Path(candidate).expanduser().resolve()
    if not path.exists():
        return {}
    payload = read_json(path)
    return payload if isinstance(payload, dict) else {}


def build_material_ai_prompts(
    topic_row: dict[str, Any],
    article_markdown: str,
    sections: list[dict[str, str]],
    reasoning_payload: dict[str, Any],
) -> tuple[str, str]:
    evidence_lines = "\n".join(
        f"- {item.get('title', '')}｜{item.get('url', '')}"
        for item in (reasoning_payload.get("evidence_items") or [])[:8]
    ) or "- 暂无"
    claim_lines = "\n".join(
        f"- {item.get('section_id', '')}｜{item.get('statement', '')}｜待补：{'；'.join(item.get('missing_proof') or ['无'])}"
        for item in (reasoning_payload.get("claims") or [])
    ) or "- 暂无"
    section_lines = "\n".join(
        f"- {item['section_id']}｜{item['heading']}"
        for item in sections
    ) or "- 暂无"
    system_prompt = (
        "你是第04环节 Material 的总编导。"
        "你必须先完整阅读文章正文，再决定这篇文章真正需要哪些素材。"
        "禁止机械地每篇都补满图表、图片、视频。"
        "如果某段不需要素材，就明确不给。"
        "你输出的是结构化 JSON，不是解释文字。"
    )
    user_prompt = f"""请阅读下面这篇终稿正文，并为第04环节 Material 生成“素材决策 JSON”。

要求：
1. 先基于全文判断主论点、章节重点、证据缺口，再决定要补什么；
2. 只在“有证明价值”时生成图表锚点，最多 4 个；
3. 图片优先人物、机构、事件现场、新闻截图，不要泛图；
4. 视频只在文中确实适合补充动态素材时再给检索词；
5. 漫画/连环画/梗图只在适配该题时生成，不强制；
6. claims 要贴合正文结构，不要沿用旧稿的僵硬 claims；
7. topic_type 只能是 finance_macro / geopolitics / industry_tech / general_commentary 之一；
8. 所有 query 都要具体可执行；
9. 如果某类素材不需要，返回空数组。

返回 JSON 对象，字段必须包含：
- core_claim
- topic_type
- article_summary
- skip_notes
- claims: [{{claim_id, section_id, heading, statement, counterpoint, missing_proof[], chart_need}}]
- chart_anchors: [{{anchor_id, section_id, title, purpose, data_sources[], chart_type, only_if_worth_chart}}]
- image_queries: [{{query, entity_type, entity, priority, channel}}]
- news_screenshot_queries: [{{query, priority, channel}}]
- video_queries: [{{query, priority}}]
- generated_visuals: {{cover_prompt, infographic_prompts[], comic_storyboard[], meme_prompts[], funny_comic_character_prompts[]}}
- scene_plan: [{{title, visual, caption}}]

【文章信息】
- 题目：{topic_row.get('title', '')}
- topic_id：{topic_row.get('topic_id', '')}
- 冻结一级结构：
{chr(10).join(f"- {item}" for item in topic_row.get('final_primary_sections', []) or []) or "- 暂无"}

【文章章节】
{section_lines}

【辅助论证骨架】
{claim_lines}

【已有证据】
{evidence_lines}

【正文全文】
```markdown
{article_markdown.strip()}
```"""
    return system_prompt, user_prompt


def build_material_ai_input_payload(
    run_id: str,
    topic_row: dict[str, Any],
    draft_row: dict[str, Any],
    article_source_type: str,
    article_path: Path,
    article_markdown: str,
    reasoning_payload: dict[str, Any],
    ai_decision: dict[str, Any],
    aggregate_decisions_file: Path,
) -> dict[str, Any]:
    evidence_items = reasoning_payload.get("evidence_items") or []
    claims = ai_decision.get("claims") or []
    return {
        "meta": {
            "id": f"{run_id}:material-input:{topic_row.get('topic_id')}",
            "object_type": "MaterialInput",
            "run_id": run_id,
            "version": "4.0.0",
            "status": "ready",
            "generated_by": "material_execute_pack.py",
        },
        "topic_id": topic_row.get("topic_id") or draft_row.get("topic_id"),
        "title": topic_row.get("title") or draft_row.get("title"),
        "core_claim": ai_decision.get("core_claim") or reasoning_payload.get("core_thesis") or topic_row.get("title") or "",
        "angle_candidates": [ai_decision.get("article_summary", ""), topic_row.get("editor_note", "")],
        "risk_notes": ai_decision.get("skip_notes") or [],
        "evidence_requirements": [item.get("statement", "") for item in claims if item.get("statement")],
        "proof_requirements": [item for item in (ai_decision.get("skip_notes") or []) if item],
        "chart_needs": [item.get("title", "") for item in (ai_decision.get("chart_anchors") or []) if item.get("title")],
        "recommended_media": [name for name, rows in {
            "chart": ai_decision.get("chart_anchors") or [],
            "image": ai_decision.get("image_queries") or [],
            "news_screenshot": ai_decision.get("news_screenshot_queries") or [],
            "video": ai_decision.get("video_queries") or [],
            "comic": (ai_decision.get("generated_visuals") or {}).get("comic_storyboard") or [],
            "meme": (ai_decision.get("generated_visuals") or {}).get("meme_prompts") or [],
            "infographic": (ai_decision.get("generated_visuals") or {}).get("infographic_prompts") or [],
        }.items() if rows],
        "evidence_items": evidence_items,
        "existing_evidence": evidence_items,
        "missing_evidence": ai_decision.get("skip_notes") or [],
        "counterintuitive_angle": next((item.get("counterpoint") for item in claims if item.get("counterpoint")), None),
        "claims": claims,
        "chart_anchors": ai_decision.get("chart_anchors") or [],
        "image_queries": ai_decision.get("image_queries") or [],
        "news_screenshot_queries": ai_decision.get("news_screenshot_queries") or [],
        "video_queries": ai_decision.get("video_queries") or [],
        "generated_visuals": ai_decision.get("generated_visuals") or {},
        "scene_plan": ai_decision.get("scene_plan") or [],
        "topic_type_hint": ai_decision.get("topic_type") or "",
        "article_markdown": article_markdown.strip(),
        "article_source": {
            "type": article_source_type,
            "path": str(article_path),
            "final_primary_sections": topic_row.get("final_primary_sections") or [],
        },
        "material_decision": ai_decision,
        "material_decision_file": str(aggregate_decisions_file),
        "generation_basis": "final_doc_ai_reading",
        "upstream_object_type": "MaterialInput",
    }


def build_material_ai_inputs_from_draft_manifest(
    draft_manifest: Path,
    final_structure_payload: dict[str, Any],
) -> tuple[Path, Path]:
    payload = read_draft_manifest(draft_manifest)
    run_id = str(payload["run_id"]).strip()
    material_dir, ai_inputs_file, ai_decisions_file = material_ai_runtime_paths(run_id)
    material_dir.mkdir(parents=True, exist_ok=True)

    topic_rows = final_structure_payload.get("topics", [])
    draft_rows = payload.get("drafts", [])
    by_topic_id = {str(item.get("topic_id")): item for item in draft_rows if item.get("topic_id")}
    ai_inputs: list[dict[str, Any]] = []
    ai_decisions: dict[str, Any] = {"run_id": run_id, "generation_basis": "final_doc_ai_reading", "topics": []}

    for topic_row in topic_rows:
        topic_id = str(topic_row.get("topic_id") or "").strip()
        draft_row = by_topic_id.get(topic_id)
        if not draft_row:
            raise RuntimeError(f"draft_manifest 中缺少 topic_id={topic_id} 的 draft 行")
        article_source_type, article_path = resolve_topic_article_source(topic_row, draft_row)
        article_markdown = article_path.read_text(encoding="utf-8")
        sections = parse_markdown_sections(article_markdown)
        reasoning_payload = read_topic_reasoning_payload(draft_row)
        system_prompt, user_prompt = build_material_ai_prompts(topic_row, article_markdown, sections, reasoning_payload)
        ai_decision = request_material_ai_json(system_prompt, user_prompt)
        if not isinstance(ai_decision.get("claims"), list):
            raise RuntimeError(f"Material AI 输出缺少 claims：topic_id={topic_id}")
        topic_decision_file = material_dir / f"material_ai_decision_{topic_id}.json"
        write_json(topic_decision_file, ai_decision)
        ai_input = build_material_ai_input_payload(
            run_id=run_id,
            topic_row=topic_row,
            draft_row=draft_row,
            article_source_type=article_source_type,
            article_path=article_path,
            article_markdown=article_markdown,
            reasoning_payload=reasoning_payload,
            ai_decision=ai_decision,
            aggregate_decisions_file=ai_decisions_file,
        )
        ai_inputs.append(ai_input)
        ai_decisions["topics"].append(
            {
                "topic_id": topic_id,
                "title": topic_row.get("title"),
                "article_source_type": article_source_type,
                "article_path": str(article_path),
                "decision_file": str(topic_decision_file),
                "decision": ai_decision,
            }
        )

    write_json(ai_inputs_file, ai_inputs)
    write_json(ai_decisions_file, ai_decisions)
    return ai_inputs_file, ai_decisions_file


def resolve_gemini_image_provider() -> dict[str, str]:
    return resolve_material_image_provider_snapshot()["gemini_generate_content"]


def resolve_optional_image_provider_status() -> dict[str, Any]:
    return resolve_material_image_provider_snapshot()["optional_fallbacks"]


def normalize_repeated_secret(secret: str) -> str:
    secret = (secret or "").strip()
    if not secret:
        return ""
    for size in range(40, len(secret) + 1):
        if len(secret) % size != 0:
            continue
        chunk = secret[:size]
        if chunk * (len(secret) // size) == secret:
            return chunk
    return secret


def sanitize_minimax_prompt(topic: TopicContext, prompt: str, task_id: str) -> str:
    sanitized = prompt.strip()
    if topic.topic_type != "geopolitics":
        return sanitized

    replacements = [
        ("高市早苗", "日本议会保守派人物的抽象剪影"),
        ("极右势力复兴", "社会保守化抬头"),
        ("极右", "保守化"),
        ("跳梁", "抬头"),
        ("政治右转", "政策保守化"),
        ("政客", "讲台人物"),
        ("政治人物", "人物剪影"),
        ("台海", "周边海域"),
        ("军演", "防务演训"),
        ("安全外溢", "安全议题外溢"),
        ("用脚投票下", "投票行为推动"),
    ]
    for src, dst in replacements:
        sanitized = sanitized.replace(src, dst)

    if task_id == "cover":
        return (
            "生成一张东亚时政深度封面：日本议会建筑夜景、城市街头人群、老龄化社会符号与防务压力图形叠加，"
            "强调社会保守化、人口结构压力、就业缺口与区域安全焦虑之间的张力。"
            "使用新闻图解风格，避免真实政治人物肖像、党派标识、竞选海报、口播截图和煽动性标语。"
        )
    if task_id == "infographic_1":
        return (
            "生成一张高密度信息图，主题是日本的人口老龄化、劳动力缺口、城市就业压力与社会结构变化。"
            "使用人口年龄层、空缺岗位、地铁通勤人群、办公楼和统计卡片表达。"
            "不要出现政治人物、人名、党派名称、旗帜、竞选元素。"
        )
    if task_id == "infographic_2":
        return (
            "生成一张时间线地图信息图，主题是议会政策变化、产业链调整、周边海运通道压力与东亚供应链风险。"
            "使用议会建筑、海运线、港口、工厂、芯片箱体、地图箭头和时间轴表达。"
            "不要出现政治人物、人名、军事冲突画面、敏感口号或旗帜对抗。"
        )
    if task_id == "infographic_3":
        return (
            "生成一张 dashboard 风格信息图，主题是人口结构变化、公共预算分配、劳动力缺口、制造业与物流风险观察。"
            "使用抽象图标、数据卡片、柱状图、环形图、表格、城市剪影和物流网络小窗表达。"
            "不要出现政治人物、人名、政党、议会席位、旗帜、竞选图像或军事元素。"
        )
    if task_id.startswith("comic-"):
        return (
            "生成一张抽象分镜插画，使用城市、议会建筑、办公室、港口、人群、数据卡片和地图元素来表现社会结构压力与区域风险。"
            "不要出现真实政治人物肖像、人名、阵营标签、攻击性符号或竞选场景。"
        )
    if task_id.startswith("funny_character_"):
        return (
            "生成一张简单搞笑漫画人物插画：仅保留头肩像与简洁动作，纯色背景，线条简洁，低细节，不要写实材质和复杂光影。"
            "避免真实政治人物肖像、旗帜对抗和煽动性符号。"
        )
    if task_id.startswith("meme_"):
        return (
            sanitized
            + "。采用轻松隐喻式梗图风格，只用动物、账单、港口、棋盘、地图、办公室道具做象征，"
              "不要出现真实国家领导人或敏感政治人物。"
        )
    return sanitized


def safe_slug(text: str) -> str:
    return (
        text.strip()
        .lower()
        .replace("/", "-")
        .replace(" ", "-")
        .replace(":", "-")
        .replace("|", "-")
    )


def build_image_filename(query: str, entity: str, candidate_rank: int, suffix: str, query_index: int) -> str:
    base = safe_slug(entity or query).strip("-_")
    if not base:
        base = f"query-{query_index:02d}"
    base = base[:40]
    normalized_suffix = suffix or ".jpg"
    if not normalized_suffix.startswith("."):
        normalized_suffix = f".{normalized_suffix}"
    return f"图片_{base}_{candidate_rank:02d}{normalized_suffix}"


def guess_ext_from_mime(mime_type: str) -> str:
    mime_type = (mime_type or "").lower()
    if "png" in mime_type:
        return ".png"
    if "webp" in mime_type:
        return ".webp"
    if "jpeg" in mime_type or "jpg" in mime_type:
        return ".jpg"
    return ".bin"


def create_requests_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


class DeadlineExceeded(TimeoutError):
    pass


def run_with_deadline(seconds: int, func: Any, *args: Any, **kwargs: Any) -> Any:
    timeout_seconds = max(1, int(seconds))
    if not hasattr(signal, "SIGALRM"):
        return func(*args, **kwargs)

    def _handle_alarm(signum: int, frame: Any) -> None:  # noqa: ARG001
        raise DeadlineExceeded(f"deadline_exceeded:{timeout_seconds}s")

    previous_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _handle_alarm)
    signal.setitimer(signal.ITIMER_REAL, float(timeout_seconds))
    try:
        return func(*args, **kwargs)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous_handler)


def download_file(
    url: str,
    output_path: Path,
    headers: dict[str, str] | None = None,
    *,
    timeout: int = 180,
    max_bytes: int = DEFAULT_IMAGE_MAX_BYTES,
) -> Path:
    payload = bytearray()
    with create_requests_session() as session:
        with session.get(
            url,
            headers=headers or {"User-Agent": USER_AGENT},
            timeout=timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            content_length = to_int(response.headers.get("content-length"))
            if content_length and content_length > max_bytes:
                raise RuntimeError(f"file_too_large:{content_length}>{max_bytes}")
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if not chunk:
                    continue
                payload.extend(chunk)
                if len(payload) > max_bytes:
                    raise RuntimeError(f"download_exceeded_limit:{len(payload)}>{max_bytes}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(bytes(payload))
    return output_path


@dataclass
class TopicContext:
    topic_root: Path
    topic_config: dict[str, Any]

    @property
    def slug(self) -> str:
        return self.topic_config["topic_slug"]

    @property
    def topic_type(self) -> str:
        return self.topic_config["topic_type"]

    @property
    def title(self) -> str:
        return self.topic_config["title"]


def discover_topics(pack_root: Path) -> list[TopicContext]:
    topics: list[TopicContext] = []
    for config in sorted(pack_root.glob("*/config/topic_config.json")):
        topic_root = config.parent.parent
        topics.append(TopicContext(topic_root=topic_root, topic_config=read_json(config)))
    if not topics:
        raise RuntimeError(f"未在 {pack_root} 下找到 topic_config.json")
    return topics


def discover_topic_by_dir(pack_root: Path, topic_dir: str) -> TopicContext:
    raw = Path(topic_dir).expanduser()
    topic_root = raw if raw.is_absolute() else (pack_root / raw)
    topic_root = topic_root.resolve()
    config_file = topic_root / "config" / "topic_config.json"
    if not config_file.exists():
        raise RuntimeError(f"topic_dir 无效，缺少文件: {config_file}")
    return TopicContext(topic_root=topic_root, topic_config=read_json(config_file))


def looks_like_pack_root(pack_root: Path) -> bool:
    return pack_root.exists() and any(pack_root.glob("*/config/topic_config.json"))


def read_draft_manifest(draft_manifest: Path) -> dict[str, Any]:
    payload = read_json(draft_manifest)
    if not isinstance(payload, dict):
        raise RuntimeError(f"draft_manifest 格式无效: {draft_manifest}")
    if not payload.get("run_id"):
        raise RuntimeError(f"draft_manifest 缺少 run_id: {draft_manifest}")
    if not isinstance(payload.get("drafts"), list) or not payload["drafts"]:
        raise RuntimeError(f"draft_manifest 缺少 drafts: {draft_manifest}")
    return payload


def material_runtime_paths(run_id: str) -> tuple[Path, Path]:
    material_dir = ROOT / "skills" / "dasheng-daily-shared" / "runtime-data" / "runs" / run_id / "artifacts" / "material"
    return material_dir, material_dir / "material_manifest.json"


def canonical_material_paths(run_id: str) -> tuple[Path, Path, Path]:
    stage_dir = canonical_stage_dir("material", run_id)
    return stage_dir, stage_dir / "material_manifest.json", stage_dir / "material_acceptance.json"


def resolve_pack_root_from_material_manifest(material_manifest_file: Path) -> Path | None:
    if not material_manifest_file.exists():
        return None
    payload = read_json(material_manifest_file)
    pack_root_value = payload.get("pack_root")
    if not pack_root_value:
        return None
    pack_root = Path(pack_root_value).expanduser().resolve()
    if looks_like_pack_root(pack_root):
        return pack_root
    return None


def build_material_plan_from_draft_manifest(draft_manifest: Path, *, force_rebuild: bool = False) -> tuple[Path, Path]:
    draft_manifest = draft_manifest.expanduser().resolve()
    payload = ensure_stage_manifest(draft_manifest, "draft")
    read_draft_manifest(draft_manifest)
    run_id = str(payload["run_id"]).strip()
    if not run_id:
        raise RuntimeError(f"draft_manifest run_id 为空: {draft_manifest}")
    final_structure_snapshot = draft_manifest.parent / "final_structure_snapshot.json"
    final_structure_payload = ensure_final_structure_gate(final_structure_snapshot)

    material_dir, material_manifest_file = material_runtime_paths(run_id)
    if force_rebuild and material_dir.exists():
        shutil.rmtree(material_dir)
    if not force_rebuild:
        existing_pack_root = resolve_pack_root_from_material_manifest(material_manifest_file)
        if existing_pack_root:
            return existing_pack_root, material_manifest_file

    node_script = ROOT / "skills" / "dasheng-daily-material" / "index.js"
    if not node_script.exists():
        raise RuntimeError(f"material planner 不存在: {node_script}")

    ai_inputs_file, _ = build_material_ai_inputs_from_draft_manifest(draft_manifest, final_structure_payload)
    command = ["node", str(node_script), str(ai_inputs_file)]
    try:
        subprocess.run(command, cwd=str(ROOT), check=True)
    except FileNotFoundError as exc:
        raise RuntimeError("未找到 node，可先安装 Node.js 或手动先运行 material planner") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"material planner 执行失败: {' '.join(command)}") from exc

    pack_root = resolve_pack_root_from_material_manifest(material_manifest_file)
    if not pack_root:
        raise RuntimeError(f"material planner 已执行，但未生成可用 pack_root: {material_manifest_file}")
    return pack_root, material_manifest_file


def fetch_fred_series(series_id: str) -> "pd.DataFrame":
    import pandas as pd

    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with create_requests_session() as session:
                response = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
            response.raise_for_status()
            df = pd.read_csv(StringIO(response.text))
            break
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt >= 3:
                raise RuntimeError(f"FRED series fetch failed: {series_id}") from exc
            time.sleep(attempt)
    else:
        raise RuntimeError(f"FRED series fetch failed: {series_id}") from last_error
    df.columns = ["trade_date", "value"]
    df["trade_date"] = pd.to_datetime(df["trade_date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


CHART_GATE_THRESHOLDS = {
    "cv_min": 0.03,
    "slope_abs_min": 0.005,
    "r2_min": 0.25,
    "trend_strength_min": 0.30,
    "group_diff_min": 0.08,
    "heatmap_var_min": 0.05,
}


def compute_series_stats(series: "pd.Series") -> dict[str, float]:
    import numpy as np

    values = series.dropna().values.astype(float)
    if len(values) < 6:
        return {"cv": 0.0, "slope": 0.0, "r2": 0.0, "trend_strength": 0.0}

    x = np.arange(len(values), dtype=float)
    mean_val = float(np.mean(values))
    std_val = float(np.std(values))
    cv = float(std_val / mean_val) if abs(mean_val) > 1e-12 else 0.0

    slope_raw, intercept = np.polyfit(x, values, 1)
    slope = float(slope_raw / mean_val) if abs(mean_val) > 1e-12 else float(slope_raw)

    pred = slope_raw * x + intercept
    ss_tot = float(np.sum((values - mean_val) ** 2))
    ss_res = float(np.sum((values - pred) ** 2))
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 1e-12 else 0.0

    trend_strength = float(min(1.0, max(abs(slope) * 12, 0.0) * 0.55 + max(min(r2, 1.0), 0.0) * 0.45))
    return {"cv": cv, "slope": slope, "r2": r2, "trend_strength": trend_strength}


def should_generate_chart(df: "pd.DataFrame", x_col: str, y_cols: list[str]) -> tuple[bool, dict[str, Any]]:
    metrics: dict[str, Any] = {"x_col": x_col, "series": {}}
    if df is None or len(df) < 6:
        return False, metrics

    for col in y_cols:
        if col not in df.columns:
            continue
        stats = compute_series_stats(df[col])
        passed = (
            stats["cv"] >= CHART_GATE_THRESHOLDS["cv_min"]
            or abs(stats["slope"]) >= CHART_GATE_THRESHOLDS["slope_abs_min"]
            or stats["r2"] >= CHART_GATE_THRESHOLDS["r2_min"]
            or stats["trend_strength"] >= CHART_GATE_THRESHOLDS["trend_strength_min"]
        )
        metrics["series"][col] = {**stats, "passed": passed}
        if passed:
            return True, metrics
    return False, metrics


def should_generate_bar_chart(df: "pd.DataFrame") -> tuple[bool, dict[str, Any]]:
    import pandas as pd

    if df is None or len(df) < 2 or len(df.columns) < 2:
        return False, {"group_diff_ratio": 0.0}
    series = pd.to_numeric(df[df.columns[1]], errors="coerce").dropna()
    if series.empty:
        return False, {"group_diff_ratio": 0.0}
    mean_abs = abs(float(series.mean()))
    diff_ratio = float((series.max() - series.min()) / (mean_abs + 1e-12))
    passed = diff_ratio >= CHART_GATE_THRESHOLDS["group_diff_min"]
    return passed, {"group_diff_ratio": diff_ratio}


def should_generate_heatmap(df: "pd.DataFrame") -> tuple[bool, dict[str, Any]]:
    import numpy as np

    if df is None or df.empty:
        return False, {"row_var_max": 0.0, "col_var_max": 0.0}

    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return False, {"row_var_max": 0.0, "col_var_max": 0.0}

    row_var_max = float(numeric.var(axis=1).fillna(0).max())
    col_var_max = float(numeric.var(axis=0).fillna(0).max())
    passed = (
        row_var_max >= CHART_GATE_THRESHOLDS["heatmap_var_min"]
        or col_var_max >= CHART_GATE_THRESHOLDS["heatmap_var_min"]
    )
    return passed, {"row_var_max": row_var_max, "col_var_max": col_var_max}


def _df_to_markdown(df: "pd.DataFrame") -> str:
    if df.empty:
        return "*（空表格）*"
    headers = list(df.columns)
    lines = [
        "| " + " | ".join(str(h) for h in headers) + " |",
        "|" + "|".join(" --- " for _ in headers) + "|",
    ]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v) for v in row.values) + " |")
    return "\n".join(lines)


def save_fallback_table(df: "pd.DataFrame", csv_path: Path, md_path: Path, title: str, gate_meta: dict[str, Any]) -> dict[str, str]:
    import pandas as pd

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    numeric_cols = [col for col in df.columns if str(df[col].dtype).startswith(("int", "float"))]
    relation_rows: list[dict[str, Any]] = []
    for col in numeric_cols:
        series = df[col].dropna()
        if series.empty:
            continue
        latest = float(series.iloc[-1])
        mean_val = float(series.mean())
        delta = latest - mean_val
        delta_pct = (delta / abs(mean_val) * 100) if abs(mean_val) > 1e-12 else 0.0
        relation = "相对稳定"
        if delta_pct >= 5:
            relation = "显著高于均值"
        elif delta_pct <= -5:
            relation = "显著低于均值"
        relation_rows.append(
            {
                "维度": col,
                "最新值": round(latest, 6),
                "均值": round(mean_val, 6),
                "偏离(%)": round(delta_pct, 2),
                "逻辑关系": relation,
                "建议写法": f"{col} 当前{relation}，但趋势不显著，宜配合背景事件解释",
            }
        )

    if not relation_rows:
        relation_rows.append(
            {
                "维度": "数据概览",
                "最新值": "",
                "均值": "",
                "偏离(%)": "",
                "逻辑关系": "无可判定关系",
                "建议写法": "该组数据波动较弱，建议以事实罗列和逻辑说明为主",
            }
        )

    relation_df = pd.DataFrame(relation_rows)
    relation_df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    notes = [
        f"门控阈值：CV≥{CHART_GATE_THRESHOLDS['cv_min']:.3f}，|slope|≥{CHART_GATE_THRESHOLDS['slope_abs_min']:.3f}，R²≥{CHART_GATE_THRESHOLDS['r2_min']:.2f}，trend_strength≥{CHART_GATE_THRESHOLDS['trend_strength_min']:.2f}",
        f"本次结论：未达门控，改用逻辑关系表格；gate={json.dumps(gate_meta, ensure_ascii=False)}",
    ]
    md_lines = [f"## {title}", "", "*无显著趋势/差异，回退为逻辑关系表格输出。*", "", _df_to_markdown(relation_df), "", "### 门控说明", ""]
    md_lines.extend([f"- {item}" for item in notes])
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return {"csv": str(csv_path), "md": str(md_path)}


def _setup_theme(font_file: "Path | None" = None) -> "FontProperties | None":
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import seaborn as sns
    from matplotlib.font_manager import FontProperties

    family_name = "DejaVu Sans"
    if font_file and font_file.exists():
        fm.fontManager.addfont(str(font_file))
        family_name = FontProperties(fname=str(font_file)).get_name()

    sns.set_theme(style="whitegrid", context="talk")
    plt.rcParams.update(
        {
            "font.family": family_name,
            "font.sans-serif": [family_name, "PingFang SC", "Hiragino Sans GB", "Heiti SC", "STHeiti", "SimHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "figure.facecolor": "#F8FAFC",
            "axes.facecolor": "#FFFFFF",
            "axes.edgecolor": "#CBD5E1",
            "axes.labelcolor": "#334155",
            "xtick.color": "#475569",
            "ytick.color": "#475569",
            "grid.color": "#E2E8F0",
            "grid.alpha": 0.5,
            "legend.framealpha": 0.90,
            "legend.edgecolor": "#CBD5E1",
            "legend.facecolor": "#FFFFFF",
        }
    )
    return FontProperties(fname=str(font_file)) if font_file and font_file.exists() else None


def save_plot(
    df: "pd.DataFrame",
    csv_path: Path,
    png_path: Path,
    title: str,
    plot_kind: str = "line",
    x_col: str | None = None,
    y_cols: list[str] | None = None,
) -> dict[str, Any]:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.font_manager import FontProperties

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    if x_col is None:
        date_cols = [c for c in df.columns if c == "trade_date" or c.endswith("_date") or c == "year"]
        x_col = date_cols[0] if date_cols else df.columns[0]
    if y_cols is None:
        y_cols = [c for c in df.columns if c != x_col]

    if plot_kind == "heatmap":
        should_plot, gate_meta = should_generate_heatmap(df)
    elif plot_kind == "bar":
        should_plot, gate_meta = should_generate_bar_chart(df)
    else:
        should_plot, gate_meta = should_generate_chart(df, x_col, y_cols)

    if not should_plot:
        markdown_dir = csv_path.parent.parent / "markdown"
        md_path = markdown_dir / f"{csv_path.stem}.md"
        fallback = save_fallback_table(df, csv_path, md_path, title, gate_meta)
        return {"type": "table", "csv": fallback["csv"], "md": fallback["md"], "png": None, "gate": gate_meta}

    font_file = resolve_cjk_font_file()
    body_font = _setup_theme(font_file)
    title_font = FontProperties(fname=str(font_file), size=18, weight="bold") if font_file else None

    fig, ax = plt.subplots(figsize=(12, 6))
    if plot_kind == "bar":
        x = df.columns[0]
        y = df.columns[1]
        palette = ["#2563EB", "#38BDF8", "#22C55E", "#F59E0B", "#EC4899", "#8B5CF6"]
        sns.barplot(data=df, x=x, y=y, ax=ax, palette=palette[: len(df)], saturation=0.92)
        ax.tick_params(axis="x", rotation=20)
    elif plot_kind == "heatmap":
        matrix = df.set_index(df.columns[0])
        sns.heatmap(matrix, annot=True, fmt=".2f", cmap="YlOrRd", ax=ax, linewidths=0.4, linecolor="#E2E8F0", cbar_kws={"shrink": 0.8})
    else:
        palette = ["#2563EB", "#F59E0B", "#10B981", "#8B5CF6", "#EF4444"]
        for col in y_cols:
            if col not in df.columns:
                continue
            color = palette[(len(ax.lines)) % len(palette)]
            ax.plot(df[x_col], df[col], label=col, linewidth=2.0, color=color)
        ax.legend(loc="best")

    ax.set_title(title, loc="left", pad=16, color="#0F172A", fontproperties=title_font)
    ax.grid(True, alpha=0.28, linestyle="--", linewidth=0.8)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        if body_font:
            label.set_fontproperties(body_font)
    if ax.legend_ is not None:
        frame = ax.legend_.get_frame()
        frame.set_facecolor("#FFFFFF")
        frame.set_edgecolor("#CBD5E1")
        frame.set_alpha(0.92)
        for text in ax.legend_.get_texts():
            if body_font:
                text.set_fontproperties(body_font)
    fig.tight_layout()
    fig.savefig(png_path, dpi=180)
    plt.close(fig)
    df.to_csv(csv_path, index=False)
    return {"type": "chart", "csv": str(csv_path), "png": str(png_path), "gate": gate_meta}


def execute_finance_charts(topic: TopicContext) -> list[dict[str, Any]]:
    import akshare as ak
    import pandas as pd
    import tushare as ts

    token = read_tushare_token()
    if not token:
        raise RuntimeError("缺少 Tushare token，无法执行 finance charts")

    ts.set_token(token)
    pro = ts.pro_api()

    charts_out: list[dict[str, Any]] = []
    charts_dir_csv = topic.topic_root
    charts_dir_png = topic.topic_root

    # Chart 1: US CPI / Core CPI
    cpi = ak.macro_usa_cpi_monthly()[["日期", "今值"]].rename(columns={"日期": "trade_date", "今值": "cpi_mom"})
    core = ak.macro_usa_core_cpi_monthly()[["日期", "今值"]].rename(columns={"日期": "trade_date", "今值": "core_cpi_mom"})
    cpi["trade_date"] = pd.to_datetime(cpi["trade_date"])
    core["trade_date"] = pd.to_datetime(core["trade_date"])
    cpi_df = cpi.merge(core, on="trade_date", how="outer").sort_values("trade_date").tail(36)
    chart_01 = save_plot(
      cpi_df,
      charts_dir_csv / "图表_美国CPI对比.csv",
      charts_dir_png / "图表_美国CPI对比.png",
      "US CPI vs Core CPI (last 36 months)",
      x_col="trade_date",
      y_cols=["cpi_mom", "core_cpi_mom"],
    )
    charts_out.append({"anchor_id": "chart-01", "render_type": chart_01["type"], "csv": chart_01["csv"], "png": chart_01.get("png"), "md": chart_01.get("md"), "gate": chart_01.get("gate")})

    # Chart 2: Oil / Gold / Breakeven
    oil = ak.futures_foreign_hist(symbol="OIL")[["date", "close"]].rename(columns={"date": "trade_date", "close": "oil_close"})
    gold = ak.futures_foreign_hist(symbol="GC")[["date", "close"]].rename(columns={"date": "trade_date", "close": "gold_close"})
    breakeven = fetch_fred_series("T10YIE").rename(columns={"value": "breakeven_10y"})
    oil["trade_date"] = pd.to_datetime(oil["trade_date"])
    gold["trade_date"] = pd.to_datetime(gold["trade_date"])
    merged = (
        oil.merge(gold, on="trade_date", how="inner")
        .merge(breakeven, on="trade_date", how="left")
        .sort_values("trade_date")
        .tail(500)
    )
    chart_02 = save_plot(
      merged,
      charts_dir_csv / "图表_石油黄金通胀预期.csv",
      charts_dir_png / "图表_石油黄金通胀预期.png",
      "Oil / Gold / 10Y Breakeven",
      x_col="trade_date",
      y_cols=["oil_close", "gold_close", "breakeven_10y"],
    )
    charts_out.append({"anchor_id": "chart-02", "render_type": chart_02["type"], "csv": chart_02["csv"], "png": chart_02.get("png"), "md": chart_02.get("md"), "gate": chart_02.get("gate")})

    # Chart 3: ETF proxy / SPX / DGS10
    spx = pro.index_global(ts_code="SPX")[["trade_date", "close"]].rename(columns={"close": "spx_close"})
    dgs10 = fetch_fred_series("DGS10").rename(columns={"value": "us10y"})
    spx["trade_date"] = pd.to_datetime(spx["trade_date"])
    spx = spx.sort_values("trade_date").tail(500)
    market_df = spx.merge(dgs10, on="trade_date", how="inner").sort_values("trade_date")
    chart_03 = save_plot(
      market_df,
      charts_dir_csv / "图表_标普500与美债收益率.csv",
      charts_dir_png / "图表_标普500与美债收益率.png",
      "SPX vs US 10Y",
      x_col="trade_date",
      y_cols=["spx_close", "us10y"],
    )
    charts_out.append({"anchor_id": "chart-03", "render_type": chart_03["type"], "csv": chart_03["csv"], "png": chart_03.get("png"), "md": chart_03.get("md"), "gate": chart_03.get("gate")})

    # Chart 4: scenario heatmap
    scenario = pd.DataFrame(
        {
            "scenario": ["再通胀抬升", "增长走弱", "利率高位钝化", "风险偏好回升"],
            "gold": [0.7, 0.6, 0.8, 0.3],
            "silver": [0.5, 0.3, 0.4, 0.6],
            "oil": [0.9, -0.4, 0.2, 0.7],
            "equity": [-0.3, -0.7, -0.4, 0.8],
        }
    )
    chart_04 = save_plot(
      scenario,
      charts_dir_csv / "图表_情景矩阵热力图.csv",
      charts_dir_png / "图表_情景矩阵热力图.png",
      "Scenario Matrix",
      plot_kind="heatmap",
    )
    charts_out.append({"anchor_id": "chart-04", "render_type": chart_04["type"], "csv": chart_04["csv"], "png": chart_04.get("png"), "md": chart_04.get("md"), "gate": chart_04.get("gate")})

    return charts_out


def execute_japan_geopolitics_charts(topic: TopicContext) -> list[dict[str, Any]]:
    import pandas as pd

    charts_out: list[dict[str, Any]] = []
    charts_dir_csv = topic.topic_root
    charts_dir_png = topic.topic_root

    def world_bank(indicator: str) -> pd.DataFrame:
        url = f"https://api.worldbank.org/v2/country/JPN/indicator/{indicator}?format=json&per_page=200"
        with create_requests_session() as session:
            payload = session.get(url, headers={"User-Agent": USER_AGENT}, timeout=60).json()
        rows = payload[1]
        data = [{"year": int(item["date"]), "value": item["value"]} for item in rows if item["value"] is not None]
        return pd.DataFrame(data).sort_values("year")

    pop = world_bank("SP.POP.TOTL").rename(columns={"value": "population"})
    age = world_bank("SP.POP.65UP.TO.ZS").rename(columns={"value": "aged_65_pct"})
    mil = world_bank("MS.MIL.XPND.GD.ZS").rename(columns={"value": "military_gdp_pct"})

    pop_age = pop.merge(age, on="year", how="inner").tail(20)
    chart_01 = save_plot(
        pop_age,
        charts_dir_csv / "chart-01_population_aging.csv",
        charts_dir_png / "chart-01_population_aging.png",
        "Japan Population and 65+ Share",
        x_col="year",
        y_cols=["population", "aged_65_pct"],
    )
    charts_out.append({"anchor_id": "chart-01", "render_type": chart_01["type"], "csv": chart_01["csv"], "png": chart_01.get("png"), "md": chart_01.get("md"), "gate": chart_01.get("gate")})

    mil_tail = mil.tail(20)
    chart_02 = save_plot(
        mil_tail,
        charts_dir_csv / "chart-02_military_gdp.csv",
        charts_dir_png / "chart-02_military_gdp.png",
        "Japan Military Spending (% GDP)",
        x_col="year",
        y_cols=["military_gdp_pct"],
    )
    charts_out.append({"anchor_id": "chart-02", "render_type": chart_02["type"], "csv": chart_02["csv"], "png": chart_02.get("png"), "md": chart_02.get("md"), "gate": chart_02.get("gate")})

    timeline = pd.DataFrame(
        [
            {"event": "LDP shift", "score": 1},
            {"event": "Coalition reset", "score": 2},
            {"event": "Security docs", "score": 3},
            {"event": "Taiwan rhetoric", "score": 4},
        ]
    )
    chart_03 = save_plot(
        timeline,
        charts_dir_csv / "chart-03_security_timeline.csv",
        charts_dir_png / "chart-03_security_timeline.png",
        "Security Escalation Timeline",
        plot_kind="bar",
    )
    charts_out.append({"anchor_id": "chart-03", "render_type": chart_03["type"], "csv": chart_03["csv"], "png": chart_03.get("png"), "md": chart_03.get("md"), "gate": chart_03.get("gate")})

    risk = pd.DataFrame(
        {
            "scenario": ["安全升级", "劳动力缺口", "外交摩擦", "供应链波动"],
            "stocks": [0.4, 0.3, 0.7, 0.8],
            "shipping": [0.6, 0.2, 0.8, 0.9],
            "yen": [0.5, 0.4, 0.6, 0.5],
            "policy": [0.8, 0.7, 0.9, 0.6],
        }
    )
    chart_04 = save_plot(
        risk,
        charts_dir_csv / "chart-04_risk_matrix.csv",
        charts_dir_png / "chart-04_risk_matrix.png",
        "Risk Matrix",
        plot_kind="heatmap",
    )
    charts_out.append({"anchor_id": "chart-04", "render_type": chart_04["type"], "csv": chart_04["csv"], "png": chart_04.get("png"), "md": chart_04.get("md"), "gate": chart_04.get("gate")})

    return charts_out


def resolve_cjk_font_file() -> Path | None:
    candidates = [
        Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
        Path("/System/Library/Fonts/STHeiti Light.ttc"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def execute_openclaw_workflow_charts(topic: TopicContext) -> list[dict[str, Any]]:
    import pandas as pd
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

    charts_out: list[dict[str, Any]] = []
    charts_dir_csv = topic.topic_root
    charts_dir_png = topic.topic_root
    charts_dir_png.mkdir(parents=True, exist_ok=True)
    charts_dir_csv.mkdir(parents=True, exist_ok=True)

    font_file = resolve_cjk_font_file()

    def fp(size: int, weight: str = "normal") -> FontProperties | None:
        if font_file:
            return FontProperties(fname=str(font_file), size=size, weight=weight)
        return None

    def add_card(ax, x: float, y: float, w: float, h: float, text: str, face: str, edge: str, size: int = 16) -> None:
        shadow = FancyBboxPatch(
            (x + 0.006, y - 0.008),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=0,
            facecolor="#94A3B8",
            alpha=0.12,
        )
        ax.add_patch(shadow)
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.02",
            linewidth=1.8,
            facecolor=face,
            edgecolor=edge,
        )
        ax.add_patch(patch)
        ax.text(
            x + w / 2,
            y + h / 2,
            text,
            ha="center",
            va="center",
            color="#1F2937",
            fontproperties=fp(size, "bold"),
        )

    def add_card_center(ax, cx: float, cy: float, w: float, h: float, text: str, face: str, edge: str, size: int = 15) -> None:
        add_card(ax, cx - w / 2, cy - h / 2, w, h, text, face, edge, size)

    def add_title(fig, title: str, subtitle: str) -> None:
        fig.text(0.06, 0.92, title, color="#111827", fontproperties=fp(24, "bold"))
        fig.text(0.06, 0.875, subtitle, color="#6B7280", fontproperties=fp(11))

    def add_badge(ax, x: float, y: float, text: str, face: str, edge: str, color: str) -> None:
        patch = FancyBboxPatch(
            (x, y),
            0.12,
            0.045,
            boxstyle="round,pad=0.01,rounding_size=0.02",
            linewidth=1.2,
            facecolor=face,
            edgecolor=edge,
        )
        ax.add_patch(patch)
        ax.text(x + 0.06, y + 0.0225, text, ha="center", va="center", color=color, fontproperties=fp(10, "bold"))

    def draw_arrow(ax, start: tuple[float, float], end: tuple[float, float], color: str = "#64748B") -> None:
        ax.annotate(
            "",
            xy=end,
            xytext=start,
            arrowprops=dict(arrowstyle="-|>", lw=1.8, color=color, shrinkA=6, shrinkB=6),
        )

    def draw_curve_arrow(
        ax,
        start: tuple[float, float],
        end: tuple[float, float],
        rad: float,
        color: str = "#475569",
        lw: float = 2.0,
    ) -> None:
        arrow = FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=lw,
            color=color,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=12,
            shrinkB=12,
        )
        ax.add_patch(arrow)

    def finish(fig, ax, output: Path) -> None:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        fig.savefig(output, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

    install_nodes = pd.read_csv(charts_dir_csv / "chart-01_install_flow_nodes.csv")
    install_steps = install_nodes["label"].tolist()
    fig, ax = plt.subplots(figsize=(14, 8), facecolor="#F8FAFC")
    add_title(fig, "OpenClaw 一键安装流程", "把高门槛环境配置拆成 5 步主流程 + 3 步失败兜底")
    add_badge(ax, 0.06, 0.80, "主路径", "#DBEAFE", "#60A5FA", "#1D4ED8")
    add_badge(ax, 0.06, 0.31, "兜底路径", "#FEF3C7", "#F59E0B", "#B45309")
    top_steps = install_steps[:5]
    fallback_steps = install_steps[5:]
    x_positions = [0.06, 0.255, 0.45, 0.645, 0.84]
    w, h = 0.13, 0.10
    for idx, (x, label) in enumerate(zip(x_positions, top_steps), start=1):
        add_card(ax, x, 0.68, w, h, label, "#DBEAFE", "#60A5FA")
        circ = Circle((x + 0.022, 0.765), 0.018, facecolor="#2563EB", edgecolor="none")
        ax.add_patch(circ)
        ax.text(x + 0.022, 0.765, str(idx), ha="center", va="center", color="white", fontproperties=fp(10, "bold"))
        if idx < len(top_steps):
            draw_arrow(ax, (x + w, 0.73), (x_positions[idx] - 0.01, 0.73))
    if fallback_steps:
        fallback_x = [0.22, 0.45, 0.68]
        for idx, (x, label) in enumerate(zip(fallback_x, fallback_steps), start=1):
            add_card(ax, x, 0.34, 0.15, 0.10, label, "#FEF3C7", "#F59E0B")
            if idx < len(fallback_steps):
                draw_arrow(ax, (x + 0.15, 0.39), (fallback_x[idx] - 0.015, 0.39), "#B45309")
        draw_arrow(ax, (x_positions[-1] + 0.03, 0.68), (fallback_x[0] + 0.075, 0.44), "#DC2626")
        ax.text(0.83, 0.62, "失败分流", color="#DC2626", fontproperties=fp(11, "bold"))
    finish(fig, ax, charts_dir_png / "chart-01_install_flow.png")
    charts_out.append({"anchor_id": "chart-01", "csv": str(charts_dir_csv / "chart-01_install_flow_nodes.csv"), "png": str(charts_dir_png / "chart-01_install_flow.png")})

    security = pd.read_csv(charts_dir_csv / "chart-02_security_boundary.csv")
    fig, ax = plt.subplots(figsize=(13, 8), facecolor="#F8FAFC")
    add_title(fig, "OpenClaw 安全边界矩阵", "可用性要服务于可审计，不能把一键安装写成无边界暴露")
    add_badge(ax, 0.06, 0.80, "默认策略", "#DCFCE7", "#22C55E", "#15803D")
    row_y = [0.70, 0.58, 0.46, 0.34, 0.22]
    item_name_map = {
        "API Key": "API 密钥",
        "Path Permission": "目录权限",
        "Package Lock": "依赖锁定",
        "Port Exposure": "端口暴露",
        "Skill Trust": "Skill 信任",
    }
    header_x = [0.42, 0.56, 0.70]
    for x, label, face, edge, color in [
        (header_x[0], "基础", "#E0F2FE", "#7DD3FC", "#0369A1"),
        (header_x[1], "受控", "#DCFCE7", "#4ADE80", "#166534"),
        (header_x[2], "严格", "#FEE2E2", "#FCA5A5", "#B91C1C"),
    ]:
        add_card(ax, x, 0.79, 0.11, 0.055, label, face, edge, 11)
    for y, (_, row) in zip(row_y, security.iterrows()):
        ax.plot([0.08, 0.86], [y - 0.015, y - 0.015], color="#E2E8F0", linewidth=1)
        ax.text(0.08, y + 0.025, item_name_map.get(str(row["item"]), str(row["item"])), color="#111827", fontproperties=fp(14, "bold"))
        for level in range(3):
            active = level < int(row["control_level_1to3"])
            is_target = (level + 1) == int(row["control_level_1to3"])
            add_card(
                ax,
                0.42 + level * 0.14,
                y,
                0.11,
                0.065,
                ["基础", "受控", "严格"][level],
                "#DCFCE7" if active else "#E5E7EB",
                "#22C55E" if active else "#CBD5E1",
                11,
            )
            if is_target:
                ax.text(0.42 + level * 0.14 + 0.055, y - 0.022, "当前建议", ha="center", color="#64748B", fontproperties=fp(9, "bold"))
    ax.text(0.08, 0.10, "建议：默认做到“受控”，涉及密钥、依赖锁定与目录权限时提升到“严格”。", color="#6B7280", fontproperties=fp(11))
    finish(fig, ax, charts_dir_png / "chart-02_security_boundary_matrix.png")
    charts_out.append({"anchor_id": "chart-02", "csv": str(charts_dir_csv / "chart-02_security_boundary.csv"), "png": str(charts_dir_png / "chart-02_security_boundary_matrix.png")})

    governance_nodes = pd.read_csv(charts_dir_csv / "chart-03_team_governance_nodes.csv")["label"].tolist()
    fig, ax = plt.subplots(figsize=(13, 8), facecolor="#F8FAFC")
    add_title(fig, "团队治理闭环", "从版本基线到回滚更新，安装流程必须有闭环而不是一次性成功")
    add_badge(ax, 0.06, 0.80, "治理循环", "#EDE9FE", "#A78BFA", "#6D28D9")
    centers = [
        (0.26, 0.64),
        (0.50, 0.74),
        (0.74, 0.64),
        (0.74, 0.36),
        (0.50, 0.26),
        (0.26, 0.36),
    ]
    colors = [
        ("#DBEAFE", "#60A5FA"),
        ("#DBEAFE", "#60A5FA"),
        ("#DBEAFE", "#60A5FA"),
        ("#DCFCE7", "#4ADE80"),
        ("#DCFCE7", "#4ADE80"),
        ("#DCFCE7", "#4ADE80"),
    ]
    for (cx, cy), label, (face, edge) in zip(centers, governance_nodes, colors):
        add_card_center(ax, cx, cy, 0.18, 0.09, label, face, edge, 14)
    core = Circle((0.50, 0.50), 0.08, facecolor="#FFFFFF", edgecolor="#CBD5E1", linewidth=1.6)
    ax.add_patch(core)
    ax.text(0.50, 0.50, "可回滚\n可验证", ha="center", va="center", color="#334155", fontproperties=fp(12, "bold"))
    for idx in range(len(centers)):
        x1, y1 = centers[idx]
        x2, y2 = centers[(idx + 1) % len(centers)]
        rad = 0.18 if idx in {0, 3} else 0.10 if idx in {1, 4} else 0.0
        draw_curve_arrow(ax, (x1, y1), (x2, y2), rad=rad, color="#475569")
    finish(fig, ax, charts_dir_png / "chart-03_team_governance_loop.png")
    charts_out.append({"anchor_id": "chart-03", "csv": str(charts_dir_csv / "chart-03_team_governance_nodes.csv"), "png": str(charts_dir_png / "chart-03_team_governance_loop.png")})

    trouble_nodes = pd.read_csv(charts_dir_csv / "chart-04_troubleshoot_nodes.csv")["label"].tolist()
    fig, ax = plt.subplots(figsize=(13, 8), facecolor="#F8FAFC")
    add_title(fig, "常见故障排查树", "优先把问题归类成依赖、权限、端口，再给出最小修复动作")
    top = trouble_nodes[0]
    mid = trouble_nodes[1:4]
    fixes = trouble_nodes[4:7]
    bottom = trouble_nodes[7]
    add_card(ax, 0.38, 0.78, 0.24, 0.09, top, "#FCE7F3", "#EC4899", 15)
    mx = [0.10, 0.39, 0.68]
    fx = [0.10, 0.39, 0.68]
    for x, label in zip(mx, mid):
        add_card(ax, x, 0.56, 0.22, 0.09, label, "#FEF3C7", "#F59E0B", 14)
        draw_arrow(ax, (0.50, 0.78), (x + 0.11, 0.65))
    for x, label in zip(fx, fixes):
        add_card(ax, x, 0.32, 0.22, 0.09, label, "#DCFCE7", "#22C55E", 13)
    for x in fx:
        draw_arrow(ax, (x + 0.11, 0.56), (x + 0.11, 0.41))
        draw_arrow(ax, (x + 0.11, 0.32), (0.50, 0.20))
    add_card(ax, 0.39, 0.12, 0.22, 0.09, bottom, "#DBEAFE", "#3B82F6", 15)
    finish(fig, ax, charts_dir_png / "chart-04_troubleshoot_tree.png")
    charts_out.append({"anchor_id": "chart-04", "csv": str(charts_dir_csv / "chart-04_troubleshoot_nodes.csv"), "png": str(charts_dir_png / "chart-04_troubleshoot_tree.png")})

    return charts_out


def execute_charts(topic: TopicContext) -> dict[str, Any]:
    title_text = f"{topic.title} {' '.join(str(item.get('statement', '')) for item in topic.topic_config.get('claim_bindings', []))}"
    energy_geopolitics = topic.topic_type == "geopolitics" and bool(
        re.search(r"油价|原油|能源|航运|海峡|霍尔木兹|供应链", title_text, flags=re.IGNORECASE)
    )
    if topic.topic_type == "finance_macro" or energy_geopolitics:
        generated = execute_finance_charts(topic)
    elif "OpenClaw" in topic.title or "龙虾" in topic.title:
        generated = execute_openclaw_workflow_charts(topic)
    elif topic.topic_type == "geopolitics" and ("日本" in topic.title or "高市" in topic.title):
        generated = execute_japan_geopolitics_charts(topic)
    else:
        generated = []
    chart_count = len([item for item in generated if item.get("render_type", "chart") == "chart"])
    table_count = len([item for item in generated if item.get("render_type") == "table"])
    result = {
        "topic": topic.slug,
        "generated": generated,
        "summary": {
            "chart_count": chart_count,
            "table_count": table_count,
            "gate_thresholds": CHART_GATE_THRESHOLDS,
        },
    }
    # 保存 manifest 到 config 目录
    config_dir = topic.topic_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    write_json(config_dir / "chart_generation_manifest.json", result)
    return result


def search_wikimedia_images(
    query: str,
    limit: int = 3,
    timeout: int = DEFAULT_IMAGE_SEARCH_TIMEOUT,
    thumb_width: int = DEFAULT_WIKIMEDIA_THUMB_WIDTH,
) -> list[dict[str, Any]]:
    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": 6,
        "gsrlimit": limit,
        "prop": "imageinfo",
        "iiprop": "url|size",
        "iiurlwidth": max(512, int(thumb_width)),
        "format": "json",
    }
    with create_requests_session() as session:
        response = session.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    response.raise_for_status()
    data = response.json()
    rows = []
    pages = data.get("query", {}).get("pages", {})
    for item in pages.values():
        info = (item.get("imageinfo") or [{}])[0]
        original_url = info.get("url")
        download_url = info.get("thumburl") or original_url
        if download_url and Path(download_url).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            rows.append({
                "title": item.get("title"),
                "url": original_url,
                "download_url": download_url,
                "descriptionurl": info.get("descriptionurl", ""),
                "width": info.get("width"),
                "height": info.get("height"),
                "thumbwidth": info.get("thumbwidth"),
                "thumbheight": info.get("thumbheight"),
            })
    return rows


def env_int(name: str, default: int) -> int:
    raw = str(os.environ.get(name, "")).strip()
    if not raw:
        return default
    try:
        return int(float(raw))
    except ValueError:
        return default


def normalize_search_queries(raw_queries: Any, default_channel: str) -> list[dict[str, Any]]:
    if not isinstance(raw_queries, list):
        return []
    records: list[dict[str, Any]] = []

    def parse_priority(value: Any) -> int:
        try:
            return int(float(value))
        except Exception:  # noqa: BLE001
            return 0

    for idx, item in enumerate(raw_queries):
        if isinstance(item, str):
            query = item.strip()
            if query:
                records.append(
                    {
                        "query": query,
                        "priority": 0,
                        "entity_type": "topic",
                        "entity": "",
                        "channel": default_channel,
                        "order": idx,
                    }
                )
            continue
        if not isinstance(item, dict):
            continue
        query = str(item.get("query", "")).strip()
        if not query:
            continue
        records.append(
            {
                "query": query,
                "priority": parse_priority(item.get("priority", 0)),
                "entity_type": str(item.get("entity_type", "topic") or "topic").strip().lower(),
                "entity": str(item.get("entity", "")).strip(),
                "channel": str(item.get("channel", default_channel) or default_channel).strip().lower(),
                "order": idx,
            }
        )
    records.sort(key=lambda row: (-int(row.get("priority", 0)), int(row.get("order", 0))))
    return records


def read_image_dimensions(payload: bytes) -> tuple[int | None, int | None]:
    if len(payload) < 24:
        return None, None
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", payload[16:24])
    if payload[:2] == b"\xff\xd8":
        index = 2
        while index < len(payload) - 1:
            while index < len(payload) and payload[index] != 0xFF:
                index += 1
            while index < len(payload) and payload[index] == 0xFF:
                index += 1
            if index >= len(payload):
                break
            marker = payload[index]
            index += 1
            if marker in {0xD8, 0xD9}:
                continue
            if index + 1 >= len(payload):
                break
            segment_length = (payload[index] << 8) + payload[index + 1]
            index += 2
            if segment_length < 2 or index + segment_length - 2 > len(payload):
                break
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
                if index + 4 >= len(payload):
                    break
                height = (payload[index + 1] << 8) + payload[index + 2]
                width = (payload[index + 3] << 8) + payload[index + 4]
                return width, height
            index += segment_length - 2
    if payload[:4] == b"RIFF" and payload[8:12] == b"WEBP":
        chunk = payload[12:16]
        if chunk == b"VP8X" and len(payload) >= 30:
            width = 1 + int.from_bytes(payload[24:27], "little")
            height = 1 + int.from_bytes(payload[27:30], "little")
            return width, height
        if chunk == b"VP8L" and len(payload) >= 25:
            b0, b1, b2, b3 = payload[21:25]
            width = 1 + (((b1 & 0x3F) << 8) | b0)
            height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
            return width, height
        if chunk == b"VP8 " and len(payload) >= 30 and payload[20:23] == b"\x9d\x01\x2a":
            width = payload[26] | ((payload[27] & 0x3F) << 8)
            height = payload[28] | ((payload[29] & 0x3F) << 8)
            return width, height
    return None, None


def gate_image_resolution(payload: bytes, min_short_edge: int) -> dict[str, Any]:
    width, height = read_image_dimensions(payload)
    if width is None or height is None:
        return {
            "accepted": False,
            "reason": "unknown_resolution",
            "width": width,
            "height": height,
            "short_edge": None,
            "min_short_edge_required": min_short_edge,
        }
    short_edge = min(width, height)
    if short_edge < min_short_edge:
        return {
            "accepted": False,
            "reason": "short_edge_below_threshold",
            "width": width,
            "height": height,
            "short_edge": short_edge,
            "min_short_edge_required": min_short_edge,
        }
    return {
        "accepted": True,
        "reason": "",
        "width": width,
        "height": height,
        "short_edge": short_edge,
        "min_short_edge_required": min_short_edge,
    }


def decode_duckduckgo_href(raw_href: str) -> str:
    href = unescape(str(raw_href or "").strip())
    if not href:
        return ""
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/l/?"):
        href = "https://duckduckgo.com" + href
    parsed = urlparse(href)
    if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
        target = (parse_qs(parsed.query).get("uddg") or [""])[0]
        return unquote(target).strip()
    return href


def search_news_pages(query: str, limit: int = 3, timeout: int = DEFAULT_NEWS_SEARCH_TIMEOUT) -> list[dict[str, Any]]:
    with create_requests_session() as session:
        response = session.get(
            "https://duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": USER_AGENT},
            timeout=timeout,
        )
    response.raise_for_status()
    pattern = re.compile(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', flags=re.IGNORECASE)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for href, raw_title in pattern.findall(response.text):
        target_url = decode_duckduckgo_href(href)
        parsed = urlparse(target_url)
        if parsed.scheme not in {"http", "https"}:
            continue
        if target_url in seen:
            continue
        seen.add(target_url)
        title = re.sub(r"<[^>]+>", "", unescape(raw_title)).strip()
        rows.append({"title": title or parsed.netloc, "url": target_url})
        if len(rows) >= limit:
            break
    return rows


def fetch_news_page_screenshot(
    page_url: str,
    width: int = 1600,
    height: int = 1200,
    timeout: int = DEFAULT_NEWS_SCREENSHOT_TIMEOUT,
) -> tuple[bytes, str]:
    encoded_page = quote(page_url, safe=":/?&=#%")
    endpoints = [
        f"https://image.thum.io/get/width/{width}/crop/{height}/noanimate/{encoded_page}",
        f"https://mini.s-shot.ru/{width}x{height}/JPEG/1200/Z100/?{encoded_page}",
    ]
    errors: list[str] = []
    for endpoint in endpoints:
        try:
            with create_requests_session() as session:
                response = session.get(endpoint, headers={"User-Agent": USER_AGENT}, timeout=timeout)
            response.raise_for_status()
            content_type = str(response.headers.get("content-type", "")).lower()
            payload = response.content
            if "image/" not in content_type and not payload.startswith((b"\xff\xd8", b"\x89PNG", b"RIFF")):
                raise RuntimeError(f"unexpected_content_type:{content_type}")
            return payload, endpoint
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{endpoint}::{exc}")
    raise RuntimeError("screenshot_fetch_failed: " + " | ".join(errors))


def execute_image_search(topic: TopicContext, per_query_download: int = 1) -> dict[str, Any]:
    # 新口径优先从 images/web_search 读取；保留 config 目录兼容 fallback
    config_dir = topic.topic_root / "config"
    queries_path = topic.topic_root / "images" / "web_search" / "image_search_queries.json"
    if not queries_path.exists():
        queries_path = config_dir / "image_search_queries.json"
    queries_raw = read_json(queries_path)
    queries = normalize_search_queries(queries_raw, default_channel="wikimedia")
    screenshot_queries_path = topic.topic_root / "images" / "web_search" / "news_screenshot_queries.json"
    if not screenshot_queries_path.exists():
        screenshot_queries_path = config_dir / "news_screenshot_queries.json"
    screenshot_queries: list[dict[str, Any]] = []
    if screenshot_queries_path.exists():
        screenshot_queries = normalize_search_queries(read_json(screenshot_queries_path), default_channel="news_screenshot")
    screenshot_queries.extend([row for row in queries if row.get("channel") == "news_screenshot"])
    screenshot_queries_map: dict[str, dict[str, Any]] = {}
    for row in screenshot_queries:
        key = row.get("query", "").strip().lower()
        if key and key not in screenshot_queries_map:
            screenshot_queries_map[key] = row
    screenshot_queries = list(screenshot_queries_map.values())

    min_short_edge = max(256, env_int("MATERIAL_IMAGE_MIN_SHORT_EDGE", IMAGE_MIN_SHORT_EDGE))
    person_download_boost = max(1, env_int("MATERIAL_PERSON_DOWNLOAD_BOOST", DEFAULT_PERSON_DOWNLOAD_BOOST))
    news_search_limit = max(1, env_int("MATERIAL_NEWS_SEARCH_LIMIT", DEFAULT_NEWS_SEARCH_LIMIT))
    screenshot_per_query = max(1, env_int("MATERIAL_NEWS_SCREENSHOT_PER_QUERY", DEFAULT_NEWS_SCREENSHOT_PER_QUERY))
    screenshot_total_limit = max(1, env_int("MATERIAL_NEWS_SCREENSHOT_TOTAL_LIMIT", DEFAULT_NEWS_SCREENSHOT_TOTAL_LIMIT))
    image_search_timeout = max(5, env_int("MATERIAL_IMAGE_SEARCH_TIMEOUT", DEFAULT_IMAGE_SEARCH_TIMEOUT))
    image_download_timeout = max(5, env_int("MATERIAL_IMAGE_DOWNLOAD_TIMEOUT", DEFAULT_IMAGE_DOWNLOAD_TIMEOUT))
    image_max_bytes = max(512 * 1024, env_int("MATERIAL_IMAGE_MAX_BYTES", DEFAULT_IMAGE_MAX_BYTES))
    wikimedia_thumb_width = max(512, env_int("MATERIAL_WIKIMEDIA_THUMB_WIDTH", DEFAULT_WIKIMEDIA_THUMB_WIDTH))
    news_search_timeout = max(5, env_int("MATERIAL_NEWS_SEARCH_TIMEOUT", DEFAULT_NEWS_SEARCH_TIMEOUT))
    news_screenshot_timeout = max(5, env_int("MATERIAL_NEWS_SCREENSHOT_TIMEOUT", DEFAULT_NEWS_SCREENSHOT_TIMEOUT))
    total_image_download_limit = max(1, env_int("MATERIAL_IMAGE_DOWNLOAD_TOTAL_LIMIT", DEFAULT_IMAGE_DOWNLOAD_TOTAL_LIMIT))
    enable_news_screenshot = str(os.environ.get("MATERIAL_ENABLE_NEWS_SCREENSHOT", "1")).strip().lower() not in {"0", "false", "no", "off"}

    all_candidates = []
    downloaded = []
    successful_wikimedia_downloads = 0
    for idx, record in enumerate(queries, start=1):
        if record.get("channel") == "news_screenshot":
            continue
        if successful_wikimedia_downloads >= total_image_download_limit:
            break
        query = str(record.get("query", "")).strip()
        if not query:
            continue
        try:
            candidates = run_with_deadline(
                image_search_timeout + 5,
                search_wikimedia_images,
                query,
                limit=3,
                timeout=image_search_timeout,
                thumb_width=wikimedia_thumb_width,
            )
        except Exception as exc:  # noqa: BLE001
            all_candidates.append({"query": query, "channel": "wikimedia", "error": str(exc)})
            continue
        all_candidates.append(
            {
                "query": query,
                "channel": "wikimedia",
                "entity_type": record.get("entity_type", "topic"),
                "priority": record.get("priority", 0),
                "candidates": candidates,
            }
        )
        download_limit = per_query_download
        if record.get("entity_type") == "person":
            download_limit = max(download_limit, person_download_boost)
        for candidate_rank, candidate in enumerate(candidates[:download_limit], start=1):
            if successful_wikimedia_downloads >= total_image_download_limit:
                break
            try:
                source_url = candidate.get("download_url") or candidate.get("url") or ""
                payload_path = topic.topic_root / f".tmp_download_{idx:02d}_{candidate_rank:02d}"
                run_with_deadline(
                    image_download_timeout + 5,
                    download_file,
                    source_url,
                    payload_path,
                    headers={"User-Agent": USER_AGENT},
                    timeout=image_download_timeout,
                    max_bytes=image_max_bytes,
                )
                payload = payload_path.read_bytes()
                payload_path.unlink(missing_ok=True)
                gate = gate_image_resolution(payload, min_short_edge=min_short_edge)
                if not gate["accepted"]:
                    downloaded.append(
                        {
                            "channel": "wikimedia",
                            "query": query,
                            "entity_type": record.get("entity_type", "topic"),
                            "entity": record.get("entity", ""),
                            "url": candidate.get("url", ""),
                            "download_url": source_url,
                            "title": candidate.get("title", ""),
                            "rejected": True,
                            "reject_reason": gate["reason"],
                            "width": gate["width"],
                            "height": gate["height"],
                            "short_edge": gate["short_edge"],
                            "min_short_edge_required": gate["min_short_edge_required"],
                        }
                    )
                    continue
                suffix = Path(candidate["url"]).suffix or ".jpg"
                filename = build_image_filename(
                    query=query,
                    entity=str(record.get("entity", "") or ""),
                    candidate_rank=candidate_rank,
                    suffix=suffix,
                    query_index=idx,
                )
                out = topic.topic_root / filename
                out.write_bytes(payload)
                downloaded.append(
                    {
                        "channel": "wikimedia",
                        "query": query,
                        "entity_type": record.get("entity_type", "topic"),
                        "entity": record.get("entity", ""),
                        "file": str(out),
                        "url": candidate.get("url", ""),
                        "download_url": source_url,
                        "title": candidate.get("title", ""),
                        "width": gate["width"],
                        "height": gate["height"],
                        "short_edge": gate["short_edge"],
                    }
                )
                successful_wikimedia_downloads += 1
            except Exception as exc:  # noqa: BLE001
                downloaded.append(
                    {
                        "channel": "wikimedia",
                        "query": query,
                        "entity_type": record.get("entity_type", "topic"),
                        "entity": record.get("entity", ""),
                        "error": str(exc),
                        "url": candidate.get("url", ""),
                    }
                )

    screenshot_taken = 0
    if enable_news_screenshot and screenshot_queries:
        # 直接保存到选题根目录，不使用子目录
        screenshot_dir = topic.topic_root
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        for idx, record in enumerate(screenshot_queries, start=1):
            if screenshot_taken >= screenshot_total_limit:
                break
            query = str(record.get("query", "")).strip()
            if not query:
                continue
            try:
                page_candidates = run_with_deadline(
                    news_search_timeout + 5,
                    search_news_pages,
                    query,
                    limit=news_search_limit,
                    timeout=news_search_timeout,
                )
            except Exception as exc:  # noqa: BLE001
                all_candidates.append({"query": query, "channel": "news_screenshot", "error": str(exc)})
                continue
            all_candidates.append({"query": query, "channel": "news_screenshot", "candidates": page_candidates})

            for page in page_candidates[:screenshot_per_query]:
                if screenshot_taken >= screenshot_total_limit:
                    break
                try:
                    payload, provider_url = run_with_deadline(
                        news_screenshot_timeout + 5,
                        fetch_news_page_screenshot,
                        page["url"],
                        timeout=news_screenshot_timeout,
                    )
                    gate = gate_image_resolution(payload, min_short_edge=min_short_edge)
                    if not gate["accepted"]:
                        downloaded.append(
                            {
                                "channel": "news_screenshot",
                                "query": query,
                                "title": page.get("title", ""),
                                "source_page_url": page.get("url", ""),
                                "screenshot_provider_url": provider_url,
                                "rejected": True,
                                "reject_reason": gate["reason"],
                                "width": gate["width"],
                                "height": gate["height"],
                                "short_edge": gate["short_edge"],
                                "min_short_edge_required": gate["min_short_edge_required"],
                            }
                        )
                        continue
                    page_host = urlparse(page.get("url", "")).netloc or "news"
                    # 使用中文前缀的描述性文件名
                    filename = f"图片_新闻截图_news_{idx:02d}_{screenshot_taken + 1:02d}__{safe_slug(query)[:40]}__{safe_slug(page_host)[:24]}.jpg"
                    out = screenshot_dir / filename
                    out.write_bytes(payload)
                    screenshot_taken += 1
                    downloaded.append(
                        {
                            "channel": "news_screenshot",
                            "query": query,
                            "title": page.get("title", ""),
                            "source_page_url": page.get("url", ""),
                            "screenshot_provider_url": provider_url,
                            "file": str(out),
                            "width": gate["width"],
                            "height": gate["height"],
                            "short_edge": gate["short_edge"],
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    downloaded.append(
                        {
                            "channel": "news_screenshot",
                            "query": query,
                            "title": page.get("title", ""),
                            "source_page_url": page.get("url", ""),
                            "error": str(exc),
                        }
                    )
    # 保存 manifest 到 config 目录（不影响素材扁平化）
    config_dir = topic.topic_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    write_json(config_dir / "image_candidates.json", all_candidates)
    write_json(config_dir / "image_download_manifest.json", downloaded)
    downloaded_ok = [d for d in downloaded if d.get("file")]
    return {
        "topic": topic.slug,
        "downloaded": len(downloaded_ok),
        "person_downloaded": len([d for d in downloaded_ok if d.get("entity_type") == "person"]),
        "news_screenshots": len([d for d in downloaded_ok if d.get("channel") == "news_screenshot"]),
        "rejected_low_resolution": len([d for d in downloaded if d.get("reject_reason") == "short_edge_below_threshold"]),
        "min_short_edge_required": min_short_edge,
        "wikimedia_download_limit": total_image_download_limit,
    }


def yt_dlp_json(spec: str) -> dict[str, Any]:
    socket_timeout = max(5, env_int("MATERIAL_YTDLP_SOCKET_TIMEOUT", DEFAULT_YTDLP_SOCKET_TIMEOUT))
    command_timeout = max(30, env_int("MATERIAL_YTDLP_COMMAND_TIMEOUT", DEFAULT_YTDLP_COMMAND_TIMEOUT))
    cmd = ["yt-dlp", "--socket-timeout", str(socket_timeout), "--retries", "1", "--flat-playlist", "--dump-single-json", spec]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=command_timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:] or "yt-dlp failed")
    return json.loads(proc.stdout)


def yt_dlp_video_metadata(url: str) -> dict[str, Any]:
    socket_timeout = max(5, env_int("MATERIAL_YTDLP_SOCKET_TIMEOUT", DEFAULT_YTDLP_SOCKET_TIMEOUT))
    command_timeout = max(30, env_int("MATERIAL_YTDLP_COMMAND_TIMEOUT", DEFAULT_YTDLP_COMMAND_TIMEOUT))
    cmd = ["yt-dlp", "--socket-timeout", str(socket_timeout), "--retries", "1", "--dump-json", "--skip-download", "--no-playlist", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=command_timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:] or "yt-dlp metadata failed")
    for line in proc.stdout.splitlines():
        text = line.strip()
        if text.startswith("{"):
            return json.loads(text)
    raise RuntimeError("yt-dlp metadata missing json payload")


def to_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_fractional_float(value: Any) -> float | None:
    text = str(value or "").strip()
    if not text:
        return None
    if "/" in text:
        left, _, right = text.partition("/")
        numerator = to_float(left)
        denominator = to_float(right)
        if numerator is None or denominator in {None, 0.0}:
            return None
        return numerator / denominator
    return to_float(text)


def matches_any_pattern(text: str, patterns: list[str]) -> bool:
    lowered = (text or "").lower()
    return any(re.search(pattern, lowered, flags=re.IGNORECASE) for pattern in patterns)


def classify_video_source(title: str, channel: str, uploader: str) -> tuple[str, bool, list[str]]:
    source_text = " ".join([title or "", channel or "", uploader or ""])
    is_news_like = matches_any_pattern(source_text, NEWS_LIVE_INTERVIEW_PATTERNS)
    is_self_media = matches_any_pattern(source_text, SELF_MEDIA_TALKING_HEAD_PATTERNS)
    trusted_newsroom = matches_any_pattern(source_text, TRUSTED_NEWSROOM_PATTERNS)

    reasons: list[str] = []
    if is_self_media and not trusted_newsroom:
        reasons.append("self_media_talking_head")
        return "self_media_talking_head", False, reasons
    if is_news_like:
        return "news_live_or_interview", True, reasons
    return "general_footage", True, reasons


def resolve_video_quality_policy(topic: TopicContext) -> dict[str, Any]:
    policy = {
        "min_height": VIDEO_MIN_HEIGHT,
        "min_duration_seconds": VIDEO_MIN_DURATION_SECONDS,
        "min_scene_changes": VIDEO_MIN_SCENE_CHANGES,
        "min_scene_change_rate": VIDEO_MIN_SCENE_CHANGE_RATE,
        "allow_news_live_or_interview": True,
        "block_self_media_talking_head": True,
        "reject_screenshot_montage": True,
    }
    topic_policy = topic.topic_config.get("video_quality_policy")
    if isinstance(topic_policy, dict):
        for key in [
            "min_height",
            "min_duration_seconds",
            "min_scene_changes",
            "min_scene_change_rate",
            "allow_news_live_or_interview",
            "block_self_media_talking_head",
            "reject_screenshot_montage",
        ]:
            if key in topic_policy:
                policy[key] = topic_policy[key]
    return policy


def evaluate_video_candidate(candidate: dict[str, Any], metadata: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    title = candidate.get("title") or ""
    channel = candidate.get("channel") or ""
    uploader = metadata.get("uploader") or channel
    source_category, source_ok, source_reasons = classify_video_source(title, channel, str(uploader))

    height = to_int(metadata.get("height")) or to_int(candidate.get("height"))
    width = to_int(metadata.get("width")) or to_int(candidate.get("width"))
    duration_seconds = to_int(metadata.get("duration")) or to_int(candidate.get("duration"))
    fps = parse_fractional_float(metadata.get("fps") or metadata.get("avg_frame_rate"))
    extractor = str(metadata.get("extractor") or "")
    source_domain = urlparse(candidate.get("url") or "").netloc.lower()

    min_height = to_int(policy.get("min_height"))
    enforce_resolution = bool(min_height and min_height > 0)

    reject_reasons: list[str] = []
    if enforce_resolution and height is not None and height < min_height:
        reject_reasons.append("resolution_below_min_height")
    if not source_ok:
        reject_reasons.extend(source_reasons)

    return {
        "source_category": source_category,
        "source_ok": source_ok,
        "resolution_height": height,
        "resolution_width": width,
        "duration_seconds_hint": duration_seconds,
        "fps_hint": round(fps, 3) if fps is not None else None,
        "extractor": extractor,
        "source_domain": source_domain,
        "min_height_required": min_height if enforce_resolution else None,
        "pre_download_pass": len(reject_reasons) == 0,
        "reject_reasons": sorted(set(reject_reasons)),
    }


def probe_video_file(file_path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
        str(file_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-800:] or "ffprobe failed")
    payload = json.loads(proc.stdout or "{}")
    video_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "video"), {})
    duration_seconds = to_float(video_stream.get("duration")) or to_float(payload.get("format", {}).get("duration"))
    fps = parse_fractional_float(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate"))
    return {
        "duration_seconds": duration_seconds,
        "height": to_int(video_stream.get("height")),
        "width": to_int(video_stream.get("width")),
        "fps": round(fps, 3) if fps is not None else None,
        "codec_name": video_stream.get("codec_name"),
    }


def measure_scene_change_density(file_path: Path, duration_seconds: float | None) -> dict[str, Any]:
    analysis_window = min(duration_seconds or 30.0, 30.0)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "info",
        "-i",
        str(file_path),
        "-vf",
        "select='gt(scene,0.12)',showinfo",
        "-frames:v",
        "900",
        "-f",
        "null",
        "-",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    stderr = proc.stderr or ""
    scene_changes = len(re.findall(r"showinfo.*pts_time:", stderr))
    rate = scene_changes / max(analysis_window, 1.0)
    return {
        "scene_changes": scene_changes,
        "analysis_window_seconds": round(analysis_window, 3),
        "scene_change_rate": round(rate, 4),
        "ffmpeg_returncode": proc.returncode,
        "ffmpeg_error": (stderr[-500:] if proc.returncode != 0 else ""),
    }


def locate_downloaded_video_file(target_dir: Path, prefix: str, before_files: set[Path]) -> Path | None:
    after_files = {p.resolve() for p in target_dir.glob(f"{prefix}*") if p.is_file()}
    new_files = sorted(after_files - before_files, key=lambda item: item.stat().st_mtime)
    if new_files:
        return new_files[-1]
    existing = sorted(after_files, key=lambda item: item.stat().st_mtime)
    return existing[-1] if existing else None


def audit_downloaded_video(file_path: Path, source_url: str, candidate_audit: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    source_domain = urlparse(source_url or "").netloc.lower()
    source_traceable = bool(source_url and source_domain)
    probe = probe_video_file(file_path)
    duration_seconds = probe["duration_seconds"]
    scene_metrics = measure_scene_change_density(file_path, duration_seconds)
    height = probe["height"]

    duration_ok = duration_seconds is not None and duration_seconds >= float(policy["min_duration_seconds"])
    min_height = to_int(policy.get("min_height"))
    enforce_resolution = bool(min_height and min_height > 0)
    resolution_ok = True if not enforce_resolution else (height is not None and height >= min_height)
    scene_changes = scene_metrics.get("scene_changes", 0)
    scene_rate = scene_metrics.get("scene_change_rate", 0.0)
    frame_variation_ok = (
        scene_changes >= int(policy["min_scene_changes"])
        and scene_rate >= float(policy["min_scene_change_rate"])
    )
    anti_screenshot_montage_pass = duration_ok and frame_variation_ok and source_traceable

    fail_reasons: list[str] = []
    if not source_traceable:
        fail_reasons.append("missing_source_trace")
    if enforce_resolution and not resolution_ok:
        fail_reasons.append("resolution_below_min_height")
    if not duration_ok:
        fail_reasons.append("duration_too_short")
    if not frame_variation_ok:
        fail_reasons.append("low_frame_variation_possible_screenshot_montage")

    return {
        "file": str(file_path),
        "source_url": source_url,
        "source_domain": source_domain,
        "source_traceable": source_traceable,
        "source_category": candidate_audit.get("source_category"),
        "extractor": candidate_audit.get("extractor"),
        "resolution_height": height,
        "resolution_width": probe["width"],
        "fps": probe["fps"],
        "codec": probe["codec_name"],
        "duration_seconds": round(duration_seconds, 3) if duration_seconds is not None else None,
        "scene_changes": scene_changes,
        "scene_change_rate": scene_rate,
        "analysis_window_seconds": scene_metrics.get("analysis_window_seconds"),
        "duration_ok": duration_ok,
        "resolution_ok": resolution_ok,
        "frame_variation_ok": frame_variation_ok,
        "anti_screenshot_montage_pass": anti_screenshot_montage_pass,
        "final_pass": len(fail_reasons) == 0,
        "fail_reasons": fail_reasons,
        "ffmpeg_error": scene_metrics.get("ffmpeg_error") or "",
    }


def add_reason_counts(counter: dict[str, int], reasons: list[str]) -> None:
    for reason in reasons:
        counter[reason] = counter.get(reason, 0) + 1


def execute_video_search(topic: TopicContext, search_limit: int = 3, download_limit: int = 0) -> dict[str, Any]:
    queries_path = topic.topic_root / "videos" / "web_search" / "video_search_queries.json"
    queries = read_json(queries_path)
    policy = resolve_video_quality_policy(topic)
    skip_probe = str(os.environ.get("MATERIAL_SKIP_VIDEO_PROBE", "0")).strip().lower() in {"1", "true", "yes", "on"}
    config_dir = topic.topic_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    if skip_probe:
        candidates_out = [
            {
                "query": query,
                "probe_skipped": True,
                "candidates": [],
                "quality": {
                    "candidate_count": 0,
                    "qualified_count": 0,
                    "rejected_count": 0,
                    "reject_reason_counts": {},
                },
            }
            for query in queries
        ]
        write_json(config_dir / "youtube_candidates.json", candidates_out)
        audit_report_path = config_dir / "video_quality_audit_report.json"
        write_json(
            audit_report_path,
            {
                "topic": topic.slug,
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
                "policy": policy,
                "probe_skipped": True,
                "summary": {
                    "candidate_total": 0,
                    "candidate_qualified": 0,
                    "candidate_rejected": 0,
                    "download_attempts": 0,
                    "download_passed": 0,
                    "download_failed": 0,
                },
            },
        )
        return {
            "topic": topic.slug,
            "candidate_queries": len(queries),
            "downloads": 0,
            "qualified_candidates": 0,
            "candidate_reject_reason_counts": {},
            "download_quality_passed": 0,
            "download_quality_failed": 0,
            "download_fail_reason_counts": {},
            "quality_audit_report": str(audit_report_path),
            "probe_skipped": True,
        }

    candidates_out = []
    download_results = []
    metadata_cache: dict[str, dict[str, Any]] = {}
    download_timeout = max(30, env_int("MATERIAL_VIDEO_DOWNLOAD_TIMEOUT_SECONDS", DEFAULT_YTDLP_COMMAND_TIMEOUT))
    socket_timeout = max(5, env_int("MATERIAL_YTDLP_SOCKET_TIMEOUT", DEFAULT_YTDLP_SOCKET_TIMEOUT))
    candidate_reason_counts: dict[str, int] = {}
    download_reason_counts: dict[str, int] = {}
    query_quality_summary = []
    candidate_total = 0
    candidate_qualified = 0

    for idx, query in enumerate(queries, start=1):
        try:
            payload = yt_dlp_json(f"ytsearch{search_limit}:{query}")
        except Exception as exc:  # noqa: BLE001
            candidates_out.append({"query": query, "error": str(exc)})
            continue
        entries = []
        per_query_reasons: dict[str, int] = {}
        for entry in payload.get("entries", [])[:search_limit]:
            video_id = entry.get("id")
            url = f"https://www.youtube.com/watch?v={video_id}" if video_id else entry.get("url")
            candidate = {
                "title": entry.get("title"),
                "url": url,
                "duration": entry.get("duration"),
                "channel": entry.get("channel") or entry.get("uploader"),
            }
            metadata: dict[str, Any] = {}
            metadata_error = ""
            if url:
                if url in metadata_cache:
                    metadata = metadata_cache[url]
                else:
                    try:
                        metadata = yt_dlp_video_metadata(url)
                    except Exception as exc:  # noqa: BLE001
                        metadata_error = str(exc)
                    metadata_cache[url] = metadata

            quality_audit = evaluate_video_candidate(candidate, metadata, policy)
            if metadata_error:
                quality_audit["metadata_error"] = metadata_error[:300]
            candidate["quality_audit"] = quality_audit
            candidate["eligible_for_download"] = quality_audit["pre_download_pass"]
            entries.append(candidate)

            candidate_total += 1
            if candidate["eligible_for_download"]:
                candidate_qualified += 1
            add_reason_counts(candidate_reason_counts, quality_audit["reject_reasons"])
            add_reason_counts(per_query_reasons, quality_audit["reject_reasons"])

        qualified_entries = [item for item in entries if item.get("eligible_for_download")]
        query_quality_summary.append(
            {
                "query": query,
                "candidate_count": len(entries),
                "qualified_count": len(qualified_entries),
                "rejected_count": len(entries) - len(qualified_entries),
                "reject_reason_counts": per_query_reasons,
            }
        )
        candidates_out.append({"query": query, "candidates": entries, "quality": query_quality_summary[-1]})

        if qualified_entries and idx <= download_limit:
            first = qualified_entries[0]
            # 生成描述性文件名
            video_desc = safe_slug(query)[:30]
            outtmpl = str(topic.topic_root / f"视频_{video_desc}.%(ext)s")
            target_dir = topic.topic_root
            before_files = {p.resolve() for p in target_dir.glob(f"视频_{video_desc}.*") if p.is_file()}
            cmd = [
                "yt-dlp",
                "--socket-timeout",
                str(socket_timeout),
                "--retries",
                "1",
                "--fragment-retries",
                "1",
                "-f",
                "mp4/bestvideo*+bestaudio/best",
                "--merge-output-format",
                "mp4",
                "--output",
                outtmpl,
                "--no-playlist",
                first["url"],
            ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=download_timeout)
                timed_out = False
            except subprocess.TimeoutExpired as exc:
                proc = subprocess.CompletedProcess(
                    cmd,
                    returncode=124,
                    stdout=(exc.stdout or "")[-500:] if isinstance(exc.stdout, str) else "",
                    stderr=((exc.stderr or "")[-500:] if isinstance(exc.stderr, str) else "") or "yt-dlp download timed out",
                )
                timed_out = True
            file_path = locate_downloaded_video_file(target_dir, f"视频_{video_desc}", before_files) if proc.returncode == 0 else None
            if file_path and proc.returncode == 0:
                try:
                    file_audit = audit_downloaded_video(file_path, first["url"], first.get("quality_audit", {}), policy)
                except Exception as exc:  # noqa: BLE001
                    file_audit = {
                        "file": str(file_path),
                        "source_url": first["url"],
                        "final_pass": False,
                        "fail_reasons": ["downloaded_file_audit_error"],
                        "error": str(exc),
                    }
            else:
                file_audit = {
                    "file": str(file_path) if file_path else "",
                    "source_url": first["url"],
                    "final_pass": False,
                    "fail_reasons": ["download_timeout" if timed_out else "download_failed_or_missing_file"],
                }
            add_reason_counts(download_reason_counts, file_audit.get("fail_reasons", []))
            download_results.append({
                "query": query,
                "url": first["url"],
                "title": first.get("title"),
                "channel": first.get("channel"),
                "returncode": proc.returncode,
                "stderr": proc.stderr[-500:],
                "stdout": proc.stdout[-500:],
                "selected_candidate_quality": first.get("quality_audit", {}),
                "file_quality_audit": file_audit,
            })
        elif idx <= download_limit:
            download_results.append(
                {
                    "query": query,
                    "url": "",
                    "title": "",
                    "channel": "",
                    "returncode": -1,
                    "stderr": "",
                    "stdout": "",
                    "selected_candidate_quality": {},
                    "file_quality_audit": {
                        "final_pass": False,
                        "fail_reasons": ["no_qualified_candidate"],
                    },
                }
            )
            add_reason_counts(download_reason_counts, ["no_qualified_candidate"])

    # 保存 manifest 到 config 目录
    write_json(config_dir / "youtube_candidates.json", candidates_out)
    if download_results:
        write_json(config_dir / "youtube_download_results.json", download_results)

    download_passed = len(
        [
            item
            for item in download_results
            if item.get("returncode") == 0 and item.get("file_quality_audit", {}).get("final_pass")
        ]
    )
    download_failed = len(download_results) - download_passed
    audit_report = {
        "topic": topic.slug,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime()),
        "policy": policy,
        "audit_fields": {
            "candidate_level": [
                "source_category",
                "source_ok",
                "resolution_height",
                "duration_seconds_hint",
                "pre_download_pass",
                "reject_reasons",
            ],
            "file_level": [
                "source_traceable",
                "resolution_height",
                "duration_seconds",
                "scene_changes",
                "scene_change_rate",
                "anti_screenshot_montage_pass",
                "final_pass",
                "fail_reasons",
            ],
        },
        "query_quality_summary": query_quality_summary,
        "summary": {
            "candidate_total": candidate_total,
            "candidate_qualified": candidate_qualified,
            "candidate_rejected": candidate_total - candidate_qualified,
            "candidate_reject_reason_counts": candidate_reason_counts,
            "download_attempts": len(download_results),
            "download_passed": download_passed,
            "download_failed": download_failed,
            "download_fail_reason_counts": download_reason_counts,
        },
    }
    audit_report_path = config_dir / "video_quality_audit_report.json"
    write_json(audit_report_path, audit_report)
    return {
        "topic": topic.slug,
        "candidate_queries": len(candidates_out),
        "downloads": len(download_results),
        "qualified_candidates": candidate_qualified,
        "candidate_reject_reason_counts": candidate_reason_counts,
        "download_quality_passed": download_passed,
        "download_quality_failed": download_failed,
        "download_fail_reason_counts": download_reason_counts,
        "quality_audit_report": str(audit_report_path),
    }


def execute_ai_prep(topic: TopicContext) -> dict[str, Any]:
    visual_plan = read_json(topic.topic_root / "images" / "generated" / "ai_visual_plan.json")
    batch_tasks = []
    prompts_dir = topic.topic_root / "prompts" / "ai"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    def add_prompt_file(name: str, prompt: str, image_name: str) -> None:
        prompt_path = prompts_dir / f"{name}.md"
        write_text(prompt_path, prompt.strip() + "\n")
        batch_tasks.append(
            {
                "id": name,
                "promptFiles": [str(prompt_path)],
                "image": str(topic.topic_root / "images" / "generated" / image_name),
                "provider": "minimax",
                "model": "image-01",
                "ar": "16:9",
            }
        )

    add_prompt_file("cover", visual_plan["cover_prompt"], "cover.png")
    for idx, prompt in enumerate(visual_plan.get("infographic_prompts", []), start=1):
        add_prompt_file(f"infographic_{idx}", prompt, f"infographic_{idx}.png")
    for frame in visual_plan.get("comic_storyboard", []):
        add_prompt_file(frame["frame_id"], frame["visual_prompt"], f"{frame['frame_id']}.png")
    for idx, prompt in enumerate(visual_plan.get("meme_prompts", []), start=1):
        add_prompt_file(f"meme_{idx}", prompt, f"meme_{idx}.png")
    for idx, prompt in enumerate(visual_plan.get("funny_comic_character_prompts", []), start=1):
        add_prompt_file(f"funny_character_{idx}", prompt, f"funny_character_{idx}.png")

    batch = {"jobs": 2, "tasks": batch_tasks}
    batch_file = topic.topic_root / "images" / "generated" / "baoyu_batch.json"
    write_json(batch_file, batch)

    # Fallback text panels
    render_fallback_panels(topic, visual_plan)

    provider_status = detect_ai_provider_status()
    optional_status = provider_status["optional_fallbacks"]

    env_file_values = load_image_env()[0]
    stop_after_first_success = str(os.environ.get("MATERIAL_AI_STOP_AFTER_FIRST_SUCCESS", "1")).strip().lower() not in {"0", "false", "no", "off"}
    provider_chain: list[tuple[str, Any]] = [
        (
            "viviai_chat_image",
            lambda: execute_chat_completion_image_generation(
                topic,
                batch_tasks,
                provider_name="viviai_chat_image",
                base_url=optional_status["viviai_chat_image"]["base_url"],
                api_key=(os.environ.get("VIVIAI_IMAGE_API_KEY") or env_file_values.get("VIVIAI_IMAGE_API_KEY", "")).strip(),
                model=optional_status["viviai_chat_image"]["model"],
            ),
        ),
        (
            "vectorengine_chat_image",
            lambda: execute_chat_completion_image_generation(
                topic,
                batch_tasks,
                provider_name="vectorengine_chat_image",
                base_url=optional_status["vectorengine_chat_image"]["base_url"],
                api_key=(
                    os.environ.get("VECTORENGINE_CHAT_IMAGE_API_KEY")
                    or env_file_values.get("VECTORENGINE_CHAT_IMAGE_API_KEY", "")
                    or os.environ.get("VECTORENGINE_API_KEY")
                    or env_file_values.get("VECTORENGINE_API_KEY", "")
                ).strip(),
                model=optional_status["vectorengine_chat_image"]["model"],
            ),
        ),
        (
            "qhaigc_seedream5",
            lambda: execute_openai_compatible_images_generation(
                topic,
                batch_tasks,
                provider_name="qhaigc_seedream5",
                base_url=optional_status["qhaigc_images"]["base_url"],
                api_key=(os.environ.get("QHAIGC_API_KEY") or env_file_values.get("QHAIGC_API_KEY", "")).strip(),
                model=optional_status["qhaigc_images"]["primary_model"],
                response_mode="url",
            ),
        ),
        (
            "qhaigc_seedream46",
            lambda: execute_openai_compatible_images_generation(
                topic,
                batch_tasks,
                provider_name="qhaigc_seedream46",
                base_url=optional_status["qhaigc_images"]["base_url"],
                api_key=(os.environ.get("QHAIGC_API_KEY") or env_file_values.get("QHAIGC_API_KEY", "")).strip(),
                model=optional_status["qhaigc_images"]["fallback_model"],
                response_mode="url",
            ),
        ),
        (
            "gitee_qwen_image",
            lambda: execute_openai_compatible_images_generation(
                topic,
                batch_tasks,
                provider_name="gitee_qwen_image",
                base_url=optional_status["gitee_images"]["base_url"],
                api_key=(os.environ.get("GITEE_AI_API_KEY") or env_file_values.get("GITEE_AI_API_KEY", "")).strip(),
                model=optional_status["gitee_images"]["qwen_model"],
                response_mode="b64_json",
            ),
        ),
        (
            "gitee_glm_image",
            lambda: execute_openai_compatible_images_generation(
                topic,
                batch_tasks,
                provider_name="gitee_glm_image",
                base_url=optional_status["gitee_images"]["base_url"],
                api_key=(os.environ.get("GITEE_AI_API_KEY") or env_file_values.get("GITEE_AI_API_KEY", "")).strip(),
                model=optional_status["gitee_images"]["glm_model"],
                response_mode="b64_json",
            ),
        ),
        (
            "vectorengine_seedream",
            lambda: execute_openai_compatible_images_generation(
                topic,
                batch_tasks,
                provider_name="vectorengine_seedream",
                base_url=optional_status["vectorengine_images"]["base_url"],
                api_key=(
                    os.environ.get("VECTORENGINE_IMAGES_API_KEY")
                    or os.environ.get("DOUBAO_IMAGE_API_KEY")
                    or os.environ.get("VECTORENGINE_API_KEY")
                    or env_file_values.get("VECTORENGINE_IMAGES_API_KEY", "")
                    or env_file_values.get("DOUBAO_IMAGE_API_KEY", "")
                    or env_file_values.get("VECTORENGINE_API_KEY", "")
                ).strip(),
                model=optional_status["vectorengine_images"]["model"],
                response_mode="url",
            ),
        ),
        ("minimax", lambda: execute_minimax_batch_generation(topic, batch_file, batch_tasks)),
        ("gemini", lambda: execute_gemini_image_generation(topic, batch_tasks)),
    ]

    live_generation: dict[str, Any] = {}
    selected_provider: str | None = None
    for provider_name, runner in provider_chain:
        if selected_provider and stop_after_first_success:
            live_generation[provider_name] = {
                "enabled": False,
                "skipped": True,
                "reason": f"skipped_after_success:{selected_provider}",
            }
            continue
        result = runner()
        live_generation[provider_name] = result
        if result.get("enabled") and int(result.get("succeeded", 0) or 0) > 0 and not selected_provider:
            selected_provider = provider_name

    manifest = {
        "provider_status": provider_status,
        "batch_file": str(batch_file),
        "task_count": len(batch_tasks),
        "live_generation": live_generation,
        "selected_provider": selected_provider,
        "stop_after_first_success": stop_after_first_success,
        "note": "已生成批处理与 fallback 图；默认按 ViviAI Chat → VectorEngine Chat → QHAIGC → Gitee → VectorEngine Seedream → MiniMax → Gemini 的优先链路执行，命中首个成功提供方后停止后续实生成。"
    }
    write_json(topic.topic_root / "images" / "generated" / "ai_generation_manifest.json", manifest)
    return manifest


def detect_ai_provider_status() -> dict[str, Any]:
    status_file = ROOT / "产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/image_generation_status.json"
    status = read_json(status_file) if status_file.exists() else {}
    provider_snapshot = resolve_material_image_provider_snapshot()
    gemini_cfg = provider_snapshot["gemini_generate_content"]
    optional_status = provider_snapshot["optional_fallbacks"]
    return {
        "vectorengine": status,
        "gemini_generate_content": {
            "provider": gemini_cfg["provider"],
            "base_url": gemini_cfg["base_url"],
            "model": gemini_cfg["model"],
            "api_key_present": bool(gemini_cfg["api_key"]),
            "env_file": gemini_cfg["env_file"],
        },
        "optional_fallbacks": optional_status,
        "minimax_env": bool(os.environ.get("MINIMAX_API_KEY")),
        "priority_order": provider_snapshot["priority_order"],
    }


def execute_gemini_image_generation(topic: TopicContext, batch_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    provider = resolve_gemini_image_provider()
    generated_dir = topic.topic_root / "images" / "generated" / "gemini"
    generated_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    max_tasks = int(os.environ.get("MATERIAL_GEMINI_GENERATE_LIMIT", os.environ.get("MATERIAL_AI_GENERATE_LIMIT", "6")) or "6")
    if max_tasks < 0:
        max_tasks = 0
    if not provider["api_key"]:
        return {
            "enabled": False,
            "reason": "missing_api_key",
            "output_dir": str(generated_dir),
            "attempted": 0,
            "succeeded": 0,
            "results_file": str(generated_dir / "generation_results.json"),
        }
    selected_tasks = batch_tasks[:max_tasks]
    for task in selected_tasks:
        prompt_files = task.get("promptFiles") or []
        if not prompt_files:
            continue
        prompt = "\n\n".join(Path(path).read_text(encoding="utf-8").strip() for path in prompt_files if Path(path).exists()).strip()
        output_stem = generated_dir / task["id"]
        result = generate_image_with_gemini(
            prompt=prompt,
            output_stem=output_stem,
            provider=provider,
            max_retries=3,
        )
        result["task_id"] = task["id"]
        result["prompt_files"] = prompt_files
        results.append(result)

    results_file = generated_dir / "generation_results.json"
    write_json(results_file, results)
    succeeded = len([item for item in results if item.get("ok")])
    return {
        "enabled": True,
        "provider": provider["provider"],
        "model": provider["model"],
        "output_dir": str(generated_dir),
        "attempted": len(results),
        "succeeded": succeeded,
        "results_file": str(results_file),
    }


def execute_minimax_batch_generation(topic: TopicContext, batch_file: Path, batch_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    skill_main = Path(os.environ.get("BAOYU_IMAGINE_SCRIPT", "~/.codex/skills/baoyu-imagine/scripts/main.ts")).expanduser()
    bun_bin = Path(os.environ.get("BUN_BINARY", "~/.bun/bin/bun")).expanduser()
    output_dir = topic.topic_root / "images" / "generated" / "minimax"
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "batch_results.json"
    manifest_file = output_dir / "generation_manifest.json"

    api_key = normalize_repeated_secret(os.environ.get("MINIMAX_API_KEY", ""))
    if not api_key:
        manifest = {
            "enabled": False,
            "reason": "missing_api_key",
            "output_dir": str(output_dir),
            "results_file": str(results_file),
        }
        write_json(manifest_file, manifest)
        return manifest
    if not skill_main.exists() or not bun_bin.exists():
        manifest = {
            "enabled": False,
            "reason": "missing_baoyu_imagine_runtime",
            "output_dir": str(output_dir),
            "results_file": str(results_file),
        }
        write_json(manifest_file, manifest)
        return manifest

    max_tasks = int(os.environ.get("MATERIAL_MINIMAX_GENERATE_LIMIT", os.environ.get("MATERIAL_AI_GENERATE_LIMIT", "6")) or "6")
    if max_tasks < 0:
        max_tasks = 0
    selected_tasks = batch_tasks[:max_tasks]
    selected_tasks = [task for task in selected_tasks if not Path(task["image"]).exists()]
    tmp_prompt_dir = output_dir / "_sanitized_prompts"
    tmp_prompt_dir.mkdir(parents=True, exist_ok=True)

    rewritten_tasks = []
    for task in selected_tasks:
        prompt_files = task.get("promptFiles") or []
        sanitized_files = []
        for idx, prompt_file in enumerate(prompt_files, start=1):
            source_path = Path(prompt_file)
            prompt_text = source_path.read_text(encoding="utf-8").strip() if source_path.exists() else ""
            sanitized_text = sanitize_minimax_prompt(topic, prompt_text, str(task.get("id", "")))
            sanitized_path = tmp_prompt_dir / f"{task.get('id', 'task')}_{idx}.md"
            write_text(sanitized_path, sanitized_text + "\n")
            sanitized_files.append(str(sanitized_path))
        rewritten = dict(task)
        rewritten["promptFiles"] = sanitized_files
        rewritten_tasks.append(rewritten)

    limited_batch = {
        "jobs": 1,
        "tasks": rewritten_tasks,
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(limited_batch, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
        tmp_batch_path = Path(tmp.name)

    env = os.environ.copy()
    env["MINIMAX_API_KEY"] = api_key
    env.setdefault("MINIMAX_IMAGE_MODEL", "image-01")
    env.setdefault("MINIMAX_BASE_URL", "https://api.minimaxi.com")
    env.setdefault("BAOYU_IMAGE_GEN_MAX_WORKERS", "1")
    env.setdefault("BAOYU_IMAGE_GEN_MINIMAX_CONCURRENCY", "1")
    env.setdefault("BAOYU_IMAGE_GEN_MINIMAX_START_INTERVAL_MS", "2500")

    cmd = [
        str(bun_bin),
        str(skill_main),
        "--batchfile",
        str(tmp_batch_path),
        "--jobs",
        "1",
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(topic.topic_root))

    parsed_stdout: Any
    stdout_text = (proc.stdout or "").strip()
    try:
        parsed_stdout = json.loads(stdout_text) if stdout_text else None
    except Exception:  # noqa: BLE001
        parsed_stdout = stdout_text

    manifest = {
        "enabled": True,
        "provider": "minimax",
        "model": env["MINIMAX_IMAGE_MODEL"],
        "base_url": env["MINIMAX_BASE_URL"],
        "attempted": len(selected_tasks),
        "returncode": proc.returncode,
        "output_dir": str(output_dir),
        "tmp_batch_file": str(tmp_batch_path),
        "stdout": parsed_stdout,
        "stderr_tail": (proc.stderr or "")[-4000:],
        "results_file": str(results_file),
    }

    generated_files = []
    for task in rewritten_tasks:
        image_path = Path(task["image"])
        if image_path.exists():
            generated_files.append(str(image_path))
    manifest["generated_files"] = generated_files
    manifest["succeeded"] = len(generated_files)

    write_json(results_file, {
        "stdout": parsed_stdout,
        "stderr": proc.stderr,
        "generated_files": generated_files,
    })
    write_json(manifest_file, manifest)
    return manifest


def execute_openai_compatible_images_generation(
    topic: TopicContext,
    batch_tasks: list[dict[str, Any]],
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
    response_mode: str,
) -> dict[str, Any]:
    output_dir = topic.topic_root / "images" / "generated" / provider_name
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "generation_results.json"

    if not api_key:
        result = {
            "enabled": False,
            "reason": "missing_api_key",
            "provider": provider_name,
            "model": model,
            "output_dir": str(output_dir),
            "results_file": str(results_file),
        }
        write_json(results_file, [])
        return result

    max_tasks = int(os.environ.get("MATERIAL_HTTP_IMAGE_LIMIT", os.environ.get("MATERIAL_AI_GENERATE_LIMIT", "4")) or "4")
    if max_tasks < 0:
        max_tasks = 0

    results: list[dict[str, Any]] = []
    selected_tasks = batch_tasks[:max_tasks]
    for task in selected_tasks:
        prompt_files = task.get("promptFiles") or []
        prompt = "\n\n".join(Path(path).read_text(encoding="utf-8").strip() for path in prompt_files if Path(path).exists()).strip()
        output_stem = output_dir / str(task["id"])
        result = generate_image_openai_compatible(
            prompt=prompt,
            output_stem=output_stem,
            base_url=base_url,
            api_key=api_key,
            model=model,
            response_mode=response_mode,
        )
        result["task_id"] = task["id"]
        result["prompt_files"] = prompt_files
        results.append(result)

    write_json(results_file, results)
    succeeded = len([item for item in results if item.get("ok")])
    return {
        "enabled": True,
        "provider": provider_name,
        "model": model,
        "base_url": base_url,
        "attempted": len(results),
        "succeeded": succeeded,
        "results_file": str(results_file),
        "output_dir": str(output_dir),
    }


def generate_image_openai_compatible(
    *,
    prompt: str,
    output_stem: Path,
    base_url: str,
    api_key: str,
    model: str,
    response_mode: str,
) -> dict[str, Any]:
    url = f"{normalize_openai_images_base_url(base_url)}/v1/images/generations"
    payload = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": "1024x1024",
    }
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180,
        )
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw_text": response.text[:2000]}
        raw_file = output_stem.with_suffix(".response.json")
        write_json(raw_file, body)
        if not response.ok:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": body,
                "response_file": str(raw_file),
            }

        item = ((body.get("data") or [None])[0]) or {}
        if response_mode == "b64_json" and item.get("b64_json"):
            image_path = output_stem.with_suffix(".png")
            image_path.write_bytes(base64.b64decode(item["b64_json"]))
            return {"ok": True, "image_file": str(image_path), "response_file": str(raw_file)}
        if response_mode == "url" and item.get("url"):
            image_path = download_file(item["url"], output_stem.with_suffix(".png"))
            return {"ok": True, "image_file": str(image_path), "source_url": item["url"], "response_file": str(raw_file)}
        return {
            "ok": False,
            "error": "unsupported_response_shape",
            "response_file": str(raw_file),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": repr(exc),
        }


def extract_image_from_chat_completion_text(content: str, output_stem: Path) -> dict[str, Any]:
    cleaned = (content or "").strip()
    data_match = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=\n\r]+)", cleaned)
    if data_match:
        image_path = output_stem.with_suffix(".png")
        image_path.write_bytes(base64.b64decode(data_match.group(1)))
        return {"ok": True, "image_file": str(image_path)}

    markdown_match = re.search(r"!\[[^\]]*\]\((https?://[^)]+)\)", cleaned)
    if markdown_match:
        image_path = download_file(markdown_match.group(1), output_stem.with_suffix(".png"))
        return {"ok": True, "image_file": str(image_path), "source_url": markdown_match.group(1)}

    url_match = re.search(r"(https?://\S+\.(?:png|jpg|jpeg|webp))", cleaned)
    if url_match:
        image_path = download_file(url_match.group(1), output_stem.with_suffix(".png"))
        return {"ok": True, "image_file": str(image_path), "source_url": url_match.group(1)}

    return {"ok": False, "error": "chat_completion_missing_image_payload"}


def generate_image_chat_completions_compatible(
    *,
    prompt: str,
    output_stem: Path,
    base_url: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    url = normalize_chat_base_url(base_url)
    payload = {
        "model": model,
        "temperature": 0.4,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    }
    try:
        session = requests.Session()
        session.trust_env = False
        response = session.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=180,
        )
        body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw_text": response.text[:4000]}
        raw_file = output_stem.with_suffix(".response.json")
        write_json(raw_file, body)
        if not response.ok:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": body,
                "response_file": str(raw_file),
            }
        content = extract_chat_content(body)
        extracted = extract_image_from_chat_completion_text(content, output_stem)
        extracted["response_file"] = str(raw_file)
        return extracted
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": repr(exc),
        }


def execute_chat_completion_image_generation(
    topic: TopicContext,
    batch_tasks: list[dict[str, Any]],
    *,
    provider_name: str,
    base_url: str,
    api_key: str,
    model: str,
) -> dict[str, Any]:
    output_dir = topic.topic_root / "images" / "generated" / provider_name
    output_dir.mkdir(parents=True, exist_ok=True)
    results_file = output_dir / "generation_results.json"
    if not api_key:
        result = {
            "enabled": False,
            "reason": "missing_api_key",
            "provider": provider_name,
            "model": model,
            "output_dir": str(output_dir),
            "results_file": str(results_file),
        }
        write_json(results_file, [])
        return result

    max_tasks = int(os.environ.get("MATERIAL_HTTP_IMAGE_LIMIT", os.environ.get("MATERIAL_AI_GENERATE_LIMIT", "4")) or "4")
    if max_tasks < 0:
        max_tasks = 0

    results: list[dict[str, Any]] = []
    selected_tasks = batch_tasks[:max_tasks]
    for task in selected_tasks:
        prompt_files = task.get("promptFiles") or []
        prompt = "\n\n".join(Path(path).read_text(encoding="utf-8").strip() for path in prompt_files if Path(path).exists()).strip()
        output_stem = output_dir / str(task["id"])
        result = generate_image_chat_completions_compatible(
            prompt=prompt,
            output_stem=output_stem,
            base_url=base_url,
            api_key=api_key,
            model=model,
        )
        result["task_id"] = task["id"]
        result["prompt_files"] = prompt_files
        results.append(result)

    write_json(results_file, results)
    succeeded = len([item for item in results if item.get("ok")])
    return {
        "enabled": True,
        "provider": provider_name,
        "model": model,
        "base_url": base_url,
        "attempted": len(results),
        "succeeded": succeeded,
        "results_file": str(results_file),
        "output_dir": str(output_dir),
    }


def generate_image_with_gemini(
    *,
    prompt: str,
    output_stem: Path,
    provider: dict[str, str],
    max_retries: int,
) -> dict[str, Any]:
    url = f"{provider['base_url']}/v1beta/models/{provider['model']}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }
    last_error: dict[str, Any] | None = None
    for attempt in range(1, max_retries + 1):
        try:
            session = requests.Session()
            session.trust_env = False
            response = session.post(
                url,
                headers={
                    "x-api-key": provider["api_key"],
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=180,
            )
            body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw_text": response.text[:2000]}
            if response.ok:
                image_path, text_parts = extract_image_from_gemini_response(body, output_stem)
                raw_file = output_stem.with_suffix(".response.json")
                write_json(raw_file, body)
                if image_path:
                    return {
                        "ok": True,
                        "attempt": attempt,
                        "image_file": str(image_path),
                        "response_file": str(raw_file),
                        "text_parts": text_parts[:3],
                    }
                last_error = {
                    "ok": False,
                    "attempt": attempt,
                    "status_code": response.status_code,
                    "error": "no_inline_image_data",
                    "response_file": str(raw_file),
                }
            else:
                last_error = {
                    "ok": False,
                    "attempt": attempt,
                    "status_code": response.status_code,
                    "error": body,
                }
        except Exception as exc:  # noqa: BLE001
            last_error = {
                "ok": False,
                "attempt": attempt,
                "error": repr(exc),
            }
        if attempt < max_retries:
            time.sleep(2 * attempt)
    return last_error or {"ok": False, "error": "unknown_error"}


def extract_image_from_gemini_response(payload: dict[str, Any], output_stem: Path) -> tuple[Path | None, list[str]]:
    text_parts: list[str] = []
    for candidate in payload.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            if isinstance(part, dict) and part.get("text"):
                text_parts.append(part["text"])
            inline = None
            if isinstance(part, dict):
                inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                ext = guess_ext_from_mime(inline.get("mimeType", "image/png"))
                image_path = output_stem.with_suffix(ext)
                image_path.write_bytes(base64.b64decode(inline["data"]))
                return image_path, text_parts
    return None, text_parts


def render_fallback_panels(topic: TopicContext, visual_plan: dict[str, Any]) -> None:
    import matplotlib.pyplot as plt

    plt.rcParams["font.sans-serif"] = ["Arial Unicode MS", "PingFang SC", "Heiti TC", "STHeiti", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    target_dir = topic.topic_root / "images" / "generated" / "fallback"
    target_dir.mkdir(parents=True, exist_ok=True)
    items = [("cover", visual_plan["cover_prompt"])]
    items.extend((f"infographic_{i}", p) for i, p in enumerate(visual_plan.get("infographic_prompts", []), start=1))
    for frame in visual_plan.get("comic_storyboard", []):
        items.append((frame["frame_id"], frame["caption_hint"]))
    for idx, p in enumerate(visual_plan.get("meme_prompts", []), start=1):
        items.append((f"meme_{idx}", p))
    for idx, p in enumerate(visual_plan.get("funny_comic_character_prompts", []), start=1):
        items.append((f"funny_character_{idx}", p))
    for name, text in items[:8]:
        fig = plt.figure(figsize=(12, 6), facecolor="white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")
        fig.text(0.06, 0.85, name, fontsize=22, fontweight="bold")
        fig.text(0.06, 0.22, "\n".join(textwrap.wrap(text, 34)), fontsize=18)
        fig.savefig(target_dir / f"{name}.png", dpi=170)
        plt.close(fig)


def execute_topic(topic: TopicContext, steps: set[str], video_download_limit: int) -> dict[str, Any]:
    summary: dict[str, Any] = {"topic": topic.slug, "title": topic.title}
    if "charts" in steps:
        summary["charts"] = execute_charts(topic)
    if "image_search" in steps:
        summary["image_search"] = execute_image_search(topic)
    if "video_search" in steps:
        summary["video_search"] = execute_video_search(topic, download_limit=video_download_limit)
    if "ai_prep" in steps:
        summary["ai_prep"] = execute_ai_prep(topic)
    return summary


def choose_layer5_template_strategy(topic: TopicContext) -> dict[str, Any]:
    title = topic.title
    topic_type = topic.topic_type

    if topic_type == "finance_macro":
        return {
            "template_id": "market_story",
            "template_name": "市场叙事面板 (Market Story Panel)",
            "selection_reason": [
                "主题属于宏观/资产定价链路",
                "需要时间序列 + 风险情景并排展示",
                "适配 worldmonitor 的 MarketPanel 与 EconomicPanel",
            ],
            "required_fields": [
                "chart_csvs",
                "chart_pngs",
                "key_metrics",
                "risk_scenarios",
                "scene_plan",
            ],
        }
    if topic_type == "geopolitics":
        return {
            "template_id": "geo_timeline_map",
            "template_name": "地缘时政时间线地图 (Geo Timeline Map)",
            "selection_reason": [
                "主题包含地缘冲突/政策演进",
                "需要事件时间线与地图风险层联动",
                "适配 DeckGLMap 与 StrategicRiskPanel",
            ],
            "required_fields": [
                "event_timeline_json",
                "map_layers_json",
                "chart_csvs",
                "chart_pngs",
                "scene_plan",
            ],
        }

    if "OpenClaw" in title or "龙虾" in title:
        return {
            "template_id": "story_page",
            "template_name": "通用故事面板 (Story Page)",
            "selection_reason": [
                "工具教程类更适合步骤化卡片+流程图",
                "强调流程节点与故障排查树",
                "优先保证清晰阅读而非地图联动",
            ],
            "required_fields": [
                "chart_csvs",
                "chart_pngs",
                "logic_relations_json",
                "scene_plan",
            ],
        }

    return {
        "template_id": "story_page",
        "template_name": "通用故事面板 (Story Page)",
        "selection_reason": [
            "默认模板，适配大多数评论型主题",
            "以图表画廊 + 媒体卡片为主",
        ],
        "required_fields": [
            "chart_csvs",
            "chart_pngs",
            "logic_relations_json",
            "scene_plan",
        ],
    }


def ensure_logic_relations_file(topic: TopicContext) -> Path:
    layer5_dir = topic.topic_root / "layer5"
    layer5_dir.mkdir(parents=True, exist_ok=True)
    target = layer5_dir / "logic_relations.json"
    if target.exists():
        return target

    chart_manifest = read_json(topic.topic_root / "charts" / "chart_generation_manifest.json") if (topic.topic_root / "charts" / "chart_generation_manifest.json").exists() else {"generated": []}
    scene_plan = read_json(topic.topic_root / "videos" / "scene_plan.json") if (topic.topic_root / "videos" / "scene_plan.json").exists() else []
    layer5_plan = read_json(layer5_dir / "layer5_delivery_plan.json") if (layer5_dir / "layer5_delivery_plan.json").exists() else {}

    logic = {
        "topic": topic.slug,
        "topic_type": topic.topic_type,
        "template_id": layer5_plan.get("template_id", ""),
        "logic_edges": [
            {
                "from": "thesis",
                "to": "chart_evidence",
                "relation": "supports",
                "notes": "主判断由图表锚点补证据",
            },
            {
                "from": "chart_evidence",
                "to": "risk_scenarios",
                "relation": "projects",
                "notes": "图表变量映射到风险情景",
            },
            {
                "from": "risk_scenarios",
                "to": "scene_plan",
                "relation": "visualizes",
                "notes": "情景映射到互动叙事分镜",
            },
        ],
        "chart_anchors": [item.get("anchor_id") for item in chart_manifest.get("generated", [])],
        "scene_ids": [item.get("title") for item in scene_plan if isinstance(item, dict)],
    }
    write_json(target, logic)
    return target


def build_layer5_topic_input(topic: TopicContext) -> dict[str, Any]:
    charts_csv = sorted(str(path) for path in (topic.topic_root / "charts" / "csv").glob("*.csv"))
    charts_png = sorted(str(path) for path in (topic.topic_root / "charts" / "png").glob("*.png"))

    layer5_dir = topic.topic_root / "layer5"
    layer5_plan_file = layer5_dir / "layer5_delivery_plan.json"
    layer5_inputs_file = layer5_dir / "layer5_delivery_inputs.json"
    layer5_topic_inputs_file = layer5_dir / "layer5_inputs.json"
    scene_plan_file = topic.topic_root / "videos" / "scene_plan.json"
    logic_relations_file = ensure_logic_relations_file(topic)

    layer5_plan = read_json(layer5_plan_file) if layer5_plan_file.exists() else {}
    layer5_inputs = read_json(layer5_inputs_file) if layer5_inputs_file.exists() else {}
    strategy = choose_layer5_template_strategy(topic)

    payload = {
        "thread_id": "019d31c5-bb7f-7a40-a087-9d219e9bd6ab",
        "topic": {
            "slug": topic.slug,
            "title": topic.title,
            "topic_type": topic.topic_type,
            "topic_root": str(topic.topic_root),
        },
        "template": {
            "selected_id": layer5_plan.get("template_id") or strategy["template_id"],
            "selected_name": layer5_plan.get("template_name") or strategy["template_name"],
            "selection_reason": strategy["selection_reason"],
            "required_fields": strategy["required_fields"],
            "available_fields": sorted(
                set(list(layer5_plan.keys()) + list(layer5_inputs.keys()))
            ),
        },
        "assets": {
            "chart_csvs": charts_csv,
            "chart_pngs": charts_png,
            "logic_relations_json": str(logic_relations_file),
            "scene_plan_json": str(scene_plan_file) if scene_plan_file.exists() else "",
            "layer5_delivery_plan_json": str(layer5_plan_file) if layer5_plan_file.exists() else "",
            "layer5_delivery_inputs_json": str(layer5_inputs_file) if layer5_inputs_file.exists() else "",
            "layer5_inputs_json": str(layer5_topic_inputs_file),
        },
        "worldmonitor": {
            "project": layer5_plan.get("worldmonitor_project", str(WORLDMONITOR_ROOT)),
            "data_dir": layer5_plan.get("worldmonitor_data_dir", str(WORLDMONITOR_ROOT / "data")),
            "public_dir": layer5_plan.get("worldmonitor_public_dir", str(WORLDMONITOR_ROOT / "public")),
            "entry": layer5_plan.get("worldmonitor_entry", "index.html"),
            "proxy_port": layer5_plan.get("proxy_port", 8787),
        },
        "key_metrics_to_emit": layer5_plan.get("key_metrics_to_emit", []),
        "risk_scenarios": layer5_plan.get("risk_scenarios", []),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_json(layer5_topic_inputs_file, payload)
    return payload


def emit_layer5_inputs_manifest(pack_root: Path, topics: list[TopicContext], execution_manifest: Path) -> tuple[Path, Path]:
    topic_inputs = [build_layer5_topic_input(topic) for topic in topics]
    output_file = pack_root / "layer5_inputs.json"
    write_json(
        output_file,
        {
            "thread_id": "019d31c5-bb7f-7a40-a087-9d219e9bd6ab",
            "pack_root": str(pack_root),
            "execution_manifest": str(execution_manifest),
            "topic_count": len(topic_inputs),
            "topics": topic_inputs,
        },
    )

    report_file = pack_root / "layer5_delivery_report.md"
    report_lines = [
        "# Layer5 交付报告",
        "",
        f"- 产物根目录：`{pack_root}`",
        f"- 线程项目：`codex://threads/019d31c5-bb7f-7a40-a087-9d219e9bd6ab`",
        f"- 主题数量：{len(topic_inputs)}",
        f"- 清单文件：`{output_file}`",
        "",
        "## 模板选择策略",
        "",
        "- `market_story`：宏观金融叙事，强调时序变量 + 风险情景矩阵。",
        "- `geo_timeline_map`：地缘主题，强调事件时间线 + 地图外溢路径。",
        "- `story_page`：通用评论/教程，强调结构化图表与逻辑卡片。",
        "",
        "## 各主题交付",
        "",
    ]
    for item in topic_inputs:
        template = item["template"]["selected_id"]
        layer5_inputs_path = item["assets"].get("layer5_delivery_inputs_json") or item["assets"].get("layer5_inputs_json") or "未生成"
        report_lines.extend(
            [
                f"### {item['topic']['title']} (`{item['topic']['slug']}`)",
                f"- 模板：`{template}`",
                f"- CSV 数量：{len(item['assets']['chart_csvs'])}",
                f"- PNG 数量：{len(item['assets']['chart_pngs'])}",
                f"- 逻辑关系：`{item['assets']['logic_relations_json']}`",
                f"- Layer5 输入：`{layer5_inputs_path}`",
                "",
            ]
        )
    write_text(report_file, "\n".join(report_lines).rstrip() + "\n")
    return output_file, report_file


def emit_chart_quality_gate_report(pack_root: Path, execution_summary: dict[str, Any]) -> dict[str, str] | None:
    topics = execution_summary.get("topics", [])
    chart_topics = [item for item in topics if isinstance(item, dict) and isinstance(item.get("charts"), dict)]
    if not chart_topics:
        return None

    first_thresholds: dict[str, Any] = {}
    for item in chart_topics:
        thresholds = (item.get("charts") or {}).get("summary", {}).get("gate_thresholds")
        if isinstance(thresholds, dict) and thresholds:
            first_thresholds = thresholds
            break

    total_chart_count = 0
    total_table_count = 0
    topic_payload: list[dict[str, Any]] = []
    lines = [
        "# 图表质量门控报告",
        "",
        f"- 产物根目录：`{pack_root}`",
        f"- 统计题目数：{len(chart_topics)}",
        "",
        "## 门控阈值",
        "",
    ]
    if first_thresholds:
        for key in ["cv_min", "slope_abs_min", "r2_min", "trend_strength_min", "group_diff_min", "heatmap_var_min"]:
            if key in first_thresholds:
                lines.append(f"- `{key}`: {first_thresholds[key]}")
    else:
        lines.append("- 未读取到阈值（可能本轮未执行 charts）。")

    lines.extend(["", "## 各题统计", ""])
    for item in chart_topics:
        topic_slug = item.get("topic", "")
        topic_title = item.get("title", "")
        charts_block = item.get("charts") or {}
        summary = charts_block.get("summary") or {}
        generated = charts_block.get("generated") or []
        chart_count = int(summary.get("chart_count", 0) or 0)
        table_count = int(summary.get("table_count", 0) or 0)
        total_chart_count += chart_count
        total_table_count += table_count
        lines.extend(
            [
                f"### {topic_title} (`{topic_slug}`)",
                f"- 图表数：{chart_count}",
                f"- 表格回退数：{table_count}",
            ]
        )
        table_items = [entry for entry in generated if entry.get("render_type") == "table"]
        if table_items:
            lines.append("- 回退表格路径：")
            for entry in table_items:
                lines.append(f"  - `{entry.get('anchor_id', '')}` CSV: `{entry.get('csv', '')}`")
                if entry.get("md"):
                    lines.append(f"  - `{entry.get('anchor_id', '')}` Markdown: `{entry.get('md', '')}`")
        lines.append("")
        topic_payload.append(
            {
                "topic_slug": topic_slug,
                "topic_title": topic_title,
                "chart_count": chart_count,
                "table_count": table_count,
                "table_fallback_items": [
                    {
                        "anchor_id": entry.get("anchor_id"),
                        "csv": entry.get("csv"),
                        "md": entry.get("md"),
                    }
                    for entry in table_items
                ],
            }
        )

    lines.extend(
        [
            "## 汇总",
            "",
            f"- 总图表数：{total_chart_count}",
            f"- 总表格回退数：{total_table_count}",
            "",
        ]
    )
    report_file_md = pack_root / "chart_quality_gate_report.md"
    write_text(report_file_md, "\n".join(lines).rstrip() + "\n")

    report_file_json = pack_root / "chart_quality_gate_report.json"
    write_json(
        report_file_json,
        {
            "pack_root": str(pack_root),
            "topic_count": len(chart_topics),
            "gate_thresholds": first_thresholds,
            "totals": {
                "chart_count": total_chart_count,
                "table_count": total_table_count,
            },
            "topics": topic_payload,
        },
    )
    return {"md": str(report_file_md), "json": str(report_file_json)}


def emit_cross_batch_chart_gate_overview(collection_root: Path) -> dict[str, str] | None:
    report_files = sorted(collection_root.glob("*/pack_assets/chart_quality_gate_report.json"))
    if not report_files:
        return None

    batch_rows: list[dict[str, Any]] = []
    total_chart_count = 0
    total_table_count = 0
    topic_acc: dict[str, dict[str, Any]] = {}

    for report_path in report_files:
        try:
            payload = read_json(report_path)
        except Exception:  # noqa: BLE001
            continue
        batch_id = report_path.parts[-3] if len(report_path.parts) >= 3 else ""
        totals = payload.get("totals", {}) or {}
        chart_count = int(totals.get("chart_count", 0) or 0)
        table_count = int(totals.get("table_count", 0) or 0)
        topic_count = int(payload.get("topic_count", 0) or 0)
        total_chart_count += chart_count
        total_table_count += table_count
        batch_rows.append(
            {
                "batch_id": batch_id,
                "pack_root": str(payload.get("pack_root", "")),
                "chart_count": chart_count,
                "table_count": table_count,
                "topic_count": topic_count,
                "chart_quality_gate_report_json": str(report_path),
            }
        )

        for topic in payload.get("topics", []) or []:
            slug = str(topic.get("topic_slug", ""))
            if not slug:
                continue
            if slug not in topic_acc:
                topic_acc[slug] = {
                    "topic_slug": slug,
                    "topic_title": str(topic.get("topic_title", "")),
                    "chart_count": 0,
                    "table_count": 0,
                    "batches": [],
                }
            topic_acc[slug]["chart_count"] += int(topic.get("chart_count", 0) or 0)
            topic_acc[slug]["table_count"] += int(topic.get("table_count", 0) or 0)
            if batch_id and batch_id not in topic_acc[slug]["batches"]:
                topic_acc[slug]["batches"].append(batch_id)

    batch_rows.sort(key=lambda x: str(x.get("batch_id", "")), reverse=True)
    topic_rows = sorted(
        topic_acc.values(),
        key=lambda x: (int(x.get("table_count", 0)), int(x.get("chart_count", 0))),
        reverse=True,
    )

    overview_json = collection_root / "chart_quality_gate_overview.json"
    write_json(
        overview_json,
        {
            "collection_root": str(collection_root),
            "batch_count": len(batch_rows),
            "totals": {
                "chart_count": total_chart_count,
                "table_count": total_table_count,
            },
            "batches": batch_rows,
            "topics": topic_rows,
        },
    )

    md_lines = [
        "# 图表门控跨批次总览",
        "",
        f"- 汇总目录：`{collection_root}`",
        f"- 批次数量：{len(batch_rows)}",
        f"- 总图表数：{total_chart_count}",
        f"- 总表格回退数：{total_table_count}",
        "",
        "## 批次汇总",
        "",
    ]
    for row in batch_rows:
        md_lines.extend(
            [
                f"### {row['batch_id']}",
                f"- 图表数：{row['chart_count']}",
                f"- 表格回退数：{row['table_count']}",
                f"- 题目数：{row['topic_count']}",
                f"- 报告：`{row['chart_quality_gate_report_json']}`",
                "",
            ]
        )
    md_lines.extend(["## 题目累计统计", ""])
    for topic in topic_rows:
        md_lines.append(
            f"- `{topic['topic_slug']}`：图表 {topic['chart_count']}，表格回退 {topic['table_count']}，出现批次 {len(topic['batches'])}"
        )
    md_lines.append("")

    overview_md = collection_root / "chart_quality_gate_overview.md"
    write_text(overview_md, "\n".join(md_lines).rstrip() + "\n")
    return {"json": str(overview_json), "md": str(overview_md)}


def merge_count_maps(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    merged: dict[str, int] = {}
    for row in rows:
        counts = row.get(key, {})
        if not isinstance(counts, dict):
            continue
        for reason, count in counts.items():
            merged[str(reason)] = merged.get(str(reason), 0) + int(count)
    return merged


def emit_video_quality_regression_report(pack_root: Path, execution_summary: dict[str, Any]) -> dict[str, str] | None:
    topics = execution_summary.get("topics", [])
    video_topics = [item for item in topics if isinstance(item, dict) and isinstance(item.get("video_search"), dict)]
    if not video_topics:
        return None

    topic_rows: list[dict[str, Any]] = []
    total_candidates = 0
    total_qualified = 0
    total_downloads = 0
    total_download_passed = 0
    total_download_failed = 0

    for item in video_topics:
        topic_slug = str(item.get("topic", ""))
        topic_title = str(item.get("title", ""))
        block = item.get("video_search") or {}
        report_path = block.get("quality_audit_report", "")
        row = {
            "topic_slug": topic_slug,
            "topic_title": topic_title,
            "candidate_queries": int(block.get("candidate_queries", 0) or 0),
            "candidate_total": 0,
            "candidate_qualified": int(block.get("qualified_candidates", 0) or 0),
            "candidate_rejected": 0,
            "download_attempts": int(block.get("downloads", 0) or 0),
            "download_passed": int(block.get("download_quality_passed", 0) or 0),
            "download_failed": int(block.get("download_quality_failed", 0) or 0),
            "candidate_reject_reason_counts": block.get("candidate_reject_reason_counts", {}),
            "download_fail_reason_counts": block.get("download_fail_reason_counts", {}),
            "quality_audit_report": str(report_path),
        }
        if report_path and Path(report_path).exists():
            try:
                report = read_json(Path(report_path))
                summary = report.get("summary", {})
                row["candidate_total"] = int(summary.get("candidate_total", row["candidate_total"]) or 0)
                row["candidate_qualified"] = int(summary.get("candidate_qualified", row["candidate_qualified"]) or 0)
                row["candidate_rejected"] = int(summary.get("candidate_rejected", row["candidate_rejected"]) or 0)
                row["download_attempts"] = int(summary.get("download_attempts", row["download_attempts"]) or 0)
                row["download_passed"] = int(summary.get("download_passed", row["download_passed"]) or 0)
                row["download_failed"] = int(summary.get("download_failed", row["download_failed"]) or 0)
                row["candidate_reject_reason_counts"] = summary.get("candidate_reject_reason_counts", row["candidate_reject_reason_counts"])
                row["download_fail_reason_counts"] = summary.get("download_fail_reason_counts", row["download_fail_reason_counts"])
            except Exception as exc:  # noqa: BLE001
                row["report_read_error"] = str(exc)

        total_candidates += int(row["candidate_total"])
        total_qualified += int(row["candidate_qualified"])
        total_downloads += int(row["download_attempts"])
        total_download_passed += int(row["download_passed"])
        total_download_failed += int(row["download_failed"])
        topic_rows.append(row)

    candidate_reject_reason_counts = merge_count_maps(topic_rows, "candidate_reject_reason_counts")
    download_fail_reason_counts = merge_count_maps(topic_rows, "download_fail_reason_counts")

    report_file_md = pack_root / "video_quality_regression_report.md"
    lines = [
        "# 视频质量回归汇总",
        "",
        f"- 产物根目录：`{pack_root}`",
        f"- 统计题目数：{len(topic_rows)}",
        "",
        "## 各题统计",
        "",
        "| topic | candidates | qualified | rejected | download_attempts | download_passed | download_failed |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in topic_rows:
        lines.append(
            f"| {row['topic_title']} (`{row['topic_slug']}`) | {row['candidate_total']} | {row['candidate_qualified']} | {row['candidate_rejected']} | {row['download_attempts']} | {row['download_passed']} | {row['download_failed']} |"
        )
    lines.extend(
        [
            "",
            "## 汇总",
            "",
            f"- 候选总数：{total_candidates}",
            f"- 合格候选：{total_qualified}",
            f"- 下载尝试：{total_downloads}",
            f"- 下载通过：{total_download_passed}",
            f"- 下载失败：{total_download_failed}",
            "",
            "### 候选拒绝原因",
            "",
        ]
    )
    if candidate_reject_reason_counts:
        for reason, count in sorted(candidate_reject_reason_counts.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- 无")
    lines.extend(["", "### 下载失败原因", ""])
    if download_fail_reason_counts:
        for reason, count in sorted(download_fail_reason_counts.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"- `{reason}`: {count}")
    else:
        lines.append("- 无")
    lines.append("")
    write_text(report_file_md, "\n".join(lines).rstrip() + "\n")

    report_file_json = pack_root / "video_quality_regression_report.json"
    write_json(
        report_file_json,
        {
            "pack_root": str(pack_root),
            "topic_count": len(topic_rows),
            "totals": {
                "candidate_total": total_candidates,
                "candidate_qualified": total_qualified,
                "candidate_rejected": total_candidates - total_qualified,
                "download_attempts": total_downloads,
                "download_passed": total_download_passed,
                "download_failed": total_download_failed,
            },
            "candidate_reject_reason_counts": candidate_reject_reason_counts,
            "download_fail_reason_counts": download_fail_reason_counts,
            "topics": topic_rows,
        },
    )
    return {"md": str(report_file_md), "json": str(report_file_json)}


def main() -> int:
    maybe_reexec_preferred_python()
    parser = argparse.ArgumentParser(description="Execute material pack plans")
    parser.add_argument("--draft-manifest", help="Path to draft_manifest.json; will auto-build or reuse material pack_assets")
    parser.add_argument("--pack-root", help=argparse.SUPPRESS)
    parser.add_argument("--topics", nargs="*", help="Optional topic slugs")
    parser.add_argument("--topic-dir", help="Execute only one topic directory under pack_root")
    parser.add_argument("--steps", default="charts,image_search,video_search,ai_prep")
    parser.add_argument("--video-download-limit", type=int, default=3)
    parser.add_argument("--layer5-only", action="store_true", help="Only run Layer5 required steps (charts + layer5 manifests)")
    parser.add_argument("--no-layer5-manifest", action="store_true", help="Disable emitting layer5_inputs.json and delivery report")
    parser.add_argument("--no-video-quality-regression-report", action="store_true", help="Disable emitting pack-level video quality regression report")
    parser.add_argument("--rebuild-material-plan", action="store_true", help="When using --draft-manifest, force rerunning the Node material planner")
    args = parser.parse_args()

    if args.pack_root:
        raise WorkflowContractError("旧入口 `--pack-root` 已停用；请改用 `--draft-manifest <draft_manifest.json>` 走 dasheng-media-sop 主链。")
    if not args.draft_manifest:
        parser.error("必须提供 canonical 上游入口：--draft-manifest <draft_manifest.json>")

    material_manifest_file: Path | None = None
    draft_manifest_path = Path(args.draft_manifest).expanduser().resolve()
    draft_manifest_payload = ensure_stage_manifest(draft_manifest_path, "draft")
    final_structure_snapshot = draft_manifest_path.parent / "final_structure_snapshot.json"
    final_structure_payload = ensure_final_structure_gate(final_structure_snapshot)
    run_id = str(draft_manifest_payload["run_id"]).strip()
    _, material_ai_inputs_file, material_ai_decisions_file = material_ai_runtime_paths(run_id)
    pack_root, material_manifest_file = build_material_plan_from_draft_manifest(
        draft_manifest_path,
        force_rebuild=args.rebuild_material_plan,
    )

    if not looks_like_pack_root(pack_root):
        raise RuntimeError(f"pack_root 无效，未找到 topic_config.json: {pack_root}")

    steps = {"charts"} if args.layer5_only else {item.strip() for item in args.steps.split(",") if item.strip()}
    topics = [discover_topic_by_dir(pack_root, args.topic_dir)] if args.topic_dir else discover_topics(pack_root)
    if args.topics:
        wanted = set(args.topics)
        topics = [topic for topic in topics if topic.slug in wanted]
        if not topics:
            raise RuntimeError("未匹配到指定 topics")

    summary = {
        "run_id": run_id,
        "stage": "material",
        "pack_root": str(pack_root),
        "steps": sorted(steps),
        "topics": [],
    }
    summary["draft_manifest"] = str(draft_manifest_path)
    summary["final_structure_snapshot"] = str(final_structure_snapshot)
    if material_ai_inputs_file.exists():
        summary["material_ai_inputs_file"] = str(material_ai_inputs_file)
    if material_ai_decisions_file.exists():
        summary["material_ai_decisions_file"] = str(material_ai_decisions_file)
    if material_manifest_file:
        summary["material_manifest"] = str(material_manifest_file)
    for topic in topics:
        summary["topics"].append(execute_topic(topic, steps, args.video_download_limit))

    execution_manifest = pack_root / "execution_manifest.json"
    write_json(execution_manifest, summary)

    if not args.no_layer5_manifest:
        layer5_inputs_file, layer5_report_file = emit_layer5_inputs_manifest(pack_root, topics, execution_manifest)
        summary["layer5_inputs_file"] = str(layer5_inputs_file)
        summary["layer5_delivery_report"] = str(layer5_report_file)
        write_json(execution_manifest, summary)

    chart_quality_report = emit_chart_quality_gate_report(pack_root, summary)
    if chart_quality_report:
        summary["chart_quality_gate_report"] = chart_quality_report["md"]
        summary["chart_quality_gate_report_json"] = chart_quality_report["json"]
        write_json(execution_manifest, summary)
        collection_root = pack_root.parent.parent
        overview_paths = emit_cross_batch_chart_gate_overview(collection_root)
        if overview_paths:
            summary["chart_quality_gate_overview_json"] = overview_paths["json"]
            summary["chart_quality_gate_overview_md"] = overview_paths["md"]
            write_json(execution_manifest, summary)

    if not args.no_video_quality_regression_report:
        video_regression_report = emit_video_quality_regression_report(pack_root, summary)
        if video_regression_report:
            summary["video_quality_regression_report"] = video_regression_report["md"]
            summary["video_quality_regression_report_json"] = video_regression_report["json"]
            write_json(execution_manifest, summary)

    stage_dir, canonical_manifest_path, material_gate_path = canonical_material_paths(run_id)
    stage_dir.mkdir(parents=True, exist_ok=True)
    canonical_manifest = {
        "run_id": run_id,
        "stage": "material",
        "status": "ready_for_material_gate",
        "generation_basis": "final_doc_ai_reading",
        "rerun_mode": "full_regenerate" if args.rebuild_material_plan else "reuse_or_incremental",
        "upstream": {
            "draft_manifest": str(draft_manifest_path),
            "final_structure_snapshot": str(final_structure_snapshot),
        },
        "material_ai_inputs_file": str(material_ai_inputs_file) if material_ai_inputs_file.exists() else None,
        "material_ai_decisions_file": str(material_ai_decisions_file) if material_ai_decisions_file.exists() else None,
        "material_skill_stack": MATERIAL_SKILL_STACK,
        "runtime_material_manifest": str(material_manifest_file) if material_manifest_file else None,
        "pack_root": str(pack_root),
        "execution_manifest": str(execution_manifest),
        "layer5_inputs_file": summary.get("layer5_inputs_file"),
        "layer5_delivery_report": summary.get("layer5_delivery_report"),
        "chart_quality_gate_report": summary.get("chart_quality_gate_report"),
        "chart_quality_gate_report_json": summary.get("chart_quality_gate_report_json"),
        "video_quality_regression_report": summary.get("video_quality_regression_report"),
        "video_quality_regression_report_json": summary.get("video_quality_regression_report_json"),
        "topics": summary["topics"],
        "final_structure_topics": final_structure_payload.get("topics", []),
        "next_stage": "rewrite",
    }
    write_json(canonical_manifest_path, canonical_manifest)
    ensure_pending_gate_file(
        material_gate_path,
        run_id=run_id,
        gate_name="Material Gate",
        topic_rows=[
            {
                "topic_id": item.get("topic_slug") or item.get("topic_id") or f"topic-{index + 1}",
                "title": item.get("title") or item.get("topic_title") or item.get("topic_slug") or f"topic-{index + 1}",
                "editor_status": "pending_review",
                "accepted_assets": [],
                "replace_assets": [],
                "rejected_assets": [],
            }
            for index, item in enumerate(summary["topics"])
        ],
        instructions=[
            "编辑确认可用素材后，将 status 改为 approved / accepted / finalized。",
            "rewrite 只能读取 canonical material_manifest.json + material_acceptance.json。",
        ],
    )

    # 复制素材文件到产物目录
    import shutil
    pack_assets_dest = stage_dir / "pack_assets"
    if pack_root.exists():
        print(f"\n📦 复制素材文件到产物目录: {pack_assets_dest}")
        if pack_assets_dest.exists():
            shutil.rmtree(pack_assets_dest)
        shutil.copytree(pack_root, pack_assets_dest)
        print(f"✓ 素材文件已复制到: {pack_assets_dest}")

    sync_material_to_desktop(run_id, stage_dir, pack_root.parent, pack_root)

    print(canonical_manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
