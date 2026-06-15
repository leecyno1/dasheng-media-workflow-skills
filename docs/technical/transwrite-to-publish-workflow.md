# Transwrite -> Publish 阶段链路

更新时间：2026-06-14

## 主链边界

正式主链：

`intake -> brief -> draft -> transwrite -> publish -> postmortem`

- Draft：完成事实、数据、图表、配图、自包含 HTML。
- Transwrite：把确认 Draft 转成渠道表达形态，采用轻内核，真正生产由 Agent/技能执行。
- Publish：只做验收、打包、推草稿/人工发布包、链接回收和验真。

## Transwrite 执行模型

`scripts/build_stage4_transwrite.py` 只负责生成任务包：

- `transwrite_manifest.json`
- `04_转写计划.md`
- 每个 lane 的 manifest、prompt、请求体、产物槽位、QC 槽位

真正生产由 Agent/skills 完成，并回写 lane manifest：

- `status`
- `final_artifacts`
- `qc.status`
- `qc.report`

## 三条 Lane

### wechat_article

职责：

- 调用 `dasheng-style-profiler` / `wechat-style-profiler`
- 调用 `baoyu-markdown-to-html`
- 可选调用 `baoyu-cover-image` / `baoyu-imagine`
- 输出 `wechat_article.final.md`、`wechat_article.final.html`、封面和 `wechat_article_qc_report.json`

### talking_head_video

职责：

- 真人口播：人声/视频为主时间轴，HTML 视觉层主动对齐
- 无真人出镜：Draft 生成口播稿，MiniMax CLI 生成连续配音，HTML/GSAP/Lottie/HyperFrames 被动对齐
- 调用 `dasheng-video-talking-head`、`dasheng-video-explainer-html`、`dasheng-html-video-bridge`、`dasheng-html-anything-bridge`
- 输出 MP4、SRT、timeline、`video_qc_report.json`

### podcast

职责：

- 从 Draft/转写稿生成播客脚本
- 调用 MiniMax CLI 或 Coze 工作流生成音频
- 输出音频、文字稿和 `podcast_qc_report.json`

## 状态机

初始包状态：

- `ready_for_agent_execution`
- `ready_for_skill_execution`
- `blocked_missing_human_media`
- `blocked_missing_audio_provider`

可进入 Publish：

- `packageable`
- `completed`

兼容旧文字包：

- `ready_base_package`

Publish 必须阻塞：

- `planned`
- `planned_for_render`
- `ready_for_agent_execution`
- `ready_for_skill_execution`
- `blocked_missing_*`
- `waiting_for_human_media`
- `failed_qc`

## 产物落点规则

运行产物不得写入 `skills/`、`openclaw-skill-exports/` 或任意 skill 根目录。

默认落点：

- Draft：`产物/05_初稿生成/<run_id>/`
- Transwrite：`产物/06_转写生产/<run_id>/`
- Publish：`产物/07_发布执行/<run_id>/`
- 实验缓存：`tmp/`
- 历史误放素材迁移：`产物/_legacy_skill_runtime_data/`

代码守卫：

- `scripts/canonical_workflow.py::ensure_runtime_output_dir`

## Publish 当前开发方向

第一阶段已经完成：

- publish 只接受 `transwrite_manifest.json` + `publish_decision.json`
- 阻塞未完成 lane
- 检查关键最终产物是否存在
- 生成 `07_发布计划.md`、`07_发布包.md`、`channel_execution_manifest.json`、`publish_verification_report.json`、`publish_manifest.json`
- Publish Guard 已进入正式闭环：
  - `scripts/publish_guard.py --publish-manifest <publish_manifest.json>`
  - 默认写出 `publish_guard_report.json` / `publish_guard_report.md`
  - 回写 `publish_manifest.publish_guard`
  - Postmortem 正式门控可用 `--require-publish-guard`

下一阶段要攻：

- 每个平台的必需字段校验：标题、摘要、标签、封面、正文、视频、音频。
- 发布包结构化导出：公众号包、视频平台包、播客包、人工 B 站包。
- 执行器路由：自动、半自动、人工包三类明确分流。
- 外部依赖桥：B站优先 `biliup-rs`，多视频平台统一上传参考 `social-auto-upload`，海外排程候选 `Postiz`。
- Link Recovery：草稿 ID、正式链接、账号、截图、错误状态回填。
- Publish Guard：验真报告不得为空，未验真不得标记已发布；`draft_url` 与 `platform_url` 必须分离。
