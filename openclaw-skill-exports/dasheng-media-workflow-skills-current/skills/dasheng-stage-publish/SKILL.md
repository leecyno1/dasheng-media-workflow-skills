---
name: dasheng-stage-publish
description: Use when entering the formal publish stage of Dasheng workflow to run channel gating, video supplement, platform adaptation, platform execution, and publish verification.
---

# Dasheng Stage: Publish

## 定位

这是 Dasheng 主链里 `publish` 阶段的正式 stage skill。

正式阶段顺序：

`intake -> brief -> draft -> material -> rewrite -> publish -> postmortem`

`distribute` 已并入 `publish`，不再单列正式阶段。

## 正式输入

- `rewrite_manifest.json`
- `material_manifest.json`
- `publish_decision.json`

缺少任一关键输入时，禁止执行。

## 五层执行

1. `Publish Gate`
2. `Video Supplement`
3. `Channel Adaptation`
4. `Channel Execution`
5. `Publish Guard`

## 发布类 skill 编排

### 视频补充

- `scripts/publish_video_supplement.py`
- 外部参考：`dasheng-stage-publish-video`

### 公众号

- 主执行：`baoyu-post-to-wechat`
- 批量草稿：`wechat-multi-publisher`
- 预处理：`md2wechat`

### 微博

- 短帖：`weibo-manager`
- 头条文章 / 浏览器半自动：`baoyu-post-to-weibo`

### X

- `baoyu-post-to-x`

### 小红书

- `xiaohongshu-auto`

### 抖音

- `douyin-upload-skill`

### 发后验真

- `publish-guard`

## 标准输出

- `07_发布计划.md`
- `07_发布包.md`
- `publish_video_supplement_report.md`
- `publish_video_supplement_manifest.json`
- `channel_adaptation_manifest.json`
- `channel_execution_manifest.json`
- `publish_verification_report.json`
- `publish_manifest.json`

## 强约束

1. 没有 `publish_decision.json` 不得执行。
2. 缺少视频补充产物时，视频平台包不得标记完成。
3. 微博短帖必须走 `Request -> Approve -> Execute`。
4. 缺少正式执行器的平台只允许导出待人工发布包。
5. 未经过 `Publish Guard` 验真，不得回报“已发布”。

## 参考

- `/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/publish-architecture.md`
- `/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/references/publish-skill-matrix.md`
- `/Volumes/PSSD/Projects/公众号文章/引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
