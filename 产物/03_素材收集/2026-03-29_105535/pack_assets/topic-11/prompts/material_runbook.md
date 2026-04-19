# 一键安装OpenClaw+常用skills，你奶奶5分钟也能用上龙虾 素材执行手册

- 主题类型：`geopolitics`
- Layer 5 模板：`geo_timeline_map`

## 先做什么

1. 先按 `charts/csv/chart_anchor_plan.csv` 生成真实图表与 CSV。
2. 再跑 `images/web_search` 与 `videos/web_search` 的下载。
3. AI 图像至少补齐连环画 10 张，梗图 3 张。
4. 需要交互稿时，再按 `layer5/layer5_delivery_plan.json` 接入 worldmonitor。

## 推荐技能

- `media-downloader`：下载图片与视频。
- `baoyu-infographic`：生成信息图。
- `baoyu-imagine` / `ai-image-generation`：生成封面、连环画、梗图。
- `remotion-best-practices`：把 scene_plan 做成视频。
- `worldmonitor`：作为 Layer 5 交互交付页母体。

## 执行命令

- 统一执行器：`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.sh --pack-root /path/to/pack_assets/topic-11 --steps charts,image_search,video_search,ai_prep`
