# Material 环节技术方案

更新时间：`2026-03-27`

## 一、定位

`material` 阶段不再是“补几张图”的松散动作，而是整个创作流里负责把终稿变成“可发、可剪、可视化、可做专题页”的资产工厂。

它解决四件事：

1. 把终稿结构与 `Reasoning Sheet` 中的 claim 转成可执行素材任务。
2. 补齐真实数据与图表。
3. 补齐真实图片、真实视频与 AI 辅助视觉。
4. 在需要时，生成交互式 Layer 5 增强交付包。

## 二、推荐分层

### Layer 1｜硬数据层

- `Python 3`
- `pandas`
- `numpy`
- `matplotlib`
- `akshare`
- `tushare`
- 官方统计 / FRED / BLS / BEA / 交易所

职责：

- 生成真实 `csv`
- 输出真实 `png` 图表
- 给正文和视频提供可复核的数据底座

### Layer 2｜真实媒体采集层

- `media-downloader`
- 原始链接回查
- Web 搜索补图
- Web 搜索补视频

职责：

- 下载多人、场景、群体、地图、工业、城市、航运、战争、市场等镜头
- 避免采访、口播、字幕污染

### Layer 3｜AI 视觉生成层

- `baoyu-infographic`
- `baoyu-imagine`
- `ai-image-generation`
- 可选：`baoyu-article-illustrator`

职责：

- 信息图
- 封面图
- 连环画分镜
- 梗图 / 搞笑图

注意：

- AI 图像不是证据层，只能做表达增强。

### Layer 4｜视频装配层

- `remotion-best-practices`
- `ffmpeg`

职责：

- 按 scene plan 把图表、视频素材、AI 图像、口播脚本装成视频
- 财经和时政都共用同一视频装配底座

### Layer 5｜增强交付层（可选）

- 复用：`/Volumes/PSSD/Projects/worldmonitor`

职责：

- 交互式故事页
- 时间线页
- 风险地图页
- 数据专题页

原则：

- 这是外挂，不进入正文主链路
- 只吃 `json/csv/png/md`

## 三、默认交付配额

每个话题默认生成：

- 图表锚点：`4-8` 个
- 图片检索词：`10` 条
- 视频检索词：`8` 条
- 原始来源视频链接：尽量 `3` 条以上
- 信息图提示词：`3` 条
- 连环画：`10` 张
- 梗图：`3` 张
- Layer 5 计划：`1` 份

## 四、资产目录标准

```text
pack_assets/<topic>/
├── charts/
│   ├── csv/
│   └── png/
├── images/
│   ├── generated/
│   └── web_search/
├── videos/
│   ├── source_links/
│   └── web_search/
├── prompts/
├── config/
└── layer5/
```

## 五、执行顺序

1. 先生成图表锚点与数据源计划
2. 再补真实图片与视频
3. 再生成 AI 信息图、连环画、梗图
4. 最后决定是否触发 Layer 5

## 五点五、统一执行入口

- 执行脚本：`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.sh`
- Python 主体：`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.py`
- 默认解释器：优先走 `.venv_media/bin/python`，避免系统 Python 的 `numpy / pyarrow` 冲突
- 并行执行器：`/Volumes/PSSD/Projects/公众号文章/scripts/material_parallel_launcher.py`

示例：

```bash
/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.sh \
  --draft-manifest /Volumes/PSSD/Projects/公众号文章/产物/05_初稿生成/<run_id>/draft_manifest.json
```

并行示例：

```bash
python3 /Volumes/PSSD/Projects/公众号文章/scripts/material_parallel_launcher.py \
  --draft-manifest /Volumes/PSSD/Projects/公众号文章/产物/05_初稿生成/<run_id>/draft_manifest.json \
  --topics <topic-1 topic-2>
```

## 六、当前工程判断

- 旧版 `skills/dasheng-daily-material/index.js` 只有占位字段，不足以支撑实际发布。
- 本轮已升级为“结构化资产包生成器”，先把每题的素材执行清单全部落盘。
- 下一步要做的是把下载器、图表脚本、AI 图像脚本逐步挂到这个结构上，而不是继续散落在临时目录。
