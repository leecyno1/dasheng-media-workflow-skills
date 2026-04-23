#!/usr/bin/env python3

from __future__ import annotations

import argparse
import http.client
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request

from canonical_workflow import ensure_pending_gate_file
from desktop_delivery import sync_draft_to_desktop
from provider_registry import extract_chat_content, resolve_chat_provider
from path_config import get_project_root, get_output_root


ROOT = get_project_root()
OUTPUT_ROOT = get_output_root("draft")


def slugify(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z\u4e00-\u9fa5]+", "-", text or "").strip("-").lower()
    return value or "topic"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_text(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data.rstrip() + "\n", encoding="utf-8")


def resolve_draft_ai_config() -> dict[str, str] | None:
    return resolve_chat_provider(
        custom_env_var="DASHENG_DRAFT_PROVIDER_ENV",
        base_url_keys=["PHASE3_AI_BASE_URL", "DRAFT_AI_BASE_URL", "QHAIGC_BASE_URL"],
        api_key_keys=["PHASE3_AI_API_KEY", "DRAFT_AI_API_KEY", "QHAIGC_API_KEY"],
        model_keys=["PHASE3_AI_MODEL", "DRAFT_AI_MODEL", "PHASE2_AI_MODEL"],
        timeout_keys=["PHASE3_AI_TIMEOUT_SECONDS", "DRAFT_AI_TIMEOUT_SECONDS"],
        default_model="gpt-4.1-mini",
        default_timeout_seconds="180",
    )


def request_ai_markdown(system_prompt: str, user_prompt: str, *, max_tokens: int = 9000) -> str:
    fake_response_file = (os.environ.get("DASHENG_DRAFT_FAKE_RESPONSE_FILE") or "").strip()
    if fake_response_file:
        return Path(fake_response_file).expanduser().resolve().read_text(encoding="utf-8")
    fake_response = os.environ.get("DASHENG_DRAFT_FAKE_RESPONSE")
    if fake_response:
        return fake_response
    config = resolve_draft_ai_config()
    if not config:
        raise RuntimeError("未找到 Draft AI 配置：缺少 QHAIGC_BASE_URL / QHAIGC_API_KEY")
    body = {
        "model": config["model"],
        "temperature": 0.75,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    api_key = config['api_key']
    req = urllib_request.Request(
        config["base_url"],
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib_request.urlopen(req, timeout=float(config["timeout_seconds"])) as resp:
                response_payload = json.loads(resp.read().decode("utf-8"))
            content = extract_chat_content(response_payload)
            if content:
                return content
            raise RuntimeError("AI 返回空内容")
        except (
            urllib_error.URLError,
            urllib_error.HTTPError,
            TimeoutError,
            json.JSONDecodeError,
            ValueError,
            http.client.RemoteDisconnected,
            RuntimeError,
        ) as exc:
            last_error = exc
            if attempt >= 2:
                break
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Draft AI 调用失败：{last_error}")


def count_cjk_chars(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text or ""))


def build_ai_draft_prompts(card: dict[str, Any], reasoning: dict[str, Any]) -> tuple[str, str]:
    evidence_lines = "\n".join(
        f"- {item.get('title', '')}｜{item.get('url', '')}"
        for item in card.get("existing_evidence", [])[:6]
    ) or "- 暂无已匹配证据"
    proof_lines = "\n".join(f"- {item}" for item in card.get("proof_requirements", [])) or "- 暂无"
    data_angle_lines = "\n".join(f"- {item}" for item in card.get("recommended_data_angles", [])) or "- 暂无"
    visual_angle_lines = "\n".join(f"- {item}" for item in card.get("recommended_visual_angles", [])) or "- 暂无"

    claim_list = []
    for claim in reasoning.get("claims", []):
        section_id = claim['section_id']
        statement = claim['statement']
        chart_need = claim.get('chart_need') or '无'
        missing_proof = claim.get('missing_proof') or ['无']
        missing_str = '；'.join(missing_proof)
        claim_list.append(f"- {section_id}｜判断：{statement}｜建议图表：{chart_need}｜待补证明：{missing_str}")
    claim_lines = "\n".join(claim_list)
    system_prompt = (
        "你是资深中文财经/时政/产业评论作者。"
        "你的任务是基于选题卡和 Reasoning Sheet 直接写出一篇可供编辑修改的标准初稿。"
        "你必须像作者一样组织文章，而不是把提纲机械展开。"
        "禁止编造不存在的事实、机构表态、具体数字。"
        "允许根据上游判断做分析，但所有强事实都必须与已知证据兼容。"
    )
    title = card['title']
    core_prop = card.get('core_proposition') or card.get('core_thesis') or ''
    one_line = card.get('one_line_judgment') or ''
    why_now = card.get('why_now') or ''
    reader_payoff = card.get('reader_payoff') or ''
    article_use = card.get('article_use') or ''
    struct_hint = card['structure_hint']
    hint_opening = struct_hint['opening']
    hint_part1 = struct_hint['part_1']
    hint_part2 = struct_hint['part_2']
    hint_part3 = struct_hint['part_3']
    hint_ending = struct_hint['ending']

    # Build anchor examples (avoid f-string issues with double braces)
    anchor_section = """
【锚点标注要求】（重要）
在文章中需要配图、链接或引用的位置，必须使用以下标注格式：
- `{{image: 描述内容}}` — 配图占位符，例如：{{image: AI工作流架构对比图}}
- `{{link: URL|显示文字}}` — 链接占位符，例如：{{link: https://example.com|相关报告}}
- `{{ref: 来源名称}}` — 参考文献标注，例如：{{ref: 麦肯锡AI报告2024}}

请在以下位置添加锚点标注：
- 每个一级标题（h2）下至少添加1个 {{image:}} 占位符，用于后续配图
- 引用外部数据或观点时，使用 {{ref:}} 标注来源
- 提到具体案例或报告时，使用 {{link:}} 标注（如果有URL）

这些锚点标注将在后续的素材收集和改写阶段保留，确保内容的完整性。
"""

    user_prompt = f"""请生成一篇标准初稿，要求如下：

【选题】
- 标题：{title}
- 主判断：{core_prop}
- 一句话判断：{one_line}
- 为什么现在值得写：{why_now}
- 读者收益：{reader_payoff}
- 文章用途：{article_use}

【结构约束】
- 必须遵从当前终稿前的标准稿框架，不要写成七八个一级标题。
- 一级标题总数控制在 3-4 个，加结尾即可。
- 可以在一级标题下使用二级标题增强层次。
- 文章总长度目标 4000-6000 字中文正文，不能短。
- 不要写成平台改写稿，这是一篇标准长文初稿。

【结构提示】
- opening：{hint_opening}
- part_1：{hint_part1}
- part_2：{hint_part2}
- part_3：{hint_part3}
- ending：{hint_ending}

【论证骨架 / Claims】
{claim_lines}

【已知证据】
{evidence_lines}

【待补证明】
{proof_lines}

【建议数据角度】
{data_angle_lines}

【建议图表/配图角度】
{visual_angle_lines}

【写作要求】
1. 开篇先明确这篇文章到底要解决什么误判或盲点。
2. 正文必须有明显的逻辑推进：事实层 -> 机制层 -> 判断层 -> 读者框架。
3. 要主动引用上游已有证据；如果证据不够，只能写成"需要进一步验证/仍待数据确认"，不能瞎补数字。
4. 文风自然、锋利、清晰，不要模板腔，不要研报腔，不要空话套话。
5. 表格如果必要，只输出标准 Markdown 表格；但除非确有必要，不要滥用表格。
6. 输出必须是完整 Markdown，直接从 `# 标题` 开始。
7. 文末加一个 `## 引用与待补源` 小节，列出现有来源和还需补的证据。
{anchor_section}
"""
    return system_prompt, user_prompt


def generate_ai_draft(card: dict[str, Any], reasoning: dict[str, Any]) -> str:
    system_prompt, user_prompt = build_ai_draft_prompts(card, reasoning)
    draft = request_ai_markdown(system_prompt, user_prompt, max_tokens=9000).strip()
    min_chars = 4000
    if count_cjk_chars(draft) >= min_chars:
        return draft
    for attempt in range(2):
        expand_prompt = (
            user_prompt
            + "\n\n下面是上一版初稿，请你在保留标题、主判断和一级结构约束的前提下继续扩写。"
            "重点补足事实层、机制层、比较层和读者框架，避免空话，直接输出完整修订版 Markdown。\n\n"
            f"{draft}\n\n"
            "扩写后正文至少达到 4000 字中文左右，仍然控制在 3-4 个一级标题。"
        )
        draft = request_ai_markdown(system_prompt, expand_prompt, max_tokens=12000).strip()
        if count_cjk_chars(draft) >= min_chars:
            return draft
        time.sleep(1 + attempt)
    if count_cjk_chars(draft) < 2800:
        raise RuntimeError(f"AI 初稿长度不足：{count_cjk_chars(draft)} 字")
    return draft


def infer_run_id(selected_topics: dict[str, Any], arg_run_id: str | None, selected_topics_file: Path) -> str:
    if arg_run_id:
        return arg_run_id
    if selected_topics.get("run_id"):
        return str(selected_topics["run_id"])
    return selected_topics_file.parent.name


def load_selected_topics(path: Path) -> dict[str, Any]:
    payload = read_json(path)
    selected = payload.get("selected_topics") or []
    if payload.get("status") != "approved" or not selected:
        raise RuntimeError(f"Brief Gate 未通过：{path} 中 status 必须为 approved 且 selected_topics 非空")
    return payload


def load_topic_cards(path: Path) -> dict[str, dict[str, Any]]:
    cards = read_json(path)
    return {card["topic_id"]: card for card in cards}


def build_claims(card: dict[str, Any]) -> list[dict[str, Any]]:
    proofs = card.get("proof_requirements") or []
    chart_needs = card.get("chart_needs") or card.get("recommended_visual_angles") or card.get("recommended_data_angles") or []
    core_thesis = card.get("core_thesis") or card.get("core_proposition") or card.get("one_line_judgment") or card["title"]
    missing_evidence = card.get("missing_evidence") or card.get("proof_requirements") or []
    topic_id = card["topic_id"]
    section_map = [
        ("section-01", proofs[0] if len(proofs) > 0 else core_thesis),
        ("section-02", proofs[1] if len(proofs) > 1 else core_thesis),
        ("section-03", proofs[2] if len(proofs) > 2 else "给出可执行框架和边界。"),
    ]
    claims = []
    for index, (section_id, statement) in enumerate(section_map, start=1):
        claims.append(
            {
                "claim_id": f"{topic_id}-claim-{index:02d}",
                "section_id": section_id,
                "statement": statement,
                "counterpoint": card.get("counterintuitive_angle") or card.get("distinctiveness_reason"),
                "missing_proof": missing_evidence[:2],
                "chart_need": chart_needs[index - 1] if len(chart_needs) >= index else None,
            }
        )
    return claims


def build_reasoning_sheet(run_id: str, card: dict[str, Any], selected_topic: dict[str, Any]) -> dict[str, Any]:
    now_iso = datetime.now().astimezone().isoformat()
    topic_id = card['topic_id']
    card_meta = card.get("meta")
    if card_meta is None:
        card_meta = {}
    upstream_id = card_meta.get("id")
    if upstream_id is None:
        upstream_id = f"{run_id}:{topic_id}:topic-card"

    title = card["title"]
    core_thesis = card.get("core_thesis") or card.get("core_proposition") or card.get("one_line_judgment") or title

    return {
        "meta": {
            "id": f"{run_id}:{topic_id}:reasoning",
            "object_type": "ReasoningSheet",
            "run_id": run_id,
            "version": "1.0.0",
            "status": "ready",
            "generated_by": "build_stage3_draft.py",
            "input_digest": f"{topic_id}::{title}",
            "upstream_ids": [upstream_id],
            "doc_refs": [],
            "created_at": now_iso,
            "updated_at": now_iso,
        },
        "topic_id": topic_id,
        "title": title,
        "core_thesis": core_thesis,
        "editor_note": selected_topic.get("editor_note", ""),
        "selection_reason": selected_topic.get("selection_reason", ""),
        "claims": build_claims(card),
        "evidence_items": card.get("existing_evidence", []),
        "structure_contract": {
            "max_primary_sections": 4,
            "inherit_from_topic_card": True,
            "source_of_truth": "selected_topics.json + topic_cards.json",
        },
    }


def render_reasoning_sheet_md(reasoning: dict[str, Any], card: dict[str, Any]) -> str:
    title = reasoning['title']
    topic_id = reasoning['topic_id']
    core_thesis = reasoning['core_thesis']
    selection_reason = reasoning.get('selection_reason') or '待补'
    editor_note = reasoning.get('editor_note') or '无'

    lines = [
        f"# 03 Reasoning Sheet｜{title}",
        "",
        f"- topic_id：`{topic_id}`",
        f"- 核心命题：{core_thesis}",
        f"- 编辑选择原因：{selection_reason}",
        f"- 编辑备注：{editor_note}",
        "",
        "## Claims",
        "",
    ]
    for claim in reasoning["claims"]:
        claim_id = claim['claim_id']
        section_id = claim['section_id']
        statement = claim['statement']
        counterpoint = claim.get('counterpoint') or '待补'
        missing_proof = claim.get('missing_proof') or ['无']
        missing_str = '；'.join(missing_proof)
        chart_need = claim.get('chart_need') or '无'

        lines.extend(
            [
                f"### {claim_id}",
                f"- section_id：`{section_id}`",
                f"- 判断：{statement}",
                f"- 反驳位：{counterpoint}",
                f"- 待补证明：{missing_str}",
                f"- 建议图表：{chart_need}",
                "",
            ]
        )
    lines.extend(["## 已有证据", ""])
    for item in reasoning["evidence_items"]:
        item_title = item.get('title')
        item_tier = item.get('source_tier', 'unknown')
        item_url = item.get('url', '')
        lines.append(f"- {item_title}｜{item_tier}｜{item_url}")
    lines.extend(["", "## 结构契约", ""])
    max_sections = reasoning['structure_contract']['max_primary_sections']
    opening_hint = card['structure_hint']['opening']
    lines.append(f"- 一级标题上限：{max_sections}")
    lines.append(f"- 起稿原则：{opening_hint}")
    return "\n".join(lines)


def render_template_draft(card: dict[str, Any], reasoning: dict[str, Any]) -> str:
    sources = card.get("existing_evidence", [])[:3]
    source_lines = "\n".join(f"- {item['title']}｜{item['url']}" for item in sources) or "- 待补权威来源"

    struct_hint = card["structure_hint"]
    section_titles = [
        ("开篇", struct_hint["opening"]),
        ("第一部分", struct_hint["part_1"]),
        ("第二部分", struct_hint["part_2"]),
        ("第三部分", struct_hint["part_3"]),
        ("结尾", struct_hint["ending"]),
    ]

    card_title = card['title']
    topic_id = card['topic_id']
    core_thesis = card['core_thesis']
    audience = card['audience']
    counterintuitive_angle = card['counterintuitive_angle']

    lines = [
        f"# 03 标准初稿｜{card_title}",
        "",
        "## 一、成稿说明",
        f"- topic_id：`{topic_id}`",
        f"- 主判断：{core_thesis}",
        f"- 目标读者：{audience}",
        f"- 结构契约：一级标题不超过 4 个，当前沿用 TopicCard 结构。",
        f"- 当前上游：`selected_topics.json` + `topic_cards.json` + `Reasoning Sheet`。",
        "",
        "## 二、标准初稿正文",
        "",
    ]
    for index, (heading, prompt) in enumerate(section_titles):
        if heading == "结尾":
            lines.append(f"### {heading}")
            lines.append("")
            lines.append(f"这篇稿子的落点不应停在情绪和表面消息，而要回到一个更硬的判断：{prompt}。只要证据链能补齐，正文就应该让读者明确看到哪些变量是真正值得继续跟踪的，哪些波动只是短期情绪。")
            lines.append("")
            continue
        lines.append(f"### {heading}：{prompt}")
        lines.append("")
        claim = reasoning["claims"][min(index, len(reasoning["claims"]) - 1)] if heading != "开篇" else None
        if heading == "开篇":
            lines.append(f"这篇文章真正想处理的，不是把新闻再复述一遍，而是把题目背后的误判点拎出来：{counterintuitive_angle}。如果这个误判不拆开，后续所有判断都会停留在热闹层，而不是结构层。")
            lines.append(f'因此开篇的任务只有一个：告诉读者为什么今天值得写、为什么这个题不该只按热点处理，以及为什么它最后会落到"{core_thesis}"这个主判断上。')
        else:
            claim_statement = claim['statement']
            claim_chart_need = claim.get('chart_need') or '关键数据图'
            lines.append(f"这一部分的核心判断是：{claim_statement}。正文应先交代事实层，再交代它为什么重要，最后给出与主线判断的连接方式。")
            lines.append(f'如果这一段容易写偏，最该防止的是把它写成情绪化描述，而忽略证据边界。这里至少需要围绕"{claim_chart_need}"补一个能证明差异和趋势的数据支点。')
        lines.append("")
    lines.extend(
        [
            "## 三、证据清单",
            source_lines,
            "",
            "## 四、待补证据项",
        ]
    )
    for item in card.get("missing_evidence", []):
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 五、写作约束",
            "- 不机械照抄 Brief，要从作者视角重组论证。",
            "- 能用数据或原始报道支撑的地方，不要停留在抽象判断。",
            "- 一级结构不超过 4 个，允许二级标题增强层次。",
        ]
    )
    return "\n".join(lines)


def render_report(run_id: str, drafts: list[dict[str, Any]]) -> str:
    lines = [
        "# 03 初稿报告",
        "",
        f"- run_id：`{run_id}`",
        f"- 题目数：`{len(drafts)}`",
        "",
        "## 本轮输出",
        "",
    ]
    for draft in drafts:
        draft_title = draft['title']
        reasoning_file = draft['reasoning_sheet_file']
        draft_file = draft['draft_file']
        lines.append(f"- `{draft_title}`")
        lines.append(f"  - Reasoning Sheet：`{reasoning_file}`")
        lines.append(f"  - 标准初稿：`{draft_file}`")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build canonical stage-3 drafts from selected topics")
    parser.add_argument("selected_topics_file", help="Path to selected_topics.json")
    parser.add_argument("topic_cards_file", help="Path to topic_cards.json")
    parser.add_argument("--output-dir", help="Output dir, default=产物/05_初稿生成/<run_id>")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    selected_topics_file = Path(args.selected_topics_file).expanduser().resolve()
    topic_cards_file = Path(args.topic_cards_file).expanduser().resolve()
    selected_payload = load_selected_topics(selected_topics_file)
    cards = load_topic_cards(topic_cards_file)
    run_id = infer_run_id(selected_payload, args.run_id, selected_topics_file)
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else OUTPUT_ROOT / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_topics_for_draft = []
    drafts = []
    for item in selected_payload["selected_topics"]:
        topic_id = item["topic_id"]
        if topic_id not in cards:
            raise RuntimeError(f"selected topic `{topic_id}` 不存在于 topic_cards.json")
        card = cards[topic_id]
        reasoning = build_reasoning_sheet(run_id, card, item)
        slug = slugify(card["title"])[:48]
        reasoning_json_file = output_dir / f"03_ReasoningSheet_{slug}.json"
        reasoning_md_file = output_dir / f"03_ReasoningSheet_{slug}.md"
        draft_file = output_dir / f"03_标准初稿_{slug}.md"
        write_json(reasoning_json_file, reasoning)
        write_text(reasoning_md_file, render_reasoning_sheet_md(reasoning, card))
        write_text(draft_file, generate_ai_draft(card, reasoning))
        selected_topics_for_draft.append(item)
        drafts.append(
            {
                "topic_id": topic_id,
                "title": card["title"],
                "reasoning_sheet_file": str(reasoning_md_file),
                "reasoning_sheet_json": str(reasoning_json_file),
                "draft_file": str(draft_file),
            }
        )

    write_json(output_dir / "selected_topics_for_draft.json", {"run_id": run_id, "selected_topics": selected_topics_for_draft})
    write_json(
        output_dir / "final_structure_snapshot.template.json",
        {
            "run_id": run_id,
            "gate": "Final Structure Gate",
            "status": "pending_editor_review",
            "instructions": [
                "编辑完成标准稿修订后，在本文件写入最终保留的一级/二级结构。",
                "material 与 rewrite 必须以该文件为上游结构快照。",
            ],
            "topics": [
                {
                    "topic_id": item["topic_id"],
                    "title": item["title"],
                    "doc_file": item["draft_file"],
                    "final_primary_sections": [],
                    "editor_note": "",
                }
                for item in drafts
            ],
        },
    )
    ensure_pending_gate_file(
        output_dir / "final_structure_snapshot.json",
        run_id=run_id,
        gate_name="Final Structure Gate",
        topic_rows=[
            {
                "topic_id": item["topic_id"],
                "title": item["title"],
                "doc_file": item["draft_file"],
                "final_primary_sections": [],
                "editor_note": "",
            }
            for item in drafts
        ],
        instructions=[
            "编辑完成标准稿修订后，在本文件写入最终保留的一级/二级结构。",
            "status 改为 approved / locked / finalized 后，material 与 rewrite 才允许继续。",
        ],
    )
    write_text(output_dir / "03_初稿_报告.md", render_report(run_id, drafts))
    write_json(
        output_dir / "draft_manifest.json",
        {
            "run_id": run_id,
            "stage": "draft",
            "status": "ready_for_review",
            "upstream": {
                "selected_topics": str(selected_topics_file),
                "topic_cards": str(topic_cards_file),
            },
            "drafts": drafts,
            "artifacts": [
                str((output_dir / "03_初稿_报告.md").resolve()),
                str((output_dir / "draft_manifest.json").resolve()),
                str((output_dir / "selected_topics_for_draft.json").resolve()),
                str((output_dir / "final_structure_snapshot.json").resolve()),
                str((output_dir / "final_structure_snapshot.template.json").resolve()),
            ]
            + [item["reasoning_sheet_file"] for item in drafts]
            + [item["reasoning_sheet_json"] for item in drafts]
            + [item["draft_file"] for item in drafts],
            "next_stage": "material",
        },
    )
    sync_draft_to_desktop(run_id, output_dir)

    print(
        json.dumps(
            {
                "success": True,
                "run_id": run_id,
                "out_dir": str(output_dir),
                "draft_count": len(drafts),
                "draft_files": [item["draft_file"] for item in drafts],
                "manifest_file": str((output_dir / "draft_manifest.json").resolve()),
                "final_structure_snapshot": str((output_dir / "final_structure_snapshot.json").resolve()),
                "drafts": drafts,
                "next_step": "dasheng-daily-material",
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
