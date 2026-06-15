#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from build_publish_payload import build_package
from prepare_publish_execution import build_plan, write_json
from record_publish_result import record_result
from skill_invoker import SkillInvoker


CONFIRM_EXECUTABLE_ROUTE_TYPES = {"skill_draft_push"}

AUTO_SKILL_ROUTES = {
    "baoyu-post-to-wechat",
    "wechat-multi-publisher",
    "md2wechat",
    "baoyu-post-to-weibo",
    "baoyu-post-to-x",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def resolve_channel_pack(plan: dict[str, Any]) -> Path:
    request = read_json(Path(plan["source_execution_request"]))
    channel_pack = request.get("channel_pack")
    if not channel_pack or str(channel_pack).startswith("<"):
        raise SystemExit("execution_request 缺少真实 channel_pack 路径，不能执行。")
    return Path(str(channel_pack)).expanduser().resolve()


def build_dry_run_response(plan: dict[str, Any], payload_report: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "mode": "dry_run",
        "will_not_publish": True,
        "requires_user_confirmation": True,
        "status": plan.get("status"),
        "selected_route": plan.get("selected_route"),
        "selected_route_type": plan.get("selected_route_type"),
        "prepared_commands": plan.get("prepared_commands") or [],
        "publish_payload": (payload_report or {}).get("publish_payload"),
        "next_step": "Review payload and rerun with --confirm-execute only for supported skill routes.",
    }


def skill_name_for_route(route: str | None, payload: dict[str, Any]) -> str | None:
    if not route:
        return None
    if route in AUTO_SKILL_ROUTES:
        return payload.get("payload", {}).get("skill") or route
    return None


def route_can_be_confirm_executed(plan: dict[str, Any]) -> bool:
    return str(plan.get("selected_route_type") or "") in CONFIRM_EXECUTABLE_ROUTE_TYPES


def normalize_skill_result(result: dict[str, Any], *, selected_route: str | None) -> dict[str, Any]:
    return {
        "success": result.get("success", False),
        "status": result.get("status"),
        "platform": result.get("platform"),
        "platform_url": result.get("platform_url") or result.get("url"),
        "platform_post_id": result.get("platform_post_id") or result.get("post_id"),
        "draft_id": result.get("draft_id") or result.get("msg_id") or result.get("draft_id_or_url"),
        "verification_status": result.get("verification_status"),
        "account": result.get("account"),
        "screenshot": result.get("screenshot") or result.get("screenshot_path"),
        "error": result.get("error"),
        "platform_response": result,
        "notes": f"recorded_from_route:{selected_route}",
    }


def execute_request(
    execution_request_path: Path,
    *,
    confirm_execute: bool,
    invoker: SkillInvoker | None = None,
) -> dict[str, Any]:
    plan = build_plan(execution_request_path)
    channel_pack = resolve_channel_pack(plan)
    payload_report = build_package(channel_pack)
    payload = read_json(Path(payload_report["publish_payload"]))
    if not confirm_execute:
        return build_dry_run_response(plan, payload_report)
    if plan.get("status") != "ready_for_user_confirmation":
        return {
            "schema_version": "1.0",
            "created_at": now_iso(),
            "mode": "execute",
            "status": "blocked",
            "will_not_publish": True,
            "error": f"route_not_ready:{plan.get('status')}",
            "plan": plan,
        }
    selected_route = plan.get("selected_route")
    if not route_can_be_confirm_executed(plan) or selected_route not in AUTO_SKILL_ROUTES:
        return {
            "schema_version": "1.0",
            "created_at": now_iso(),
            "mode": "execute",
            "status": "blocked_manual_or_external_route",
            "will_not_publish": True,
            "selected_route": selected_route,
            "selected_route_type": plan.get("selected_route_type"),
            "prepared_commands": plan.get("prepared_commands") or [],
            "error": "Selected route requires browser/manual/MCP/external API or CLI confirmation; not executed by this script.",
        }
    skill_name = skill_name_for_route(selected_route, payload)
    if not skill_name:
        return {
            "schema_version": "1.0",
            "created_at": now_iso(),
            "mode": "execute",
            "status": "blocked_missing_skill_name",
            "will_not_publish": True,
            "selected_route": selected_route,
        }
    result = (invoker or SkillInvoker()).invoke(skill_name, payload)
    normalized = normalize_skill_result(result, selected_route=selected_route)
    record = record_result(channel_pack, normalized, source=f"execute_publish_request:{selected_route}")
    return {
        "schema_version": "1.0",
        "created_at": now_iso(),
        "mode": "execute",
        "status": "executed_and_recorded",
        "selected_route": selected_route,
        "skill": skill_name,
        "publish_payload": payload_report["publish_payload"],
        "skill_result": result,
        "record": record,
        "final_publish_requires_confirmation": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely execute a publish execution_request.json. Defaults to dry-run.")
    parser.add_argument("--execution-request", required=True)
    parser.add_argument("--confirm-execute", action="store_true", help="Actually invoke supported local skill routes.")
    parser.add_argument("--output", help="Optional JSON report path.")
    args = parser.parse_args()

    result = execute_request(Path(args.execution_request).expanduser().resolve(), confirm_execute=args.confirm_execute)
    if args.output:
        write_json(Path(args.output).expanduser().resolve(), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
