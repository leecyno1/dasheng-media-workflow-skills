# AI：真正拉开差距的是功能演示还是工作流落地 素材执行手册

- 主题类型：`industry_tech`
- 生成依据：`final_doc_ai_reading`
- Layer 5 模板：`story_page`

## 先做什么

1. 先按 `charts/csv/chart_anchor_plan.csv` + `charts/config/chart_quality_gate.json` 执行图表质量门控。
   - 阈值：CV>=0.03、|slope|>=0.005、R²>=0.25、trend_strength>=0.30。
   - 未达阈值时不生成图表 PNG，改输出逻辑关系表：`charts/csv/*.csv` + `charts/markdown/*.md`。
2. 再跑 `images/web_search` 与 `videos/web_search` 的下载，并检查 `videos/web_search/video_quality_audit_report.json`。
3. 关注 pack 根目录自动生成的 `video_quality_regression_report.json` / `video_quality_regression_report.md` 汇总。
4. AI 图像至少补齐连环画 0 张，梗图 0 张，搞笑人物 0 张。
5. 需要交互稿时，再按 `layer5/layer5_delivery_plan.json` 接入 worldmonitor。

## 视频质检规则

- 分辨率门槛：关闭（按来源可追溯、时长、帧变化筛选）。
- 来源放宽：允许新闻直播 / 访谈素材。
- 来源拦截：过滤口播自媒体出镜内容。
- 防拼接：启用“文件来源 + 时长 + 帧变化”三重检查，拦截截图拼视频。

## 推荐技能

- `media-downloader`：下载图片与视频。
- `baoyu-infographic`：生成信息图。
- `baoyu-imagine` / `ai-image-generation`：生成封面、连环画、梗图。
- `remotion-best-practices`：把 scene_plan 做成视频。
- `worldmonitor`：作为 Layer 5 交互交付页母体。

## 执行命令

- 推荐主链命令：`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.sh --draft-manifest /path/to/draft_manifest.json --topic-dir topic-ai-真正拉开差距的是功能演示还是工作流落地 --steps charts,image_search,video_search,ai_prep`
- 正式命令：`python3 /Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.py --draft-manifest <draft_manifest.json>`
