# 大圣 Daily｜主链阶段接口

本文件定义唯一主链、唯一对象模型、唯一人工闸门，以及各阶段正式交付接口。

## 一、唯一主链

固定阶段顺序：

`intake -> brief -> draft -> transwrite -> publish -> postmortem`

可选前置资产：`ParadigmProfile`。当用户提供标准文章、内容模板、爆款样本或渠道模板时，可先生成范式画像，再供 `brief / draft / transwrite / publish` 调用；它不改变正式主链顺序，也不作为强制 gate。

固定对象链：

`Run -> ParadigmProfile(optional) -> TopicPool -> SelectedTopic -> Draft/FinalDoc -> TranswritePack -> PublishPack -> Postmortem`

文档只是交付视图，不是唯一状态源。唯一状态源必须同时满足：

- 阶段目录存在 canonical manifest
- 上游对象可追溯
- HITL gate 文件存在且状态明确

## 二、唯一对象模型

- `Run`
  - 一次当日生产批次
  - 唯一键：`run_id`
- `TopicCard`
  - 候选题卡，服务编辑决策
  - 唯一键：`topic_id`
- `SelectedTopic`
  - 通过 `Brief Gate` 进入 draft 的正式题目
- `Claim`
  - 正文中的核心判断，供 Draft 论证与按需补证使用
- `EvidenceItem`
  - 支撑 `Claim` 的链接、数据、截图、图表、视频
- `AssetItem`
  - 图片、图表、视频、封面、互动视频等资产
- `ChannelPack`
  - 某一渠道可直接发布的内容包
- `ParadigmProfile`
  - 从标准文章或模板中提炼出的结构范式、叙事路径、论证模型、场景适配和渠道框架
  - 与 `Style DNA` 分离：前者解决“怎么组织内容”，后者解决“像谁表达”

对象 schema 统一位于：

- `skills/dasheng-daily-shared/schema/base-meta.schema.json`
- `skills/dasheng-daily-shared/schema/topic-card.schema.json`
- `skills/dasheng-daily-shared/schema/selected-topic.schema.json`
- `skills/dasheng-daily-shared/schema/claim.schema.json`
- `skills/dasheng-daily-shared/schema/evidence-item.schema.json`
- `skills/dasheng-daily-shared/schema/asset-item.schema.json`
- `skills/dasheng-daily-shared/schema/channel-pack.schema.json`
- `skills/dasheng-daily-shared/schema/reasoning-sheet.schema.json`

## 三、5 个强制 HITL Gate

### 1. Intake Gate

- 文件：`intake_review.json`
- 作用：删除噪音、广告、低信息密度样本，确认保留范围
- 无该文件：允许继续 brief，但必须标记 `status=pending_review`

### 2. Brief Gate

- 文件：`selected_topics.json`
- 作用：编辑确认本轮进入 draft 的题目
- 无该文件或无 `selected_topics`：禁止进入 draft

### 3. Final Structure Gate

- 文件：`final_structure_snapshot.json`
- 作用：锁定终稿结构，确认后进入 transwrite

### 4. Transwrite Gate

- 文件：`transwrite_decision.json`
- 作用：确认每个题目需要走哪些转写通路：公众号文章、口播视频、播客

### 5. Channel Gate

- 文件：`publish_decision.json`
- 作用：确认标题、封面、平台版本、发布时间

## 四、阶段接口

### 0.5 Paradigm Learning｜可选范式学习

- 目标：把用户提供的标准文章、内容模板或渠道样本沉淀为可复用的文章范式资产
- 推荐输入：
  - 标准文章、历史高质量稿、爆款样本、渠道模板
  - 目标场景、目标渠道、目标风格约束
- 正式产物：
  - `00_范式画像.md`
  - `paradigm_profile.yaml`
  - `paradigm_prompt_block.md`
  - `paradigm_manifest.json`
- 关键规则：
  - 默认放在 `brief` 前；如果用户在 `draft / transwrite / publish` 临时提供模板，也可即时生成并绑定当前 run
  - 只提炼结构范式、章节框架、叙事路径、论证模型、信息密度、渠道适配和禁用项
  - 不替代事实来源，不搬运样本事实，不参与事实真伪判断

### 0.6 Video Style Training｜可选视频训练

- 目标：把用户提供的大量样板视频沉淀为可复用的 `Video Style DNA`，供真人口播和无真人科普视频生产引用
- 推荐输入：
  - 样板视频目录
  - `style_id`
  - 博主名、平台名、目标使用场景
- 正式产物：
  - `training_manifest.json`
  - `per_video/*/analysis.json`
  - `style_profile.json`
  - `style_profile.md`
- 默认目录：
  - `~/Desktop/自媒体创作/00_范式学习/视频训练/<style_id>/`
- 关键规则：
  - 这是独立可选资产，不改变主链顺序，不作为 transwrite 必需 gate
  - 只学习剪辑节奏、场景结构、转场、动效、模板偏好、声音氛围和证据密度
  - 不生成市场事实、不替代 Draft 数据图表、不复制样片脚本或画面
  - 样板源视频只记录路径；压缩上传缓存写入 `<style_id>/_upload_cache/`
  - 禁止把视频、音频、字幕、审核页、训练缓存写入项目根目录或 `skills/`

### 1. Intake｜内容采集 / 话题雷达

- 目标：采集当天热点样本，并升级为“事件-人物-议题”雷达
- 推荐输入：
  - 默认：本地 `8001` 的聊天记录 / 本地新闻流
  - 公开新闻兜底：同花顺、华尔街见闻、彭博市场，保留热度、情绪和类别评价
  - 公开热榜兜底：Reddit RSS、Hacker News、微博热搜、知乎热榜、抖音热榜、虎扑热榜、头条热榜、财经 RSS
  - 回滚：`DASHENG_INTAKE_MODE=legacy` 时才启用旧 `5173` / `reports` / `8000 public wechat`
- 正式产物：
  - `notes/01_内容采集_底稿.md`
  - `notes/01_内容采集_报告.md`
  - `raw/intake_records.json`
  - `ai_hot_topics.json`
  - `entity_rankings.json`
  - `event_clusters.json`
  - `source_quality_report.json`
  - `channel_top10.json`
  - `brief_input.json`
  - `channel_tasks.json`
  - `intake_review.json`
  - `intake_manifest.json`
- 关键要求：
  - 不做观点筛选，只做真实采集、热度评级、标准化与交接
  - `报告` 必须按渠道输出 Top10，且每条保留真实标题与真实链接
  - `底稿` 必须保留全量标准化来源清单、重复/噪音池和下游原始输入池
  - 必须额外输出 `AI热点` Top10，默认从本地新闻流、公开新闻兜底与公开热榜中派生
  - `AI热点` 在 Brief handoff 中使用更高权重，但不能替代原始渠道样本
  - 热度评级采用渠道内相对分层：`S/A/B/C/D`
  - 旧 `8000 public wechat API` 仅属于 legacy 模式，默认不再主动调用
  - 去重要同时覆盖 URL、标题近似与同事件重复转载

### 2. Brief｜AI-only 选题库 + Research Brief

- 目标：从热点转成“可写性驱动”的独立 `TopicCard`
- 主输入优先级：
  - `brief_input.json`
  - `channel_top10.json`
  - `event_clusters.json`
  - `raw/intake_records.json`
  - 可选：`paradigm_profile.yaml`
- 正式产物：
  - `02_编辑Brief库.md`
  - `02_研究Brief库.md`
  - `02_编辑Brief_报告.md`
  - `topic_cards.json`
  - `selected_topics.json`
  - `selected_topics.template.json`
  - `brief_manifest.json`
- 每张题卡至少包含：
  - `topic_id`
  - `topic_kind`（默认 `independent`）
  - `title`
  - `one_line_judgment`
  - `core_proposition`
  - `why_now`
  - `reader_payoff`
  - `article_use`
  - `distinctiveness_reason`
  - `evidence_gap_summary`
  - `proof_requirements`
  - `recommended_data_angles`
  - `recommended_visual_angles`
  - `priority_people`
  - `priority_orgs`
  - `priority_news_queries`
  - `existing_evidence`
  - `question_units` / `opinion_units` / `case_units` / `solution_units`
  - `structure_hint`
- 关键规则：
  - Stage 2 正式模式为 `ai_only`
  - 输出是 8-10 个平铺独立题卡，不再把母题 / 变体作为正式业务主语义
  - 不做硬题材配额，但要避免单一逻辑链占满榜单
  - 高优先证据池按“信号强度 × 逻辑独立性 × 主题新颖度”做弱重排
  - AI 返回的来源必须能回贴到 canonical evidence
  - 禁止把采集原始标题直接抬升为编辑题目
  - 如存在 `ParadigmProfile`，每个候选题必须标注推荐范式、适用场景、风险边界和不适用理由
  - 若同一逻辑链占比超过半数，阶段直接失败

### 3. Draft｜Reasoning Sheet + 标准稿 + HTML 草稿

- 目标：先完成论证结构，再产出标准初稿，并同步生成可编辑、自包含 HTML 草稿
- Draft 只读取：
  - `selected_topics.json`
  - `topic_cards.json`
  - 可选：`draft_asset_specs.json` / `--asset-specs-file`（按 `topic_id` 提供 `chart_specs` / `image_specs`）
  - 可选：`finance_chart_requests`（由 `dasheng-finance-data` 展开为金融行情 `chart_specs`）
  - 可选：`paradigm_profile.yaml`
- 正式产物：
  - `03_ReasoningSheet_<topic>.md`
  - `03_ReasoningSheet_<topic>.json`
  - `03_标准初稿_<topic>.md`
  - `03_HTML草稿_<topic>.html`
  - `03_质量门禁_<topic>.json`
  - `03_DraftAssets_<topic>.json`
  - `03_IllustrationIntents_<topic>.json`
  - `03_初稿_报告.md`
  - `draft_quality_gate.json`
  - `final_structure_snapshot.template.json`
  - `draft_manifest.json`
- 结构规则：
  - 一级标题默认 3-4 个，最多 4 个
  - 一级结构必须继承选题本意，不能机械复制 Brief 列表
  - `Reasoning Sheet` 中每个 `Claim` 必须映射 `EvidenceItem / MissingProof / ChartNeed`
  - 可继承范式画像里的章节骨架、论证顺序和信息密度要求，但不得继承样本文风、情绪词或渠道包装语
- HTML 规则：
  - 单文件自包含，CSS/JS 内联，离线可用，不允许 CDN 或本地引用
  - 有 Chart.js 图表时内联 v4.4.4 UMD；自写图表脚本必须 `DOMContentLoaded`、`typeof Chart` 降级、`responsive:false`、显式 canvas 宽高、`deepMerge` 合并配置
  - log 坐标写 `type:'logarithmic'`，不得写 `type:'log'`
  - 表格标签类放 `<td>` 内 `<span>`；根内容区 `contenteditable="true"`，支持编辑/预览切换、全选、保存下载
  - 图表、配图、数据必须绑定 `claim_id` 与来源；未核验数据只留待补槽，不得伪造
  - 图片压缩后 base64 嵌入，最长边不超过 1200px；微信公众号发布前 canvas 图表建议截图替换为静态图
  - Draft 不得只输出 `chart_plan` / `image_plan`；需求锚点只能进入 `chart_requests` / `image_requests`，真正交付物必须是已嵌入 HTML 的 `chart_specs` / `image_specs`
  - 如正文需要图表或配图但缺少可核验数据/图片，`draft_manifest.status` 必须标记为 `incomplete_assets`，不得伪装为完成稿
  - 股票、指数、ETF、汇率、商品、股债跨资产走势与经济日历统计优先通过 `dasheng-finance-data` 生成 `chart_specs`，禁止凭记忆手填行情或宏观日历序列
  - 正文出现有认知价值的比喻、举例、类比、拟人或抽象机制时，Draft 调用 `dasheng-lemon-illustrations` 输出 illustration intent；关键词命中只负责召回，Agent 决定是否值得画
  - 必需漫画使用柠檬人，紧跟原段落嵌入 HTML；不得集中堆到文末，不得替代真实图表、网页、表格、文档、地图或来源证据
  - 必需 illustration intent 未生成对应 `illustration_specs` 时，`illustration_status` 与 Draft 资产状态不得标记 complete

### 按需工具：Rewrite Variants

独立素材环节已删除；真实数据、图表、配图和 HTML 嵌入都必须在 Draft 内完成。

- 多版本改写：只在 Transwrite 需要额外作者口吻、平台变体或短视频脚本时调用 `dasheng-stage-rewrite-v3`。
- 改写工具不得生成新的主链 gate，不得要求 `rewrite_manifest.json` 才能进入 transwrite 或 publish。
- 工具产物只能作为 `transwrite_manifest` / `publish_decision` 的附加资源引用。

### 4. Transwrite｜转写生产

- 目标：把确认后的 Draft 转为可验收的渠道生产包
- 正式输入：
  - `draft_manifest.json`
  - `final_structure_snapshot.json`
  - `transwrite_decision.json`
  - 可选：`paradigm_profile.yaml`
  - 可选：`video-style-training/style_profile.json`
- 正式产物：
  - `04_转写计划.md`
  - `transwrite_manifest.json`
  - `wechat_article/wechat_article_manifest.json`
  - `wechat_article/agent_rewrite_prompt.md`
  - `wechat_article/cover_prompt.md`
  - `wechat_article/illustration_intents.json`
  - `talking_head_video/talking_head_video_manifest.json`
  - `talking_head_video/video_storyboard.json`
  - `talking_head_video/talking_head_script.md`
  - `talking_head_video/html_overlay.html`
  - `talking_head_video/render_plan.json`
  - `talking_head_video/illustration_intents.json`
  - `podcast/podcast_manifest.json`
  - `podcast/podcast_script.md`
  - `podcast/provider_request.json`
- 三条通路：
  - `wechat_article`：DNA / humanize / 内容扩展 / 微信格式转写 / 封面生成 / 原比喻与举例的段后柠檬漫画
  - `talking_head_video`：真人口播可选、视觉层透明/非透明、真人音频/合成音频、主动/被动对齐 / illustration intent 动态分镜
  - `podcast`：Coze / MiniMax API 请求包
- 强约束：
  - 不补事实、不补数据、不重做图表；缺口必须退回 Draft
  - 外部 API、真人素材或渲染器缺失时必须写入状态
  - 不得把计划或请求体误报为已生成视频/音频
  - 公众号与视频必须消费同一 Draft illustration intent；视频按“设置 -> 柠檬人动作 -> 结果”改造成动态分镜，不得重新发明冲突比喻

### 5. Publish｜发布执行

- 目标：验收转写包，生成发布包，推草稿/人工包，回收链接
- 正式输入：
  - `transwrite_manifest.json`
  - `publish_decision.json`
- 正式产物：
  - `07_发布计划.md`
  - `07_发布包.md`
  - `channel_execution_manifest.json`
  - `publish_verification_report.json`
  - `publish_manifest.json`
- 平台执行器矩阵：
  - 公众号：`baoyu-post-to-wechat`、`wechat-multi-publisher`、`md2wechat`
  - 微博：`baoyu-post-to-weibo`
  - X：`baoyu-post-to-x`
  - 小红书：`xiaohongshu-auto`（OpenClaw）
  - 抖音：`douyin-upload-skill`（OpenClaw）
  - B站：人工投稿包
  - 播客：人工上传或音频平台 API
  - 验真：`publish-guard`
- 强约束：
  - 没有 `Channel Gate`，publish 禁止执行
  - Publish 不再生成正文、封面、视频或播客
  - 缺少正式平台执行器的平台，只允许导出待人工发布包
  - 未经过链接回收和 `Publish Guard` 验真，不得向用户汇报“已发布”

### 6. Postmortem｜知识回写

- 目标：将结果回写为下一轮可复用知识
- 正式输入：
  - `publish_manifest.json`
- 正式产物：
  - `08_复盘报告.md`
  - `08_L1回写建议.md`
  - `postmortem_manifest.json`
- 至少回写 4 类知识：
  - `Topic Pattern Library`
  - `Evidence Pattern Library`
  - `Visual Pattern Library`
  - `Channel Pattern Library`

## 五、飞书同步接口

- 常规同步：
  - `python3 {DASHENG_ROOT}/scripts/feishu_stage_sync.py --latest`
- 断点续跑：
  - `python3 {DASHENG_ROOT}/scripts/feishu_stage_sync.py --resume-only <run_id>`
- 强制重跑：
  - `python3 {DASHENG_ROOT}/scripts/feishu_stage_sync.py --fresh <run_id>`
- 默认原则：
  - 先 `--resume-only`
  - 后 `--fresh`
- live 进度文件：
  - `skills/dasheng-daily-shared/runtime-data/runs/<run_id>/bridge/live-execution-progress.json`

## 六、总规则

1. 任一阶段都必须能从 manifest 追溯到上游对象。
2. 飞书文档是协作视图，不是唯一状态源。
3. 不允许依赖“猜最新目录”或旧命名习惯切阶段。
4. `Brief Gate` 未选题，禁止进入 draft。
5. `Final Structure Gate` 通过后，主链进入 transwrite。
6. 多选题时，draft / transwrite / publish 默认按题目并行、目录独立。
7. 独立素材环节已删除；Rewrite 只作为 transwrite 的按需工具，不得再作为主链阶段或 gate。
8. 本文件一旦变更，相关 schema、skill 文档、Feishu 计划器必须同步更新。
