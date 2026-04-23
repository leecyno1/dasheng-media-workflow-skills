# 阶段地图

## 1. Intake

- 目标：采集原始来源，保留链接，形成当天底稿与报告。
- 常见输入：端口数据、网页、公众号文章、外部热点。
- 交付：`01_内容采集_底稿.md`、`01_内容采集_报告.md`、`intake_manifest.json`
- 默认采集规模：X、微博各 `100` 条，其它平台各 `50` 条。
- 报告默认只做话题频次 `Top10` 统计，不做主观初筛。

## 2. Brief

- 目标：基于 canonical intake 证据池生成 8-10 个 AI-only 独立题卡。
- 常见输入：`brief_input.json`、`channel_top10.json`、`event_clusters.json`、`raw/intake_records.json`
- 交付：`02_编辑Brief库.md`、`02_研究Brief库.md`、`02_编辑Brief_报告.md`、`topic_cards.json`、`brief_manifest.json`
- 结构要求：每题包含标题、判断、核心命题、证据缺口、推荐数据角度、推荐视觉角度、关键来源。
- 人工指定选题必须强制入池；同一逻辑链超过半数则阶段失败。

## 3. Draft

- 目标：形成标准初稿，默认是 `4000-8000` 字长文底稿，并供编辑直接改造成终稿。
- 常见输入：确认题目、核心判断、骨架、来源包。
- 交付：`03_标准初稿_<topic>.md`、`03_初稿_报告.md`、`draft_manifest.json`
- 结构规则：优先 `开篇 + 三段论 + 结尾` 或 `开篇 + 4 章 + 结尾`，一级标题不得超过 `4` 个。
- 内容规则：只写标准事实稿，不注入账号 DNA 和平台腔；主动补数据、表格和权威来源。

## 4. Material（含补素材）

- 目标：围绕编辑已确认的终稿补齐图表、图片、视频、封面，并直接回填到终稿文档。
- 常见输入：终稿文档、素材锚点、topic pack 目录。
- 交付：`05_MaterialPack.md`、`05_Material_报告.md`、`material_manifest.json`
- 可选增强：`layer5_delivery_plan.json`、`scene_plan.json`、`ai_visual_plan.json`
- 事实基准：只对编辑确认后的终稿工作底板补素材，不回填旧 draft。
- 结果要求：素材目录按题目独立，优先直接回填飞书终稿。

## 5. Rewrite

- 目标：把回填后终稿改成指定 `DNA × Channel × Emotion` 的多版本成品稿。
- 常见输入：回填后终稿、改写参数矩阵、DNA 配置、渠道约束。
- 交付：每题独立目录，包含 `rewrite_bundle.md`、4 篇改写正文、`meta.json`、`rewrite_manifest.json`
- 默认矩阵：
  - 公众号｜鲁迅｜热烈
  - 公众号｜Lemon｜正常
  - 小红书视频｜鲁迅｜热烈
  - 小红书视频｜Lemon｜正常
- 字数规则：
  - 公众号两篇：`4000-8000`
  - 小红书视频两篇：`>=1800`
- 执行原则：多题目默认多 agent 并行，每题独立目录，不能混稿。

## 6. Publish

- 目标：在发布前完成视频补充、渠道适配、平台执行与发后验真。
- 常见输入：改写稿、补素材产物、标题、封面、渠道模板、Layer5 CSV。
- 发布前补充（强制）：
  - 互动图表视频：CSV -> `finance-motion-8787` -> `webm/mp4`
  - motion 叙事视频：改写稿框架/关键数据 -> 动画场景 -> `webm/mp4`
- 平台执行矩阵：
  - 公众号：`baoyu-post-to-wechat` / `wechat-multi-publisher` / `md2wechat`
  - 微博：`weibo-manager` / `baoyu-post-to-weibo`
  - X：`baoyu-post-to-x`
  - 小红书：`xiaohongshu-auto`（正式执行器）
  - 抖音：`douyin-upload-skill`（正式执行器）
  - B站：当前无正式投稿器，仅导出人工投稿包；`bilibili-youtube-watcher` 仅作辅助研究
  - 视频号：当前无正式上传器，仅导出人工发布包
  - 验真：`publish-guard`
- 交付：`07_发布包.md`、`07_发布计划.md`、`publish_video_supplement_report.md`、`publish_video_supplement_manifest.json`、`channel_adaptation_manifest.json`、`channel_execution_manifest.json`、`publish_verification_report.json`、`publish_manifest.json`
- 备注：平台分发动作并入 `publish`，不再单列 `distribute` 正式阶段。

## 7. Postmortem

- 目标：复盘效果，输出继续/停止/测试建议，并回写知识库。
- 常见输入：发布链接、平台数据、人工反馈。
- 交付：`08_复盘报告.md`、`08_L1回写建议.md`、`postmortem_manifest.json`
