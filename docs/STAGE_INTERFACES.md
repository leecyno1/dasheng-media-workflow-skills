# Dasheng 主链阶段接口

这是当前唯一正式阶段契约文档。

正式主链：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

## 1. 全局约束

- 唯一正式总入口：`dasheng-media-sop`
- 状态源：各阶段 `*_manifest.json` + gate 文件
- 禁止通过“最新目录”“历史命名习惯”“旧阶段名”猜阶段
- 同一 `run_id` 下，多选题必须独立目录、独立文档、独立素材、独立改写包

## 2. 对象链

```text
Run
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

### Stage 3｜Draft

输入：

- `selected_topics.json`
- `topic_cards.json`

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

输出：

- `<topic>/rewrite_bundle.md`
- `<topic>/<variant>.md`
- `<topic>/meta.json`
- `rewrite_manifest.json`

说明：

- 继承终稿结构
- 每题独立
- 默认每题 4 个版本

### Stage 6｜Publish

输入：

- `rewrite_manifest.json`
- `material_manifest.json`
- `publish_decision.json`

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
