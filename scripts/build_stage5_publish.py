#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from canonical_workflow import (
    WorkflowContractError,
    canonical_stage_dir,
    ensure_runtime_output_dir,
    ensure_publish_decision_gate,
    ensure_stage_manifest,
    write_json,
)
from record_publish_result import aggregate_publish_state


PUBLISH_BROWSER_PROFILE_CONFIG = Path(__file__).resolve().parent.parent / "configs" / "publish" / "browser_profiles.json"

CHANNEL_RULES = {
    "wechat_article": {
        "executor_skill": "baoyu-post-to-wechat",
        "mode": "draft_push_or_browser_confirm",
        "source_lane": "wechat_article",
    },
    "weibo_post": {
        "executor_skill": "baoyu-post-to-weibo",
        "mode": "browser_confirm",
        "source_lane": "wechat_article",
    },
    "x_post": {
        "executor_skill": "baoyu-post-to-x",
        "mode": "browser_confirm",
        "source_lane": "wechat_article",
    },
    "xiaohongshu_video": {
        "executor_skill": "dasheng-xhs-publish-bridge",
        "mode": "api_first_with_browser_fallback",
        "source_lane": "talking_head_video",
    },
    "douyin_video": {
        "executor_skill": "douyin-upload-skill",
        "mode": "manual_or_openclaw",
        "source_lane": "talking_head_video",
    },
    "bilibili_video": {
        "executor_skill": "manual_upload",
        "mode": "manual_only",
        "source_lane": "talking_head_video",
    },
    "podcast": {
        "executor_skill": "manual_or_audio_platform_api",
        "mode": "manual_package",
        "source_lane": "podcast",
    },
}

PUBLISH_READY_LANE_STATUSES = {"completed", "packageable", "ready_base_package"}
PUBLISH_BLOCKING_LANE_STATUSES = {
    "missing_lane",
    "planned",
    "planned_for_render",
    "ready_for_agent_execution",
    "ready_for_agent_dna_humanize",
    "ready_for_skill_execution",
    "ready_for_audio_generation",
    "blocked_missing_api_key",
    "blocked_missing_provider",
    "blocked_missing_audio_provider",
    "blocked_missing_human_media",
    "waiting_for_human_media",
    "failed_qc",
}

CONFIRM_EXECUTABLE_ROUTE_TYPES = {"skill_draft_push"}


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def publish_browser_profiles() -> dict[str, Any]:
    if not PUBLISH_BROWSER_PROFILE_CONFIG.exists():
        return {}
    payload = read_json(PUBLISH_BROWSER_PROFILE_CONFIG)
    profiles = payload.get("profiles")
    return profiles if isinstance(profiles, dict) else {}


def browser_profile_for_channel(channel: str, profile_key: str | None = None) -> dict[str, Any] | None:
    profiles = publish_browser_profiles()
    profile = profiles.get(profile_key or channel)
    if not isinstance(profile, dict):
        return None
    profile_dir = profile.get("profile_dir")
    return {
        "platform": profile.get("platform") or channel,
        "profile_key": profile_key or channel,
        "profile_dir": str(Path(str(profile_dir)).expanduser()) if profile_dir else None,
        "entry_url": profile.get("entry_url"),
        "notes": profile.get("notes"),
        "open_command": f"python3 scripts/open_publish_browser.py {profile_key or channel}",
    }


def safe_slug(value: Any, fallback: str = "item") -> str:
    text = str(value or "").strip()
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned or fallback


def normalize_channels(row: dict[str, Any]) -> list[str]:
    channels = row.get("channels") or row.get("lanes") or ["wechat_article"]
    if isinstance(channels, str):
        channels = [channels]
    return [channel for channel in channels if channel in CHANNEL_RULES]


def topics_by_id(transwrite_manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(topic.get("topic_id")): topic
        for topic in transwrite_manifest.get("topics") or []
        if isinstance(topic, dict) and topic.get("topic_id")
    }


def lane_status(topic: dict[str, Any], lane_name: str) -> tuple[str, str | None, dict[str, Any] | None]:
    lane = (topic.get("lanes") or {}).get(lane_name)
    if not isinstance(lane, dict):
        return "missing_lane", None, None
    manifest_path = lane.get("manifest")
    return str(lane.get("status") or "unknown"), manifest_path, lane


def artifact_exists(value: Any) -> bool:
    if not value:
        return False
    candidate = Path(str(value)).expanduser()
    return candidate.exists()


def lane_final_artifacts(lane: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(lane, dict):
        return {}
    artifacts = lane.get("final_artifacts")
    return artifacts if isinstance(artifacts, dict) else {}


def artifact_hint_for_lane(lane: dict[str, Any] | None) -> dict[str, Any]:
    lane = lane or {}
    final_artifacts = lane_final_artifacts(lane)
    return {
        "wechat_markdown": final_artifacts.get("markdown") or lane.get("final_markdown") or lane.get("base_markdown"),
        "wechat_html": final_artifacts.get("html") or lane.get("final_html") or lane.get("source_html"),
        "video": final_artifacts.get("video") or lane.get("final_video"),
        "video_srt": final_artifacts.get("srt") or lane.get("srt"),
        "video_render_plan": final_artifacts.get("timeline") or lane.get("render_plan"),
        "podcast_audio": final_artifacts.get("audio") or lane.get("audio_file"),
        "podcast_request": lane.get("provider_request"),
        "qc_report": (lane.get("qc") or {}).get("report") if isinstance(lane.get("qc"), dict) else None,
    }


def missing_required_artifacts(channel: str, lane: dict[str, Any] | None, hint: dict[str, Any]) -> list[str]:
    if not lane:
        return ["lane_manifest"]
    if channel in {"wechat_article", "weibo_post", "x_post"}:
        if artifact_exists(hint.get("wechat_html")) or artifact_exists(hint.get("wechat_markdown")):
            return []
        return ["wechat_html_or_markdown"]
    if channel in {"xiaohongshu_video", "douyin_video", "bilibili_video"}:
        return [] if artifact_exists(hint.get("video")) else ["video"]
    if channel == "podcast":
        return [] if artifact_exists(hint.get("podcast_audio")) else ["podcast_audio"]
    return []


def build_channel_pack(topic: dict[str, Any], decision_row: dict[str, Any], channel: str) -> dict[str, Any]:
    rule = CHANNEL_RULES[channel]
    status, manifest_path, lane = lane_status(topic, rule["source_lane"])
    hint = artifact_hint_for_lane(lane)
    missing_artifacts = missing_required_artifacts(channel, lane, hint)
    ready = status in PUBLISH_READY_LANE_STATUSES and not missing_artifacts
    if status not in PUBLISH_READY_LANE_STATUSES:
        blocking_reason = f"lane_status_not_publish_ready:{status}"
    elif missing_artifacts:
        blocking_reason = "missing_required_artifacts:" + ",".join(missing_artifacts)
    else:
        blocking_reason = None
    browser_profile_key = (
        decision_row.get(f"{channel}_browser_profile_key")
        or decision_row.get("browser_profile_key")
        or channel
    )
    browser_profile = browser_profile_for_channel(channel, str(browser_profile_key))
    pack = {
        "topic_id": topic.get("topic_id"),
        "title": decision_row.get("title") or decision_row.get("topic_name") or topic.get("title"),
        "channel": channel,
        "source_lane": rule["source_lane"],
        "lane_status": status,
        "lane_manifest": manifest_path,
        "status": "ready_for_execution" if ready else "blocked_or_waiting",
        "blocking_reason": blocking_reason,
        "missing_artifacts": missing_artifacts,
        "executor_skill": rule["executor_skill"],
        "execution_mode": rule["mode"],
        "artifact_hint": hint,
        "publish_metadata": {
            "title": decision_row.get("title") or decision_row.get("topic_name") or topic.get("title"),
            "summary": decision_row.get("summary") or decision_row.get("description"),
            "tags": decision_row.get("tags") or [],
            "scheduled_at": decision_row.get("scheduled_at") or decision_row.get("publish_time"),
            "visibility": decision_row.get("visibility") or "default",
            "cover": decision_row.get("cover") or hint.get("cover"),
            "platform_notes": decision_row.get(channel) or {},
        },
    }
    if browser_profile:
        pack["browser_profile"] = browser_profile
    return pack


def render_channel_readme(pack: dict[str, Any]) -> str:
    lines = [
        f"# {pack['title']}｜{pack['channel']}",
        "",
        f"- 状态：`{pack['status']}`",
        f"- 阻塞原因：`{pack['blocking_reason'] or 'none'}`",
        f"- 执行器：`{pack['executor_skill']}`",
        f"- 执行模式：`{pack['execution_mode']}`",
        f"- 来源 lane：`{pack['source_lane']}`",
        f"- lane manifest：`{pack['lane_manifest']}`",
        "",
        "## 关键产物",
    ]
    for key, value in (pack.get("artifact_hint") or {}).items():
        if value:
            lines.append(f"- {key}: `{value}`")
    browser_profile = pack.get("browser_profile") or {}
    if browser_profile:
        lines.extend(
            [
                "",
                "## 持久化浏览器 Profile",
                f"- 平台：`{browser_profile.get('platform')}`",
                f"- Profile key：`{browser_profile.get('profile_key')}`",
                f"- Profile 目录：`{browser_profile.get('profile_dir')}`",
                f"- 入口：`{browser_profile.get('entry_url')}`",
                f"- 打开命令：`{browser_profile.get('open_command')}`",
            ]
        )
    if pack.get("missing_artifacts"):
        lines.extend(["", "## 缺失产物", *[f"- `{item}`" for item in pack["missing_artifacts"]]])
    execution_commands = pack.get("execution_commands") or {}
    if execution_commands:
        lines.extend(["", "## 安全执行命令"])
        if execution_commands.get("safe_executor_command"):
            lines.extend(
                [
                    "",
                    "安全执行预演，不发布：",
                    "",
                    "```bash",
                    str(execution_commands["safe_executor_command"]),
                    "```",
                ]
            )
        if execution_commands.get("confirmed_executor_command"):
            lines.extend(
                [
                    "",
                    "当前会话明确确认后才允许执行：",
                    "",
                    "```bash",
                    str(execution_commands["confirmed_executor_command"]),
                    "```",
                ]
            )
    lines.extend(
        [
            "",
            "## 执行说明",
            "",
            "发布前必须人工确认标题、封面、正文/视频/音频、平台规则和风险提示。",
            "浏览器型或审批型渠道只允许推草稿或打开待确认页面，不自动点击最终发布。",
        ]
    )
    return "\n".join(lines)


def confirm_execute_supported_for_pack(pack: dict[str, Any]) -> bool:
    if pack.get("status") != "ready_for_execution":
        return False
    routes = xhs_execution_routes(pack) if pack.get("channel") == "xiaohongshu_video" else generic_execution_routes(pack)
    return any(str(route.get("type") or "") in CONFIRM_EXECUTABLE_ROUTE_TYPES for route in routes)


def execution_commands_for_pack(pack: dict[str, Any]) -> dict[str, str | bool | None]:
    execution_request = pack.get("execution_request")
    if not execution_request:
        return {"safe_executor_command": None, "confirmed_executor_command": None, "confirm_execute_supported": False}
    base = f"python3 scripts/execute_publish_request.py --execution-request {execution_request}"
    supported = confirm_execute_supported_for_pack(pack)
    return {
        "safe_executor_command": base,
        "confirmed_executor_command": f"{base} --confirm-execute" if supported else None,
        "confirm_execute_supported": supported,
    }


def xhs_execution_routes(pack: dict[str, Any]) -> list[dict[str, Any]]:
    title = (pack.get("publish_metadata") or {}).get("title") or pack.get("title")
    video_path = (pack.get("artifact_hint") or {}).get("video")
    tags = (pack.get("publish_metadata") or {}).get("tags") or []
    return [
        {
            "route": "all-in-one",
            "type": "api_first_cli",
            "upstream": "https://github.com/cv-cat/All-IN-ONE",
            "preflight": ["aione auth xhs status", "aione xhs creator-login check-session --output json"],
            "plan": [
                "upload_media_with_creator_profile",
                "build_note_info_json_from_channel_pack",
                "post_note_with_creator_api",
                "query_published_note_info",
            ],
            "command_templates": [
                'aione xhs media upload --path-or-file "<video_or_image_path>" --media-type "<image_or_video>" --output json',
                'aione xhs creator post-note --note-info "<json>" --output json',
                "aione xhs publish all-note-info --output json",
            ],
            "payload_hint": {
                "title": title,
                "video": video_path,
                "tags": tags,
            },
        },
        {
            "route": "xhs-skills-spider-xhs",
            "type": "api_first_skill",
            "upstream": "https://github.com/cv-cat/XhsSkills + https://github.com/cv-cat/Spider_XHS",
            "plan": [
                "call_creator_media_upload",
                "call_creator_post_note",
                "recover_note_id_or_creator_publish_status",
            ],
        },
        {
            "route": "xiaohongshu-mcp",
            "type": "mcp_fallback",
            "upstream": "https://github.com/xpzouying/xiaohongshu-mcp",
            "plan": ["publish_video_or_image_note", "recover_mcp_result"],
        },
        {
            "route": "rednote-mcp",
            "type": "mcp_fallback",
            "upstream": "https://github.com/TimeCyber/mcp-xiaohongshu",
            "plan": ["publish_note_with_playwright_mcp", "recover_mcp_result"],
        },
        {
            "route": "browser-profile",
            "type": "browser_confirm_fallback",
            "open_command": (pack.get("browser_profile") or {}).get("open_command"),
            "plan": ["open_persistent_profile", "fill_creator_publish_form", "wait_for_user_confirmation"],
        },
    ]


def generic_execution_routes(pack: dict[str, Any]) -> list[dict[str, Any]]:
    channel = pack.get("channel")
    if channel == "wechat_article":
        return [
            {
                "route": "baoyu-post-to-wechat",
                "type": "skill_draft_push",
                "plan": ["push_wechat_draft", "recover_draft_id"],
            },
            {
                "route": "wechat-multi-publisher",
                "type": "skill_batch_draft_push_guarded_required",
                "plan": ["push_batch_draft", "recover_draft_id"],
            },
            {
                "route": "md2wechat",
                "type": "preprocess_fallback",
                "plan": ["convert_markdown_to_wechat_html", "export_browser_package"],
            },
            {
                "route": "browser-profile",
                "type": "browser_confirm_fallback",
                "open_command": (pack.get("browser_profile") or {}).get("open_command"),
                "plan": ["open_persistent_profile", "fill_wechat_editor", "wait_for_user_confirmation"],
            },
        ]
    if channel == "douyin_video":
        return [
            {
                "route": "douyin-upload-skill",
                "type": "skill_or_api_upload",
                "plan": ["doctor", "auth", "prepare_video_upload", "wait_for_user_confirmation"],
            },
            {
                "route": "social-auto-upload",
                "type": "external_uploader_fallback",
                "upstream": "https://github.com/dreammis/social-auto-upload",
                "plan": ["convert_channel_pack", "dry_run_upload", "wait_for_user_confirmation"],
            },
            {
                "route": "browser-profile",
                "type": "browser_confirm_fallback",
                "open_command": (pack.get("browser_profile") or {}).get("open_command"),
                "plan": ["open_persistent_profile", "fill_douyin_upload_form", "wait_for_user_confirmation"],
            },
        ]
    if channel == "bilibili_video":
        return [
            {
                "route": "bilibili-upload-bridge",
                "type": "skill_bridge",
                "plan": ["build_submission_payload", "dry_run_upload", "wait_for_user_confirmation"],
            },
            {
                "route": "biliup-rs",
                "type": "external_cli",
                "upstream": "https://github.com/biliup/biliup-rs",
                "binary": "biliup",
                "plan": ["check_login", "prepare_submission", "wait_for_user_confirmation"],
            },
            {
                "route": "social-auto-upload",
                "type": "external_uploader_fallback",
                "upstream": "https://github.com/dreammis/social-auto-upload",
                "plan": ["convert_channel_pack", "dry_run_upload", "wait_for_user_confirmation"],
            },
            {
                "route": "manual-package",
                "type": "manual_package",
                "plan": ["export_title_description_cover_video", "wait_for_human_upload"],
            },
        ]
    if channel == "weibo_post":
        return [
            {
                "route": "baoyu-post-to-weibo",
                "type": "browser_confirm",
                "plan": ["prepare_weibo_post", "wait_for_user_confirmation"],
            },
        ]
    if channel == "x_post":
        return [
            {
                "route": "baoyu-post-to-x",
                "type": "browser_or_api_confirm",
                "plan": ["prepare_x_post", "wait_for_user_confirmation"],
            },
            {
                "route": "xurl",
                "type": "external_api_cli_fallback",
                "plan": ["check_x_api_auth", "prepare_media_upload"],
            },
        ]
    return [
        {
            "route": pack.get("executor_skill"),
            "type": pack.get("execution_mode"),
            "input_manifest": pack.get("pack_manifest"),
        }
    ]


def platform_for_channel(channel: Any) -> str:
    if channel == "xiaohongshu_video":
        return "xiaohongshu"
    if channel == "douyin_video":
        return "douyin"
    if channel == "bilibili_video":
        return "bilibili"
    if channel == "wechat_article":
        return "wechat"
    if channel == "weibo_post":
        return "weibo"
    if channel == "x_post":
        return "x"
    return str(channel or "unknown")


def build_execution_request(pack: dict[str, Any]) -> dict[str, Any]:
    artifacts = pack.get("artifact_hint") or {}
    request: dict[str, Any] = {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "topic_id": pack.get("topic_id"),
        "title": pack.get("title"),
        "channel": pack.get("channel"),
        "status": "blocked" if pack.get("status") != "ready_for_execution" else "ready_for_user_confirmation",
        "executor_skill": pack.get("executor_skill"),
        "execution_mode": pack.get("execution_mode"),
        "requires_user_confirmation": True,
        "channel_pack": pack.get("pack_manifest"),
        "inputs": {
            "artifacts": artifacts,
            "publish_metadata": pack.get("publish_metadata") or {},
            "browser_profile": pack.get("browser_profile"),
        },
        "blocking_reason": pack.get("blocking_reason"),
        "fallback_policy": {
            "on_auth_failure": "open_persistent_browser_profile_or_export_manual_package",
            "on_platform_risk_or_captcha": "stop_and_request_user_action",
            "on_executor_missing": "export_manual_package",
        },
        "output_contract": {
            "write_result_under": "same_channel_pack_directory",
            "required_fields": ["success", "status", "platform", "draft_id_or_url", "screenshot_or_error"],
        },
    }
    if pack.get("channel") == "xiaohongshu_video":
        request["platform"] = "xiaohongshu"
        request["route_priority"] = xhs_execution_routes(pack)
        request["notes"] = [
            "小红书优先 API-first / CLI / MCP，不把浏览器粘贴当主路径。",
            "任何最终发布点击都必须经过当前会话人工确认。",
        ]
    else:
        request["platform"] = platform_for_channel(pack.get("channel"))
        request["route_priority"] = generic_execution_routes(pack)
    return request


def build_verification_request(pack: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "topic_id": pack.get("topic_id"),
        "title": pack.get("title"),
        "channel": pack.get("channel"),
        "platform": platform_for_channel(pack.get("channel")),
        "status": "pending_execution",
        "channel_pack": pack.get("pack_manifest"),
        "execution_request": pack.get("execution_request"),
        "required_evidence": [
            "platform_url_or_draft_id",
            "account_identifier",
            "published_or_draft_at",
            "screenshot_or_platform_response",
        ],
        "guard_skill": "publish-guard",
        "success_condition": "Only mark published after URL/draft id is recovered and checked.",
    }


def write_channel_pack_files(out_dir: Path, pack: dict[str, Any]) -> dict[str, str]:
    pack_dir = out_dir / "channel_packs" / safe_slug(pack.get("topic_id"), "topic") / safe_slug(pack.get("channel"), "channel")
    pack_path = pack_dir / "channel_pack.json"
    readme_path = pack_dir / "README.md"
    execution_request_path = pack_dir / "execution_request.json"
    verification_request_path = pack_dir / "verification_request.json"
    paths = {
        "pack_dir": str(pack_dir.resolve()),
        "pack_manifest": str(pack_path.resolve()),
        "readme": str(readme_path.resolve()),
        "execution_request": str(execution_request_path.resolve()),
        "verification_request": str(verification_request_path.resolve()),
    }
    pack_with_paths = {**pack, **paths}
    pack_with_paths["execution_commands"] = execution_commands_for_pack(pack_with_paths)
    write_json(pack_path, pack_with_paths)
    write_text(readme_path, render_channel_readme(pack_with_paths))
    write_json(execution_request_path, build_execution_request(pack_with_paths))
    write_json(verification_request_path, build_verification_request(pack_with_paths))
    return {**paths, "execution_commands": pack_with_paths["execution_commands"]}


def build_execution_manifest(run_id: str, channel_packs: list[dict[str, Any]]) -> dict[str, Any]:
    executions = []
    for pack in channel_packs:
        blocked = pack["status"] != "ready_for_execution"
        executions.append(
            {
                "topic_id": pack["topic_id"],
                "title": pack["title"],
                "channel": pack["channel"],
                "status": "waiting_for_transwrite_lane" if blocked else "pending_user_confirmation",
                "executor_skill": pack["executor_skill"],
                "executor_invocation": {
                    "type": "skill_or_manual_package",
                    "mode": pack["execution_mode"],
                    "input_manifest": pack.get("pack_manifest") or pack["lane_manifest"],
                    "execution_request": pack.get("execution_request"),
                    "verification_request": pack.get("verification_request"),
                    "safe_executor_command": (pack.get("execution_commands") or {}).get("safe_executor_command"),
                    "confirmed_executor_command": (pack.get("execution_commands") or {}).get("confirmed_executor_command"),
                    "confirm_execute_supported": (pack.get("execution_commands") or {}).get("confirm_execute_supported", False),
                    "notes": "发布前必须人工确认标题、封面、正文和平台规则。",
                    "browser_profile": pack.get("browser_profile"),
                },
            }
        )
    return {
        "run_id": run_id,
        "stage": "publish",
        "status": "pending_execution",
        "executions": executions,
    }


def render_publish_plan(run_id: str, channel_packs: list[dict[str, Any]]) -> str:
    lines = [
        f"# 07 发布执行计划｜{run_id}",
        "",
        "Publish 只做验收、打包、推草稿/人工发布包和链接回收；不再生成正文、图表、封面或视频。",
        "",
    ]
    for pack in channel_packs:
        lines.append(f"- {pack['title']}｜{pack['channel']}：{pack['status']}（{pack['executor_skill']}）")
    return "\n".join(lines)


def render_publish_package(channel_packs: list[dict[str, Any]]) -> str:
    lines = ["# 07 发布包", ""]
    for pack in channel_packs:
        lines.extend(
            [
                f"## {pack['title']}｜{pack['channel']}",
                "",
                f"- 状态：`{pack['status']}`",
                f"- 来源 lane：`{pack['source_lane']}`",
                f"- lane manifest：`{pack['lane_manifest']}`",
                f"- 执行器：`{pack['executor_skill']}`",
                "",
            ]
        )
    return "\n".join(lines)


def build_publish_outputs(
    *,
    transwrite_manifest_path: Path,
    publish_decision_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    transwrite_manifest = ensure_stage_manifest(transwrite_manifest_path, "transwrite")
    publish_decision = ensure_publish_decision_gate(publish_decision_path)
    run_id = str(transwrite_manifest.get("run_id") or publish_decision.get("run_id") or "").strip()
    if not run_id:
        raise WorkflowContractError("无法从 transwrite_manifest 或 publish_decision 推断 run_id")
    out_dir = ensure_runtime_output_dir(output_dir or canonical_stage_dir("publish", run_id), label="publish output_dir")
    out_dir.mkdir(parents=True, exist_ok=True)
    topic_map = topics_by_id(transwrite_manifest)

    channel_packs: list[dict[str, Any]] = []
    for row in publish_decision.get("topics") or []:
        topic_id = str(row.get("topic_id") or "").strip()
        topic = topic_map.get(topic_id)
        if not topic:
            raise WorkflowContractError(f"publish_decision 中的 topic_id 未命中 transwrite_manifest：{topic_id or '<empty>'}")
        for channel in normalize_channels(row):
            channel_packs.append(build_channel_pack(topic, row, channel))

    channel_packs = [{**pack, **write_channel_pack_files(out_dir, pack)} for pack in channel_packs]

    plan_path = out_dir / "07_发布计划.md"
    package_path = out_dir / "07_发布包.md"
    execution_path = out_dir / "channel_execution_manifest.json"
    verification_path = out_dir / "publish_verification_report.json"
    manifest_path = out_dir / "publish_manifest.json"
    write_text(plan_path, render_publish_plan(run_id, channel_packs))
    write_text(package_path, render_publish_package(channel_packs))
    execution_manifest = build_execution_manifest(run_id, channel_packs)
    write_json(execution_path, execution_manifest)
    initial_manifest_stub = {"channel_packs": channel_packs}
    publish_summary = aggregate_publish_state(out_dir, [], initial_manifest_stub)
    verification = {
        "run_id": run_id,
        "stage": "publish",
        "status": publish_summary["status"],
        "records": [],
        "published_links": [],
        "draft_records": [],
        "publish_summary": publish_summary,
        "instructions": ["发布后回填平台链接、发布时间、账号、截图或草稿 ID。"],
    }
    write_json(verification_path, verification)
    publish_manifest = {
        "run_id": run_id,
        "stage": "publish",
        "status": "pending_execution",
        "created_at": now_iso(),
        "source_transwrite_manifest": str(transwrite_manifest_path.resolve()),
        "publish_decision": str(publish_decision_path.resolve()),
        "channel_packs": channel_packs,
        "publish_results": [],
        "publish_summary": publish_summary,
        "artifacts": [
            str(plan_path.resolve()),
            str(package_path.resolve()),
            str(execution_path.resolve()),
            str(verification_path.resolve()),
        ],
        "next_stage": "postmortem",
    }
    write_json(manifest_path, publish_manifest)
    return {**publish_manifest, "manifest_file": str(manifest_path.resolve()), "out_dir": str(out_dir.resolve())}


def main() -> None:
    parser = argparse.ArgumentParser(description="Dasheng Stage 5 Publish execution pack builder")
    parser.add_argument("--transwrite-manifest", required=True)
    parser.add_argument("--publish-decision", required=True)
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    result = build_publish_outputs(
        transwrite_manifest_path=Path(args.transwrite_manifest).expanduser().resolve(),
        publish_decision_path=Path(args.publish_decision).expanduser().resolve(),
        output_dir=Path(args.output_dir).expanduser().resolve() if args.output_dir else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
