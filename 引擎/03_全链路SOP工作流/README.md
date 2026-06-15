# 全链路 SOP 工作流

本目录用于把现有两层引擎与 `openclaw-skill-exports` 导入的执行能力合并成一条可落地的创作流水线。

当前采用的 6 阶段定义如下：

1. Intake 内容采集
2. Brief：AI-only 选题生成 + Research Brief + 来源确认
3. Draft 写作、可发布底稿与 HTML 草稿
4. Transwrite 转写生产
5. Publish 发布执行
6. Postmortem 复盘

补充能力：`Paradigm Profile 范式学习` 作为阶段 0.5 的可选预处理资产，不单列为正式主链阶段。用户可在正式生产前提供标准文章、爆款样本、渠道模板或内部内容模板，由系统提炼“文章范式与框架”，再按场景、渠道、风格注入 Brief / Draft / Transwrite / Publish 的约束中。

统一原则：

- 每个阶段结尾都必须保留人工干预位，允许增删素材、修正文案、调整结论。
- 每个阶段都必须交付下游可直接消费的文档，不允许只留口头结论。
- 第 3 阶段产出可审核、可发布的正文底稿，不引用内部采集统计当正文论据。
- 第 3 阶段默认采用 `开篇 + 三段论 + 结尾` 或 `开篇 + 4 章 + 结尾`，一级标题不得超过 `4` 个。
- 第 3 阶段可继承 `Paradigm Profile` 中的结构范式；轻量润色和渠道源稿整理并入本环节。
- 第 3 阶段要主动补数据与表格，不做被动复述型初稿。
- 第 3 阶段同步生成可编辑、自包含、离线可用 HTML 草稿；真实图表和配图必须绑定 `claim_id` 与来源。
- 日常对外交付统一导出到桌面：`/Users/lichengyin/Desktop/自媒体创作/<run_id>/`
- `intake / brief / draft / transwrite / publish` 的交付文件统一直接放在该 `run` 根目录，不再另建桌面 stage 子目录

## 合并原则

- 业务结构仍然只有三层：`素材/`、`项目/`、`引擎/`
- `skills/` 是执行器层，不单独视为业务目录
- `openclaw-skill-exports/` 是快照源；实际运行统一以根目录 `skills/` 为准
- L1 负责风格知识沉淀，L2 负责改写与版本延展，L3 负责把前后环节串起来

## 六阶段映射

| 阶段 | 目标 | 主执行器 | 本地引擎/脚本 | 关键产物 |
| --- | --- | --- | --- | --- |
| 01 Intake 内容采集 | 本地 8001 优先采集聊天/新闻流，并用公开新闻与热榜源兜底 | `dasheng-daily-intake` | `scripts/run_stage1_intake.py` | 采集底稿、采集报告、`intake_records` |
| 02 Brief | 基于 canonical intake 生成 8-10 个独立候选题卡，并给出研究入口 | `dasheng-daily-phase2` | `scripts/phase2_rebuilder.py` + `02_Brief_AI生成规则.md` | 编辑 Brief 库、研究 Brief、来源包 |
| 03 Draft | 基于确认选题形成可审核正文底稿，并同步生成可编辑 HTML 草稿 | `dasheng-daily-draft` | `scripts/build_stage3_draft.py` + `05_初稿生成_prompt.md` | 分题正文、HTML 草稿、Reasoning Sheet、质量门禁、`draft_manifest` |
| 04 Transwrite | 基于确认 Draft 生成公众号、口播视频、播客生产包 | `dasheng-stage-transwrite` | `scripts/build_stage4_transwrite.py` | 转写计划、三路 lane manifest、Agent prompt、API 请求体 |
| 05 Publish | 验收转写包，生成发布包，推草稿/人工包并回收链接 | `dasheng-stage-publish` | `scripts/build_stage5_publish.py` + 渠道发布 skill | 发布包、执行清单、验真报告 |
| 06 Postmortem | 回收发布数据并修正模型 | `dasheng-daily-postmortem` | `scripts/postmortem_writeback.py` | 复盘报告、知识库更新 |

独立素材环节已删除；数据、图表、配图和 HTML 嵌入都在 Draft 内完成。`dasheng-stage-rewrite-v3` 只在 Transwrite 需要额外多版本改写时调用，不得阻塞 Publish。

## 可选前置能力：范式学习

`Paradigm Profile` 适合放在 `Brief` 之前、`Intake` 之后或日常生产之外的资产沉淀环节，原因是它学习的是“内容组织方法”，不是单篇事实材料，也不是末端润色技巧。

- **放在 Brief 前**：把样本文章提炼成选题适配规则、叙事角度、章节骨架、论证推进方式，帮助后续题卡直接匹配“该用哪种写法”。
- **作用到 Draft**：标准初稿可采用范式的结构骨架和论证顺序，但不得提前注入作者口吻、情绪词或平台包装。
- **作用到 Transwrite / Publish**：Transwrite 使用范式拆渠道形态，Publish 只按人工确认的发布决策执行。
- **按需工具**：Rewrite 只在具体渠道变体缺口出现时调用，不单列为正式阶段。

推荐对象链补充为：

`Run -> ParadigmProfile(optional) -> TopicPool -> SelectedTopic -> Draft -> TranswritePack -> PublishPack -> Postmortem`

`ParadigmProfile` 应与 `Style DNA` 分开管理：前者回答“这类文章怎么搭结构、怎么推进、适合什么场景”，后者回答“像谁写、用什么语气和句式”。

## 统一对象链路

| 对象 | 来源 | 对应用途 | 建议存放位置 |
| --- | --- | --- | --- |
| `IntakeRecord` | `skills/dasheng-daily-shared/schema/intake-record.schema.json` | 标准化采集条目 | `01_内容采集/` |
| `ContentBrief` | `content-brief.schema.json` | 编辑 Brief 库中的单题卡片 | `02_内容聚合及选题分析/` |
| `OutlinePlan` | `outline-plan.schema.json` | 初稿大纲 | `02_内容聚合及选题分析/` |
| `DraftPackage` | `draft-package.schema.json` | 可审核、可发布正文底稿（每题一篇） | `05_初稿生成/` |
| `TranswritePackage` | 本项目补充约定 | 公众号、口播视频、播客生产包 | `06_转写生产/` |
| `PublishPackage` | 本项目补充约定 | 各渠道执行包 | `07_发布执行/` |
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
- 是否生成了自包含 HTML，并把图表、配图、数据需求绑定到 `claim_id`？

### 04 Transwrite

- 公众号版本是否已完成 DNA/humanize、封面提示和微信格式转写？
- 有真人口播素材时，是否已经转成主动对齐的视觉层计划？
- 没有真人口播素材时，是否已经形成合成音频与动画被动对齐计划？
- 播客是否已经形成 Coze / MiniMax 请求体，并标注 API key 状态？

### 05 Publish

- 转写包是否满足目标平台发布要求？
- 哪些平台能推草稿，哪些只能导出人工包？
- 是否已生成渠道执行清单、发布包和链接回收位？
- 是否明确标记了未完成视频、音频或 API 的阻塞状态？

### 06 Postmortem

- 这篇内容为什么起量或不起量？
- 是选题问题、结构问题、证据问题还是标题问题？
- 哪些模式应该沉淀进 L1，哪些模型权重该调整？

## 推荐执行顺序

1. 阶段 1 完成后，把原始链接和采集结论落到项目目录
2. 阶段 2 形成 Brief、大纲和来源包
3. 阶段 3 生成可审核、可发布正文底稿和可编辑 HTML 草稿
4. 阶段 4 基于确认 Draft 和转写决策生成公众号、口播视频、播客生产包
5. 阶段 5 基于转写包和发布决策生成发布包并执行/半执行分发
6. 阶段 6 复盘并回写 `引擎/01_调性分析引擎/STYLE_KNOWLEDGE_BASE.md`

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
- 阶段 4 Transwrite：`skills/dasheng-stage-transwrite/SKILL.md`
- 阶段 5 Publish：`skills/dasheng-stage-publish/SKILL.md`
- 阶段 6 Postmortem：`引擎/03_全链路SOP工作流/08_分析复盘_prompt.md`
- 按需多版本改写工具：`引擎/03_全链路SOP工作流/06_改写_prompt.md`
- 阶段接口说明：`引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`

## 执行硬规则

- 阶段 1-3 只进事实与编辑决策，不写定稿口吻
- 阶段 3 只写标准初稿，不做风格 DNA 注入，不得把内部流程统计写进正文
- 阶段 3 每个题目单独成文、单独建飞书文档
- 阶段 3 HTML 禁止 CDN/本地引用；Chart.js 必须内联，canvas 图表发布前建议截图替换
- 按需素材工具只补证据与素材，不允许借机改主判断
- 按需多版本改写只在 Transwrite 明确需要多渠道版本时调用，不再阻塞主链
- 阶段 4 的转写生产不能改变核心判断
- 阶段 5 不再生产正文、封面、视频或播客，只做验收、打包、执行和链接回收
- 阶段 6 必须给出“继续做 / 停止做 / 继续测试”的明确结论
