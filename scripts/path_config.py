#!/usr/bin/env python3
"""
Path Configuration Module
统一管理所有硬编码路径，支持环境变量覆盖

COMPATIBILITY WRAPPER: get_project_root 已委托给 core.path_resolver，
以消除项目根目录检测逻辑的重复。本模块保留其他历史辅助函数以兼容现有脚本。
新代码建议直接使用 core.path_resolver。
"""

import os
import sys
from pathlib import Path

# 将项目根目录加入路径以导入 core.path_resolver（当从 scripts/ 运行时）
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from core.path_resolver import PathResolver


def get_project_root() -> Path:
    """
    获取项目根目录

    基于 core.path_resolver.PathResolver，但优先尊重 DASHENG_PROJECT_ROOT 环境变量，
    并在环境变量变化时重新解析，避免单例缓存导致测试失败。
    优先级：
    1. 环境变量 DASHENG_PROJECT_ROOT
    2. 自动检测（查找 CLAUDE.md）
    """
    env_root = os.environ.get("DASHENG_PROJECT_ROOT")
    if env_root:
        return Path(env_root).expanduser()
    return PathResolver().get_project_root()


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
    """获取指定阶段的输出根目录

    默认输出到 ~/Desktop/自媒体创作/，避免产物堆积在项目目录下。
    可通过 DASHENG_OUTPUT_ROOT 环境变量覆盖。
    """
    output_base = Path(os.getenv("DASHENG_OUTPUT_ROOT", str(Path.home() / "Desktop" / "自媒体创作")))
    stage_dirs = {
        "intake": "01_内容采集",
        "brief": "02_内容聚合及选题分析",
        "draft": "05_初稿生成",
        "transwrite": "06_转写生产",
        "publish": "07_发布执行",
        "postmortem": "08_分析复盘",
        "paradigm": "00_范式学习",
        "rewrite": "06_改写",
        "hotspot": "00_热点捕捉",
    }
    stage_dir = stage_dirs.get(stage, stage)
    return output_base / stage_dir


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
  DASHENG_OUTPUT_ROOT           - 产物输出根目录 (default: ~/Desktop/自媒体创作)

Feishu Configuration:
  DASHENG_FEISHU_CONFIG         - 飞书API配置 (default: ~/clawd/configs/feishu_api.conf)
  DASHENG_FEISHU_BOT_CONFIG     - 飞书Bot配置 (default: {PROJECT_ROOT}/configs/feishu/liweis_bot_config.json)
  DASHENG_FEISHU_STAGE_CONTRACT - 飞书阶段合约 (default: {PROJECT_ROOT}/configs/feishu/stage_review_contract.json)

Usage:
  export DASHENG_PROJECT_ROOT=/path/to/project
  python3 scripts/workflow_doctor.py

Note: get_project_root now delegates to core.path_resolver. Prefer core.path_resolver for new code.
"""


if __name__ == "__main__":
    print("Current Path Configuration:")
    print(f"  Project Root: {get_project_root()}")
    print(f"  Desktop Root: {get_desktop_root()}")
    print(f"  Output Root (intake): {get_output_root('intake')}")
    print(f"  Output Root (publish): {get_output_root('publish')}")
    print(f"  Feishu Config: {get_feishu_config_path()}")
    print(f"  Feishu Bot Config: {get_feishu_bot_config_path()}")
    print(f"  Feishu Stage Contract: {get_feishu_stage_contract_path()}")
    print(f"  Templates Dir: {get_templates_dir()}")
    print(f"  Skills Dir: {get_skills_dir()}")
    print(f"  DNA Config: {get_dna_config_path()}")
    print()
    print(ENV_VARS_HELP)
    print(f"  Feishu Bot Config: {get_feishu_bot_config_path()}")
    print(f"  Feishu Stage Contract: {get_feishu_stage_contract_path()}")
    print(f"  Templates Dir: {get_templates_dir()}")
    print(f"  Skills Dir: {get_skills_dir()}")
    print(f"  DNA Config: {get_dna_config_path()}")
    print()
    print(ENV_VARS_HELP)
    print(f"  Feishu Bot Config: {get_feishu_bot_config_path()}")
    print(f"  Feishu Stage Contract: {get_feishu_stage_contract_path()}")
    print(f"  Templates Dir: {get_templates_dir()}")
    print(f"  Skills Dir: {get_skills_dir()}")
    print(f"  DNA Config: {get_dna_config_path()}")
    print()
    print(ENV_VARS_HELP)
