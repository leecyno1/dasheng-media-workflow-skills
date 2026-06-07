# 大圣 Daily｜主链阶段接口

本文件定义唯一主链、唯一对象模型、唯一人工闸门，以及各阶段正式交付接口。

## 一、唯一主链

固定阶段顺序：

`intake -> brief -> draft -> publish -> postmortem`

可选前置资产：`ParadigmProfile`。当用户提供标准文章、内容模板、爆款样本或渠道模板时，可先生成范式画像，再供 `brief / draft / publish` 调用；它不改变正式主链顺序，也不作为强制 gate。

固定对象链：

`Run -> ParadigmProfile(optional) -> TopicPool -> SelectedTopic -> Draft/FinalDoc -> PublishPack -> Postmortem`

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

## 三、4 个强制 HITL Gate

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
- 作用：锁定终稿结构，确认后可直接进入 publish

### 4. Channel Gate

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
  - 默认放在 `brief` 前；如果用户在 `draft / rewrite / publish` 临时提供模板，也可即时生成并绑定当前 run
  - 只提炼结构范式、章节框架、叙事路径、论证模型、信息密度、渠道适配和禁用项
  - 不替代事实来源，不搬运样本事实，不参与事实真伪判断

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

### 按需工具：Material Refill / Rewrite Variants

Material 和独立 Rewrite 已从正式主链删除。

- 补素材、封面、图表、视频素材：只在用户明确要求、或 Draft/Publish 明确缺口时调用 `dasheng-daily-material` / `dasheng-stage-material-refill`。
- 多版本改写：只在需要额外作者口吻、平台变体或短视频脚本时调用 `dasheng-stage-rewrite-v3`。
- 这些工具不得生成新的主链 gate，不得要求 `material_manifest.json` 或 `rewrite_manifest.json` 才能进入 publish。
- 工具产物只能作为 `draft_manifest` / `publish_decision` 的附加资源引用。
- 不允许新增隐藏的 Material AI provider；Draft 内需要真实数据、图表或配图时，由当前 Agent 主动搜索、核验、生成并写入 `draft_manifest`。

### 4. Publish｜渠道包与发布

- 目标：输出真正可发的渠道包
- 正式输入：
  - `draft_manifest.json`
  - `final_structure_snapshot.json`
  - `publish_decision.json`
  - 可选：`paradigm_profile.yaml`
- 正式产物：
  - `07_发布包.md`
  - `07_发布计划.md`
  - `publish_video_supplement_report.md`
  - `publish_video_supplement_manifest.json`
  - `channel_adaptation_manifest.json`
  - `channel_execution_manifest.json`
  - `publish_verification_report.json`
  - `publish_decision.json`
  - `publish_manifest.json`
- 发布前必须具备：
  - 标题候选
  - 封面候选
  - 渠道版本矩阵
  - 发布时间建议
  - 风险检查清单
  - 可选：图表动效视频 / 叙事动效视频
- 内部正式子层：
  - `Publish Gate`
  - `Video Supplement`（可选）
  - `Channel Adaptation`
  - `Channel Execution`
  - `Publish Guard`
- 平台执行器矩阵：
  - 公众号：`baoyu-post-to-wechat`、`wechat-multi-publisher`、`md2wechat`
  - 微博：`weibo-manager`、`baoyu-post-to-weibo`
  - X：`baoyu-post-to-x`
  - 小红书：`xiaohongshu-auto`（OpenClaw）
  - 抖音：`douyin-upload-skill`（OpenClaw）
  - B站：当前无正式投稿 skill，只有研究辅助 `bilibili-youtube-watcher`
  - 验真：`publish-guard`
- 强约束：
  - 不再允许 `latest_dir(...)` 或历史目录猜测
  - 没有 `Channel Gate`，publish 禁止执行
  - 渠道适配可消费范式画像中的平台框架，但必须以人工确认的发布决策为准
  - 缺少正式平台执行器的平台，只允许导出待人工发布包
  - 未经过 `Publish Guard` 验真，不得向用户汇报“已发布”

### 5. Postmortem｜知识回写

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
5. `Final Structure Gate` 通过后，主链直接进入 publish。
6. 多选题时，draft / publish 默认按题目并行、目录独立。
7. Material / Rewrite 只作为按需工具，不得再作为主链阶段或 gate。
8. 本文件一旦变更，相关 schema、skill 文档、Feishu 计划器必须同步更新。
