---
agent: cx
status: active
updated_at: 2026-05-31 22:57
task: 范式学习能力与主线契约收口
mode: manual
---

# Handoff

## Goal

统一 Dasheng 媒体工作流的正式 7 阶段主链、可选 ParadigmProfile 资产、导出包和交接上下文，避免后续代理继续按旧 8 阶段/distribute 口径执行。

## Done

- 新增测试锁定：导出包必须包含 `dasheng-paradigm-profiler`，doctor 的正式 stages 不包含 `paradigm`。
- 拆分 `CANONICAL_STAGE_ROOTS` 与 `OPTIONAL_ASSET_ROOTS`，`paradigm` 改为 optional asset。
- `build_paradigm_profile.py` 改用 optional asset 目录。
- `workflow_doctor.py` 报告 `optional_assets`，但主链 contract 只包含正式阶段。
- `export_skill_suite.py` 已导出 `dasheng-paradigm-profiler`。
- `CLAUDE.md` 与 `skills/SKILL_ALIASES.md` 已更新为 7 阶段 + 可选范式学习口径。
- `run_mainline_stage.py` 已支持可选 `paradigm` 命令入口，并转发到 `build_paradigm_profile.py`。
- 文档已补充 `ParadigmProfile` 与 `Style DNA` 的边界、默认路径和下游注入规则。
- 全量测试已通过：`python3 -m pytest tests -q` -> `129 passed, 2 skipped in 2.14s`。
- 导出烟测已通过：`python3 scripts/export_skill_suite.py --target-dir /private/tmp/dasheng-export-check-codex`。
- 导出包关键文件已验证存在：`EXPORT_MANIFEST.json`、`scripts/run_mainline_stage.py`、`skills/dasheng-paradigm-profiler/SKILL.md`。
- 导出 manifest 已验证 `formal_skills` 包含 `dasheng-paradigm-profiler`。

## In Progress

- 当前相关改动已整理为可提交变更集；无关 `outputs/` 保持未暂存。

## Changed Files

- `CLAUDE.md`
- `docs/STAGE_INTERFACES.md`
- `scripts/canonical_workflow.py`
- `scripts/build_paradigm_profile.py`
- `scripts/run_mainline_stage.py`
- `scripts/workflow_doctor.py`
- `scripts/export_skill_suite.py`
- `skills/dasheng-paradigm-profiler/`
- `skills/dasheng-media-sop/SKILL.md`
- `skills/dasheng-media-sop/references/stage-module-map.md`
- `skills/SKILL_ALIASES.md`
- `tests/test_export_skill_suite.py`
- `tests/test_mainline_hardening.py`
- `tests/test_paradigm_profile.py`
- `tests/test_workflow_doctor.py`
- `引擎/03_全链路SOP工作流/00_范式学习_prompt.md`
- `引擎/03_全链路SOP工作流/OBJECT_MODEL.md`
- `引擎/03_全链路SOP工作流/README.md`
- `引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
- `.jiebang/runtime/current-task.md`
- `.jiebang/runtime/handoffs/cx.md`

## Risks

- 未做真实 OpenClaw/Hermes 安装验证。
- `outputs/` 是无关未跟踪目录，本次不应纳入提交。

## Next Step

如需继续真实环境验证，下一步是在 OpenClaw/Hermes 中安装导出包并跑一轮端到端试用。
