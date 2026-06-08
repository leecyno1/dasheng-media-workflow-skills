# 大圣 Daily｜对象模型

## 核心原则

- 对象优先，文档降级为视图
- 每个对象必须有稳定 ID、上游引用、状态和 manifest
- 每个阶段只读上游 canonical 对象，不猜目录、不猜最新文件

## 对象定义

### `Run`

- 一次完整日更批次
- 唯一键：`run_id`
- 记录阶段状态、对象索引、飞书视图映射

### `ParadigmProfile`（可选）

- 从用户提供的标准文章、内容模板、爆款样本或渠道模板中提炼出的文章范式资产
- 用于约束结构框架、叙事路径、论证模型、信息密度、场景适配和渠道适配
- 默认在 Brief 前生成，也可在 Draft / Rewrite / Publish 临时绑定到当前 `run_id`
- 与 `Style DNA` 分离：`ParadigmProfile` 解决“怎么组织内容”，`Style DNA` 解决“像谁表达”
- 不保存或复用样本事实，不替代外部证据，不参与事实真伪判断

### `TopicCard`

- 候选题卡
- 用于编辑判断“是否值得写”
- 核心字段：
  - `title`
  - `core_thesis`
  - `scorecard`
  - `proof_requirements`
  - `existing_evidence`
  - `missing_evidence`

### `SelectedTopic`

- 由编辑确认进入 draft 的题
- 必须通过 `selected_topics.json`

### `Claim`

- 正文中的关键判断
- Draft 阶段生成的图表、图像、视频锚点都必须绑定到 Claim

### `EvidenceItem`

- 支撑 Claim 的证据对象
- 类型包括链接、数据、截图、图表、视频、原始报道

### `AssetItem`

- 可以直接回填或发布的资产对象
- 必须带 `claim_id / section_id / usage_type / relevance_score / editor_status`

### `ChannelPack`

- 某一渠道的正式发稿包
- 例如公众号长文、小红书视频口播、视频平台分镜稿

## Gate 文件

- `intake_review.json`
- `selected_topics.json`
- `final_structure_snapshot.json`
- `publish_decision.json`

Gate 文件是人工介入写回系统的正式入口。
