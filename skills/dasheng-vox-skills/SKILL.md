---
name: dasheng-vox-skills
description: Orchestrate complete VOX-style editorial video production from content distillation, creator-led script rewriting, retention design and review storyboards through approved director shots, Codex reference images, official Gemini API or signed-in Chrome Gemini Omni generation, Remotion re-editing, narration-bound subtitles, and final QC. Use when creating, continuing, repairing, or productizing VOX explainers, paper-collage B-roll, Gemini/Omni/Veo image-to-video batches, or an existing VOX manifest.
---

# 大圣 VOX 视频制作

统一编排现有组件，不重复实现导演、浏览器或 Remotion。

开始前按任务读取：

- 所有新视频先读取 `../dasheng-video-vox/references/director-workflow.md`，执行内容提炼、剧本重写和审核分镜。
- 选择 API、浏览器或备用路由时，读取 [references/provider-routing.md](references/provider-routing.md)。
- 设计参考图、验收单镜或检查成片时，读取 [references/quality-gates.md](references/quality-gates.md)。
- 需要详细 VOX 视觉语法时，读取 `../dasheng-video-vox/references/visual-grammar.md`。

## 工作流

1. 用 `dasheng-video-vox` 从文章提炼中心问题、3–5 层递进观点、关键证据、反方边界和未来判断，生成 `video_content_brief.md`。
2. 将文章重写为独立口播稿 `narration_script.rewritten.md`。固定设计前 8 秒钩子、首条有效信息后的单句博主介绍、每 45–60 秒有效互动、阶段性反转和悬念兑现。
3. 先按 10–25 秒 `story_segment` 生成 `storyboard_review.md`，让用户审核内容、口吻、论证和留存。默认只做核心对应，不把文章章节或自然段直接拆成生产镜。
4. 用户批准后，才把叙事段拆成平均 8–12 秒的 `director_shot`，并规划 2.5–5 秒 `micro_beat`；随后建立视觉圣经和 `scene_plan.json`。
5. 用本 Skill 的 `scripts/vox_manifest.py build` 建立统一 Manifest。以后所有 Provider、失败记录和断点续跑都以它为准。
6. 用 Codex `imagegen` 生成每镜 16:9 参考图。先生成母版，后续镜头继承材质、配色、英雄物件和留白规则。
7. 生成参考图接触表并审核。未通过的镜头不得进入视频生成。
8. 按 Manifest 的 `provider_order` 逐镜生成：官方 Gemini API 优先；API 不可用时调用 `dasheng-video-omni-browser`；单镜失败再回退，禁止整片静默换 Provider。
9. 默认 `motion_mode: assemble`。若模型拆解、漂移或卡死，只把该镜改成 `in_place` 重试一次。
10. 每镜抽查首、中、尾帧。将尝试、错误、输出与审核状态写回 Manifest；已通过镜头不重做。
11. 把通过的片段导入 `vox-editorial-collage` Remotion 家族，加入真实证据、精确文字、图表、旁白、原时间轴字幕、重点花字、人物/机构/关键物件说明标签和 BGM。
12. 执行全片渲染 QC 与最终交付绑定。

## 核心命令

先生成重写口播与 10–25 秒审核分镜：

```bash
python scripts/dasheng_video_director.py \
  --lane vox_explainer_video \
  --article-html <article.html> \
  --output-dir <project>/director
```

审核通过后再拆生产镜：

```bash
python scripts/dasheng_video_director.py \
  --lane vox_explainer_video \
  --article-html <article.html> \
  --output-dir <project>/director \
  --storyboard-review-gate <project>/director/storyboard_review_gate.json
```

创建统一 Manifest：

```bash
python skills/dasheng-vox-skills/scripts/vox_manifest.py build \
  --shots <shots.json> \
  --output-dir <project>/vox_run
```

使用官方 Gemini/Veo API 生成单镜：

```bash
python skills/dasheng-vox-skills/scripts/gemini_video_api.py \
  --prompt-file <shot.video.txt> \
  --reference <shot.png> \
  --first-frame <optional-empty-background.png> \
  --last-frame <optional-completed-reference.png> \
  --output <shot.mp4> \
  --model <available-google-video-model> \
  --duration 8 \
  --final-duration 10
```

传入 `gemini-omni-flash-preview` 等 Omni 模型名时，脚本兼容 `gbro-collage-broll` 的官方 Interactions API 路线；传入 Veo 模型名时走 `models.generate_videos`。只传 `--reference` 时做单图生视频；同时传首尾帧时做从空背景组装到完成构图。

Omni 可请求 3–10 秒；官方 Veo 当前原生生成 4–8 秒。VOX 时间轴仍按 8–12 秒设计，Veo 可用 `--final-duration 10` 统一补稳定尾帧，最终仍在 Remotion 中按旁白节拍剪辑。

生成单镜首、中、尾帧质检包：

```bash
python skills/dasheng-vox-skills/scripts/shot_qc.py \
  --video <shot.mp4> \
  --output-dir <shot-qc-dir>
```

没有 API 凭据时，使用 `dasheng-video-omni-browser` 执行同一个 Manifest 中待生成的镜头。

## 不可违反

- 参考图片只由 Codex `imagegen` 生成；Gemini 只负责视频。
- 剧本必须经过独立重写；禁止直接把文章章节、自然段或摘要当成最终口播和生产分镜。
- 审核分镜未获批准前，不得拆生产镜、锁视觉圣经或生成素材。
- 真实新闻、人物发言、历史影像、精确数字和引用必须使用真实素材或 Remotion 覆盖。
- 字幕绑定原旁白时间轴，不使用每镜摘要伪造字幕。
- 重点句必须规划同步花字；人物、机构、地点和关键物件首次出现时必须有同步说明标签。
- 禁止第三方聚合服务。
- MiniMax/MMX 与 Seedance 仅在用户明确允许时作为单镜备用。
- 不让生成模型一次制作完整成片；一镜一视频，最后统一二剪。

## 内部组件

- `dasheng-video-vox`：内容提炼、剧本重写、留存设计、审核分镜、生产镜拆分和视觉语法。
- `dasheng-video-omni-browser`：Chrome 已登录 Gemini Omni 执行器。
- `scripts/video_vox_omni_pack.py`：旧镜头包兼容器。
- `scripts/video_vox_mmx_generate.py`：显式备用生成器。
- Remotion 与现有视频 QC 脚本：二剪、字幕、声音和交付。
