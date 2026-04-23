#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from canonical_workflow import canonical_stage_dir, ensure_stage_manifest, write_json


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def build_postmortem_payload(publish_manifest: dict[str, Any], publish_manifest_path: Path) -> dict[str, Any]:
    topic_rows = publish_manifest.get("channel_packs", [])
    selected_channels = Counter()
    video_ok_counter = Counter()

    topic_summaries = []
    performance_metrics = []  # 新增：性能指标列表

    for item in topic_rows:
        channels = item.get("channels") or []
        selected_channels.update(channels)
        video_ok_counter.update(
            {
                "interactive_chart_ok": 1 if item.get("interactive_chart_video_ok") else 0,
                "motion_narrative_ok": 1 if item.get("motion_narrative_video_ok") else 0,
            }
        )

        # 尝试从已发布的微信文章提取真实阅读数据
        wechat_url = item.get("wechat_article_url", "")
        wechat_stats = {}
        if wechat_url and "wechat" in channels:
            try:
                from skill_invoker import invoke_skill
                extract_result = invoke_skill(
                    "wechat-article-extractor-skill",
                    {"url": wechat_url}
                )

                if extract_result.get("success"):
                    stats = extract_result.get("stats", {})
                    wechat_stats = {
                        "read_count": stats.get("read_count", 0),
                        "like_count": stats.get("like_count", 0),
                        "share_count": stats.get("share_count", 0),
                        "comment_count": stats.get("comment_count", 0),
                    }
                    performance_metrics.append({
                        "platform": "wechat",
                        "topic_id": item.get("topic_id"),
                        "url": wechat_url,
                        **wechat_stats
                    })
            except Exception:
                # 提取失败不影响主流程
                pass

        topic_summaries.append(
            {
                "topic_id": item.get("topic_id"),
                "topic_name": item.get("topic_name"),
                "published": bool(channels),
                "selected_channels": channels,
                "selected_title_count": len(item.get("title_candidates") or []),
                "selected_cover_count": len(item.get("cover_candidates") or []),
                "material_usage": {
                    "interactive_chart_video_ok": bool(item.get("interactive_chart_video_ok")),
                    "motion_narrative_video_ok": bool(item.get("motion_narrative_video_ok")),
                },
                "performance": wechat_stats,  # 新增：性能数据
            }
        )

    return {
        "run_id": publish_manifest["run_id"],
        "stage": "postmortem",
        "status": "completed",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "upstream": {
            "publish_manifest": str(publish_manifest_path),
        },
        "topics": topic_summaries,
        "performance_metrics": performance_metrics,  # 新增：性能指标
        "writeback": {
            "topic_pattern_library": {
                "selected_channel_counts": dict(selected_channels),
                "published_topics": sum(1 for item in topic_summaries if item["published"]),
            },
            "evidence_pattern_library": {
                "interactive_chart_ok_topics": video_ok_counter["interactive_chart_ok"],
                "motion_narrative_ok_topics": video_ok_counter["motion_narrative_ok"],
            },
            "visual_pattern_library": {
                "topics_with_cover_candidates": sum(1 for item in topic_rows if item.get("cover_candidates")),
            },
            "channel_pattern_library": {
                "channel_frequency": dict(selected_channels),
            },
        },
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# 08 复盘报告",
        "",
        f"- run_id：`{payload['run_id']}`",
        f"- 发布题数：`{len(payload['topics'])}`",
        "",
    ]

    # 性能指标总览
    if payload.get("performance_metrics"):
        lines.extend([
            "## 性能指标总览",
            "",
        ])
        for metric in payload["performance_metrics"]:
            lines.extend([
                f"### {metric.get('platform', 'unknown').upper()} - {metric.get('topic_id', 'N/A')}",
                f"- URL: {metric.get('url', 'N/A')}",
                f"- 阅读数: {metric.get('read_count', 0)}",
                f"- 点赞数: {metric.get('like_count', 0)}",
                f"- 分享数: {metric.get('share_count', 0)}",
                f"- 评论数: {metric.get('comment_count', 0)}",
                "",
            ])

    for item in payload["topics"]:
        lines.extend(
            [
                f"## {item['topic_name']}",
                f"- 已发布：`{item['published']}`",
                f"- 渠道：`{item['selected_channels']}`",
                f"- 标题候选数：`{item['selected_title_count']}`",
                f"- 封面候选数：`{item['selected_cover_count']}`",
                f"- 图表动效视频：`{item['material_usage']['interactive_chart_video_ok']}`",
                f"- 叙事动效视频：`{item['material_usage']['motion_narrative_video_ok']}`",
            ]
        )

        # 显示性能数据
        if item.get("performance"):
            perf = item["performance"]
            lines.extend([
                f"- 阅读数：`{perf.get('read_count', 'N/A')}`",
                f"- 点赞数：`{perf.get('like_count', 'N/A')}`",
                f"- 分享数：`{perf.get('share_count', 'N/A')}`",
                f"- 评论数：`{perf.get('comment_count', 'N/A')}`",
            ])

        lines.append("")

    return "\n".join(lines)


def render_l1_writeback(payload: dict[str, Any]) -> str:
    writeback = payload["writeback"]
    return "\n".join(
        [
            "# 08 L1 回写建议",
            "",
            f"- 题材回写：`{writeback['topic_pattern_library']}`",
            f"- 证据回写：`{writeback['evidence_pattern_library']}`",
            f"- 视觉回写：`{writeback['visual_pattern_library']}`",
            f"- 渠道回写：`{writeback['channel_pattern_library']}`",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Canonical postmortem writeback")
    parser.add_argument("--publish-manifest", required=True, help="Path to canonical publish_manifest.json")
    parser.add_argument("--output-dir", help="Output directory; default=产物/08_分析复盘/<run_id>")
    args = parser.parse_args()

    publish_manifest_path = Path(args.publish_manifest).expanduser().resolve()
    publish_manifest = ensure_stage_manifest(publish_manifest_path, "publish")
    run_id = str(publish_manifest["run_id"]).strip()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else canonical_stage_dir("postmortem", run_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_postmortem_payload(publish_manifest, publish_manifest_path)
    write_json(output_dir / "postmortem_manifest.json", payload)
    write_text(output_dir / "08_复盘报告.md", render_report(payload))
    write_text(output_dir / "08_L1回写建议.md", render_l1_writeback(payload))
    print(str(output_dir / "postmortem_manifest.json"))


if __name__ == "__main__":
    main()
