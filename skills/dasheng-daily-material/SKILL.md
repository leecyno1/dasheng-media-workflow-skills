---
name: dasheng-daily-material
description: Use only as an optional material-refill tool when a draft or publish package needs charts, visuals, source packs, images, or video assets. It is no longer a formal mainline stage.
---

# dasheng-daily-material

## 状态

`optional tool / Material Refill 执行层`

## 当前定位

这是已从主链退出的按需素材补充工具。

它不是总控入口，也不是正式阶段；只有在 Draft / Publish 明确缺少素材、封面、图表或视频时才调用。

当前优先上游为：

- `draft_manifest.json`
- `final_structure_snapshot.json`
- 终稿正文 `doc_file`
- `03_ReasoningSheet_<topic>.json`

## 上游与下游

- 上游：`draft / final structure`
- 本工具：`material-refill`
- 下游：回到 `draft` 或 `publish`

总控入口始终是：

- `../dasheng-media-sop/SKILL.md`

## 标准职责

- 优先先读终稿正文、`ReasoningSheet` 与 `brief_context`，生成 `material_plan.json`
- `material_plan` 是 Claim-driven 素材任务单，每个任务都必须说明服务哪条 `claim_id`
- 由当前 Agent/本地 Planner 基于上游材料判断哪些段落真正需要图表、图片、新闻截图、视频、漫画或信息图
- 组织真实来源、下载素材和生成图表
- 形成 `Material Pack` 和素材清单
- 不改主判断，不重写正文
- 所有资产必须绑定 `claim_id / section_id / usage_type / relevance_score / editor_status`
- 泛概念图、装饰性图片、无法说明支撑论点的素材不进入主计划
- 图片/视频搜索优先追求召回质量与可用性，版权不作为当前 Material Gate 的主要拦截项
- 搜索计划、候选、下载 manifest 统一收进 `config/`；真实图片、视频素材直接平铺在 topic 根目录
- 本阶段没有独立 `Material AI provider`；不要在 Material 内再配置大模型判断层

## 已集成的 OpenClaw 能力栈

- 检索证据：`news-radar`、`web-search`、`multi-search-engine`、`tavily-search`、`reddit`、`twitter`、`google-trends`
- 中文内容抽取：`wechat-search`、`wechat-article-extractor-skill`、`xiaohongshu-extract`
- 视觉生成：`baoyu-article-illustrator`、`baoyu-comic`、`baoyu-cover-image`、`baoyu-infographic`、`baoyu-xhs-images`、`baoyu-image-gen`、`ai-image-generation`
- 视频辅助：`media-downloader`、`video-download`、`video-frames`、`video-subtitles`、`bilibili-youtube-watcher`
- 动效补充：`remotion`、`remotion-video`、`remotion-video-toolkit`

这些能力不会替代主链判断，而是以 `material_skill_stack` 的形式固化到 `material_manifest.json`，供按需追踪。

## 标准交付

- `04_MaterialPack.md`
- `04_Material_报告.md`
- `material_plan.json`
- `material_manifest.json`
- `material_acceptance.json`
- `pack_assets/<topic>/...`
- `material_manifest.json.material_skill_stack`

每个 `pack_assets/<topic>/` 根目录必须同时满足：

- 有 `素材交付清单.md` / `素材交付清单.json`
- 可直接使用的图片、视频、图表平铺在根目录，文件名前缀分别为 `图片_`、`视频_`、`图表_`
- `config/` 只保存计划、候选、下载日志、失败诊断，不作为编辑验收入口
- provider 子目录、下载缓存、`generation_results.json` 里的文件不算交付；必须先提升到 topic 根目录或写入缺口清单

## Claim-driven 素材计划

每个 `material_plan` 条目至少包含：

- `plan_id`
- `claim_id`
- `section_id`
- `asset_type`
- `usage_type`
- `need`
- `source_queries`
- `expected_outputs`
- `relevance_score`
- `editor_status`
- `source_quality`

推荐映射：

- `chart_need` 或数据型 `missing_proof`：生成 `evidence_chart`
- 周期、城市、国家、市场之间的比较：生成 `comparison_chart`
- `question_units`：生成 `logic_diagram`
- `opinion_units`：生成 `source_screenshot` 或证据核对任务
- `case_units`：生成 `case_table`
- `solution_units`：生成 `proof_checklist`

## 图片与视频搜索

- 图片默认引擎：`duckduckgo_image,wikimedia`
- 图片引擎环境变量：`MATERIAL_IMAGE_SEARCH_ENGINES`
- 如环境变量存在，会自动追加增强搜索源：`TAVILY_API_KEY` -> `tavily_image`，`BRAVE_SEARCH_API_KEY` -> `brave_image`
- 指定 `channel=wikimedia` 时只走 Wikimedia；指定 `channel=news_screenshot` 时只走新闻截图
- 视频默认搜索：`ytsearch,ytsearchdate`
- 视频搜索环境变量：`MATERIAL_VIDEO_SEARCH_PROVIDERS`
- 如 `BRAVE_SEARCH_API_KEY` 存在，视频候选会自动追加 `brave_video`
- 视频候选会按 URL 去重，再进入质量筛选与下载
- `--video-download-limit` 表示全局下载尝试上限，不再等同于前 N 个 query
- 不在项目内保存 API Key；只读取环境变量
- `config/image_search_queries.json`、`config/news_screenshot_queries.json`、`config/video_search_queries.json` 会携带 `claim_id / section_id / plan_id`
- 下载文件名会带 Claim 前缀，例如 `图片_claim-policy_住建部_01.jpg`、`视频_claim-cycle_城市更新新闻发布会.mp4`

## 执行入口

- 推荐：`python3 ../../scripts/material_execute_pack.py --draft-manifest <draft_manifest.json> --rebuild-material-plan`
- 并行：`python3 ../../scripts/material_parallel_launcher.py --draft-manifest <draft_manifest.json>`
- 复跑：`python3 ../../scripts/material_parallel_launcher.py --material-manifest <material_manifest.json> --topics <topic-1 topic-2>`
- 如需强制重建素材规划：`python3 ../../scripts/material_execute_pack.py --draft-manifest <draft_manifest.json> --rebuild-material-plan`
- 主链自检：`python3 ../../scripts/workflow_doctor.py --run-id <run_id>`

默认执行步骤包含 `finalize`。如果手动指定 `--steps`，也必须带上 `finalize`，否则图片/视频可能只停留在内部目录，编辑在 Finder 中看不到可用素材。

## 模型策略

- 素材规划由当前 Agent 执行，依据终稿正文、`final_structure_snapshot.json`、`ReasoningSheet`、来源争议观点、图表清单。
- Material 内不读取 `MATERIAL_AI_* / QHAIGC_*`，也不提供 `MATERIAL_USE_EXTERNAL_AI` 这类二级模型开关。
- 搜索 API、图片生成服务、视频下载器只属于素材执行工具，不参与主判断。

## 注意

- 正式主链已禁用 `--pack-root` 和旧目录猜测。
- 本工具只能从 canonical `draft_manifest.json` 或历史 `material_manifest.json` 衔接。
- 如果用户说“从头开始”“继续下一阶段”或“跑整条创作流”，不要直接从本 skill 起步，应回到总控 skill。
