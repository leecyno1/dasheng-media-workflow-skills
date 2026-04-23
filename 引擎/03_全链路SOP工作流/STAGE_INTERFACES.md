# 大圣 Daily｜主链阶段接口

本文件定义唯一主链、唯一对象模型、唯一人工闸门，以及各阶段正式交付接口。

## 一、唯一主链

固定阶段顺序：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

固定对象链：

`Run -> TopicPool -> SelectedTopic -> Draft -> FinalDoc -> MaterialPack -> RewritePack -> PublishPack -> Postmortem`

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
  - 正文中的核心判断，material 必须围绕 claim 补证据
- `EvidenceItem`
  - 支撑 `Claim` 的链接、数据、截图、图表、视频
- `AssetItem`
  - 图片、图表、视频、封面、互动视频等资产
- `ChannelPack`
  - 某一渠道可直接发布的内容包

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
- 作用：锁定终稿结构，作为 material / rewrite 的共同上游

### 4. Material Gate

- 文件：`material_acceptance.json`
- 作用：确认可回填素材、待替换素材、弃用素材

### 5. Channel Gate

- 文件：`publish_decision.json`
- 作用：确认标题、封面、平台版本、发布时间

## 四、阶段接口

### 1. Intake｜内容采集 / 话题雷达

- 目标：采集当天热点样本，并升级为“事件-人物-议题”雷达
- 推荐输入：
  - `5173` / `reports` / `8001`
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
  - `底稿` 必须保留全量标准化来源清单、重复/噪音池、TrendRadar 补充池
  - 必须额外输出 `AI热点` Top10，来源至少覆盖 `Reddit RSS + Hacker News + B站 AI 样本`
  - `AI热点` 在 Brief handoff 中使用更高权重，但不能替代原始渠道样本
  - 热度评级采用渠道内相对分层：`S/A/B/C/D`
  - 公众号正式走 `8000 public wechat API`，视为慢源，允许等待与补抓；最终稿必须记录补抓轮次与等待时长
  - 去重要同时覆盖 URL、标题近似与同事件重复转载

### 2. Brief｜AI-only 选题库 + Research Brief

- 目标：从热点转成“可写性驱动”的独立 `TopicCard`
- 主输入优先级：
  - `brief_input.json`
  - `channel_top10.json`
  - `event_clusters.json`
  - `raw/intake_records.json`
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
  - `structure_hint`
- 关键规则：
  - Stage 2 正式模式为 `ai_only`
  - 输出是 8-10 个平铺独立题卡，不再把母题 / 变体作为正式业务主语义
  - 不做硬题材配额，但要避免单一逻辑链占满榜单
  - 高优先证据池按“信号强度 × 逻辑独立性 × 主题新颖度”做弱重排
  - AI 返回的来源必须能回贴到 canonical evidence
  - 禁止把采集原始标题直接抬升为编辑题目
  - 若同一逻辑链占比超过半数，阶段直接失败

### 3. Draft｜Reasoning Sheet + 标准稿

- 目标：先完成论证结构，再产出标准初稿
- Draft 只读取：
  - `selected_topics.json`
  - `topic_cards.json`
- 正式产物：
  - `03_ReasoningSheet_<topic>.md`
  - `03_ReasoningSheet_<topic>.json`
  - `03_标准初稿_<topic>.md`
  - `03_初稿_报告.md`
  - `final_structure_snapshot.template.json`
  - `draft_manifest.json`
- 结构规则：
  - 一级标题默认 3-4 个，最多 4 个
  - 一级结构必须继承选题本意，不能机械复制 Brief 列表
  - `Reasoning Sheet` 中每个 `Claim` 必须映射 `EvidenceItem / MissingProof / ChartNeed`

### 4. Material｜证据化素材包

- 目标：围绕 `Claim` 补充真正相关的图表、图片、视频、逻辑图
- 优先输入：
  - `draft_manifest.json`
  - `03_ReasoningSheet_<topic>.json`
- 标准执行：
  - `python3 {DASHENG_ROOT}/scripts/material_execute_pack.py --draft-manifest <draft_manifest.json>`
- 正式产物：
  - `04_MaterialPack.md`
  - `04_Material_报告.md`
  - `material_manifest.json`
  - `material_acceptance.json`
  - `pack_assets/<topic>/...`
- 素材必须绑定：
  - `claim_id`
  - `section_id`
  - `usage_type`
  - `relevance_score`
  - `editor_status`
- 子能力拆分：
  - `Evidence Charts`
  - `Visual References`
  - `Generated Visuals`
  - `Video Assets`
- 强约束：
  - 必须存在且通过 `Final Structure Gate`，否则 material 禁止执行
  - 不再允许 `--pack-root`、旧 `content-briefs.json`、旧目录猜测作为正式入口
  - AI provider 与图片 provider 统一读取 `configs/image_generation/providers.local.env`

### 5. Rewrite｜结构继承改写

- 目标：在不破坏终稿结构的前提下做渠道适配
- 正式输入：
  - `material_manifest.json`
  - `material_acceptance.json`
  - `final_structure_snapshot.json`
- 正式产物：
  - `<topic>__rewrite_bundle.md`
  - `<topic>__wechat_luxun_hot.md`
  - `<topic>__wechat_lemon_normal.md`
  - `<topic>__xhs_video_luxun_hot.md`
  - `<topic>__xhs_video_lemon_normal.md`
  - `meta.json`
  - `rewrite_manifest.json`
- 必须记录：
  - 继承了哪些一级标题
  - 哪些二级结构被保留
  - 哪些平台化改写是新增
  - 哪些素材锚点被保留 / 删去 / 新增
- 强约束：
  - 不再允许硬编码 dated 目录、默认源目录或旧稿反推结构
  - 没有 `Material Gate` 或 `Final Structure Gate`，rewrite 禁止执行

### 6. Publish｜渠道包与视频增强

- 目标：输出真正可发的渠道包
- 正式输入：
  - `rewrite_manifest.json`
  - `material_manifest.json`
  - `publish_decision.json`
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
  - 图表动效视频 / 叙事动效视频
- 内部正式子层：
  - `Publish Gate`
  - `Video Supplement`
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
  - 缺少正式平台执行器的平台，只允许导出待人工发布包
  - 未经过 `Publish Guard` 验真，不得向用户汇报“已发布”

### 7. Postmortem｜知识回写

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
5. `Material` 与 `Rewrite` 必须基于 `Final Structure Gate` 的结构快照。
6. 多选题时，draft / material / rewrite 默认按题目并行、目录独立。
7. 本文件一旦变更，相关 schema、skill 文档、Feishu 计划器必须同步更新。
