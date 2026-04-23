#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from canonical_workflow import CANONICAL_STAGE_ROOTS, canonical_manifest_path, ensure_json_file, stage_contract_snapshot
from desktop_delivery import DESKTOP_ROOT
from provider_registry import resolve_chat_provider, resolve_material_image_provider_snapshot
from path_config import (
    get_project_root,
    get_feishu_config_path,
    get_feishu_bot_config_path,
    get_feishu_stage_contract_path,
)


ROOT = get_project_root()
FEISHU_CONFIG_FILES = [
    get_feishu_config_path(),
    get_feishu_bot_config_path(),
    get_feishu_stage_contract_path(),
]
LEGACY_ENTRYPOINTS = [
    ROOT / "skills" / "dasheng-daily-brief" / "index.js",
    ROOT / "skills" / "dasheng-daily-clustering" / "index.js",
    ROOT / "skills" / "dasheng-daily-draft" / "index.js",
    ROOT / "skills" / "dasheng-daily-outline" / "index.js",
    ROOT / "skills" / "dasheng-daily-final" / "index.js",
]


def mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    secret = str(value)
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}***{secret[-4:]}"


def discover_latest_run_id() -> str | None:
    candidates: dict[str, float] = {}
    for root in CANONICAL_STAGE_ROOTS.values():
        if not root.exists():
            continue
        for stage_dir in root.iterdir():
            if not stage_dir.is_dir():
                continue
            stat = stage_dir.stat()
            candidates[stage_dir.name] = max(candidates.get(stage_dir.name, 0.0), stat.st_mtime)
    if not candidates:
        return None
    return sorted(candidates.items(), key=lambda item: item[1], reverse=True)[0][0]


def load_manifest_if_exists(stage: str, run_id: str) -> dict[str, Any] | None:
    path = canonical_manifest_path(stage, run_id)
    if not path.exists():
        return None
    try:
        return ensure_json_file(path, f"{stage}_manifest.json")
    except Exception as exc:
        return {
            "_invalid": True,
            "status": "invalid",
            "error": str(exc),
            "path": str(path),
        }


def stage_issues(contract: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    stages = contract.get("stages") or {}
    for stage, row in stages.items():
        if stage == "intake":
            continue
        previous_ready = True
        if stage == "brief":
            previous_ready = bool(stages.get("intake", {}).get("manifest_exists"))
        elif stage == "draft":
            previous_ready = bool(stages.get("brief", {}).get("gate_exists"))
        elif stage == "material":
            previous_ready = bool(stages.get("draft", {}).get("gate_exists"))
        elif stage == "rewrite":
            previous_ready = bool(stages.get("material", {}).get("gate_exists"))
        elif stage == "publish":
            previous_ready = bool(stages.get("rewrite", {}).get("manifest_exists"))
        elif stage == "postmortem":
            previous_ready = bool(stages.get("publish", {}).get("manifest_exists"))
        if previous_ready and not row.get("manifest_exists"):
            issues.append(f"{stage}: 上游已就绪，但本阶段 manifest 缺失")
    return issues


def provider_summary() -> dict[str, Any]:
    def sanitize(provider: dict[str, Any] | None) -> dict[str, Any] | None:
        if not provider:
            return None
        # Preserve _unavailable marker for diagnostics
        if provider.get("_unavailable"):
            return {"_unavailable": True, "status": "unavailable"}
        payload = dict(provider)
        if "api_key" in payload:
            payload["api_key"] = mask_secret(payload.get("api_key"))
            payload["api_key_present"] = bool(provider.get("api_key"))
        return payload

    image_snapshot = resolve_material_image_provider_snapshot()
    image_snapshot["gemini_generate_content"] = {
        **image_snapshot["gemini_generate_content"],
        "api_key": mask_secret(image_snapshot["gemini_generate_content"].get("api_key")),
        "api_key_present": bool(image_snapshot["gemini_generate_content"].get("api_key")),
    }
    return {
        "brief": sanitize(resolve_chat_provider(
            custom_env_var="DASHENG_PHASE2_PROVIDER_ENV",
            base_url_keys=["PHASE2_AI_BASE_URL", "QHAIGC_BASE_URL"],
            api_key_keys=["PHASE2_AI_API_KEY", "QHAIGC_API_KEY"],
            model_keys=["PHASE2_AI_MODEL", "PHASE3_AI_MODEL", "DRAFT_AI_MODEL"],
            timeout_keys=["PHASE2_AI_TIMEOUT_SECONDS"],
        )),
        "draft": sanitize(resolve_chat_provider(
            custom_env_var="DASHENG_DRAFT_PROVIDER_ENV",
            base_url_keys=["PHASE3_AI_BASE_URL", "DRAFT_AI_BASE_URL", "QHAIGC_BASE_URL"],
            api_key_keys=["PHASE3_AI_API_KEY", "DRAFT_AI_API_KEY", "QHAIGC_API_KEY"],
            model_keys=["PHASE3_AI_MODEL", "DRAFT_AI_MODEL", "PHASE2_AI_MODEL"],
            timeout_keys=["PHASE3_AI_TIMEOUT_SECONDS", "DRAFT_AI_TIMEOUT_SECONDS"],
        )),
        "material": sanitize(resolve_chat_provider(
            custom_env_var="DASHENG_MATERIAL_PROVIDER_ENV",
            base_url_keys=["MATERIAL_AI_BASE_URL", "QHAIGC_BASE_URL"],
            api_key_keys=["MATERIAL_AI_API_KEY", "QHAIGC_API_KEY"],
            model_keys=["MATERIAL_AI_MODEL", "PHASE4_AI_MODEL", "PHASE3_AI_MODEL", "DRAFT_AI_MODEL"],
            timeout_keys=["MATERIAL_AI_TIMEOUT_SECONDS", "PHASE3_AI_TIMEOUT_SECONDS", "DRAFT_AI_TIMEOUT_SECONDS"],
        )),
        "image_generation": image_snapshot,
    }


def build_report(run_id: str) -> dict[str, Any]:
    contract = stage_contract_snapshot(run_id)
    desktop_root = DESKTOP_ROOT / run_id
    manifests = {stage: load_manifest_if_exists(stage, run_id) for stage in CANONICAL_STAGE_ROOTS}
    invalid_manifests = [
        f"{stage}: manifest 无法解析"
        for stage, manifest in manifests.items()
        if manifest and manifest.get("_invalid")
    ]
    return {
        "run_id": run_id,
        "canonical_contract": contract,
        "issues": stage_issues(contract) + invalid_manifests,
        "desktop_delivery": {
            "root": str(desktop_root),
            "exists": desktop_root.exists(),
            "export_manifests": sorted(item.name for item in desktop_root.glob("*__desktop_export_manifest.json")) if desktop_root.exists() else [],
        },
        "feishu": {
            "files": [{"path": str(path), "exists": path.exists()} for path in FEISHU_CONFIG_FILES],
        },
        "providers": provider_summary(),
        "legacy_entrypoints": [{"path": str(path), "exists": path.exists()} for path in LEGACY_ENTRYPOINTS],
        "stage_status": {
            stage: {
                "manifest_status": (manifest or {}).get("status"),
                "next_stage": (manifest or {}).get("next_stage"),
                "manifest_error": (manifest or {}).get("error"),
            }
            for stage, manifest in manifests.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Dasheng 主链 doctor / 自检")
    parser.add_argument("--run-id")
    parser.add_argument("--latest", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    run_id = args.run_id or (discover_latest_run_id() if args.latest else None)
    if not run_id:
        raise SystemExit("请提供 --run-id，或使用 --latest")

    report = build_report(run_id)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict and report["issues"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
