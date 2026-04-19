---
name: dasheng-stage-draft
description: Stage 3 Draft - 初稿生成（标准基线稿）
version: 1.0.0
stage: draft
runner: node
---

# Dasheng Stage Draft - 初稿生成

## 功能概述

Stage 3 Draft 是大声自媒体创作工作台的初稿生成阶段，负责将编辑确认的选题转化为标准基线初稿。

**核心原则**：
- 生成标准基线稿（不注入风格DNA，不做渠道定制）
- 严格限制顶层结构为3-4个一级标题
- 每个论断必须可追溯到外部来源
- 绝不在文章内容中包含内部统计数据

## 输入要求

### 必需输入
- `selected_topics.json` - 编辑确认的选题列表（来自Brief阶段的HITL gate）

### 可选输入
- `topic_cards.json` - 选题卡片详细信息
- `--run-id` - 自定义运行ID（默认自动生成）
- `--output-dir` - 自定义输出目录

## 输出产物

### 文档交付视图
- `03_ReasoningSheet_<topic>.md` - 论证结构表（包含论断、证据、缺失证明）
- `03_标准初稿_<topic>.md` - 标准初稿（每个选题一篇）
- `03_初稿_报告.md` - 初稿生成报告

### 正式状态源（Canonical State）
- `draft_manifest.json` - 初稿清单（包含所有初稿元数据）
- `final_structure_snapshot.json` - **MANDATORY GATE** - 最终结构快照（供Material和Rewrite阶段使用）

### 结构化数据
- `03_ReasoningSheet_<topic>.json` - 论证结构JSON（供Material阶段绑定素材）

## 执行方式

### Node.js API
```javascript
const { runDraft } = require('./skills/dasheng-stage-draft');

const result = runDraft('/path/to/selected_topics.json', {
  runId: '2026-04-14_120000',
  topicCardsFile: '/path/to/topic_cards.json',
  outputDir: '/custom/output/dir'
});

console.log(result);
// {
//   success: true,
//   run_id: '2026-04-14_120000',
//   out_dir: '/Volumes/PSSD/Projects/公众号文章/产物/05_初稿生成/2026-04-14_120000',
//   draft_count: 3,
//   draft_files: ['...', '...', '...'],
//   manifest_file: '.../draft_manifest.json',
//   final_structure_snapshot: '.../final_structure_snapshot.json',
//   next_step: 'dasheng-daily-material'
// }
```

### Python 直接调用
```bash
python3 scripts/build_stage3_draft.py \
  /path/to/selected_topics.json \
  /path/to/topic_cards.json \
  --run-id 2026-04-14_120000
```

## Gate 验证规则

### Upstream Gate: `selected_topics.json`
- 必须包含非空的 `selected_topics` 数组
- 每个选题必须有 `topic_id`, `title`, `core_proposition`
- 状态必须为 `approved` 或 `confirmed`

### Output Gate: `final_structure_snapshot.json`
- 初始状态为 `pending`（等待编辑确认）
- 编辑修订初稿后，必须在此文件中写入最终保留的一级/二级结构
- 状态改为 `approved` / `locked` / `finalized` 后，Material 和 Rewrite 才允许继续

## 质量标准

1. **结构限制**：顶层结构严格限制为3-4个一级标题，绝不超过4个
2. **可追溯性**：每个论断（Claim）必须映射到 `EvidenceItem` / `MissingProof` / `ChartNeed`
3. **无内部统计**：绝不在文章内容中包含intake统计数据、聚类数据或内部流程指标
4. **基线稿定位**：这是标准基线稿，不注入风格DNA，不做渠道定制

## 锚点标注规范

生成初稿时，在需要配图/链接的位置使用以下标注：
- `{{image: 描述内容}}` - 配图占位
- `{{link: URL|显示文字}}` - 链接占位
- `{{ref: 来源名称}}` - 参考文献标注

这些锚点将在Material阶段被实际素材替换。

## 人工迭代循环

Draft阶段支持人工+AI迭代循环：
1. 编辑可人工写初稿、修改AI初稿、或投喂范文让AI生成
2. AI生成后，编辑提出修改意见，AI修改，进入下一轮
3. 编辑使用 `@批改意见示例@` 标注需要修改的内容
4. AI完成修改后，必须删除所有 `@` 锚点标记
5. 循环终止条件：编辑发送"approve"/"通过"、确认"中版/终版"、或明确指示"进入下一环节"

## 相关素材附加

如果Intake阶段存在相关主题的文章或视频链接，须附在初稿末尾，供编辑回看和拓展思路。

## 下游阶段

- **Next Stage**: `dasheng-daily-material` (Stage 4 Material - 素材收集)
- **Dependent Stages**: Material (Stage 4), Rewrite (Stage 5)

## 技术实现

- **执行器**: `scripts/build_stage3_draft.py`
- **包装器**: `skills/dasheng-stage-draft/index.js`
- **超时限制**: 5分钟
- **输出格式**: JSON to stdout
