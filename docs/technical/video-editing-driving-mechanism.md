# 视频剪辑驱动机制

Date: 2026-06-13

## 核心判断

小林说和巫师财经的关键差异不在“用了多少动画”，而在“谁负责维持注意力和信任”。

- 小林说类真人口播：人是信任锚点，B-roll、文件、图表负责视觉推进。剪辑目标是让观众一直觉得“有人在解释”，但眼睛不断看到证据。
- 巫师财经类无真人科普：旁白是时间轴，视觉本身承担主播角色。剪辑目标是让每个画面都在推进调查、证据或情绪，不允许变成 PPT 翻页。

因此驱动机制必须从“文稿 -> 模板”升级为：

`文稿语义 -> 证据需求 -> 注意力债务 -> 信任债务 -> 认知负荷 -> 镜头类型 -> 模板/素材 -> 动效 -> 转场 -> 音频`

## 两类样板的剪辑本质

### 小林说类真人口播

真人口播不是“全程露脸”，而是“周期性露脸”。真人画面负责建立关系和解释可信度，资料画面负责让内容不空。

可复用规律：

- 开头先让人出现，迅速建立话题和人格，不要一上来就堆图表。
- 每提出一个判断，随后要给一个证据画面：新闻、表格、网页、图表、历史素材、地图、人物照片。
- 证据画面可以全屏，但 8-20 秒内要回到真人，或者至少保留小窗，避免观众忘记“谁在讲”。
- 镜头切换以硬切为主。真人口播里的花哨转场会显得廉价，除非是章节转折或强冲突。
- 字幕服务语义，不服务 ASR 分段。完整短句优先，不要按固定字符硬切。
- 视觉节奏更快：中位镜头约 2.5-4 秒，短镜头可以 0.7-1.5 秒，但只用于素材蒙太奇，不用于讲复杂数据。

### 巫师财经类无真人科普

无真人视频的核心是“旁白 + 资料纪录片”。画面不是装饰，而是替代主播成为叙事主体。

可复用规律：

- 每个章节都有一个“资料调查感”的视觉壳：黑底、终端、报纸、文件夹、浏览器、数据面板。
- 镜头可以更长，但每个镜头内部必须动：数字增长、图表 reveal、文件 zoom、路径高亮、光影移动、焦点切换。
- 旁白不能只是文章朗读，要按镜头节奏重写成 6-12 秒的信息单元。
- 重要数据必须给可读时间。图表/表格不是贴纸，至少要留 6-15 秒并配合旁白解释。
- 情绪转场可以更多：淡入、推近、漏光、黑场、低频 riser，但必须服务章节结构。
- 证据密度要稳定：20-35 秒内必须出现一次真实证据，否则会变成空泛评论。

## 驱动变量

每个文稿切片计算六个变量，再决定镜头和模板。

| 变量 | 含义 | 高分时动作 |
| --- | --- | --- |
| `evidence_need` | 这句话是否需要证据支撑 | 上图表、文件、网页、表格，不上空泛动画 |
| `attention_debt` | 距离上次视觉变化多久 | 切镜头、换构图、加动效、插 B-roll |
| `trust_debt` | 真人口播里多久没见到人 | 回真人全屏/半屏/小窗 |
| `cognitive_load` | 信息复杂度和阅读负担 | 降低动效、延长停留、分拆场景 |
| `novelty` | 当前视觉是否重复 | 换模板族或换素材类型 |
| `platform_readability` | 竖屏手机是否能看清 | 限制字数、放大图表、减少模块 |

权重建议写入 [video_editing_driver_rules.json](/Volumes/PSSD/Projects/公众号文章/configs/video/video_editing_driver_rules.json)：

| 变量 | 权重 |
| --- | ---: |
| `evidence_need` | 0.34 |
| `attention_debt` | 0.18 |
| `trust_debt` | 0.16 |
| `cognitive_load` | 0.14 |
| `novelty` | 0.10 |
| `platform_readability` | 0.08 |

## Beat 分类到镜头决策

| Beat | 文稿触发 | 镜头动作 | 首选模板/素材 |
| --- | --- | --- | --- |
| Hook | 反常识、冲突、提问 | 强标题或真人开场 | `frame-glitch-title`、`frame-liquid-bg-hero`、真人全屏 |
| Claim | 核心判断、本质、关键 | 真人 punch-in 或观点卡 | `frame-electric-studio`、`vfx-text-cursor` |
| Evidence Data | 数字、百分比、估值、利率、IPO | 图表/表格/数字卡 | `frame-data-chart-nyt`、`frame-data-rollup`、`frame-pentagram-stat` |
| Evidence Document | 文件、政策、公告、新闻 | 文档 zoom / browser capture | `doc-kami-parchment`、`docs-page`、自定义 HTML scene |
| Logic Chain | 因为所以、传导、链条 | 路径高亮/流程图 | `frame-decision-tree`、`frame-flowchart-sticky` |
| Objection | 有人说、是不是、但 | 回真人或社交反馈卡 | `social-x-post-card`、真人全屏 |
| Chapter | 第一第二、回到正题 | 章节卡 + 声音 hit | `frame-bold-signal`、`frame-light-leak-cinema` |
| Recap | 总结、一句话、所以 | 结构回收/CTA | `frame-logo-outro`、outline recap |

## Lane A：真人口播状态机

真人口播应按状态机推进，而不是逐句贴模板。

```text
speaker_anchor
  -> claim_closeup
  -> evidence_fullscreen
  -> broll_with_pip
  -> document_zoom / chart_card
  -> speaker_return
```

强制规则：

- 只要文稿有明确数字、来源、政策、公司名，就优先进入 `evidence_fullscreen`。
- 距离上次真人主画面超过 16 秒，下一段优先 `speaker_return`。
- 一段复杂数据不要同时叠真人、字幕、表格、动画；要么全屏证据，要么小窗真人。
- B-roll 和 HTML 贴纸不是“装饰层”，必须绑定当前句子的证据或比喻。
- 摄像机运动只做微推拉和 crop shift，不要频繁大幅变焦。

输出 timeline 字段应扩展为：

```json
{
  "beat_class": "evidence_data",
  "driver_scores": {
    "evidence_need": 0.92,
    "attention_debt": 0.48,
    "trust_debt": 0.31,
    "cognitive_load": 0.7,
    "novelty": 0.52,
    "platform_readability": 0.66
  },
  "shot": "chart_card",
  "template_id": "frame-data-chart-nyt",
  "evidence_refs": ["article_table_02"],
  "transition": "data_reveal",
  "audio": {"duck_bgm": true, "sfx": "soft_tick"}
}
```

## Lane B：无真人科普状态机

无真人视频要让画面承担讲述者身份。

```text
hook_card
  -> question_setup
  -> chapter_card
  -> evidence_scene
  -> logic_animation
  -> cinematic_bridge
  -> evidence_scene
  -> recap_card
  -> outro
```

强制规则：

- 旁白是主时间轴，所有 scene duration 以后期 TTS 实际时长为准。
- 每 20-35 秒至少一次真实证据画面。
- 每 45-90 秒至少一次章节卡或结构回收。
- 每个 scene 至少有一个明确动效：入场、焦点变化、数据 reveal、路径高亮或出场。
- 没有真实数据时，不能生成“看起来像数据”的假图表，只能用观点卡、文档卡、概念图或素材画面。

## 转场驱动

转场不是随机套效果，而由语义决定。

| 场景关系 | 转场 | 原因 |
| --- | --- | --- |
| 同一论点继续 | `hard_cut` 或轻微 push | 保持节奏，不打断理解 |
| 观点反转/冲突 | `impact_cut` / glitch 8-12 帧 | 制造注意力峰值 |
| 进入文件/网页 | `push_zoom` | 模拟调查视角 |
| 图表出现 | `data_reveal` | 让观众跟着读数据 |
| 因果链推进 | `path_highlight` | 强化逻辑方向 |
| 章节结束 | `fade_or_light_leak` | 给认知喘息 |
| 结尾 CTA | `resolve_fade` | 收束，不再制造新信息 |

## 音频驱动

音频决定“专业感”的下限。

- 人声目标约 `-16 LUFS`，不能忽大忽小。
- BGM 要 duck 到人声下方约 `-18` 到 `-24 dB`，不要跟人声抢中频。
- 章节切换可用短 hit，数据 reveal 可用轻 tick，风险段可用低频 riser。
- 中途停顿不能直接留空：真人口播用 J-cut/L-cut 或 B-roll 盖掉，无真人视频用音乐尾音和画面动效填充。
- MiniMax CLI 是默认 TTS / 配乐入口；本地 `say` 只做烟测。

## 质检失败条件

以下任一出现即视为未达标：

- 最终视频出现开发标签、slot 名、position 名。
- 图表或数字无来源，或用装饰图伪装数据。
- 字幕遮脸、遮图表，或多条字幕重叠。
- 真人口播超过 24 秒没有真人回归，且不是高密度证据段。
- 无真人视频超过 40 秒没有真实证据画面。
- 单个 scene 超过 12 秒但没有动效或焦点变化。
- 同一期视频混用超过两个视觉系统，风格乱跳。

## 对现有工程的落点

已有文档 [video-script-template-routing-guide.md](/Volumes/PSSD/Projects/公众号文章/docs/technical/video-script-template-routing-guide.md) 解决“文稿部件选哪个模板”。本文件补上“什么时候切、为什么切、切到什么强度”。

下一步应把三份产物串起来：

1. `video_script_segments.json`：文稿切片和 beat 分类。
2. `video_template_timeline.json`：模板/素材选择和变量。
3. `video_director_timeline.json`：镜头、转场、音频、字幕、安全区、QC 规则。

最终 skill 不应只叫模板路由，建议定位为 `dasheng-video-director`：

- `dasheng-video-template-router` 负责模板池和语义槽位。
- `dasheng-video-director` 负责剪辑状态机、节奏、转场、音频和 QC。
