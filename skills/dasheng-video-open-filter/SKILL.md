---
name: dasheng-video-open-filter
description: Use when applying open-source warm cinematic portrait filters to Dasheng talking-head videos after rough cut.
---

# Dasheng Video Open Filter｜开源滤镜增强

## 定位

这是 `transwrite -> talking_head_video` 的可选后处理子环节，用于粗剪后给真人口播视频做低风险视觉增强。

默认不再额外生成字幕，适合原视频已经烧录大字幕的场景。

## 技术栈

- FFmpeg 开源滤镜：
  - `hqdn3d`：全局降噪柔化
  - `bilateral`：亮度平面轻磨皮
  - `colorbalance` / `colorlevels` / `eq`：暖光电影调色、增白、对比度与饱和度
  - `gradfun`：减轻色带
  - `unsharp`：柔化后轻锐化
  - `vignette`：轻电影暗角
  - `scale` / `pad`：低风险轻拉瘦
- 音频沿用粗剪链路的 FFmpeg 开源增强：`afftdn -> dynaudnorm -> acompressor -> loudnorm -> alimiter`

## 推荐命令

```bash
cd "${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}"

.venv_media/bin/python scripts/video_open_filter.py \
  --input-video "/path/to/roughcut_hardsub.mp4" \
  --output-dir "产物/06_转写生产/<run_id>/talking_head_video/open_filter" \
  --preset warm_cinema \
  --strength medium
```

先看 15 秒预览：

```bash
.venv_media/bin/python scripts/video_open_filter.py \
  --input-video "/path/to/roughcut_hardsub.mp4" \
  --output-dir "tmp/video_filter_preview" \
  --preset warm_cinema \
  --strength medium \
  --preview-only
```

## 强度建议

- `soft`：轻暖光、轻柔化，最不容易塑料感。
- `medium`：默认交付强度，暖光明显，人物更白，画面更电影。
- `strong`：仅用于灰暗、噪点重、人物太暗的视频；容易让字幕边缘和皮肤质感变假。

## 约束

1. 原视频已有硬字幕时，不再封装 softsub，避免两套字幕。
2. 当前素材是侧脸远景时，不启用局部 FaceMesh 拉瘦，避免人脸和字幕漂移。
3. `slim-factor` 不低于 `0.94`；推荐 `0.982-0.988`。
4. 任何强滤镜版本必须保留原片对照审核页。
