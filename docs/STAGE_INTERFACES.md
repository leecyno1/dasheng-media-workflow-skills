# Dasheng 主链阶段接口

这是当前唯一正式阶段契约文档。

正式主链：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

可选预处理资产：`ParadigmProfile`。它不改变正式主链顺序，只在用户提供标准文章、内容模板、爆款样本或渠道模板时生成，可被后续 `brief / draft / rewrite / publish` 消费。

## 1. 全局约束

- 唯一正式总入口：`dasheng-media-sop`
- 状态源：各阶段 `*_manifest.json` + gate 文件
- 禁止通过“最新目录”“历史命名习惯”“旧阶段名”猜阶段
- 同一 `run_id` 下，多选题必须独立目录、独立文档、独立素材、独立改写包
- `ParadigmProfile` 与 `Style DNA` 必须分离：前者约束结构范式、场景适配和内容推进方式；后者约束作者口吻、语言节奏和表达习惯

## 2. 对象链

```text
Run
  -> ParadigmProfile(optional)
  -> TopicPool
  -> SelectedTopic
  -> Draft
  -> Final Structure Snapshot
  -> Material Pack
  -> Rewrite Pack
  -> Publish Pack
  -> Postmortem
```

## 3. 阶段接口

### Stage 0.5｜Paradigm Learning（可选）

输入：

- 用户提供的标准文章、内容模板、历史高质量稿、爆款样本或渠道模板
- 目标场景：深度长文、观点短文、商业分析、行业解读、产品发布、社群转发等
- 目标渠道：公众号、小红书、短视频脚本、微博、社群、飞书内参等
- 可选作者或账号风格约束

输出：

- `00_范式画像.md`
- `paradigm_profile.yaml`
- `paradigm_prompt_block.md`
- `paradigm_manifest.json`

说明：

- 不单列为正式主链阶段，也不设置强制 gate
- 默认在 Brief 前生成；如果用户在 Draft / Rewrite / Publish 时临时提供模板，也允许即时生成并绑定当前 run
- 只提炼结构、框架、叙事路径、论证模型、渠道适配规则和禁用项
- 不替代事实来源，不参与事实判断，不允许把样本中的事实挪用到新文章

### Stage 1｜Intake

输入：

- 渠道采集源
- AI 热点补充源

输出：

- `01_内容采集_报告.md`
- `01_内容采集_底稿.md`
- `raw/intake_records.json`
- `channel_top10.json`
- `event_clusters.json`
- `brief_input.json`
- `intake_manifest.json`

说明：

- 只允许真实标题 + 真实链接
- 只做采集、整理、热度评级，不做选题立场判断

### Stage 2｜Brief

输入：

- `brief_input.json`
- `channel_top10.json`
- `event_clusters.json`
- `raw/intake_records.json`
- 可选：`paradigm_profile.yaml`

输出：

- `02_编辑Brief库.md`
- `02_研究Brief库.md`
- `02_编辑Brief_报告.md`
- `topic_cards.json`
- `selected_topics.template.json`
- `selected_topics.json`
- `brief_manifest.json`

门禁：

- `selected_topics.json`

说明：

- 当前模式固定为 `ai_only`
- 代码只做证据编排、结构校验和落盘
- 如存在 `ParadigmProfile`，Brief 需为每个候选题标注推荐范式、适用场景、风险边界和不适用理由

### Stage 3｜Draft

输入：

- `selected_topics.json`
- `topic_cards.json`
- 可选：`paradigm_profile.yaml`

输出：

- `03_ReasoningSheet_<topic>.md`
- `03_ReasoningSheet_<topic>.json`
- `03_标准初稿_<topic>.md`
- `03_初稿_报告.md`
- `draft_manifest.json`
- `final_structure_snapshot.json`

门禁：

- `final_structure_snapshot.json`

说明：

- 这是标准基线稿
- 不注入 DNA，不写平台腔
- 可继承范式画像里的章节骨架、论证顺序和信息密度要求，但不得继承样本文风或渠道包装语

### Stage 4｜Material

输入：

- `draft_manifest.json`
- `final_structure_snapshot.json`
- `03_ReasoningSheet_<topic>.json`

输出：

- `04_MaterialPack.md`
- `04_Material_报告.md`
- `material_manifest.json`
- `material_acceptance.json`
- `pack_assets/<topic>/...`

门禁：

- `material_acceptance.json`

说明：

- 只围绕终稿结构与 claim 补素材
- 不允许从旧改写稿反推素材需求

### Stage 5｜Rewrite

输入：

- `material_manifest.json`
- `final_structure_snapshot.json`
- 回填后的终稿
- 可选：`paradigm_profile.yaml`
- 可选：`Style DNA`

输出：

- `<topic>/rewrite_bundle.md`
- `<topic>/<variant>.md`
- `<topic>/meta.json`
- `rewrite_manifest.json`

说明：

- 继承终稿结构
- 每题独立
- 默认每题 4 个版本
- 可把范式画像与风格 DNA 组合使用：范式控制“怎么组织”，DNA 控制“像谁表达”

### Stage 6｜Publish

输入：

- `rewrite_manifest.json`
- `material_manifest.json`
- `publish_decision.json`
- 可选：`paradigm_profile.yaml`

输出：

- `07_发布计划.md`
- `07_发布包.md`
- `publish_video_supplement_report.md`
- `publish_video_supplement_manifest.json`
- `channel_adaptation_manifest.json`
- `channel_execution_manifest.json`
- `publish_verification_report.json`
- `publish_manifest.json`

门禁：

- `publish_decision.json`

说明：

- `distribute` 已并入 `publish`
- 发布前视频补充属于 `publish` 强制子环节
- 渠道适配可消费范式画像中的平台框架，但必须以 `publish_decision.json` 为人工门禁

### Stage 7｜Postmortem

输入：

- `publish_manifest.json`
- 发布结果与人工反馈

输出：

- `08_复盘报告.md`
- `08_L1回写建议.md`
- `postmortem_manifest.json`

## 4. Gate 规则

| Gate | 文件 | 未满足时 |
| --- | --- | --- |
| Brief Gate | `selected_topics.json` | Draft 必须失败 |
| Final Structure Gate | `final_structure_snapshot.json` | Material / Rewrite 必须失败 |
| Material Gate | `material_acceptance.json` | Rewrite 必须失败 |
| Channel Gate | `publish_decision.json` | Publish 必须失败 |

## 5. 路径口径

当前正式文档路径：

- `./docs/STAGE_INTERFACES.md`（相对路径，相对于项目根目录）

兼容镜像路径：

- `./引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
