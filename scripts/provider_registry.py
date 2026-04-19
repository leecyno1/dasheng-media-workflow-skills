from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable

from path_config import get_project_root


ROOT = get_project_root()
IMAGE_ENV_FILE = ROOT / "configs" / "image_generation" / "providers.local.env"
LEGACY_IMAGE_ENV_FILE = ROOT / "产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/vectorengine_gemini_image.env"


def load_env_pairs(path: Path) -> dict[str, str]:
    if not path.exists() or not path.is_file():
        return {}
    pairs: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        pairs[key.strip()] = value.strip()
    return pairs


def load_provider_env(extra_candidates: Iterable[Path] | None = None) -> tuple[dict[str, str], str | None]:
    for candidate in [*(extra_candidates or []), IMAGE_ENV_FILE, LEGACY_IMAGE_ENV_FILE]:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if not path.exists() or not path.is_file():
            continue
        return load_env_pairs(path), str(path)
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


def first_non_empty(env_values: dict[str, str], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        runtime_value = os.environ.get(key)
        if runtime_value:
            return str(runtime_value).strip()
        file_value = env_values.get(key)
        if file_value:
            return str(file_value).strip()
    return default.strip()


def resolve_chat_provider(
    *,
    custom_env_var: str | None = None,
    base_url_keys: list[str],
    api_key_keys: list[str],
    model_keys: list[str],
    timeout_keys: list[str],
    default_model: str = "gpt-4.1-mini",
    default_timeout_seconds: str = "90",
    default_base_url: str = "",
) -> dict[str, str] | None:
    extra_candidates: list[Path] = []
    if custom_env_var:
        custom_env = os.environ.get(custom_env_var, "").strip()
        if custom_env:
            extra_candidates.append(Path(custom_env))
    env_values, env_file = load_provider_env(extra_candidates)
    base_url = normalize_chat_base_url(first_non_empty(env_values, base_url_keys, default_base_url))
    api_key = first_non_empty(env_values, api_key_keys)
    if not base_url or not api_key:
        return None
    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": first_non_empty(env_values, model_keys, default_model) or default_model,
        "timeout_seconds": first_non_empty(env_values, timeout_keys, default_timeout_seconds) or default_timeout_seconds,
        "env_file": env_file or "",
    }


def resolve_material_image_provider_snapshot() -> dict[str, Any]:
    env_values, env_file = load_provider_env()
    env_file_value = env_file or str(IMAGE_ENV_FILE)
    gemini_provider = {
        "provider": "vectorengine_gemini_generate_content",
        "base_url": normalize_gemini_base_url(
            first_non_empty(
                env_values,
                ["GEMINI_IMAGE_BASE_URL", "VECTORENGINE_BASE_URL"],
                "https://api.vectorengine.ai",
            )
        ),
        "model": first_non_empty(
            env_values,
            ["GEMINI_IMAGE_MODEL", "VECTORENGINE_MODEL"],
            "gemini-3.1-flash-image-preview",
        ),
        "api_key": first_non_empty(
            env_values,
            ["VECTORENGINE_API_KEY", "GEMINI_IMAGE_API_KEY"],
        ),
        "env_file": env_file_value,
    }
    return {
        "gemini_generate_content": gemini_provider,
        "optional_fallbacks": {
            "viviai_chat_image": {
                "base_url": normalize_chat_base_url(
                    first_non_empty(env_values, ["VIVIAI_IMAGE_BASE_URL"], "https://api.viviai.cc/v1/chat/completions")
                ),
                "model": first_non_empty(env_values, ["VIVIAI_IMAGE_MODEL"], "gemini-3.1-flash-image-preview"),
                "api_key_present": bool(first_non_empty(env_values, ["VIVIAI_IMAGE_API_KEY"])),
                "api_style": ["/v1/chat/completions"],
                "env_file": env_file_value,
            },
            "vectorengine_chat_image": {
                "base_url": normalize_chat_base_url(
                    first_non_empty(
                        env_values,
                        ["VECTORENGINE_CHAT_IMAGE_BASE_URL"],
                        "https://api.vectorengine.ai/v1/chat/completions",
                    )
                ),
                "model": first_non_empty(
                    env_values,
                    ["VECTORENGINE_CHAT_IMAGE_MODEL", "VECTORENGINE_MODEL"],
                    "gemini-3.1-flash-image-preview",
                ),
                "api_key_present": bool(
                    first_non_empty(env_values, ["VECTORENGINE_CHAT_IMAGE_API_KEY", "VECTORENGINE_API_KEY"])
                ),
                "api_style": ["/v1/chat/completions"],
                "env_file": env_file_value,
            },
            "qhaigc_images": {
                "base_url": normalize_openai_images_base_url(
                    first_non_empty(env_values, ["QHAIGC_BASE_URL"], "https://api.qhaigc.net")
                ),
                "primary_model": first_non_empty(env_values, ["QHAIGC_IMAGE_MODEL"], "seedream-5"),
                "fallback_model": first_non_empty(env_values, ["QHAIGC_IMAGE_FALLBACK_MODEL"], "seedream-4.6"),
                "chat_model": first_non_empty(env_values, ["QHAIGC_CHAT_IMAGE_MODEL"], "gemini-2.5-flash-image"),
                "api_key_present": bool(first_non_empty(env_values, ["QHAIGC_API_KEY"])),
                "api_style": ["/v1/images/generations", "/v1/chat/completions"],
                "env_file": env_file_value,
            },
            "gitee_images": {
                "base_url": normalize_openai_images_base_url(
                    first_non_empty(env_values, ["GITEE_AI_BASE_URL"], "https://ai.gitee.com")
                ),
                "qwen_model": first_non_empty(env_values, ["GITEE_QWEN_IMAGE_MODEL"], "Qwen-Image"),
                "glm_model": first_non_empty(env_values, ["GITEE_GLM_IMAGE_MODEL"], "GLM-Image"),
                "api_key_present": bool(first_non_empty(env_values, ["GITEE_AI_API_KEY"])),
                "api_style": ["/v1/images/generations"],
                "env_file": env_file_value,
            },
            "vectorengine_images": {
                "base_url": normalize_openai_images_base_url(
                    first_non_empty(
                        env_values,
                        ["VECTORENGINE_IMAGES_BASE_URL", "DOUBAO_IMAGE_BASE_URL", "VECTORENGINE_BASE_URL"],
                        "https://api.vectorengine.ai",
                    )
                ),
                "model": first_non_empty(
                    env_values,
                    ["VECTORENGINE_IMAGES_MODEL", "DOUBAO_IMAGE_MODEL"],
                    "doubao-seedream-5-0-260128",
                ),
                "api_key_present": bool(
                    first_non_empty(
                        env_values,
                        ["VECTORENGINE_IMAGES_API_KEY", "DOUBAO_IMAGE_API_KEY", "VECTORENGINE_API_KEY"],
                    )
                ),
                "api_style": ["/v1/images/generations"],
                "env_file": env_file_value,
            },
        },
        "minimax": {
            "base_url": first_non_empty(env_values, ["MINIMAX_BASE_URL"], "https://api.minimaxi.com"),
            "model": first_non_empty(env_values, ["MINIMAX_IMAGE_MODEL"], "image-01"),
            "api_key_present": bool(first_non_empty(env_values, ["MINIMAX_API_KEY"])),
            "env_file": env_file_value,
        },
        "priority_order": [
            "viviai_chat_image",
            "vectorengine_chat_image",
            "qhaigc_seedream5",
            "qhaigc_seedream46",
            "gitee_qwen_image",
            "gitee_glm_image",
            "vectorengine_seedream",
            "minimax",
            "gemini_generate_content",
        ],
    }


def extract_chat_content(response_payload: dict[str, Any]) -> str:
    choices = response_payload.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                if text:
                    parts.append(str(text))
        return "\n".join(parts).strip()
    return ""


def dump_provider_snapshot(snapshot: dict[str, Any]) -> str:
    return json.dumps(snapshot, ensure_ascii=False, indent=2)
