# Material 技能矩阵

更新时间：`2026-04-14`

## 保留并正式集成

| Skill | 用途 | 集成决策 | 在 Material 中的角色 |
| --- | --- | --- | --- |
| `news-radar` | 国际新闻聚合与多源趋势判断 | 正式集成 | 热点证据池 / 新闻线索 |
| `web-search` | 通用网页检索 | 正式集成 | 图片/新闻页/背景检索 |
| `multi-search-engine` | 多搜索引擎并行检索 | 正式集成 | 补充检索召回 |
| `tavily-search` | LLM 友好搜索 | 正式集成 | 结构化搜索补充 |
| `reddit` | Reddit 热点与讨论样本 | 正式集成 | 海外热点补充 |
| `twitter` | X 热点与账号样本 | 正式集成 | 海外人物/机构信号 |
| `google-trends` | 趋势热度变化 | 正式集成 | 趋势判断补充 |
| `wechat-search` | 微信文章搜索 | 正式集成 | 中文资讯补充 |
| `wechat-article-extractor-skill` | 微信文章正文抽取 | 正式集成 | 微信证据抽取器 |
| `xiaohongshu-extract` | 小红书内容抽取 | 正式集成 | 题图/笔记线索抽取 |
| `baoyu-article-illustrator` | 按文章结构补插图 | 正式集成 | 插图规划器 |
| `baoyu-comic` | 连环画/搞笑漫画生成 | 正式集成 | 漫画资产生成 |
| `baoyu-cover-image` | 封面图生成 | 正式集成 | 封面候选 |
| `baoyu-infographic` | 信息图生成 | 正式集成 | 高密度信息图 |
| `baoyu-xhs-images` | 小红书图组生成 | 正式集成 | 社媒图组补充 |
| `baoyu-image-gen` | 多 provider 生图 | 正式集成 | 主生图执行器 |
| `ai-image-generation` | inference.sh 系图像生成 | 正式集成 | 备选生图执行器 |
| `media-downloader` | 智能媒体下载 | 正式集成 | 图片/视频下载助手 |
| `video-download` | 通用视频下载 | 正式集成 | 外链视频落盘 |
| `video-frames` | 视频抽帧 | 正式集成 | 截帧图补充 |
| `video-subtitles` | 字幕生成与转写 | 正式集成 | 视频理解补充 |
| `bilibili-youtube-watcher` | B站/YouTube 视频转录 | 正式集成 | 长视频内容理解 |
| `remotion` | Remotion 规范 | 正式集成 | 视频模板规范 |
| `remotion-video` | 标准 Remotion 视频工作流 | 正式集成 | 叙事视频执行层 |
| `remotion-video-toolkit` | Remotion 工具箱 | 正式集成 | 动效能力补充 |

## 集成原则

1. `material` 先读终稿、ReasoningSheet、claim 与锚点，再决定调用哪类 skill。
2. 搜索类 skill 负责“找证据”，不直接替代图表或图片生成。
3. 生成类 skill 负责“产资产”，但必须回写来源、提示词或生成 manifest。
4. 视频类 skill 在 `material` 只承担素材理解与片段获取；正式发布前视频补充仍归 `publish`。
5. 所有能力已统一收口为 `material_skill_stack`，由 `scripts/material_execute_pack.py` 写入 manifest。

## 不作为正式执行器

| Skill | 原因 |
| --- | --- |
| `xiaohongshu-ops` | 偏运营流程，不是 material 执行器 |
| `planner-image-post` | 可作为创意辅助，但不作为正式主链入口 |
| `planner-video-script` | 更适合 rewrite/publish 的视频脚本，不作为 material 主执行器 |
