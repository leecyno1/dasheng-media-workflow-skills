# Layer 5 增强交付融合方案

更新时间：`2026-03-27`

## 一、结论

`8787` 对应的增强交付层，不应在当前仓库内重写。

最合适的复用母体是：

- `/Volumes/PSSD/Projects/worldmonitor`

不建议混入的是：

- `/Volumes/PSSD/Projects/openclaw/src/telegram/webhook.ts`

原因很简单：

- `worldmonitor` 已经具备故事页、时间线、地图、面板等内容交付能力。
- `openclaw` 里的 `8787` 更偏 webhook 与消息入口，不是内容交付前端。

## 二、关键位置

### 1. 代理与端口

- `/Volumes/PSSD/Projects/worldmonitor/deploy/nginx/brotli-api-proxy.conf`

说明：

- 这里把请求反代到 `http://127.0.0.1:8787`
- 当前本机 `8787` 没有进程监听，因此只能先按“接口约定”融合，不直接依赖在线服务

### 2. 前端入口

- `/Volumes/PSSD/Projects/worldmonitor/src/main.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/App.ts`

### 3. API 与页面能力

- `/Volumes/PSSD/Projects/worldmonitor/api/story.js`
- `/Volumes/PSSD/Projects/worldmonitor/api/og-story.js`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/CountryTimeline.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/DeckGLMap.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/MarketPanel.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/EconomicPanel.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/StrategicRiskPanel.ts`
- `/Volumes/PSSD/Projects/worldmonitor/src/components/StrategicPosturePanel.ts`

## 三、融合边界

只做三件事：

1. 内容注入
2. 数据喂给
3. 模板裁剪

不做三件事：

1. 不回写正文
2. 不改写 SOP 前四阶段
3. 不在本仓库重复造一套前端

## 四、模板分工

### 财经专题

- 推荐模板：`market_story`
- 组件优先：
  - `MarketPanel`
  - `EconomicPanel`
  - `CountryTimeline`

适合内容：

- 再通胀
- 黄金 / 白银 / 原油
- ETF 配置
- 利率与资产联动

### 时政专题

- 推荐模板：`geo_timeline_map`
- 组件优先：
  - `StrategicRiskPanel`
  - `StrategicPosturePanel`
  - `DeckGLMap`
  - `CountryTimeline`

适合内容：

- 战争
- 制裁
- 台海
- 航运通道
- 日本右转

## 五、输入文件约束

Layer 5 只接这类文件：

- `article.md`
- `scene_plan.json`
- `event_timeline.json`
- `map_layers.geojson`
- `charts/*.csv`
- `charts/*.png`
- `key_metrics.json`

## 六、在 SOP 里的位置

主链路仍是：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

Layer 5 的位置是：

`material` 之后、`publish` 之前的可选外挂分支

也就是：

`material -> Layer 5（可选） -> rewrite -> publish`

## 七、当前执行建议

- 先把 `material` 阶段输出稳定成结构化资产目录。
- 每次只在“财经专题”或“时政专题”里选一类模板，不要混着上。
- 等 `worldmonitor` 重新启动后，再做自动注入，不要在当前阶段强绑定 `8787` 在线可用。
