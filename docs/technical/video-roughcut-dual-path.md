# 口播粗剪双路径实验记录

## 目标

在一段时间内并行保留两条口播粗剪路径，按真实素材比较质量、效率和稳定性，再决定后续合并、保留或删除。

## 路径 A：Agent + 开源媒体链路

定位：当前主链路，负责可复现、可追溯的粗剪基准版本。

技术栈：

- ASR：FunASR `paraformer-zh + fsmn-vad + ct-punc`
- 语义整理：主 Agent 根据原始转写做轻量整理、断句、错字和口水词处理
- 时间轴映射：`scripts/video_roughcut_agent_align.py`
- 渲染剪辑：FFmpeg
- 音频增强：`highpass -> lowpass -> afftdn -> dynaudnorm -> acompressor -> loudnorm -> alimiter`
- 视觉增强：`scripts/video_open_filter.py`，基于 FFmpeg 开源滤镜做暖光、柔化、增白和低风险轻拉瘦
- 审核：本地 HTML 审核页和 manifest

优点：

- 结果可复现，适合批量化和回滚。
- 删除片段、字幕、音频处理都有文件记录。
- 不依赖剪映 UI 版本和弹窗。

风险：

- 对“这个、那个、嗯、就是、其实”等口水词的精细删除依赖转写质量和时间轴对齐。
- 字词级硬切容易破坏口播连续性，默认仍应以句段级删除为主。

## 路径 B：剪映专业版智能剪口播

定位：实验通路，只测试剪映内置“智能剪口播”本身的质量。

本轮约束：

- 不让 Agent 根据原提纲做二次语义检查。
- 不把剪映路径改造成复杂自动导出系统；当前痛点不是导出。
- 允许使用 Computer Use 操作剪映专业版完成导入、智能剪口播、保存草稿。
- 助理可通过剪映云端草稿继续处理，因此本地草稿可作为交付物。

技术栈：

- 剪辑决策：剪映专业版内置智能剪口播
- UI 操作：Codex Computer Use
- 草稿存储：`~/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/`
- 草稿同步：剪映云端草稿，由人工或助理继续精修

优点：

- 可能更擅长识别停顿、口水音、局部重复和口播节奏。
- 可直接进入剪映生态，后续美颜、滤镜、花字、模板更顺手。
- 适合人工助理继续接力。

风险：

- Computer Use 直接点 UI 容易受版本、弹窗、窗口布局影响。
- 剪映内部 AI 的删除逻辑不透明，可追溯性弱。
- 草稿部分元数据可能被加密，不能默认用 JSON 解析完整还原时间轴。
- 如果智能剪口播误删内容，当前实验路径不做 Agent 二次纠错。

## 备选技术栈

- `jianying-editor-skill`：适合参考剪映 skill 的工作流边界，但不能稳定调用剪映内置实时 AI 功能。
- `pyJianYingDraft`：适合生成或修改剪映草稿、字幕、滤镜、特效；不负责触发智能剪口播 UI。
- `capcut-cli`：适合作为 Agent 与剪映草稿之间的结构化接口，后续可测试读取或生成草稿。
- `capcut-mate`：适合未来服务化草稿生成，不作为本轮最小实验依赖。
- `videocut-skills`：适合参考交互审核页和字幕/重复处理思路，不替代剪映智能剪口播实验。

## 对比指标

- 粗剪后时长变化。
- 口水词和重复句去除效果。
- 句子连续性和断句自然度。
- 字幕时间轴是否重叠、延迟或截断语义。
- 音量、降噪和响度是否可直接审看。
- 交付物是否方便人工助理继续接力。

## 当前样本

- 原始素材备份：`/Users/lichengyin/Desktop/6月11日_双路径实验/input/6月11日_source.mov`
- 现有路径 A 粗剪：`/Users/lichengyin/Desktop/6月11日_粗剪交付/6月11日_剪辑师安全版.mp4`
- 现有路径 A 滤镜版：`/Users/lichengyin/Desktop/6月11日_滤镜交付/final/6月11日_剪辑师安全版_warm_cinema_medium.mp4`
- 已发现剪映草稿：`/Users/lichengyin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/6月11日`

## 2026-06-12 实验记录：6月11日口播

路径 A 基准：

- 输入：`/Users/lichengyin/Desktop/6月11日_粗剪交付/6月11日_剪辑师安全版.mp4`
- 时长：`00:17:32.80`
- 视频：`1920x1080 H.264`
- 音频：`AAC`
- 字幕：独立 `.srt`，631 行；视频文件本身不含 soft subtitle 轨
- 音量：`mean_volume -16.4 dB`，`max_volume -0.1 dB`

路径 B 剪映实验：

- 输入：`/Users/lichengyin/Desktop/6月11日_双路径实验/input/6月11日_source.mov`
- 草稿：`/Users/lichengyin/Movies/JianyingPro/User Data/Projects/com.lveditor.draft/6月12日`
- 操作方式：新建干净草稿 -> 导入原片 -> 根据选中素材新建时间线 -> 在时间线片段右键触发 `智能剪口播`
- 剪映识别：`503` 个无效词
- 剪映分类：约 `364` 个语气词、`25` 个重复、`54` 个停顿
- 静音阈值：`0.8s`
- 输出时间线：`时间线02`
- UI 显示时长：约 `00:14:12:10`
- 草稿公开附件确认：`ai_remove_filter_words.enter_source = remove_invalid_smart_broadcast`

本轮观察：

- 从素材库右键触发 `智能剪口播` 会进入“选择文本插入时间线”的文本剪辑模式，不是本轮需要的自动去水词路径。
- 正确路径是先把素材放到时间线，再对时间线片段右键触发 `智能剪口播`。
- 剪映会生成可视化文本、标注水词、停顿和重复，并能直接生成新的剪后时间线。
- 剪映草稿的主要时间线文件在当前版本中有封装/加密，不能稳定按普通 JSON 解析全部切片。
- 当前剪映路径可以作为“草稿交付给人工/助理继续精修”的路线；若要程序化读取切片，还需要后续验证 `capcut-cli`、`pyJianYingDraft` 或剪映旧版草稿格式兼容性。
