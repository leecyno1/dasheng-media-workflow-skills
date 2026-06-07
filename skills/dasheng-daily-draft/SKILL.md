---
name: dasheng-daily-draft
description: Use when running Stage 3 Draft from approved Brief topics and producing Reasoning Sheets, standard drafts, and draft quality gates.
version: 1.0.0
stage: draft
runner: python
---

# dasheng-daily-draft

## 定位

这是大圣工作流第三环节 Draft 的正式单阶段 skill。

职责：
- 读取 Brief Gate 通过的 `selected_topics.json`
- 读取完整 `topic_cards.json`
- 为每个选题生成 `Reasoning Sheet`
- 生成可审核、可发布的标准正文
- 同步生成可编辑、自包含、离线可用的 HTML 草稿
- 按需在本环节完成轻量风格润色或渠道源稿整理
- 输出文字洁癖 / 质量门禁，供编辑审核

不负责：
- 微信排版
- 发布

## canonical 输入

- `selected_topics.json`：状态必须为 `approved`，且 `selected_topics` 非空
- `topic_cards.json`：必须包含对应 `topic_id` 的完整题卡

## canonical 输出

- `03_ReasoningSheet_<topic>.md`
- `03_ReasoningSheet_<topic>.json`
- `03_标准初稿_<topic>.md`
- `03_HTML草稿_<topic>.html`
- `03_质量门禁_<topic>.json`
- `03_初稿_报告.md`
- `selected_topics_for_draft.json`
- `final_structure_snapshot.json`
- `final_structure_snapshot.template.json`
- `draft_quality_gate.json`
- `draft_manifest.json`

## 执行方式

```bash
python3 scripts/run_mainline_stage.py draft --run-id <run_id>
```

或直接执行：

```bash
python3 scripts/build_stage3_draft.py \
  产物/02_内容聚合及选题分析/<run_id>/selected_topics.json \
  产物/02_内容聚合及选题分析/<run_id>/topic_cards.json \
  --run-id <run_id>
```

## 质量门禁

`draft_quality_gate.json` 会记录：

- 中文字数
- 一级标题数量
- 是否存在引用与待补源小节
- AI 味高频句式命中

当前重点检查并提示少用：

- `不是……而是……`
- `这意味着`
- `本质上`
- `不可否认`
- `综上所述`

门禁状态为 `warning` 不阻塞编辑审核，但会写入 `draft_manifest.json.quality_gate`。

## HTML 草稿规则

- HTML 与 Markdown 同步生成；HTML 负责编辑预览和微信公众号导入前检查，Markdown 负责事实源稿。
- HTML 必须自包含：CSS/JS 内联，离线可打开，不允许 CDN 或本地引用。
- Chart.js 图表必须内联 v4.4.4 UMD；自写图表初始化必须 `DOMContentLoaded`、`typeof Chart` 降级、`responsive:false`、显式 canvas 宽高、`deepMerge` 合并配置，log 坐标写 `type:'logarithmic'`。
- 表格标签类放 `<td>` 内 `<span>`，根内容区 `contenteditable="true"`，必须支持编辑/预览切换、全选、保存下载。
- 图表、配图、数据来源必须绑定 `claim_id`；未核验数据只能留下待补槽，不能生成假走势或假来源。
- 配图可由运行 Agent 调用 image 工具生成，压缩后 base64 嵌入；发布前 canvas 图表建议截图替换成静态图。

## 硬规则

- Draft 只写标准事实稿，不做 DNA 改写
- 必须继承 Brief 的来源内容、争议点、观点和内容单元
- 不得把多个选题混成一篇
- 不得编造不存在的来源、数据和机构表态
- `final_structure_snapshot.json` 确认后可直接进入 publish
- 补素材、封面、图表、多版本改写只作为按需工具，不再是主链阶段
- 不新增隐藏的 Material AI provider；真实搜索、取数、配图生成由当前 Agent 在 Draft 内完成
