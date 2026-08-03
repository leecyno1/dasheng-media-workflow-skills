# Video Production Lines

Date: 2026-06-13

本文件定义当前 video 环节的两条主链路。目标是把视频从 publish 补充物升级为 transwrite/video 生产能力，同时保持 publish 只做验收、打包、推草稿和回收链接。

流水线治理、阶段产物契约、工具注册表和审核门见 [video-pipeline-governance.md](video-pipeline-governance.md)。视频生产不再直接从脚本跳到渲染，而是按：

`project run manifest -> pipeline manifest -> stage artifact -> tool registry -> checkpoint/review -> render/publish`

执行。对应配置位于：

- `configs/video/pipelines/talking_head.yaml`
- `configs/video/pipelines/explainer_html.yaml`
- `configs/video/pipelines/style_training.yaml`
- `configs/video/artifact_schemas/*.schema.json`
- `configs/video/tool_registry.json`
- `configs/workflow/project_run_manifest.schema.json`

## Lane A: 真人出镜口播

定位：用户提供真人口播素材，系统完成粗剪、音频优化、字幕校对、导演时间轴、证据层、HTML 贴纸/图表、转场与质检。

导演机制见 [video-editing-driving-mechanism.md](video-editing-driving-mechanism.md)。Lane A 不按“每句话贴一个模板”执行，而按 `speaker_anchor -> claim_closeup -> evidence_fullscreen -> broll_with_pip -> speaker_return` 状态机执行。编辑微镜头生成后，必须先归并为 8-12 个核心命题并通过 Claim/Evidence Ledger，才允许生成正式素材。

外部依赖：

- `html-video` 和 `html-anything` 都是外部依赖，不进入本仓库，不锁版本。
- 首次使用或换机器时运行 `python3 scripts/ensure_video_external_deps.py --dep all --mode install --install-node-deps`。
- 默认路径可用 `HTML_VIDEO_ROOT` / `HTML_ANYTHING_ROOT` 覆盖。
- MiniMax CLI 是配音、配乐、图片生成、口播音频生成的默认入口；使用前运行 `mmx auth status --no-color` 和 `mmx quota --no-color`。

第一产物：

```bash
python3 scripts/video_director_timeline.py \
  --srt <agent_proofread.srt> \
  --source-video <speaker.mp4> \
  --title "<title>" \
  --output <talking_head_timeline.json>
```

关键约束：

- 真人音频/视频是主时间轴。
- Remotion 是主时间轴与合成器；HTML Video、HyperFrames、GSAP 和 Lottie 负责具体场景动画。
- HTML 动画只做证据层、标题卡、图表卡或素材层，不替代真人层。
- 字幕必须先经过 Agent 语义校对，再进入终版渲染。
- 图表和数据必须来自 Draft 文章或已验证数据源，不允许假图。
- 事实、估值比较、因果与历史命题必须有逐项直接证据；传闻、预测和测算必须在画面中披露。
- 最终视频不允许出现开发说明、slot 名、position 名等工作流标签。

参考节奏：

| 指标 | 目标 |
| --- | --- |
| 中位视觉段落 | 2.5-4 秒 |
| B-roll/证据画面占比 | 45%-65% |
| 真人回归间隔 | 8-20 秒 |
| 人声音量 | 约 -16 LUFS |
| 字幕 | 1-2 行，语义断句，无重叠 |

## Lane B: 无真人 HTML 科普

定位：用户提供 HTML 文章，系统生成口播稿、TTS、分镜、HTML 动画、配乐和最终竖版科普视频。

导演机制见 [video-editing-driving-mechanism.md](video-editing-driving-mechanism.md)。Lane B 不做 PPT 翻页，而按 `hook_card -> question_setup -> chapter_card -> evidence_scene -> logic_animation -> cinematic_bridge -> recap_card` 状态机执行。

生产音频/素材默认走 MiniMax CLI：

```bash
mmx speech synthesize \
  --text-file <scene.txt> \
  --out <voice.wav> \
  --model speech-2.8-hd \
  --voice "Chinese (Mandarin)_Radio_Host" \
  --speed 1.08 \
  --format wav \
  --sample-rate 44100 \
  --channels 1 \
  --language Chinese

mmx music generate \
  --prompt "cinematic financial documentary, restrained tension, no vocals" \
  --instrumental \
  --out <bgm.mp3>

mmx image generate \
  --prompt "<article-specific visual prompt>" \
  --aspect-ratio 9:16 \
  --out <image.jpg>
```

第一产物：

```bash
python3 scripts/build_html_anything_template_router.py \
  --output configs/video/html_anything_template_router.json

python3 scripts/video_explainer_storyboard.py \
  --html <article.html> \
  --template-router configs/video/html_anything_template_router.json \
  --output <explainer_storyboard.json> \
  --preview-html <storyboard_preview.html>

python3 scripts/build_html_anything_video_timeline.py \
  --storyboard <explainer_storyboard.json> \
  --article-html <article.html> \
  --template-router configs/video/html_anything_template_router.json \
  --output <html_anything_video_timeline.json>
```

关键约束：

- HTML 文章是事实源，不新建第二条事实链。
- 文章里的表格、图表、图片、claim 是分镜证据来源。
- 外部 `html-video` 是默认渲染器。
- 外部 `html-anything` 只提供视觉语言和模板参考。
- TTS、配乐、AI 配图默认使用 MiniMax CLI；macOS `say` 只能作为本地烟测 fallback。
- 渲染前必须先把文章内容部件映射到 HTML Anything 模板，不能再直接用自绘兜底卡片生成全片。
- 视觉层默认采用 HyperFrames 思路；GSAP 控制动画时间轴；Lottie 只做辅助动效素材。
- 数据图表、表格、截图和来源证据必须来自文章或取数链路，Lottie 不能伪装成事实图表。
- 先审 storyboard，再渲染 MP4。

参考节奏：

| 指标 | 目标 |
| --- | --- |
| 平均 scene | 5-7 秒 |
| 中位 scene | 4-5 秒 |
| 证据画面 | 每 20-35 秒至少一次 |
| 章节卡 | 每 45-90 秒一次 |
| 动效 | 数据 reveal、文档 zoom、路径高亮、标题 kinetic |

### Motion Stack

| Layer | Responsibility |
| --- | --- |
| HyperFrames | HTML/CSS/JS 场景组织和本地渲染模型 |
| GSAP | scene 内动画编排：入场、出场、错峰、路径、数字、图表 reveal |
| Lottie | 现成设计师动效：警报、数据流、金融 ticker、文档扫描、品牌 outro |
| Draft Data | 真实事实层：图表、表格、截图、来源、claim |

`scripts/render_html_anything_timeline_pack.py --motion-runtime auto` 会从外部 `html-video` 读取并内联真实 `gsap` / `lottie-web`。如果依赖缺失，用 `scripts/ensure_video_external_deps.py --dep html-video --mode install --install-node-deps` 补齐。

## Skill Mapping

| Skill | 责任 |
| --- | --- |
| `dasheng-video-talking-head` | Lane A 导演时间轴和真人包装规则 |
| `scripts/video_claim_evidence_ledger.py` | 将微分镜归并为核心命题，生成证据缺口门禁和 HTML 审核页 |
| `scripts/build_remotion_renderer_pack.py` | 生成 10 个生产级渲染器族及 Remotion 主时间轴工程 |
| `dasheng-video-explainer-html` | Lane B HTML 文章分镜和无真人科普规则 |
| `dasheng-html-video-bridge` | 调用 html-video 创建/预览/渲染项目 |
| `dasheng-html-anything-bridge` | 借用 HTML Anything 的视觉模板和文章 HTML 经验 |
| `media-downloader` | 搜索和下载外部图片、视频素材 |
| MiniMax CLI `mmx` | 生产配音、配乐、AI 图片、口播音频，不在项目中硬编码 API key |
| `scripts/ensure_video_external_deps.py` | 检查、安装或更新 video 外部依赖，不做版本锁 |
| `scripts/build_html_anything_template_router.py` | 扫描 HTML Anything 75 个模板并生成内容部件路由表 |
| `scripts/build_html_anything_video_timeline.py` | 将文章 storyboard 扩展成 HTML Anything 模板时间轴 |

## Current Implementation

- `scripts/video_director_timeline.py`
- `scripts/video_explainer_storyboard.py`
- `scripts/video_driver_rules.py`
- `scripts/build_html_anything_template_router.py`
- `scripts/build_html_anything_video_timeline.py`
- `configs/video/video_editing_driver_rules.json`
- `tests/test_video_production_schemas.py`
- `tests/test_html_anything_template_router.py`

这些文件先稳定中间结构。`video_driver_rules.py` 已把 `video_editing_driver_rules.json` 接入真人口播和无真人分镜，输出包含 `beat_class`、`driver_scores`、`director_state/shot`、`transition_to_next`、`audio`。`render_html_anything_timeline_pack.py` 负责生成 scene HTML 状态类、转场动效和分镜包；最终视频必须走 `render_html_anything_scene_pack_animated.py` 逐场景录制真实 HTML/GSAP/Lottie 动画。旧的静态截图、PNG 拼接和 Ken Burns/zoompan 路径已从生产链路删除。后续剪映路径、html-video 项目生成都应读取 `talking_head_timeline.json`、`explainer_storyboard.json` 或 `html_anything_video_timeline.json`，不要各自重新发明分镜格式。
