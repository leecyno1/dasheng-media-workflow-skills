# Pack Assets 报告

运行批次：`2026-03-26_123247`

## 1. 当前固化结果

- 已为两个选题建立标准资产目录：`videos/`、`images/`、`charts/`、`prompts/`、`shared/config/`、`shared/scripts/`
- 已落盘 `CSV + PNG` 图表各 `6` 组，对应 6 个锚点
- 已生成 Python 信息图 `6` 张，作为 `baoyu-*` 缺失情况下的可执行 fallback
- 已下载网络图片 `10` 张
- 已下载可直接使用的视频：`source_links` 目录内 `3` 项（其中 1 项为 fallback 替代），`web_search` 目录内 `7` 段视频

## 2. 模型与 skill 状态

- `baoyu-infographic` / `baoyu-image-gen`：本地未发现实体 skill
- `VectorEngine gemini-3.1-flash-image-preview`：已配置，但当前接口返回 `403 渠道已禁用`
- 已保留兼容配置与客户端脚本，位置：
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/vectorengine_gemini_image.env`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/vectorengine_gemini_image.env)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/image_generation_status.json`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/config/image_generation_status.json)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/vectorengine_image_client.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/vectorengine_image_client.py)

## 3. 视频说明

- `Douyin` 原始链接因缺少新鲜 cookies 无法直下
- 已保留失败说明并补入高相关度 fallback：
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/videos/source_links/source_link_03_douyin_failure_note.md`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/videos/source_links/source_link_03_douyin_failure_note.md)

## 4. 可直接使用的重点文件

- 图表清单：
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/charts/png/oil_price_inflation_expectation.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/charts/png/oil_price_inflation_expectation.png)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/charts/png/fed_stagflation_signal.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/charts/png/fed_stagflation_signal.png)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/charts/png/aging_labor_gap.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/charts/png/aging_labor_gap.png)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/charts/png/coalition_right_shift.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/charts/png/coalition_right_shift.png)
- 信息图：
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/images/generated/oil_price_inflation_expectation_infographic.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/reinflation/images/generated/oil_price_inflation_expectation_infographic.png)
  - [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/images/generated/coalition_right_shift_infographic.png`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/takaichi/images/generated/coalition_right_shift_infographic.png)

## 5. 下次复跑入口

- [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/search_youtube_candidates.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/search_youtube_candidates.py)
- [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/download_selected_videos.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/download_selected_videos.py)
- [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/download_wikipedia_images.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/download_wikipedia_images.py)
- [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/generate_anchor_charts.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/generate_anchor_charts.py)
- [`/Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/generate_python_infographics.py`](file:///Volumes/PSSD/Projects/公众号文章/产物/03_素材收集/2026-03-26_123247/pack_assets/shared/scripts/generate_python_infographics.py)
