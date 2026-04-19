# 第04环节 Material Pack

运行批次：`2026-04-10_074121`
上游对象：`MaterialInput[]`
上游入口：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime-data/runs/2026-04-10_074121/artifacts/material/material_ai_inputs.json`
素材包根目录：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime-data/runs/2026-04-10_074121/artifacts/material/pack_assets`

## 本轮标准

- Material 优先消费 `ReasoningSheet`；若未提供，则向后兼容旧 `ContentBrief`。
- 每个话题默认补：图表锚点、图片检索词、新闻截图检索词、视频检索词、AI 图像计划、Layer 5 交互交付计划。
- AI 图像默认包含：封面、信息图、连环画、梗图、搞笑漫画人物。
- 视频素材默认分两路：素材库原始链接 + 外网检索下载线索。
- 视频质检默认：不设分辨率硬门槛，允许新闻直播/访谈，过滤口播自媒体，拦截截图拼视频。

## 话题清单

### 题目 1：鲍威尔讲话终结加息预期引发市场转向降息押注

- 主题类型：`finance_macro`
- 素材目录：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime-data/runs/2026-04-10_074121/artifacts/material/pack_assets/t001`
- Layer 5 模板：`market_story`
- Claim 绑定：4 条
- 图表锚点：4 个
- 图片计划：8 项
- 视频计划：9 项
- 主要缺口：文章结构清晰，论证充分，主要缺口在于具体市场数据和图表展示以增强说服力；不涉及需要视频动态演示的内容，且漫画和梗图不适用。

### 题目 2：中东冲突与霍尔木兹海峡封锁导致油价坚挺形成全球能源供应链风险

- 主题类型：`finance_macro`
- 素材目录：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime-data/runs/2026-04-10_074121/artifacts/material/pack_assets/t002`
- Layer 5 模板：`market_story`
- Claim 绑定：4 条
- 图表锚点：1 个
- 图片计划：9 项
- 视频计划：10 项
- 主要缺口：全文重点在于地缘政治影响与能源供应链风险，已有详细文字分析和示意数据，文章未涉及具体人物访谈或事件现场图片需求，且无明确适合视频补充的动态场景，故不补充视频及漫画、梗图素材。

### 题目 3：全球央行大规模抛售美债引发金融市场系统性风险担忧

- 主题类型：`finance_macro`
- 素材目录：`/Volumes/PSSD/Projects/公众号文章/skills/dasheng-daily-shared/runtime-data/runs/2026-04-10_074121/artifacts/material/pack_assets/t003`
- Layer 5 模板：`market_story`
- Claim 绑定：4 条
- 图表锚点：3 个
- 图片计划：8 项
- 视频计划：4 项
- 主要缺口：全文结构清晰，论点充分，主要缺口在权威数据支持和具体量化指标，尤其是央行美债持仓变化、抛售规模及市场流动性指标。文中已有权威视频链接支持抛售事实，部分数据需后续补充，不宜强行添加无数据支撑的图表。视频素材适合补充动态市场反应。

