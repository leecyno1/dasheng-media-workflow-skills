# 7 阶段主链 -> 模块映射表

更新时间：`2026-04-01`

## 主映射

| 阶段 | 对外语义 | 当前主入口 | 内部模块 / 脚本 | 交付接口 |
| --- | --- | --- | --- | --- |
| `intake` | 内容采集 | `dasheng-media-sop` | `dasheng-daily-intake`、`scripts/` 下采集脚本 | `01_内容采集_底稿.md` / `01_内容采集_报告.md` / `intake_manifest.json` |
| `brief` | AI-only 编辑题池 | `dasheng-media-sop` | `dasheng-daily-phase2`、`scripts/phase2_rebuilder.py` | `02_编辑Brief库.md` / `02_研究Brief库.md` / `02_编辑Brief_报告.md` / `brief_manifest.json` |
| `draft` | 标准初稿 | `dasheng-media-sop` | 项目级 Draft 流程、草稿模板与写作控制文件 | `03_标准初稿_<topic>.md` / `03_初稿_报告.md` / `draft_manifest.json` |
| `material` | 素材与补素材 | `dasheng-media-sop` | `dasheng-daily-material`、`scripts/material_*`、OpenClaw `material_skill_stack` | `04_MaterialPack.md` / `04_Material_报告.md` / `material_manifest.json` |
| `rewrite` | 每题 4 版改写 + 飞书推送 | `dasheng-media-sop` | `引擎/00_控制中心/rewrite_*`、DNA 配置、渠道包、`scripts/feishu_rewrite_push.js` | `topic*/rewrite_bundle.md` / `topic*/*.md` / `meta.json` / `rewrite_manifest.json` |
| `publish` | 发布编排（含视频补充、平台适配、执行与验真） | `dasheng-media-sop` / `dasheng-stage-publish` | `dasheng-stage-publish`、平台发布 skill 组合、`scripts/publish_video_supplement.py`、`scripts/convert_finance_motion_to_remotion.py`、`/Volumes/PSSD/Projects/finance-motion-8787`、`publish-guard` | `publish_video_supplement_report.md` / `publish_video_supplement_manifest.json` / `channel_adaptation_manifest.json` / `channel_execution_manifest.json` / `publish_verification_report.json` / `07_发布包.md` / `07_发布计划.md` / `publish_manifest.json` |
| `postmortem` | 复盘回写 | `dasheng-media-sop` | `dasheng-daily-postmortem` | `08_复盘报告.md` / `08_L1回写建议.md` / `postmortem_manifest.json` |

## 入口原则

1. 对外只记一个入口：`dasheng-media-sop`
2. 旧 `dasheng-daily-*` 只分为三类：
   - `internal module`
   - `historical module`
   - `legacy`
3. 任何阶段调整，先改：
   - 总控 skill
   - 本映射表
   - `STAGE_INTERFACES.md`
   - 对应技能矩阵（如 `material-skill-matrix.md` / `publish-skill-matrix.md`）
4. `material` 在 `rewrite` 之前，`rewrite` 一律基于回填后终稿。

## 已退出主链的旧模块

- `dasheng-daily-outline`
- `dasheng-daily-final`
- `dasheng-daily-draft`

说明：

- `dasheng-daily-draft` 仍可用于查阅历史产物，但不再作为任何正式入口暴露。

## 已归档的旧模块

- `dasheng-caiji`
- `dasheng-clustering`
- `dasheng-xuanti`
- `dasheng-xuanti-skill`
- `dasheng-intake-brief-prod`
- `dasheng-brief-builder`
