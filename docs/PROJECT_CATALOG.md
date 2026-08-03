# 大圣媒体工作流项目目录

> 本文件由 `scripts/build_project_catalog.py` 根据机器注册表生成，请不要手工维护列表。

更新日期：`2026-08-03`

## 总览

- 正式主链：`intake -> brief -> draft -> transwrite -> publish -> postmortem`
- 正式/按需 Skill 登记：`22`
- 已保留上游项目：`42`
- 候选储备：`4`
- 已剔除项目：`13`
- 内部功能模块：`9`

### 储备分布

| 类别 | 数量 |
| --- | ---: |
| `catalog` | 1 |
| `design` | 9 |
| `publish` | 14 |
| `render` | 2 |
| `video` | 16 |

### 级别分布

| 级别 | 数量 |
| --- | ---: |
| `account_management_console` | 1 |
| `archived_historical_fallback` | 1 |
| `backup` | 15 |
| `browser_cli_fallback` | 1 |
| `browser_session_fallback` | 1 |
| `catalog_source` | 1 |
| `experimental` | 3 |
| `preferred_local_experiment` | 1 |
| `primary_execution` | 1 |
| `production_candidate` | 14 |
| `reference` | 2 |
| `reference_only` | 1 |

## 六阶段处理流程

### 1. 内容采集 (`intake`)

- 入口：`dasheng-daily-intake` / `scripts/run_stage1_intake.py`
- 输入：网页、公众号、热点数据源、人工指定素材
- 处理：采集 -> 标准化 -> 去重 -> 聚类 -> 保留来源
- 输出：intake_manifest.json 、raw/intake_records.json 、01_内容采集_报告.md
- 门禁：无

### 2. 选题与研究 Brief (`brief`)

- 入口：`dasheng-daily-phase2` / `scripts/phase2_rebuilder.py`
- 输入：intake_manifest.json 、raw/intake_records.json
- 处理：事件归并 -> 角度分流 -> 证据缺口识别 -> 题卡排序
- 输出：brief_manifest.json 、topic_cards.json 、selected_topics.json
- 门禁：selected_topics.json

### 3. 初稿与证据底稿 (`draft`)

- 入口：`dasheng-daily-draft` / `scripts/build_stage3_draft.py`
- 输入：brief_manifest.json 、selected_topics.json
- 处理：事实底稿 -> 数据/图表 -> 长文结构 -> HTML -> 封面与插图意图
- 输出：draft_manifest.json 、final_structure_snapshot.json 、transwrite_decision.json 、每题 Markdown/HTML
- 门禁：final_structure_snapshot.json + transwrite_decision.json

### 4. 多通路转写生产 (`transwrite`)

- 入口：`dasheng-stage-transwrite` / `scripts/build_stage4_transwrite.py`
- 输入：draft_manifest.json 、final_structure_snapshot.json 、transwrite_decision.json
- 处理：公众号文章 -> 真人口播 -> 无头 HTML 视频 -> 播客包 -> 导演与渲染 QC
- 输出：transwrite_manifest.json 、lane manifests 、可发布文章/视频/音频包
- 门禁：publish_decision.json

### 5. 账号路由与发布 (`publish`)

- 入口：`dasheng-stage-publish` / `scripts/build_stage5_publish.py`
- 输入：transwrite_manifest.json 、publish_decision.json
- 处理：平台包装 -> 账号矩阵 -> 表单预检 -> 本地 API/CLI/浏览器执行 -> 回执验真
- 输出：publish_manifest.json 、channel packs 、publish_verification_report.json 、平台链接/稿件 ID
- 门禁：Publish Guard

### 6. 复盘与知识回写 (`postmortem`)

- 入口：`dasheng-daily-postmortem` / `scripts/postmortem_writeback.py`
- 输入：publish_manifest.json 、publish verification 、平台数据 、人工反馈
- 处理：效果聚合 -> 差异归因 -> 继续/停止/试验建议 -> DNA 与规则回写
- 输出：postmortem_manifest.json 、08_复盘报告.md 、08_L1回写建议.md
- 门禁：无

## 功能模块

| 模块 | 主要路径 | 职责 |
| --- | --- | --- |
| 总控与契约 | `scripts/run_mainline_stage.py`<br>`scripts/canonical_workflow.py`<br>`skills/dasheng-media-sop` | 阶段路由、manifest/gate、输出路径、失败恢复 |
| 采集、选题与写作 | `skills/dasheng-daily-intake`<br>`skills/dasheng-daily-phase2`<br>`skills/dasheng-daily-draft` | 来源池、题卡、研究底稿、文章 HTML |
| 财经数据与证据 | `skills/dasheng-finance-data`<br>`scripts/video_claim_evidence_ledger.py`<br>`scripts/video_finance_evidence.py`<br>`scripts/video_official_evidence.py` | 数据表、图表、官方文档、命题-证据台账 |
| 视频导演与分镜 | `skills/dasheng-video-director`<br>`configs/video/pipelines`<br>`scripts/dasheng_video_director.py` | 口播节奏、分镜、构图、真实 B-roll、工具路由 |
| 动画与渲染 | `skills/dasheng-html-video-bridge`<br>`skills/dasheng-caption-motion`<br>`scripts/build_remotion_renderer_pack.py` | HTML Video、Remotion、HyperFrames、GSAP/Lottie、字幕与动态图表 |
| 剪辑与媒体处理 | `skills/dasheng-video-roughcut`<br>`skills/dasheng-ffmpeg-toolkit`<br>`skills/dasheng-video-editing-bridge` | ASR、粗剪、EDL、FFmpeg、媒体 QC |
| 发布与账号中心 | `skills/dasheng-stage-publish`<br>`configs/publish`<br>`scripts/start_publish_console.py` | 多账号、多平台、封面/标签/声明、发布队列、链接回收 |
| 范式学习与进化 | `skills/dasheng-paradigm-profiler`<br>`skills/dasheng-video-style-trainer`<br>`skills/dasheng-video-self-learning` | 文章范式、视频 DNA、每日增量学习、导演笔记 |
| 质量门禁与治理 | `tests`<br>`scripts/workflow_doctor.py`<br>`scripts/video_render_qc.py`<br>`scripts/publish_guard.py` | 契约测试、渲染 QC、发布验真、仓库卫生 |

## Skill 注册表

| Skill | 版本 | 状态 | 职责 |
| --- | --- | --- | --- |
| `dasheng-media-sop` | 1.0.0 | ✅ 正式 | 总控入口，唯一正式编排 skill |
| `dasheng-paradigm-profiler` | 1.0.0 | ✅ 正式 | 可选前置资产，提炼文章结构范式 |
| `dasheng-daily-intake` | 1.0.0 | ✅ 正式 | 内容采集阶段 |
| `dasheng-daily-phase2` | 1.0.0 | ✅ 正式 | 选题分析阶段（替代 dasheng-daily-brief） |
| `dasheng-daily-draft` | 1.0.0 | ✅ 正式 | 写作与可发布底稿阶段 |
| `dasheng-stage-transwrite` | 1.0.0 | ✅ 正式 | 转写生产阶段，生成公众号/视频/播客包 |
| `dasheng-stage-publish` | 1.0.0 | ✅ 正式 | 发布执行阶段 |
| `dasheng-daily-postmortem` | 1.0.0 | ✅ 正式 | 复盘与知识回写 |
| `dasheng-finance-data` | 0.1.0 | ✅ 正式 | Draft 金融数据增强工具，生成 Chart.js 图表规格 |
| `dasheng-style-profiler` | 1.0.0 | ✅ 正式 | 文风 Style DNA 提炼 |
| `feishu-doc-creator` | 1.0.0 | ✅ 正式 | 飞书文档创建辅助 |
| `dasheng-html-video-bridge` | 0.1.0 | ✅ 正式 | 转写阶段调用本地 html-video 的口播视频桥接 skill |
| `dasheng-html-anything-bridge` | 0.1.0 | ✅ 正式 | Draft/Transwrite 调用 HTML Anything 模板和视觉语言的桥接 skill |
| `dasheng-lemon-illustrations` | 0.1.0 | ✅ 正式 | 口播视频默认概念卡通插画系统，使用柠檬人替代上游角色 |
| `dasheng-video-talking-head` | 0.1.0 | ✅ 正式 | 真人出镜口播视频导演时间轴、证据层和包装工作流 |
| `dasheng-video-explainer-html` | 0.1.0 | ✅ 正式 | HTML 文章转无真人竖版科普视频的分镜工作流 |
| `dasheng-video-broll-generator` | 0.1.0 | 🧰 按需 | B-roll、Vox 拼贴、生成式插入片段和贴纸动画的证据安全路由 |
| `dasheng-caption-motion` | 0.1.0 | 🧰 按需 | 将 SRT/词级时间戳路由为 HyperFrames 或 Remotion 字幕动效 |
| `dasheng-video-editing-bridge` | 0.1.0 | 🧰 按需 | 内部管线、剪映、chengfeng-videocut 与 video-use 的全流程剪辑路由 |
| `dasheng-ffmpeg-toolkit` | 0.1.0 | 🧰 按需 | 受控媒体探测、转码、裁剪、音频提取和图片水印工具 |
| `social-auto-upload-bridge` | 0.2.0 | ✅ 正式 | Publish 阶段调用外部 social-auto-upload，支持四平台预演、登录检查、确认执行与结果回填 |
| `bilibili-upload-bridge` | 0.1.0 | ✅ 正式 | Publish 阶段调用外部 B站上传工具的投稿桥 |

## 保留上游项目

第三方源码默认克隆到 `vendor/reserved/` 或 `vendor/publish/`，不进入主仓库 Git 历史。

| 项目 | 类别 | 级别 | 依赖状态 | 本地路径 | 上游 |
| --- | --- | --- | --- | --- | --- |
| `boutique-openclaw-skills` | `catalog` | `catalog_source` | `source_ready` | `vendor/reserved/catalog/boutique-openclaw-skills` | [upstream](https://github.com/leecyno1/boutique-openclaw-skills.git) |
| `anthropics-skills` | `design` | `production_candidate` | `skill_ready` | `vendor/reserved/design/anthropics-skills` | [upstream](https://github.com/anthropics/skills.git) |
| `baoyu-skills` | `design` | `production_candidate` | `dependency_ready_with_local_missing_package_workaround` | `vendor/reserved/design/baoyu-skills` | [upstream](https://github.com/JimLiu/baoyu-skills.git) |
| `emilkowalski-skills` | `design` | `production_candidate` | `skill_ready` | `vendor/reserved/design/emilkowalski-skills` | [upstream](https://github.com/emilkowalski/skills.git) |
| `guizang-social-card-skill` | `design` | `production_candidate` | `dependency_ready` | `vendor/reserved/design/guizang-social-card-skill` | [upstream](https://github.com/op7418/guizang-social-card-skill.git) |
| `inference-skills` | `design` | `backup` | `skill_ready_needs_model_access` | `vendor/reserved/design/inference-skills` | [upstream](https://github.com/inference-sh/skills.git) |
| `media-downloader` | `design` | `production_candidate` | `dependency_ready` | `vendor/reserved/design/media-downloader` | [upstream](https://github.com/yizhiyanhua-ai/media-downloader.git) |
| `minimax-skills` | `design` | `backup` | `skill_ready_needs_api_key` | `vendor/reserved/design/minimax-skills` | [upstream](https://github.com/MiniMax-AI/skills.git) |
| `remotion-video-toolkit` | `design` | `production_candidate` | `skill_ready` | `vendor/reserved/design/remotion-video-toolkit` | [upstream](https://github.com/shreefentsar/remotion-video-toolkit.git) |
| `taste-skill` | `design` | `production_candidate` | `skill_ready` | `vendor/reserved/design/taste-skill` | [upstream](https://github.com/Leonxlnx/taste-skill.git) |
| `agent-skills-launch-pack` | `publish` | `backup` | `cloned` | `vendor/reserved/publish/agent-skills-launch-pack` | [upstream](https://github.com/chenjin-cmd/agent-skills-launch-pack_.git) |
| `all-in-one` | `publish` | `backup` | `cloned` | `vendor/reserved/publish/all-in-one` | [upstream](https://github.com/cv-cat/All-IN-ONE.git) |
| `autoclaw-xhs-skills` | `publish` | `backup` | `cloned` | `vendor/reserved/publish/autoclaw-xhs-skills` | [upstream](https://github.com/autoclaw-cc/xiaohongshu-skills.git) |
| `biliup-rs` | `publish` | `archived_historical_fallback` | `archived_not_primary` | `vendor/reserved/publish/biliup-rs` | [upstream](https://github.com/biliup/biliup-rs.git) |
| `opencli` | `publish` | `browser_cli_fallback` | `dependencies_installed_cli_built` | `vendor/reserved/publish/opencli` | [upstream](https://github.com/jackwener/OpenCLI.git) |
| `postbot` | `publish` | `browser_session_fallback` | `extension_dependencies_installed_build_ready` | `vendor/reserved/publish/postbot` | [upstream](https://github.com/gitcoffee-os/postbot.git) |
| `postiz` | `publish` | `backup` | `cloned_server_stack_not_installed` | `vendor/reserved/publish/postiz` | [upstream](https://github.com/gitroomhq/postiz-app.git) |
| `qianfan-sync` | `publish` | `account_management_console` | `backend_frontend_and_mcp_installed` | `vendor/reserved/publish/qianfan-sync` | [upstream](https://github.com/DevilJie/social-auto-upload-web-ui.git) |
| `social-auto-upload` | `publish` | `primary_execution` | `runtime_ready_needs_named_account_login` | `vendor/publish/social-auto-upload` | [upstream](https://github.com/dreammis/social-auto-upload.git) |
| `spider-xhs` | `publish` | `backup` | `cloned` | `vendor/reserved/publish/spider-xhs` | [upstream](https://github.com/cv-cat/Spider_XHS.git) |
| `xhs-downloader` | `publish` | `backup` | `cloned_needs_login` | `vendor/reserved/publish/xhs-downloader` | [upstream](https://github.com/JoeanAmier/XHS-Downloader.git) |
| `xhs-skills` | `publish` | `backup` | `cloned` | `vendor/reserved/publish/xhs-skills` | [upstream](https://github.com/cv-cat/XhsSkills.git) |
| `xiaohongshu-mcp` | `publish` | `backup` | `cloned_needs_login` | `vendor/reserved/publish/xiaohongshu-mcp` | [upstream](https://github.com/xpzouying/xiaohongshu-mcp.git) |
| `xurl` | `publish` | `backup` | `cloned_needs_api_credentials` | `vendor/reserved/publish/xurl` | [upstream](https://github.com/xdevplatform/xurl.git) |
| `html-anything` | `render` | `production_candidate` | `dependency_ready` | `vendor/reserved/render/html-anything` | [upstream](https://github.com/nexu-io/html-anything.git) |
| `html-video` | `render` | `production_candidate` | `dependency_ready` | `vendor/reserved/render/html-video` | [upstream](https://github.com/nexu-io/html-video.git) |
| `auto-editor` | `video` | `backup` | `cli_ready_uv_tool_29.3.1` | `vendor/reserved/video/auto-editor` | [upstream](https://github.com/WyattBlue/auto-editor.git) |
| `chengfeng-videocut-skills` | `video` | `experimental` | `runtime_incomplete` | `vendor/reserved/video/chengfeng-videocut-skills` | [upstream](https://github.com/Agentchengfeng/chengfeng-videocut-skills.git) |
| `claude-code-video-toolkit` | `video` | `reference` | `dependency_ready_needs_provider_keys` | `vendor/reserved/video/claude-code-video-toolkit` | [upstream](https://github.com/digitalsamba/claude-code-video-toolkit.git) |
| `claude-real-video` | `video` | `production_candidate` | `dependency_ready` | `vendor/reserved/video/claude-real-video` | [upstream](https://github.com/HUANGCHIHHUNGLeo/claude-real-video.git) |
| `claude-shorts` | `video` | `backup` | `dependency_ready_with_npm_audit_warnings` | `vendor/reserved/video/claude-shorts` | [upstream](https://github.com/AgriciDaniel/claude-shorts.git) |
| `freecut` | `video` | `preferred_local_experiment` | `dependency_ready` | `vendor/reserved/video/freecut` | [upstream](https://github.com/Moh4696/freecut.git) |
| `hyperframes` | `video` | `production_candidate` | `dependency_ready` | `vendor/reserved/video/hyperframes` | [upstream](https://github.com/heygen-com/hyperframes.git) |
| `ian-xiaohei-illustrations` | `video` | `production_candidate` | `skill_ready` | `vendor/reserved/video/ian-xiaohei-illustrations` | [upstream](https://github.com/helloianneo/ian-xiaohei-illustrations.git) |
| `palmier-pro` | `video` | `experimental` | `source_ready_needs_desktop_app` | `vendor/reserved/video/palmier-pro` | [upstream](https://github.com/palmier-io/palmier-pro.git) |
| `remotion-video-skill` | `video` | `reference` | `skill_ready_runtime_not_promoted` | `vendor/reserved/video/remotion-video-skill` | [upstream](https://github.com/wshuyi/remotion-video-skill.git) |
| `seedance2-skill` | `video` | `backup` | `skill_ready_needs_model_access` | `vendor/reserved/video/seedance2-skill` | [upstream](https://github.com/dexhunter/seedance2-skill.git) |
| `talking-head-editor` | `video` | `reference_only` | `reference_runtime_ready` | `vendor/reserved/video/talking-head-editor` | [upstream](https://github.com/chrislema/videoeditor.git) |
| `text-to-lottie` | `video` | `production_candidate` | `built_with_local_skip_lib_check_for_upstream_kobalte_types` | `vendor/reserved/video/text-to-lottie` | [upstream](https://github.com/diffusionstudio/lottie.git) |
| `video-use` | `video` | `experimental` | `dependency_ready` | `vendor/reserved/video/video-use` | [upstream](https://github.com/browser-use/video-use.git) |
| `video-wrapper` | `video` | `production_candidate` | `dependency_ready` | `vendor/reserved/video/video-wrapper` | [upstream](https://github.com/op7418/Video-Wrapper-Skills.git) |
| `vox-director` | `video` | `backup` | `installed_needs_api_key` | `vendor/reserved/video/vox-director` | [upstream](https://github.com/Alisa0808/vox-director.git) |

## 候选储备

| 项目 | 类别 | 级别 | 下一步 | 阻断项 |
| --- | --- | --- | --- | --- |
| `video-shotcraft` | `video` | `high_priority_reserve` | promote_after_dasheng_adapter_and_smoke_render |  |
| `gsap-skills` | `design` | `high_priority_suite_reserve` | register_as_one_suite_router_with_subskill_dispatch |  |
| `impeccable` | `design` | `medium_high_priority_reserve` | promote_as_html_scene_visual_qc_advisor |  |
| `video-autopilot-kit` | `video` | `high_priority_adapter_reserve` | build_guarded_dasheng_adapter_before_registration | no_standard_skill_md、capcut_schema_and_output_contract_need_review |

## 已剔除项目

| 项目 | 原因 |
| --- | --- |
| `video-editing-pipeline` | No stable independent upstream repository. |
| `ffmpeg-usage` | No stable independent upstream; covered by the internal FFmpeg toolkit. |
| `caption-clip` | Low adoption, no clear license, and duplicated caption capability. |
| `product-launch-video-skill` | Niche and lower quality than retained Remotion toolkits. |
| `rednote-mcp` | Duplicated by the retained xiaohongshu-mcp and stronger browser/API routes. |
| `x-cli` | Duplicated by xurl and existing publishing routes. |
| `boutique/remotion-video` | Hard-coded obsolete local paths. |
| `boutique/video-subtitles` | Hebrew/English-oriented and unsuitable for the Chinese primary workflow. |
| `boutique/demo-video` | Depends on obsolete Clawdbot browser paths. |
| `boutique/video-agent` | Documentation-only HeyGen API wrapper with no installable upstream. |
| `boutique/animation-duplicates` | Materially duplicated by retained Remotion, HyperFrames, Lottie and animation-review Skills. |
| `governed-dcf-skill` | Useful finance methodology but weak fit for video generation or self-media operations; upstream has no declared license, so keep outside the executable reserve. |
| `livo-redskill-p5-attachments` | No stable public upstream or license was verified. Generic procedural-motion ideas are already covered by algorithmic-art and GSAP; do not register as executable. |

## 依赖

### 系统依赖

| 依赖 | 最低版本 | 必需 |
| --- | --- | --- |
| Python | `3.10` | 是 |
| Git | `2.x` | 是 |
| Node.js | `18` | 否 |
| FFmpeg/ffprobe | `5.x` | 否 |
| pnpm | `9` | 否 |
| bun | `1.x` | 否 |
| yt-dlp | `current` | 否 |

### Python 核心依赖

```text
anthropic>=0.18.0
requests>=2.31.0
beautifulsoup4>=4.12.0
PyYAML>=6.0.0
pandas>=2.0.0
numpy>=1.26.0
matplotlib>=3.8.0
seaborn>=0.13.0
akshare>=1.12.0
tushare>=1.4.0
pytest>=8.0.0
```

### Python 媒体扩展

```text
-r requirements.txt
funasr>=1.3.9
modelscope>=1.37.1
torch>=2.12.0
torchaudio>=2.11.0
addict>=2.4.0
datasets>=5.0.0
sortedcontainers>=2.4.0
simplejson>=4.1.1
```

## 发布技术路线

| 优先级 | 路线 | 状态 | 技术路径 |
| ---: | --- | --- | --- |
| 1 | `qianfan_local_api` | `current_default` | `local payload -> POST http://127.0.0.1:5409/postVideo -> platform adapter -> CloakBrowser/Playwright -> verification` |
| 2 | `qianfan_async_queue` | `batch_candidate` | `draft -> /api/v2/drafts/batch-publish -> task queue -> task verification` |
| 3 | `social_auto_upload_cli` | `fallback` | `channel pack -> guarded CLI -> named account session -> result callback` |

## 克隆、安装和检查

```bash
./scripts/install.sh
source .venv/bin/activate
python scripts/sync_reserved_projects.py --mode check
python scripts/sync_reserved_projects.py --mode clone --category video
python scripts/apply_upstream_patches.py --mode check
python scripts/ensure_video_external_deps.py --dep all --mode check
python scripts/check_publish_upstreams.py
python -m pytest tests -q
```

## 公开仓库边界

- 提交：自研 Skills、脚本、非敏感配置、契约、测试、文档、上游注册表和兼容补丁。
- 不提交：第三方源码副本、虚拟环境、`node_modules`、Cookie/浏览器 Profile、API 密钥、验证码、抓取快照、视频成品和每日运行产物。
- 外部项目许可证与使用条款以各自上游仓库为准。
