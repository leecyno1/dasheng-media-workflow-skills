---
name: dasheng-digital-human-talking-head
description: Create a governed animal-head or masked talking presenter from an authorized real-person portrait by preserving the body, replacing only the head with Codex imagegen, animating speech in Luma Dream Machine with MiniMax audio, and handing the result to the Dasheng talking-head director and Remotion pipeline. Use for 数字人、类真人、有头口播、动物头像口播、大猩猩头、牛头、马头、悍匪头套 or Luma lip-sync presenter videos.
---

# 大圣动物头数字人口播

主路线：

`授权真人照片 → Codex imagegen 完整换头图 → Luma Dream Machine 中文口型视频 → 大圣口播导演链二剪`

不再使用 Inochi2D 贴图换头作为正式路线。它和 JoyVASA 只保留为历史实验/离线备用。

## 路由

- `human_video`：已有真人口播视频，直接走 `dasheng-video-roughcut`。
- `luma_animal_presenter`：当前默认。保留真人身材、服装、姿势和手部，用 imagegen 将头部重绘为写实 3D 动物头或头套，再让 Luma 按 MiniMax 音频生成口型与自然微动作。
- `joyvasa_liveportrait`：Luma 不可用且用户明确要求完全本地时才使用；必须先过 6–10 秒短样。
- `inochi2d_openseeface`：仅用于技术研究，不得作为正式交付。

## 标准流程

1. **确认授权**：只处理本人、已授权人物或虚构角色。未确认肖像和声音权利时停止。
2. **锁定音频**：使用审核后的 MiniMax 中文音频。它是全片唯一主音频。
3. **检查原图**：优先单人正面、头肩或半身、手部完整、背景干净的 768–1536px 照片。
4. **用 imagegen 换头**：先查看原图，再调用内置 imagegen 编辑。只替换头部，保留身体、服装、姿势、手、背景、镜头和光线。
5. **默认造型**：大猩猩优先，其次牛、马、戴头套悍匪。生成一版后先由用户确认，再进入付费视频生成。
6. **建立任务包**：

```bash
python3 scripts/build_digital_human_job.py \
  --image <animal_head_portrait.png> \
  --audio <minimax.wav> \
  --output-dir <project>/digital_human_source \
  --consent confirmed \
  --engine luma_dream_machine \
  --profile animal_presenter
```

7. **进入 Luma**：使用用户现有登录会话。上传换头图和 MiniMax 音频，选择支持音频驱动/口型同步的工作流。账号、付费、额度和 CAPTCHA 由用户确认。
8. **生成短样**：先做 6–10 秒。要求镜头锁定、人物正面、身体和手势只做自然小动作、口型按中文音频、动物身份不漂移。
9. **审核短样**：重点检查口型延迟、嘴部畸变、牙齿闪烁、眼神、动物头尺寸、头颈接缝、手部和身体漂移。
10. **生成正文段落**：按字幕停顿拆成短段，失败只重做对应段。最终以 MiniMax 主音频重新对齐，不依赖 Luma 输出音频作为母带。
11. **转入导演链**：将 Luma 成片作为 `base_video`，再执行分镜、证据、B-roll、字幕、花字、Remotion 和 QC。
12. **披露**：发布时明确标注“AI 生成角色/AI 生成画面”。

## imagegen 换头约束

提示词必须明确：

- `Replace only the human head`；
- 原图是编辑目标，不是风格参考；
- 完整保留身材、服装、姿势、双手、手表、座椅、背景、构图和光线；
- 动物头为原创、可爱但写实的电影级 3D/VFX 造型；
- 头部尺寸接近原真人头，脖子自然进入衣领；
- 正视镜头，嘴唇/口腔结构清晰，便于后续中文口型；
- 禁止新增动物身体、改变手部、放大头部、加文字或水印。

大猩猩可参考高质量智慧猿类电影质感，但不得复制具体版权角色。

## Luma 提示词基线

```text
Locked camera, front-facing seated presenter. Preserve the exact character, body,
suit, hands, chair, background and framing from the input image. The realistic 3D
animal character speaks the supplied Chinese audio with accurate, restrained lip
sync and natural jaw motion. Add subtle blinking, breathing, tiny head motion and
small natural hand/body movement only. No identity drift, no head-size change, no
camera move, no scene cut, no new objects, no warped hands, no subtitles or text.
```

## 与导演系统的约定

- `presenter_source.kind`：`human_video` 或 `digital_human`。
- `presenter_source.engine`：默认 `luma_dream_machine`。
- `voice.provider`：`minimax`；主音频只挂载一次。
- Luma 输出若带音频，进入 Remotion 前先静音，只保留视觉层。
- 数字人不是事实证据；所有数据和判断仍绑定真实图表、新闻或文件。
- 每 8–20 秒切换证据、图表或 B-roll，避免长时间盯着合成角色。

## 硬门禁

- 无肖像授权、声音授权或人物身份不明：停止。
- 用公众人物照片替其发言：停止。
- 未经用户确认换头图：不得消耗 Luma 额度。
- 账号选择、首次授权、付费、购买额度、CAPTCHA：交给用户。
- 短样出现身份漂移、严重嘴部畸变或手部变形：不得生成长片。

## 输出

- `animal_head_portrait.png`
- `digital_human_job.json`
- `presenter_source_manifest.json`
- `luma_segments/*.mp4`
- `digital_human_source.mp4`
- `digital_human_qc.json`

需要了解旧本地方案和回退边界时，读取 [references/model-selection.md](references/model-selection.md)。
