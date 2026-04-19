---
name: dasheng-daily-intake
description: Use when running the canonical Dasheng intake stage for the current day and producing real-title, real-link source radar outputs for Brief handoff.
---

# dasheng-daily-intake

## 定位

这是 **大圣工作流的 Intake 单环节 Skill**，但执行口径以本地 canonical Stage 1 为准。

它吸收并替代历史上 `dasheng-caiji` 的采集职责，不再并行维护两套采集定义。

职责：
- 执行当天 canonical intake 采集
- 生成真实标题、真实链接的报告 / 底稿
- 输出交给 Brief 的标准 JSON 接口
- 如当前链路要求，再交给飞书同步层做共享文档与群通知

不负责：
- 聚类
- Brief
- 大纲
- 初稿
- 强化版

---

## 数据源

### 1）5173
用途：推荐笔记榜单 / content research / 数据分析分组

固定要求：
- 必须读取 **推荐笔记榜单** 与 **content research** 对应分组内容
- 必须将分组下的核心条目写入飞书文档
- 每条都要带原链接
- 不再要求发送截图

### 2）18080
用途：Newsrear / Reports / 新闻舆情

固定要求：
- 必须写入 **reports 的内容摘要**
- 必须补充当天 `news` 代表性条目
- 每条都要带原链接
- 不再要求发送截图

### 3）8000 public wechat
用途：公众号公开订阅源

固定要求：
- 前端入口可见地址是 `http://45.197.148.64:8000/channels?channel_id=all&platform=wechat`
- 正式抓取一律走其公开 API：`/api/v1/wx/public/channels` 与 `/api/v1/wx/public/channels/<id>/articles`
- 文章原链接通过 `/api/v1/wx/articles/<article_id>` 回补
- 必须把 **公众号文章列表** 写入飞书文档
- 每条都要带原链接

### 4）AI 热点汇总
用途：补充当天 AI / Agent / Skill / Workflow 方向的高时效证据池

固定要求：
- 数据源至少包括：`Reddit RSS`、`Hacker News`、`B站 AI 相关样本`
- 固定输出 `10` 条 `AI热点` 汇总
- 这些样本进入 intake 分析池与 brief handoff 时使用更高权重
- 但不替代全量原始采集底稿

---

## Intake 必须交付的内容

1. `notes/01_内容采集_报告.md`
2. `notes/01_内容采集_底稿.md`
3. `raw/intake_records.json`
4. `ai_hot_topics.json`
5. `channel_top10.json`
6. `event_clusters.json`
7. `brief_input.json`
8. `intake_manifest.json`

---

## 执行顺序

1. 获取 5173 推荐笔记榜单 / content research 分组内容
2. 获取 Reports / news 内容
3. 获取 8000 public wechat 频道与文章（慢源允许等待和补抓）
4. 聚合 Reddit RSS + Hacker News + B站 AI 热点，生成 `AI热点` Top10
5. 对各渠道样本做真实标题清洗、去重、渠道内热度评级
6. 生成渠道 Top10、底稿全量清单、重复/噪音池、TrendRadar 补充池
7. 落盘 canonical manifest 与 handoff 文件
8. 如启用飞书同步，再把 canonical 产物映射到飞书

---

## 硬规则

- **截图全部取消**，不作为 intake 正式交付物
- **报告与底稿必须只出现真实抓取标题**
- **以上内容都必须带原始链接**
- **X / 微博默认各取 100 条，其它平台各取 50 条**
- **每个渠道都要单独产出 Top10；不足 10 条如实展示**
- **`AI热点` 必须单列产出 Top10，并进入 `brief_input.json.ai_hot_candidates`**
- **公众号属于慢源，抓不全时必须等待后补抓，并记录轮次与等待时长**
- **正式执行脚本是**：`/Volumes/PSSD/Projects/公众号文章/scripts/run_stage1_intake.py`

---

一句话版：

**daily intake = 跑本地 canonical Stage 1，生成真实标题 / 真实链接的 intake 雷达，并把标准交接文件交给 Brief。**
