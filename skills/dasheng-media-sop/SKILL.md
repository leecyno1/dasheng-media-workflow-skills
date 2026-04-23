---
name: dasheng-media-sop
description: Use when running, resuming, auditing, or updating the Dasheng self-media workflow in this repo. This is the only formal orchestration entry and it governs the 7-stage canonical chain.
---

# dasheng-media-sop

## 定位

这是本仓库唯一正式总控 skill。

唯一正式主仓：`{DASHENG_ROOT}`（环境变量，默认为本仓库根目录）

唯一正式主链：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

`distribute` 不再单列为正式阶段；平台适配与分发动作并入 `publish`。

## 何时使用

- 从头开始跑当天创作流
- 继续下一阶段
- 审核某一阶段是否能进入下游
- 收口或更新 workflow / skill / SOP
- 检查某次 run 是否符合 canonical stage contract

## 统一规则

- 只允许 canonical manifest + gate 文件驱动阶段切换。
- 禁止通过"最新目录""旧命名习惯""历史 skill 别名"猜阶段。
- 每个选题独立目录、独立文档、独立素材、独立改写包。
- 文档只是交付视图，不是唯一状态源；状态源以本地 manifest + gate 为准。
- 阶段 1-3 不写平台腔，不写终稿口吻，不把内部流程统计当正文论据。
- `material` 只围绕终稿和 claim 补证据，不重写主判断。
- `rewrite` 必须继承终稿结构，不得脱离终稿重新写一篇。
- `publish` 负责 `Channel Gate -> Video Supplement -> Channel Adaptation -> Channel Execution -> Publish Guard` 五层闭环。
- 所有发布动作都必须绑定正式平台执行 skill，不允许把"生成了文案/视频"误报为"已发布"。

## 阶段路由

- `intake` → `dasheng-daily-intake` → `scripts/run_stage1_intake.py`
- `brief` → `dasheng-daily-phase2` → `scripts/phase2_rebuilder.py`
- `draft` → Draft 主链脚本 / Prompt / gate
- `material` → `dasheng-daily-material` → `scripts/material_execute_pack.py`
- `rewrite` → `scripts/rewrite_rerun_with_final_structure.py`
- `publish` → `dasheng-stage-publish` → `scripts/publish_video_supplement.py` + 平台发布 skill 组合
- `postmortem` → `dasheng-daily-postmortem` → `scripts/postmortem_writeback.py`

## 全链路CLI

- 诊断：`python3 scripts/workflow_doctor.py --latest`
- 统一 CLI：`python3 scripts/run_mainline_stage.py`
- 分阶段：`scripts/run_mainline_stage.py <stage> --run-id <run_id>`

## 参考文档

- 阶段契约：`docs/STAGE_INTERFACES.md`
- 阶段地图：`skills/dasheng-media-sop/references/stage-map.md`
- 模块映射：`skills/dasheng-media-sop/references/stage-module-map.md`
- 交付接口：`skills/dasheng-media-sop/references/file-contracts.md`
- Publish 架构：`skills/dasheng-media-sop/references/publish-architecture.md`
- Material 技能矩阵：`skills/dasheng-media-sop/references/material-skill-matrix.md`
- Publish 技能矩阵：`skills/dasheng-media-sop/references/publish-skill-matrix.md`
- 迁移表：`skills/dasheng-media-sop/references/legacy-migration-map.md`

## OpenClaw 能力集成

| 平台 | Skill | 来源 |
|------|-------|------|
| 微信公众号 | wechat-multi-publisher | OpenClaw |
| 小红书 | xiaohongshu-auto | OpenClaw |
| 抖音 | douyin-upload-skill | OpenClaw |
| 微博 | baoyu-post-to-weibo | OpenClaw |

## 运行时目录结构

```
{DASHENG_ROOT}/
├── scripts/          # 所有阶段脚本
├── skills/           # 所有技能包
├── 产物/             # 运行产物
│   ├── 01_内容采集/
│   ├── 02_内容聚合及选题分析/
│   ├── 03_内容写作/
│   ├── 04_素材准备/
│   ├── 05_多版本改写/
│   ├── 06_内容发布/
│   └── 07_复盘/
└── 引擎/             # SOP文档与规范
```

## 安装与配置

详见 `docs/INSTALLATION.md` 或执行安装脚本 `bash scripts/install.sh`。

环境变量：
- `DASHENG_ROOT`：项目根目录（默认自动检测）
- `DASHENG_OUTPUT_DIR`：产物输出目录（默认 `{DASHENG_ROOT}/产物`）
- `DASHENG_WORLDMONITOR_ROOT`：WorldMonitor项目目录（可选）
- `DASHENG_FINANCE_MOTION_ROOT`：Finance Motion项目目录（可选）