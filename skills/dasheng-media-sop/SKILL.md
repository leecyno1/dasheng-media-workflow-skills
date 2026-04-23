---
name: dasheng-media-sop
description: Use when running, resuming, auditing, or updating the Dasheng self-media workflow in this repo. This is the only formal orchestration entry and it governs the 7-stage canonical chain.
---

# dasheng-media-sop

## 定位

这是本仓库唯一正式总控 skill。

唯一正式主仓：

- `/Volumes/PSSD/Projects/公众号文章`

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
- 禁止通过“最新目录”“旧命名习惯”“历史 skill 别名”猜阶段。
- 每个选题独立目录、独立文档、独立素材、独立改写包。
- 文档只是交付视图，不是唯一状态源；状态源以本地 manifest + gate 为准。
- 阶段 1-3 不写平台腔，不写终稿口吻，不把内部流程统计当正文论据。
- `material` 只围绕终稿和 claim 补证据，不重写主判断。
- `rewrite` 必须继承终稿结构，不得脱离终稿重新写一篇。
- `publish` 负责 `Channel Gate -> Video Supplement -> Channel Adaptation -> Channel Execution -> Publish Guard` 五层闭环。
- 所有发布动作都必须绑定正式平台执行 skill，不允许把“生成了文案/视频”误报为“已发布”。

## 阶段路由

- `intake` → `dasheng-daily-intake` → `scripts/run_stage1_intake.py`
- `brief` → `dasheng-daily-phase2` → `scripts/phase2_rebuilder.py`
- `draft` → Draft 主链脚本 / Prompt / gate
- `material` → `dasheng-daily-material` → `scripts/material_execute_pack.py`
- `rewrite` → `scripts/rewrite_rerun_with_final_structure.py`
- `publish` → `dasheng-stage-publish` → `scripts/publish_video_supplement.py` + 平台发布 skill 组合
- `postmortem` → `dasheng-daily-postmortem` → `scripts/postmortem_writeback.py`

## Gate 硬门禁

- `brief` 结束后必须有 `selected_topics.json`
- `draft` 结束后必须有 `final_structure_snapshot.json`
- `material` 结束后必须有 `material_acceptance.json`
- `publish` 前必须有 `publish_decision.json`
- 任一 gate 未通过，禁止进入下一阶段

## Intake 新口径

- 公众号源正式切换到 `8000 public wechat`，不再依赖旧 `8001` 登录态链路作为正式入口
- Stage 1 额外维护一条 `AI热点` 汇总通道：
  - `Reddit RSS`
  - `Hacker News`
  - `B站 AI 相关样本`
- `AI热点` 固定沉淀 `10` 条并输出到 `ai_hot_topics.json`
- 这条通道在 `event_clusters` 和 `brief_input` 中享有更高权重，但不覆盖原始底稿

## Brief 口径

- 正式实现：`dasheng-daily-phase2`
- 正式模式：`ai_only`
- 正式输出：8-10 个平铺独立题卡
- 不再保留“规则主导 + AI 润色”的旧口径
- 导出包中的 `dasheng-stage-brief-ai` 已吸收到本地 Stage 2 规范，不再作为独立正式入口

## Publish 口径

- `publish` 内部包含：
  - `Publish Gate`
  - `Video Supplement`
  - `Channel Adaptation`
  - `Channel Execution`
  - `Publish Guard`
- 当前正式集成的发布 skill 角色：
  - 公众号：`baoyu-post-to-wechat`（主执行）、`wechat-multi-publisher`（批量草稿）、`md2wechat`（预处理/封面/预览）
  - 微博：`weibo-manager`（短帖审批流主执行）、`baoyu-post-to-weibo`（头条文章/浏览器半自动）
  - X：`baoyu-post-to-x`
  - 小红书：`xiaohongshu-auto`（来源：`/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/xiaohongshu-auto/SKILL.md`）
  - 抖音：`douyin-upload-skill`（来源：`/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/douyin-upload-skill/SKILL.md`）
  - B站：当前无正式投稿执行器；`bilibili-youtube-watcher` 仅作研究辅助，不算发布器
  - 发布验真：`publish-guard`
- `dasheng-stage-distribute` 的平台知识已并入当前 `publish`；旧 distribute 不再是正式阶段。
- 若某平台缺少正式执行器，例如当前 `视频号` 与 `B站`，只允许输出渠道包与待人工发布清单，不得伪装成“已发布”。

## Material 口径

- `material` 阶段已正式吸收一组 OpenClaw 能力栈，按角色使用：
  - 证据与热点：`news-radar`、`web-search`、`multi-search-engine`、`tavily-search`、`reddit`、`twitter`、`google-trends`、`wechat-search`、`wechat-article-extractor-skill`、`xiaohongshu-extract`
  - 图片与信息图：`baoyu-article-illustrator`、`baoyu-comic`、`baoyu-cover-image`、`baoyu-infographic`、`baoyu-xhs-images`、`baoyu-image-gen`、`ai-image-generation`
  - 视频与媒体：`media-downloader`、`video-download`、`video-frames`、`video-subtitles`、`bilibili-youtube-watcher`
  - 动效补充：`remotion`、`remotion-video`、`remotion-video-toolkit`
- 当前项目已将这组能力沉淀为 `material_skill_stack`，写入 `material_manifest.json`，供后续 `rewrite / publish / audit` 复用。
- `material` 仍坚持一个原则：AI 先读终稿与 claim，再决定需要调用哪类能力，不做“固定素材模板套用”。

## 每日首跑自检

首次运行当天任务前，先检查：

- `引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
- `skills/dasheng-media-sop/references/stage-contract.md`
- 当前阶段所需上游 manifest / gate 是否齐全
- `python3 /Volumes/PSSD/Projects/公众号文章/scripts/workflow_doctor.py --latest`

## 主链命令入口

- 统一 CLI：`python3 /Volumes/PSSD/Projects/公众号文章/scripts/run_mainline_stage.py`
- 常用：
  - `... intake --run-id <run_id>`
  - `... brief --run-id <run_id>`
  - `... draft --run-id <run_id>`
  - `... material --run-id <run_id>`
  - `... rewrite --run-id <run_id> --source-root <source_root>`
  - `... publish --run-id <run_id>`
  - `... postmortem --run-id <run_id>`
  - `... doctor --run-id <run_id>`

## 引用文件

- 阶段契约：`/Volumes/PSSD/Projects/公众号文章/引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
- 阶段地图：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/stage-map.md`
- 模块映射：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/stage-module-map.md`
- 交付接口：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/file-contracts.md`
- Publish 架构：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/publish-architecture.md`
- Material 技能矩阵：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/material-skill-matrix.md`
- Publish 技能矩阵：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/publish-skill-matrix.md`
- 迁移表：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/legacy-migration-map.md`
