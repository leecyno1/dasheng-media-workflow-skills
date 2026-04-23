---
name: dasheng-daily-material
description: Use when the workflow is in the 第04环节 material stage and a concrete execution module is needed to read the final article, let AI decide required assets, and build charts, visuals, source packs, and asset files.
---

# dasheng-daily-material

## 状态

`internal module / Material 执行层`

## 当前定位

这是当前主链中应保留的内部执行模块之一。

它不是总控入口，而是 `material` 阶段的落地层。

当前优先上游为：

- `draft_manifest.json`
- `final_structure_snapshot.json`
- 终稿正文 `doc_file`
- `03_ReasoningSheet_<topic>.json`

## 上游与下游

- 上游：`draft / final structure`
- 本阶段：`material`
- 下游：`rewrite`

总控入口始终是：

- `../dasheng-media-sop/SKILL.md`

## 标准职责

- 优先先读终稿正文，再由 AI 判断哪些段落真正需要图表、图片、新闻截图、视频、漫画或信息图
- 组织真实来源、下载素材和生成图表
- 形成 `Material Pack` 和素材清单
- 不改主判断，不重写正文
- 所有资产尽量绑定 `claim_id / section_id / usage_type / relevance_score / editor_status`

## 已集成的 OpenClaw 能力栈

- 检索证据：`news-radar`、`web-search`、`multi-search-engine`、`tavily-search`、`reddit`、`twitter`、`google-trends`
- 中文内容抽取：`wechat-search`、`wechat-article-extractor-skill`、`xiaohongshu-extract`
- 视觉生成：`baoyu-article-illustrator`、`baoyu-comic`、`baoyu-cover-image`、`baoyu-infographic`、`baoyu-xhs-images`、`baoyu-image-gen`、`ai-image-generation`
- 视频辅助：`media-downloader`、`video-download`、`video-frames`、`video-subtitles`、`bilibili-youtube-watcher`
- 动效补充：`remotion`、`remotion-video`、`remotion-video-toolkit`

这些能力不会替代主链判断，而是以 `material_skill_stack` 的形式固化到 `material_manifest.json`。

## 标准交付

- `04_MaterialPack.md`
- `04_Material_报告.md`
- `material_manifest.json`
- `material_acceptance.json`
- `pack_assets/<topic>/...`
- `material_manifest.json.material_skill_stack`

## 执行入口

- 推荐：`python3 ../../scripts/material_execute_pack.py --draft-manifest <draft_manifest.json> --rebuild-material-plan`
- 并行：`python3 ../../scripts/material_parallel_launcher.py --draft-manifest <draft_manifest.json>`
- 复跑：`python3 ../../scripts/material_parallel_launcher.py --material-manifest <material_manifest.json> --topics <topic-1 topic-2>`
- 如需强制重建素材规划：`python3 ../../scripts/material_execute_pack.py --draft-manifest <draft_manifest.json> --rebuild-material-plan`
- 主链自检：`python3 ../../scripts/workflow_doctor.py --run-id <run_id>`

## 注意

- 正式主链已禁用 `--pack-root` 和旧目录猜测。
- 本阶段只能从 canonical `draft_manifest.json` 或 `material_manifest.json` 衔接。
- 如果用户说“从头开始”“继续下一阶段”或“跑整条创作流”，不要直接从本 skill 起步，应回到总控 skill。
