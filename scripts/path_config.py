#!/usr/bin/env python3
"""
Path Configuration Module
统一管理所有硬编码路径，支持环境变量覆盖

DEPRECATED: 此模块已废弃，请使用 core.path_resolver 替代
"""

import os
from pathlib import Path


def get_project_root() -> Path:
    """
    获取项目根目录

    优先级：
    1. 环境变量 DASHENG_PROJECT_ROOT
    2. 自动检测（查找 CLAUDE.md）
    """
    if "DASHENG_PROJECT_ROOT" in os.environ:
        return Path(os.environ["DASHENG_PROJECT_ROOT"])

    # 自动检测项目根目录
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / 'CLAUDE.md').exists():
            return parent

    # Fallback（不应该到达这里）
    raise RuntimeError("Cannot detect project root: CLAUDE.md not found")


def get_desktop_root() -> Path:
    """获取桌面交付目录"""
    default = Path.home() / "Desktop" / "自媒体创作"
    return Path(os.getenv("DASHENG_DESKTOP_ROOT", str(default)))


def get_feishu_config_path() -> Path:
    """获取飞书API配置文件路径"""
    default = Path.home() / "clawd" / "configs" / "feishu_api.conf"
    return Path(os.getenv("DASHENG_FEISHU_CONFIG", str(default)))


def get_feishu_bot_config_path() -> Path:
    """获取飞书Bot配置文件路径"""
    root = get_project_root()
    default = root / "configs" / "feishu" / "liweis_bot_config.json"
    return Path(os.getenv("DASHENG_FEISHU_BOT_CONFIG", str(default)))


def get_feishu_stage_contract_path() -> Path:
    """获取飞书阶段审核合约路径"""
    root = get_project_root()
    default = root / "configs" / "feishu" / "stage_review_contract.json"
    return Path(os.getenv("DASHENG_FEISHU_STAGE_CONTRACT", str(default)))


def get_output_root(stage: str) -> Path:
    """获取指定阶段的输出根目录"""
    root = get_project_root()
    stage_dirs = {
        "intake": "01_内容采集",
        "brief": "02_Brief",
        "draft": "03_初稿生成",
        "material": "04_素材收集",
        "rewrite": "06_改写",
        "publish": "07_渠道分发",
        "postmortem": "08_分析复盘"
    }
    stage_dir = stage_dirs.get(stage, stage)
    return root / "产物" / stage_dir


def get_templates_dir() -> Path:
    """获取模板目录"""
    root = get_project_root()
    return root / "skills" / "dasheng-media-rewrite-v2" / "templates"


def get_skills_dir() -> Path:
    """获取skills目录"""
    root = get_project_root()
    return root / "skills"


def get_scripts_dir() -> Path:
    """获取scripts目录"""
    root = get_project_root()
    return root / "scripts"


def get_engine_dir() -> Path:
    """获取引擎目录"""
    root = get_project_root()
    return root / "引擎"


def get_dna_config_path() -> Path:
    """获取DNA配置文件路径"""
    root = get_project_root()
    return root / "dna" / "dna_config.yaml"


# 环境变量说明
ENV_VARS_HELP = """
Path Configuration Environment Variables:

Core Paths:
  DASHENG_PROJECT_ROOT          - 项目根目录 (default: auto-detect via CLAUDE.md)
  DASHENG_DESKTOP_ROOT          - 桌面交付目录 (default: ~/Desktop/自媒体创作)

Feishu Configuration:
  DASHENG_FEISHU_CONFIG         - 飞书API配置 (default: ~/clawd/configs/feishu_api.conf)
  DASHENG_FEISHU_BOT_CONFIG     - 飞书Bot配置 (default: {PROJECT_ROOT}/configs/feishu/liweis_bot_config.json)
  DASHENG_FEISHU_STAGE_CONTRACT - 飞书阶段合约 (default: {PROJECT_ROOT}/configs/feishu/stage_review_contract.json)

Usage:
  export DASHENG_PROJECT_ROOT=/path/to/project
  python3 scripts/workflow_doctor.py

Note: This module is deprecated. Use core.path_resolver instead.
"""


if __name__ == "__main__":
    print("Current Path Configuration:")
    print(f"  Project Root: {get_project_root()}")
    print(f"  Desktop Root: {get_desktop_root()}")
    print(f"  Feishu Config: {get_feishu_config_path()}")
    print(f"  Feishu Bot Config: {get_feishu_bot_config_path()}")
    print(f"  Feishu Stage Contract: {get_feishu_stage_contract_path()}")
    print(f"  Templates Dir: {get_templates_dir()}")
    print(f"  Skills Dir: {get_skills_dir()}")
    print(f"  DNA Config: {get_dna_config_path()}")
    print()
    print(ENV_VARS_HELP)
