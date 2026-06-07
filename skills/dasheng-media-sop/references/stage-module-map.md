# 5 阶段主链 -> 模块映射表

更新时间：`2026-04-01`

## 主映射

### 可选前置能力

| 能力 | 对外语义 | 当前主入口 | 内部模块 / 脚本 | 交付接口 |
| --- | --- | --- | --- | --- |
| `paradigm-learning` | 从标准文章/模板学习文章范式 | `dasheng-paradigm-profiler` | `引擎/03_全链路SOP工作流/00_范式学习_prompt.md`、`skills/dasheng-paradigm-profiler` | `00_范式画像.md` / `paradigm_profile.yaml` / `paradigm_prompt_block.md` / `paradigm_manifest.json` |

说明：`paradigm-learning` 不是正式主链阶段，不改变 `intake -> brief -> draft -> publish -> postmortem`。它是可选资产生成器，默认在 `brief` 前运行，也可在 `draft / publish` 临时触发。

| 阶段 | 对外语义 | 当前主入口 | 内部模块 / 脚本 | 交付接口 |
| --- | --- | --- | --- | --- |
| `intake` | 内容采集 | `dasheng-media-sop` | `dasheng-daily-intake`、`scripts/` 下采集脚本 | `01_内容采集_底稿.md` / `01_内容采集_报告.md` / `intake_manifest.json` |
| `brief` | AI-only 编辑题池 | `dasheng-media-sop` | `dasheng-daily-phase2`、`scripts/phase2_rebuilder.py` | `02_编辑Brief库.md` / `02_研究Brief库.md` / `02_编辑Brief_报告.md` / `brief_manifest.json` |
| `draft` | 可审核、可发布正文底稿 | `dasheng-media-sop` | 项目级 Draft 流程、草稿模板与写作控制文件 | `03_标准初稿_<topic>.md` / `03_初稿_报告.md` / `final_structure_snapshot.json` / `draft_manifest.json` |
| `publish` | 发布编排（含按需视频补充、平台适配、执行与验真） | `dasheng-media-sop` / `dasheng-stage-publish` | `dasheng-stage-publish`、平台发布 skill 组合、`scripts/publish_video_supplement.py`、`scripts/convert_finance_motion_to_remotion.py`、`/Volumes/PSSD/Projects/finance-motion-8787`、`publish-guard` | `publish_video_supplement_report.md` / `publish_video_supplement_manifest.json` / `channel_adaptation_manifest.json` / `channel_execution_manifest.json` / `publish_verification_report.json` / `07_发布包.md` / `07_发布计划.md` / `publish_manifest.json` |
| `postmortem` | 复盘回写 | `dasheng-media-sop` | `dasheng-daily-postmortem` | `08_复盘报告.md` / `08_L1回写建议.md` / `postmortem_manifest.json` |

## 按需工具

| 工具 | 对外语义 | 当前入口 | 交付接口 |
| --- | --- | --- | --- |
| `material-refill` | 补图表、封面、图片、视频素材 | `dasheng-daily-material` / `dasheng-stage-material-refill` | `material_plan.json` / `material_manifest.json` / 素材目录 |
| `rewrite-variants` | 额外多版本改写 | `dasheng-stage-rewrite-v3` | `rewrite_manifest.json` / per-topic variant files |

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
4. `material` / `rewrite` 只能作为按需工具出现，不得重新变成主链 gate。

## 已退出主链的旧模块

- `dasheng-daily-outline`
- `dasheng-daily-final`

说明：

- `dasheng-daily-draft` 已恢复为主链 Draft 单阶段执行器，旧 outline/final 不再作为正式入口暴露。

## 已归档的旧模块

- `dasheng-caiji`
- `dasheng-clustering`
- `dasheng-xuanti`
- `dasheng-xuanti-skill`
- `dasheng-intake-brief-prod`
- `dasheng-brief-builder`
