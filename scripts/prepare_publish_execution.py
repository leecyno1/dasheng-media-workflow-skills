#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from path_config import get_project_root


ROOT = get_project_root()
UPSTREAM_REGISTRY = ROOT / "configs" / "publish" / "upstream_repos.json"
LOCAL_SKILLS = ROOT / "skills"
SKILL_ROOTS = [
    LOCAL_SKILLS,
    Path.home() / ".codex" / "skills",
    Path.home() / ".agents" / "skills",
    Path.home() / ".claude" / "skills",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_upstream_rows() -> dict[str, dict[str, Any]]:
    if not UPSTREAM_REGISTRY.exists():
        return {}
    registry = read_json(UPSTREAM_REGISTRY)
    return {str(row.get("name")): row for row in registry.get("repositories") or [] if row.get("name")}


def _expand_env_vars(value: str) -> str:
    """展开 ${VAR:-default} 风格的环境变量。"""
    pattern = r"\$\{([^:}]+)(?::-(.*?))?\}"

    def replacer(match: re.Match[str]) -> str:
        var_name, default = match.groups()
        return os.environ.get(var_name, default or "")

    return re.sub(pattern, replacer, value)


def resolve_root(row: dict[str, Any] | None) -> Path | None:
    if not row:
        return None
    env_name = str(row.get("default_root_env") or "")
    value = os.getenv(env_name) if env_name else None
    raw = value or _expand_env_vars(str(row.get("default_root") or ""))
    return Path(raw).expanduser() if raw else None


def root_exists(rows: dict[str, dict[str, Any]], name: str) -> tuple[bool, str | None]:
    root = resolve_root(rows.get(name))
    return (bool(root and root.exists()), str(root) if root else None)


def local_skill_exists(name: str) -> bool:
    return any((root / name / "SKILL.md").exists() for root in SKILL_ROOTS)


def local_skill_path(name: str) -> str | None:
    for root in SKILL_ROOTS:
        candidate = root / name / "SKILL.md"
        if candidate.exists():
            return str(candidate)
    return None


def route_commands(route_name: str, request: dict[str, Any]) -> list[str]:
    platform = request.get("platform")
    channel_pack = request.get("channel_pack") or "<channel_pack.json>"
    if route_name == "browser-profile":
        open_command = (((request.get("inputs") or {}).get("browser_profile") or {}).get("open_command"))
        return [open_command] if open_command else []
    if route_name == "manual-package":
        return ["open channel_pack directory and upload manually"]
    if route_name == "baoyu-post-to-wechat":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke baoyu-post-to-wechat --payload-file <publish_payload.json>",
        ]
    if route_name == "wechat-multi-publisher":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke wechat-multi-publisher --payload-file <publish_payload.json>",
        ]
    if route_name == "md2wechat":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke md2wechat --payload-file <publish_payload.json>",
        ]
    if route_name == "all-in-one":
        return [
            "aione auth xhs status",
            "aione xhs creator-login check-session --output json",
            "aione xhs creator post-note --note-info <note_info.json> --output json",
        ]
    if route_name == "xhs-skills-spider-xhs":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke dasheng-xhs-publish-bridge --payload-file <publish_payload.json>",
        ]
    if route_name == "xiaohongshu-mcp":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke xiaohongshu-mcp --payload-file <publish_payload.json>",
        ]
    if route_name == "rednote-mcp":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke rednote-mcp --payload-file <publish_payload.json>",
        ]
    if route_name == "douyin-upload-skill":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke douyin-upload-skill --payload-file <publish_payload.json>",
        ]
    if route_name == "social-auto-upload":
        return [
            f"python3 scripts/build_video_upload_package.py --channel-pack {channel_pack}",
            "python3 scripts/check_publish_upstreams.py --name social-auto-upload",
        ]
    if route_name == "bilibili-upload-bridge":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            f"python3 scripts/build_video_upload_package.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke bilibili-upload-bridge --payload-file <bilibili_submission.json>",
        ]
    if route_name == "biliup-rs":
        return [
            f"python3 scripts/build_video_upload_package.py --channel-pack {channel_pack}",
            "biliup --help",
            "biliup login status",
        ]
    if route_name == "baoyu-post-to-weibo":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke baoyu-post-to-weibo --payload-file <publish_payload.json>",
        ]
    if route_name == "baoyu-post-to-x":
        return [
            f"python3 scripts/build_publish_payload.py --channel-pack {channel_pack}",
            "python3 scripts/skill_invoker.py invoke baoyu-post-to-x --payload-file <publish_payload.json>",
        ]
    if route_name == "xurl":
        return ["xurl --help"]
    return [f"prepare {platform} route {route_name}"]


def check_route(route: dict[str, Any], rows: dict[str, dict[str, Any]], request: dict[str, Any]) -> dict[str, Any]:
    route_name = str(route.get("route") or "")
    route_type = str(route.get("type") or "")
    check: dict[str, Any] = {
        "route": route_name,
        "type": route_type,
        "available": False,
        "reason": "unsupported_route",
        "commands": route_commands(route_name, request),
    }

    if route_name in {
        "baoyu-post-to-wechat",
        "wechat-multi-publisher",
        "md2wechat",
        "douyin-upload-skill",
        "bilibili-upload-bridge",
        "baoyu-post-to-weibo",
        "baoyu-post-to-x",
    }:
        exists = local_skill_exists(route_name)
        check.update({
            "available": exists,
            "reason": "local_skill_found" if exists else "missing_local_skill",
            "skill_path": local_skill_path(route_name) or str(LOCAL_SKILLS / route_name / "SKILL.md"),
        })
        return check

    if route_name == "all-in-one":
        binary = shutil.which("aione")
        exists, root = root_exists(rows, "all-in-one")
        check.update({
            "available": bool(binary or exists),
            "reason": "aione_binary_found" if binary else ("upstream_root_found" if exists else "missing_all_in_one"),
            "binary": binary,
            "upstream_root": root,
        })
        return check

    if route_name == "xhs-skills-spider-xhs":
        xhs_exists, xhs_root = root_exists(rows, "xhs-skills")
        spider_exists, spider_root = root_exists(rows, "spider-xhs")
        check.update({
            "available": bool(xhs_exists and spider_exists),
            "reason": "upstream_roots_found" if (xhs_exists and spider_exists) else "missing_xhs_skills_or_spider_xhs",
            "upstream_root": {"xhs_skills": xhs_root, "spider_xhs": spider_root},
        })
        return check

    if route_name == "xiaohongshu-mcp":
        exists, root = root_exists(rows, "xiaohongshu-mcp")
        check.update({
            "available": exists,
            "reason": "upstream_root_found" if exists else "missing_xiaohongshu_mcp_root",
            "upstream_root": root,
        })
        return check

    if route_name == "rednote-mcp":
        exists, root = root_exists(rows, "rednote-mcp")
        check.update({
            "available": exists,
            "reason": "upstream_root_found" if exists else "missing_rednote_mcp_root",
            "upstream_root": root,
        })
        return check

    if route_name == "social-auto-upload":
        exists, root = root_exists(rows, "social-auto-upload")
        check.update({
            "available": exists,
            "reason": "upstream_root_found" if exists else "missing_social_auto_upload_root",
            "upstream_root": root,
        })
        return check

    if route_name == "biliup-rs":
        binary = shutil.which("biliup")
        exists, root = root_exists(rows, "biliup-rs")
        check.update({
            "available": bool(binary or exists),
            "reason": "biliup_binary_found" if binary else ("upstream_root_found" if exists else "missing_biliup_rs"),
            "binary": binary,
            "upstream_root": root,
        })
        return check

    if route_name == "xurl":
        binary = shutil.which("xurl")
        exists, root = root_exists(rows, "xurl")
        check.update({
            "available": bool(binary or exists),
            "reason": "xurl_binary_found" if binary else ("upstream_root_found" if exists else "missing_xurl"),
            "binary": binary,
            "upstream_root": root,
        })
        return check

    if route_name == "browser-profile":
        open_command = route.get("open_command") or (((request.get("inputs") or {}).get("browser_profile") or {}).get("open_command"))
        script_exists = (ROOT / "scripts" / "open_publish_browser.py").exists()
        check.update({
            "available": bool(open_command and script_exists),
            "reason": "persistent_browser_profile_available" if (open_command and script_exists) else "missing_browser_profile_open_command",
            "commands": [str(open_command)] if open_command else [],
        })
        return check

    if route_name == "manual-package":
        channel_pack = request.get("channel_pack")
        check.update({
            "available": bool(channel_pack),
            "reason": "manual_package_available" if channel_pack else "missing_channel_pack",
        })
        return check

    return check


def choose_route(route_checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    for check in route_checks:
        if check.get("available") and check.get("route") not in {"browser-profile", "manual-package"}:
            return check
    for check in route_checks:
        if check.get("available"):
            return check
    return None


def route_can_be_confirm_executed(route: dict[str, Any] | None) -> bool:
    if not route:
        return False
    # Only local draft-push skills are allowed through execute_publish_request.
    # Browser, manual package, MCP, external CLI, and direct API uploader routes
    # must remain plan-only until a dedicated guarded adapter exists.
    return str(route.get("type") or "") == "skill_draft_push"


def build_plan(execution_request_path: Path) -> dict[str, Any]:
    request = read_json(execution_request_path)
    rows = load_upstream_rows()
    route_checks = [check_route(route, rows, request) for route in request.get("route_priority") or []]
    selected = choose_route(route_checks)
    status = "ready_for_user_confirmation" if selected else "blocked_missing_executor"
    if request.get("status") == "blocked":
        status = "blocked_by_channel_pack"
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "dry_run": True,
        "source_execution_request": str(execution_request_path.resolve()),
        "topic_id": request.get("topic_id"),
        "title": request.get("title"),
        "platform": request.get("platform"),
        "channel": request.get("channel"),
        "status": status,
        "selected_route": selected.get("route") if selected else None,
        "selected_route_type": selected.get("type") if selected else None,
        "requires_user_confirmation": True,
        "will_not_publish": True,
        "route_checks": route_checks,
        "prepared_commands": selected.get("commands") if selected else [],
        "safe_executor_command": (
            f"python3 scripts/execute_publish_request.py --execution-request {execution_request_path.resolve()}"
            if selected
            else None
        ),
        "confirmed_executor_command": (
            f"python3 scripts/execute_publish_request.py --execution-request {execution_request_path.resolve()} --confirm-execute"
            if route_can_be_confirm_executed(selected)
            else None
        ),
        "confirm_execute_supported": route_can_be_confirm_executed(selected),
        "next_step": (
            "Ask user to confirm route and login state before executing any publish command."
            if selected
            else "Install/configure one upstream route or use a manual package."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare generic publish execution from execution_request.json without publishing.")
    parser.add_argument("--execution-request", required=True)
    parser.add_argument("--output", help="Optional path for publish_execution_plan.json")
    args = parser.parse_args()

    execution_request = Path(args.execution_request).expanduser().resolve()
    plan = build_plan(execution_request)
    if args.output:
        write_json(Path(args.output).expanduser().resolve(), plan)
    print(json.dumps(plan, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
