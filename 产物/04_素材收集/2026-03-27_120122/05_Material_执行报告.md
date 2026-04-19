# 05 Material 执行报告

- 执行批次：`2026-03-27_120122`
- 执行目录：`/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122`
- Pack Root：`/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets`
- 执行步骤：`charts` / `image_search` / `video_search` / `ai_prep`
- 说明：本次在两篇已确认选题素材包基础上，先补齐图表与视频，再接入 `Minimax` 自动出图，并完成时政题安全改写。

## 总结论

- `Gemini 3.1 flash image preview` 已接入执行器，但当前 `vectorengine` 图像通道仍不可用，实际成功数为 `0`
- `Minimax` 国内接口 `https://api.minimaxi.com` 已打通，且已固化到执行器
- 财经题可稳定出图；时政题需经过“建筑 / 人群 / 地图 / 数据卡片 / 物流网络”式安全改写后才能稳定出图

## 主题一：再通胀

- 真实图表：4 张
- 视频素材：目录内累计 `7` 段 `.mp4`
- AI 实图：已落地 `5` 张，失败 `1` 张
- 已有图片：
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/cover.png`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/infographic_1.png`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/infographic_3.png`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/comic-01.png`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/comic-02.png`
- 未过审项：
  - `infographic_2.png`：`input new_sensitive`，已二次改写 prompt 并单独重跑，仍失败
- 关键清单：
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/ai_generation_manifest.json`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/reinflation/images/generated/minimax/generation_manifest.json`

## 主题二：高市早苗 / 日本右转

- 真实图表：4 张
- 视频素材：目录内累计 `8` 段 `.mp4`
- AI 实图：已落地 `15` 张，全部成功
- 已有图片结构：
  - 封面：1 张
  - 信息图：3 张
  - 连环画：8 张
  - 梗图：3 张
- 关键目录：
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/takaichi/images/generated`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/takaichi/images/generated/minimax/generation_manifest.json`
  - `/Volumes/PSSD/Projects/公众号文章/产物/04_素材收集/2026-03-27_120122/pack_assets/takaichi/images/generated/minimax/_sanitized_prompts`

## 本轮关键改造

- 执行器：`/Volumes/PSSD/Projects/公众号文章/scripts/material_execute_pack.py`
- 新增能力：
  - 自动修复重复拼接的 `MINIMAX_API_KEY`
  - 自动切换 `Minimax` 国内接口
  - `Gemini` / `Minimax` 分开统计与限额控制
  - 地缘政治题自动执行安全改写
  - 已存在图片自动跳过，避免重复出图
  - `jobs=1` 与延迟节流，降低 RPM 报错

## 风险与待办

- `Gemini` 图像通道仍不可用，后续如上游恢复，可再打开真实出图分支
- 再通胀题仍有 `1` 张信息图未过审，需要单独改写 prompt 后补跑
- 再通胀题剩余 `infographic_2` 在 `Minimax` 上连续重试仍失败，后续建议换模型而不是继续在同通道消耗
- 当前 `image_search` 产出偏弱，后续可补接更稳定的网络图源

## 推荐下一步

1. 审核两题 `images/generated`、`videos/web_search`、`charts/png`
2. 优先把再通胀题剩余 `infographic_2` 补齐
3. 将已生成图片按 rewrite 锚点插回稿件
4. 如需发布图文或视频，再进入下游 `rewrite` / `publish` 环节
