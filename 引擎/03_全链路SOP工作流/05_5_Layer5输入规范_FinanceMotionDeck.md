# Layer 5 输入规范：Finance Motion Deck

本文件定义 `Layer 5 增强交付（可选）` 对 `Finance Motion Deck` 的标准输入。目标不是重建一套前端系统，而是把上游已经确认过的内容、图表和节奏，转成可直接喂给 `dashboard/scenes.json` 的结构化资产。

适用母体目录：

- `/Volumes/PSSD/Projects/finance-motion-8787/dashboard`

核心输入原则：

- 只吃上游已经确认的结构化结果，不重新做选题判断。
- 只服务交付展示，不反向修改 `draft`、`rewrite` 正文。
- 上游所有事实必须先在正文或素材环节完成核验，Layer 5 只做表现层转换。

## 1. 输入来源阶段

Layer 5 的输入只允许来自以下两个环节：

- `04 改写`：提供文章主结构、分段标题、锚点、主结论。
- `05 Material`：提供图表数据、图片、时间线条目、视频锚点、补充证据。

不允许直接从 `01 intake`、`02 brief` 的内部统计结果生成交互页。

## 2. 标准输入文件清单

每次调用 Layer 5，至少应准备以下文件：

- `layer5_delivery_plan.json`
- `scene_plan.json`
- `scene_data.json`
- `asset_manifest.json`

可选补充文件：

- `timeline.json`
- `charts_index.csv`
- `video_markers.json`
- `captions.md`
- `visual_notes.md`

建议落地目录：

- `产物/05_素材收集/<日期项目>/layer5/`

## 3. `layer5_delivery_plan.json`

作用：定义这次要��什么交付，不含具体大段数据。

推荐字段：

```json
{
  "topic_id": "reinflation_2026_03_27",
  "topic_title": "表面在交易事件，真正的主线会不会其实是再通胀？",
  "vertical": "finance",
  "delivery_types": [
    "timeline_page",
    "video_companion_page",
    "light_data_story"
  ],
  "primary_channel": "wechat_article",
  "related_video_channel": "xiaohongshu_video",
  "tone": "normal",
  "scene_count_target": 8,
  "use_live_data": true,
  "data_priority": [
    "tushare",
    "akshare",
    "manual_verified"
  ],
  "forbidden_outputs": [
    "heavy_map_site",
    "multi-route专题站"
  ]
}
```

## 4. `scene_plan.json`

作用：定义页面/视频里有哪些 scene，以及每个 scene 的展示目的。

每个 scene 至少包含：

- `id`
- `template`
- `label`
- `purpose`
- `source_anchor`
- `data_ref`
- `asset_refs`
- `duration_ms`

推荐示例：

```json
{
  "meta": {
    "title": "再通胀交易交互页",
    "description": "给视频和长文配套的轻交互场景组"
  },
  "scenes": [
    {
      "id": "macro-line-core",
      "template": "multiLine",
      "label": "通胀、利率、商品三线对照",
      "purpose": "先把主线立住",
      "source_anchor": "[图表-01]",
      "data_ref": "scene_data.json#macro-line-core",
      "asset_refs": [],
      "duration_ms": 9000
    },
    {
      "id": "event-run",
      "template": "timeline",
      "label": "事件冲击不是主线，只是引线",
      "purpose": "交代因果顺序",
      "source_anchor": "[图表-02]",
      "data_ref": "timeline.json#event-run",
      "asset_refs": [],
      "duration_ms": 8000
    }
  ]
}
```

## 5. `scene_data.json`

作用：给每个 scene 提供实际绘图数据。

数据要求：

- 数值型字段必须已清洗，可直接绘图。
- 时间字段统一使用 ISO 日期或 `YYYY-MM`。
- 不要把解释性长文塞进这里；说明文字只保留短标签。

模板映射建议：

- `lineRise` / `multiLine`：利率、金价、油价、ETF 规模、仓位序列
- `barGrow` / `stackedBar`：国家比较、板块对比、配置拆分
- `waterfall`：影响拆解、涨跌归因、成本项传导
- `heatmapPulse`：行业分层、情绪热度、时段热度
- `bubbleScatter`：主题注意力 x 确定性、风险 x 回报
- `timeline`：事件序列、政策节奏、市场反应链
- `ticker`：摘要流、bullet point、关键 headline
- `candlestick`：期货/ETF/K 线表现

## 6. `asset_manifest.json`

作用：告诉 Layer 5 可以使用哪些静态资源。

推荐字段：

- `images`
- `charts_png`
- `csv_files`
- `video_stills`
- `cover_candidates`
- `copyright_status`

要求：

- 每个资源要有 `id`、`path`、`source_url`、`usage_scope`
- 没有来源的图，默认不进入 Layer 5

## 7. `timeline.json`

作用：专供 `timeline` 场景和“视频配套交互页”的事件序列。

每个事件建议字段：

- `time`
- `title`
- `summary`
- `evidence_url`
- `importance`

约束：

- 只保留 5-12 个事件点
- 每个标题控制在 8-20 字
- 不要写成长段评论

## 8. 与上游锚点的衔接规则

`rewrite` 阶段已经在正文中插入方括号锚点。Layer 5 只认这些锚点，不自行发明新锚点。

统一写法：

- `[图表-01]`
- `[时间线-01]`
- `[配图-01]`
- `[视频-01]`

要求：

- `scene_plan.json.source_anchor` 必须与正文锚点一致
- 同一个锚点可映射多个 scene，但必须有主次

## 9. 不进入 Layer 5 的内容

以下内容不应进入 `Finance Motion Deck`：

- intake 统计口径
- brief 内部聚类结果
- 编辑打分过程
- 未核验的草稿数据
- 需要真实地理底图的地图任务
- 依赖多接口实时聚合的重型专题站需求

## 10. 最小可运行输入包

如果要快速跑通一次 Layer 5，最小只需要：

- `layer5_delivery_plan.json`
- `scene_plan.json`
- `scene_data.json`
- `asset_manifest.json`

其中至少有：

- 1 个 `timeline`
- 1 个 `multiLine` / `lineRise`
- 1 个 `ticker` / `heatmapPulse`

这三类组合，就足够构成一版可审核的财经/时政配套交付页。
