# Layer 5 输出规范：Finance Motion Deck

本文件定义 `Finance Motion Deck` 接入当前自媒体 SOP 后，应该交付什么，不应该交付什么，以及如何回传给发布环节。

## 1. 输出定位

Layer 5 不是正文，不是发布渠道文案，也不是大而全的可视化平台。它的定位只有三个：

- 给长文提供可点击的配套交互页
- 给视频提供配套的节奏预览页和动效数据页
- 给编辑/运营提供可审核的 scene deck

## 2. 标准输出物

每次运行 Layer 5，标准输出建议包括以下文件：

- `index.html`
- `scenes.json`
- `layer5_manifest.json`
- `layer5_report.md`
- `preview_cover.png`

如需进入视频链，还应补充：

- `scene_export_plan.json`
- `remotion_handoff.json`

建议目录：

- `产物/05_素材收集/<日期项目>/layer5/output/`

## 3. 输出类型定义

### A. `timeline_page`

用途：

- 时政事件梳理
- 宏观叙事演进
- 政策-市场-资产的顺序拆解

标准组成：

- 1 个 `timeline` scene
- 1 个 `ticker` scene
- 1 个总结型 `barGrow` / `bubbleScatter`

### B. `video_companion_page`

用途：

- 给视频审核时看节奏
- 给发布时做额外配套链接
- 给剪辑师确认信息块顺序

标准组成：

- 5-10 个 scene 的自动轮播 deck
- 每个 scene 对应一个正文锚点或视频锚点
- 可直接截图供封面/中插使用

### C. `light_data_story`

用途：

- 给长文补充“证据展示层”
- 给运营做朋友圈、公众号、知识星球附加链接

标准组成：

- 2-4 个图表型 scene
- 1 个时间线或摘要型 scene
- 1 个结论页 scene

## 4. `layer5_manifest.json`

作用：给下游发布环节和归档环节提供总索引。

推荐字段：

```json
{
  "topic_id": "reinflation_2026_03_27",
  "engine": "finance-motion-deck",
  "source_dashboard": "/Volumes/PSSD/Projects/finance-motion-8787/dashboard",
  "output_dir": "产物/05_素材收集/2026-03-27_xxx/layer5/output",
  "deliveries": [
    {
      "type": "timeline_page",
      "entry": "index.html",
      "scene_ids": ["event-run", "macro-line-core", "headline-strip"]
    }
  ],
  "preview_assets": [
    "preview_cover.png"
  ],
  "handoff_files": [
    "remotion_handoff.json"
  ]
}
```

## 5. `layer5_report.md`

作用：人工审核用，不面向外发。

建议包含：

- 本次调用主题
- 产出了哪些 scene
- 每个 scene 对应哪个正文锚点
- 哪些 scene 可直接截图进文章
- 哪些 scene 适合进入视频
- 当前未覆盖的缺口

长度保持简洁，重点做“能不能用”的判断。

## 6. 对发布环节的交付接口

Layer 5 向 `07 发布` 只交付三类东西：

- 可点击网页入口
- 可复用的截图/封面
- 可交给视频链的 scene 计划

发布环节可消费字段：

- `entry_url_or_path`
- `preview_cover`
- `recommended_embed_position`
- `recommended_caption`
- `recommended_scene_for_video`

## 7. 对视频链的交付接口

如果要进一步送入 Remotion 或视频剪辑环节，Layer 5 不直接输出成片，而是输出 `remotion_handoff.json`。

建议包含：

- `scene_id`
- `template`
- `duration_ms`
- `data_ref`
- `recommended_voiceover`
- `asset_refs`

原则：

- Layer 5 负责“可视化表达结构”
- Remotion 负责“成片渲染”

## 8. 可接受的输出风格边界

允许：

- 金融图表风格
- 轻交互轮播
- 单页卡片切换
- 时间线播放
- 结论页收束

不允许：

- 多级路由专题站
- 高耦合后端查询页
- 真实地图底图系统
- 把正文整篇搬成网页

## 9. 财经 / 时政共用边界

### 共用输出

- `timeline_page`
- `video_companion_page`
- `light_data_story`
- `preview_cover.png`
- `remotion_handoff.json`

### 财经优先输出

- 多线图
- K 线
- 热力图
- 配置拆分
- 因子散点

### 时政优先输出

- 事件时间线
- headline ticker
- 风险等级条图
- 关系变化对比图

### 明确不在当前母体内的输出

- 地缘地图页
- 航运/港口真实空间互动页
- 复杂地理路线可视化

## 10. 进入发布前的验收标准

Layer 5 交付只有同时满足以下条件，才算可进入发布环节：

- scene 与正文锚点已建立映射
- 所有数值来源已在 Material 环节核验
- 页面不引入新的事实判断
- 至少有 1 张可直接用于发布的截图
- 至少有 1 份可交给视频链的 handoff 文件

## 11. 最小推荐输出组合

对绝大多数财经/时政选题，推荐默认只产出以下 5 项：

- `index.html`
- `scenes.json`
- `layer5_manifest.json`
- `layer5_report.md`
- `preview_cover.png`

如果该题要进入视频化，再额外增加：

- `remotion_handoff.json`

这就是当前项目里 Layer 5 的最小稳定交付面，不再外扩。
