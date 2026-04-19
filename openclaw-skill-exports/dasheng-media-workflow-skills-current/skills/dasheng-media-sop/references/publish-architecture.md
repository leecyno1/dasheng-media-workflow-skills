# Publish 阶段正式架构

更新时间：`2026-04-13`

## 目标

`publish` 不是“把稿子丢给平台”的黑盒，而是正式的 5 层发布闭环：

1. `Publish Gate`
2. `Video Supplement`
3. `Channel Adaptation`
4. `Channel Execution`
5. `Publish Guard`

正式阶段顺序不变：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

`distribute` 的能力已并入 `publish`，不再单列正式阶段。

## 正式输入

- `rewrite_manifest.json`
- `material_manifest.json`
- `publish_decision.json`

若缺少 `publish_decision.json`，`publish` 必须拒绝执行。

## 五层架构

### 1. Publish Gate

只做发布决策校验，不做内容生成。

必须确认：

- 发布平台矩阵
- 每题每平台对应变体
- 标题、封面、摘要、标签是否已确认
- 发布时间与可见性
- 是否允许立即发布，还是仅创建草稿 / 打开浏览器待人工确认

对应 gate 文件：

- `publish_decision.json`

### 2. Video Supplement

发布前强制补两类视频：

- `Chart Motion`
  - CSV / 表格 / 结构化数据
  - → `finance-motion-8787`
  - → `webm/mp4`
- `Narrative Motion`
  - 改写稿核心框架 + 关键数据
  - → motion / remotion 场景
  - → `webm/mp4`

标准输出：

- `publish_video_supplement_report.md`
- `publish_video_supplement_manifest.json`

### 3. Channel Adaptation

这层负责把改写稿和视频转成“平台可发包”，不直接调用平台。

每个平台至少生成：

- 标题
- 正文 / 描述
- 标签 / 话题
- 封面 / 首图
- 视频引用
- 发布方式
- 风险提示

标准输出：

- `channel_adaptation_manifest.json`
- `07_发布计划.md`

### 4. Channel Execution

只调用正式平台 skill 执行，不在这一层再重新写内容。

每条执行记录至少包含：

- `platform`
- `topic_id`
- `variant_id`
- `executor_skill`
- `mode`
- `status`
- `platform_url`
- `platform_post_id`
- `manual_action_required`

标准输出：

- `channel_execution_manifest.json`
- `07_发布包.md`

### 5. Publish Guard

所有平台执行后都要经过验真层，禁止“只执行命令就宣称已发布”。

验真职责：

- URL 可访问性检查
- Soft-404 检查
- 平台回执 / 草稿状态检查
- 审批流状态检查
- 限流 / 风险回写

标准输出：

- `publish_verification_report.json`
- 汇总到 `publish_manifest.json`

## 平台矩阵

| 平台 | 正式执行 skill | Dasheng 角色 | 自动化等级 | 默认策略 |
| --- | --- | --- | --- | --- |
| 微信公众号文章 | `baoyu-post-to-wechat` | 单篇文章执行器 | 半自动 | 默认先入草稿或浏览器确认 |
| 微信公众号多篇草稿 | `wechat-multi-publisher` | 批量草稿箱执行器 | 半自动 | 用于一主多副或批量入草稿 |
| 微信公众号预处理 | `md2wechat` | HTML/封面/信息图预处理 | 辅助 | 不单独视为发布完成 |
| 微信视频号 | 无正式 skill | 输出包/待人工发布 | 手动 | 仅导出脚本与素材 |
| 微博短帖 | `weibo-manager` | 审批流主执行器 | 强审批 | 必须 `Request -> Approve -> Execute` |
| 微博头条文章 | `baoyu-post-to-weibo` | 浏览器半自动执行器 | 半自动 | 用户最终确认发布 |
| X / Twitter | `baoyu-post-to-x` | 浏览器半自动执行器 | 半自动 | 用户最终确认发布 |
| 小红书图文/视频 | `xiaohongshu-auto` | 自动发布执行器 | 自动 | 由 Dasheng 侧控制节流与审核 |
| 抖音视频 | `douyin-upload-skill` | 官方 API / fallback 执行器 | 自动/半自动 | 优先官方发布，失败则 outbox |
| 发布验真 | `publish-guard` | 后验真与审计 | 守卫层 | 没有验真不得报成功 |

## 平台策略

### 公众号

- 正式载体是文章，不是 HTML 文件本身。
- 默认优先：
  1. `baoyu-post-to-wechat`
  2. `wechat-multi-publisher`
  3. `md2wechat` 仅做预处理
- 除非 `publish_decision.json` 明确要求立即发布，否则默认只创建草稿或打开浏览器待确认。

### 微博

- 短帖优先 `weibo-manager`，因为它有强审批流。
- 头条文章可用 `baoyu-post-to-weibo`。
- 不允许 agent 绕过审批直接发短帖。

### X

- 正式执行用 `baoyu-post-to-x`。
- 默认浏览器填充 + 用户最终确认。

### 小红书

- `xiaohongshu-auto` 负责图文/视频自动投递。
- Dasheng 侧必须补：
  - 发布节流
  - 每日数量上限
  - 素材存在性校验
  - 发后验真

### 抖音

- `douyin-upload-skill` 负责 `doctor / auth / prepare / publish / fallback`。
- Dasheng 侧负责从改写稿生成口播简介、字幕候选与发布计划。

## 输出对象

`publish` 阶段正式对象：

- `ChannelPack`
- `channel_adaptation_manifest.json`
- `channel_execution_manifest.json`
- `publish_verification_report.json`
- `publish_manifest.json`

最终 `publish_manifest.json` 至少要汇总：

- 上游 manifest
- gate 文件
- 视频补充状态
- 各平台执行结果
- 验真结果
- 待人工动作

## 强约束

1. 不允许恢复独立 `distribute` 正式阶段。
2. 不允许通过旧目录猜测 `rewrite` 或 `material` 输入。
3. 不允许没有 `publish_decision.json` 就执行发布。
4. 不允许没有验真就向用户汇报“已发布”。
5. 不允许把缺少正式执行器的平台伪装为自动发布完成。
