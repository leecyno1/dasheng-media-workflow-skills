# 全链路 SOP 工作流

本目录用于把现有两层引擎与 `openclaw-skill-exports` 导入的执行能力合并成一条可落地的创作流水线。

当前采用的 7 阶段定义如下：

1. Intake 内容采集
2. Brief：AI-only 选题生成 + Research Brief + 来源确认
3. Draft 初稿
4. Material 素材收集（含补素材）
5. 改写
6. 发布
7. 复盘

统一原则：

- 每个阶段结尾都必须保留人工干预位，允许增删素材、修正文案、调整结论。
- 每个阶段都必须交付下游可直接消费的文档，不允许只留口头结论。
- 第 3 阶段只产出“标准初稿基线”，不做风格 DNA 注入，不做渠道定制，不引用内部采集统计当正文论据。
- 第 3 阶段默认采用 `开篇 + 三段论 + 结尾` 或 `开篇 + 4 章 + 结尾`，一级标题不得超过 `4` 个。
- 第 3 阶段要主动补数据与表格，不做被动复述型初稿。
- 日常对外交付统一导出到桌面：`/Users/lichengyin/Desktop/自媒体创作/<run_id>/`
- `intake / brief / draft / rewrite / material` 的交付文件统一直接放在该 `run` 根目录，不再另建桌面 stage 子目录

## 合并原则

- 业务结构仍然只有三层：`素材/`、`项目/`、`引擎/`
- `skills/` 是执行器层，不单独视为业务目录
- `openclaw-skill-exports/` 是快照源；实际运行统一以根目录 `skills/` 为准
- L1 负责风格知识沉淀，L2 负责改写与版本延展，L3 负责把前后环节串起来

## 七阶段映射

| 阶段 | 目标 | 主执行器 | 本地引擎/脚本 | 关键产物 |
| --- | --- | --- | --- | --- |
| 01 Intake 内容采集 | 把外部信息拉齐并标准化 | `dasheng-daily-intake` | `scripts/run_stage1_intake.py` | 采集底稿、采集报告、`intake_records` |
| 02 Brief | 基于 canonical intake 生成 8-10 个独立候选题卡，并给出研究入口 | `dasheng-daily-phase2` | `scripts/phase2_rebuilder.py` + `02_Brief_AI生成规则.md` | 编辑 Brief 库、研究 Brief、来源包 |
| 03 Draft 初稿 | 基于确认选题与已知外部来源形成标准底稿 | `dasheng-media-sop` | `05_初稿生成_prompt.md` + `03_标准初稿结构模板.md` + `05_标准初稿检查清单.md` | 分题标准初稿、证据清单 |
| 04 Material | 围绕编辑确认后的终稿缺口补证据、图、案例，并完成回填 | `dasheng-daily-material` | TuShare / AkShare 图表脚本、`scripts/material_*` | Material Pack、图表、引文、缺口清单、回填说明 |
| 05 改写 | 基于回填后终稿生成每题 4 版独立改写 | `dasheng-media-sop` | L1 风格库 + L2 改写引擎 + `scripts/feishu_rewrite_push.js` | 每题 4 版改写、bundle、meta、飞书文档 |
| 06 发布 | 生成最终发布包并执行分发 | 渠道模板 + 人工确认 | `07_渠道分发模板.md` | 发布包、发布时间、渠道成品 |
| 07 复盘 | 回收发布数据并修正模型 | `dasheng-daily-postmortem` | `scripts/style_ingest.py` | 复盘报告、知识库更新 |

## 统一对象链路

| 对象 | 来源 | 对应用途 | 建议存放位置 |
| --- | --- | --- | --- |
| `IntakeRecord` | `skills/dasheng-daily-shared/schema/intake-record.schema.json` | 标准化采集条目 | `01_内容采集/` |
| `ContentBrief` | `content-brief.schema.json` | 编辑 Brief 库中的单题卡片 | `02_内容聚合及选题分析/` |
| `OutlinePlan` | `outline-plan.schema.json` | 初稿大纲 | `02_内容聚合及选题分析/` |
| `DraftPackage` | `draft-package.schema.json` | 标准初稿（每题一篇） | `05_初稿生成/` |
| `FinalPackage` | `final-package.schema.json` | 改写稿与发布主版本 | `06_改写/` 与 `07_渠道分发/` |
| `MaterialPack` | `material-pack.schema.json` | 素材包与终稿回填说明 | `03_素材收集/` |
| `DistributionPackage` | 本项目补充约定 | 各渠道成品包 | `07_渠道分发/` |
| `PostmortemRecord` | `postmortem-record.schema.json` | 复盘记录 | `08_分析复盘/` |

## 每一阶段必须回答的问题

### 01 Intake

- 今天哪些信息值得看？
- 这些信息的原始链接是否齐全？
- 是否已经区分了新闻、观点、二手转述和个人判断？

### 02 Brief

- 哪些条目其实在讨论同一件事？
- 哪些是噪声，哪些是真正的母题？
- 当前最值得编辑筛选的 8-10 个题是什么？
- 每个题的一步深化、大纲骨架和来源边界是什么？
- 如果人工指定了题，是否已经强制入池？

### 03 Draft

- 正文里的每个事实是否都能回溯到外部来源？
- 是否完全剔除了 intake、brief、内部统计等流程数据？
- 是否输出的是“标准稿”，而不是已被风格化的发布稿？
- 是否把一级标题压在 `3-4` 个以内，而不是碎片化罗列？
- 是否主动补充了必要数据表、时间线或对比表？

### 04 Material

- 编辑确认后的终稿缺口是否已补齐？
- 哪些图必须画，哪些图可以不要？
- 哪些数据、图片、引用需要回填？
- 回填后是否改变原有主判断？

### 05 改写

- 是否在不改变事实边界的前提下完成逻辑压缩、语气统一、标题增强？
- 是否按每题独立产出 4 个版本，而不是混成一个总文档？
- 是否都基于回填后终稿，而不是回退到旧初稿？
- 是否全部通过字数硬校验，并生成 `rewrite_bundle.md` 与 `meta.json`？

### 06 发布

- 同一观点是否已按平台消费方式重写？
- 首屏、标题、封面、摘要是否各自独立优化？
- 是否保留统一判断，但改变表达密度和节奏？

### 07 复盘

- 这篇内容为什么起量或不起量？
- 是选题问题、结构问题、证据问题还是标题问题？
- 哪些模式应该沉淀进 L1，哪些模型权重该调整？

## 推荐执行顺序

1. 阶段 1 完成后，把原始链接和采集结论落到项目目录
2. 阶段 2 形成 Brief、大纲和来源包
3. 阶段 3 先生成标准初稿
4. 阶段 4 围绕编辑确认后的终稿缺口补足证据并回填
5. 阶段 5 基于回填后终稿生成每题 4 版改写
6. 阶段 6 生成发布包并执行分发
7. 阶段 7 复盘并回写 `引擎/01_调性分析引擎/STYLE_KNOWLEDGE_BASE.md`

## 飞书同步执行模式

- 常规模式：
  - `python3 /Volumes/PSSD/Projects/公众号文章/scripts/feishu_stage_sync.py <run_id>`
  - `python3 /Volumes/PSSD/Projects/公众号文章/scripts/feishu_stage_sync.py --latest`
- 断点续跑：
  - `python3 /Volumes/PSSD/Projects/公众号文章/scripts/feishu_stage_sync.py --resume-only <run_id>`
  - 适用于飞书同步中断、超时、Node 进程退出、素材上传做到一半的场景
  - 会读取 `skills/dasheng-daily-shared/runtime-data/runs/<run_id>/bridge/live-execution-progress.json`
  - 已完成的 action 会跳过，只继续未完成部分
- 强制重跑：
  - `python3 /Volumes/PSSD/Projects/公众号文章/scripts/feishu_stage_sync.py --fresh <run_id>`
  - 适用于旧进度错误、文档映射错乱、确认需要整套重建的场景
  - 会清理本次 run 的 live 进度与同步摘要，再重新执行
- 执行原则：
  - 默认先用 `--resume-only`
  - 只有明确要放弃旧进度时才用 `--fresh`
  - `--fresh` 和 `--resume-only` 不能同时使用

## Prompt 入口

- 控制中心入口：`引擎/00_控制中心/00_控制文件导航.md`
- 阶段 1：`引擎/03_全链路SOP工作流/01_内容采集_prompt.md`
- 阶段 2：`引擎/03_全链路SOP工作流/02_内容聚合及选题分析_prompt.md`
- 阶段 2 标准模板：`引擎/03_全链路SOP工作流/02_标准编辑Brief模板.md`
- 阶段 3：`引擎/03_全链路SOP工作流/05_初稿生成_prompt.md`
- 阶段 3 结构模板：`引擎/03_全链路SOP工作流/03_标准初稿结构模板.md`
- 阶段 4：`引擎/03_全链路SOP工作流/04_素材收集_prompt.md`
- 阶段 5：`引擎/03_全链路SOP工作流/06_改写_prompt.md`
- Layer 5 输入规范：`引擎/03_全链路SOP工作流/05_5_Layer5输入规范_FinanceMotionDeck.md`
- Layer 5 输出规范：`引擎/03_全链路SOP工作流/05_5_Layer5输出规范_FinanceMotionDeck.md`
- 阶段 6：`引擎/03_全链路SOP工作流/07_渠道分发_prompt.md`
- 阶段 6 模板：`引擎/03_全链路SOP工作流/07_渠道分发模板.md`
- 阶段 7：`引擎/03_全链路SOP工作流/08_分析复盘_prompt.md`
- 阶段接口说明：`引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 执行硬规则

- 阶段 1-3 只进事实与编辑决策，不写定稿口吻
- 阶段 3 只写标准初稿，不做风格 DNA 注入，不得把内部流程统计写进正文
- 阶段 3 每个题目单独成文、单独建飞书文档
- 阶段 4 只补证据与素材，并直接回填到终稿文档，不允许借机改主判断
- 阶段 5 每个题目必须形成 4 个独立改写版本，并通过字数硬校验
- 阶段 6 的发布包装不能改变核心判断
- 阶段 7 必须给出“继续做 / 停止做 / 继续测试”的明确结论
