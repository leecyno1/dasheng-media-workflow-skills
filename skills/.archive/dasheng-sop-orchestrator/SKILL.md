---
name: dasheng-sop-orchestrator
description: Use when running, resuming, or auditing the full Dasheng 8-stage media workflow with strict stage contracts and delivery outputs.
---

# Dasheng SOP Orchestrator

## 目的

统一调度 8 阶段创作流，防止越级、混稿、漏交付。

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 固定主链

`intake -> brief -> draft -> material -> rewrite -> publish -> distribute -> postmortem`

## 执行规则

1. 先识别当前阶段（用户说”继续/开始某阶段”时不得猜错阶段）。
2. 只调用当前阶段技能，不提前产出下游正式交付。
3. 每阶段必须产出文档 + manifest。
4. 多选题必须分题独立目录，禁止混稿。

## 阶段路由

- `intake` -> `dasheng-stage-intake-brief-draft` (intake 环节)
- `brief` -> **`dasheng-stage-brief-ai`** (AI 驱动选题生成，替代旧的规则系统)
- `draft` -> `dasheng-stage-intake-brief-draft` (draft 环节)
- `material` -> `dasheng-stage-material-refill`
- `rewrite` -> `dasheng-stage-rewrite` (已集成框架和策略)
- `publish` -> `dasheng-stage-publish-video` (视频补充生成)
- `distribute` -> **`dasheng-stage-distribute`** (多平台分发：微信/小红书/抖音/微博/X)
- `postmortem` -> 按项目复盘约定执行（可沿用现有复盘脚本）

### Distribute 阶段说明

**新增阶段（在 publish 和 postmortem 之间）**：`dasheng-stage-distribute`
- ✅ 读取 rewrite_manifest.json 自动路由内容到各平台
- ✅ 生成平台适配内容（微博摘要/X 推文串/抖音字幕）
- ✅ 调用现有 OpenClaw 平台 skill 执行发布
- ✅ 支持微信/小红书/抖音/微博/X 五大平台
- ⚠️ 微信仅保存草稿，需后台手动发布
- ⚠️ 微博需飞书审批后执行
- ⚠️ X 需用户在浏览器中手动确认

**调用的外部 Skills**：
```
wechat-multi-publisher  → 微信公众号
weibo-manager           → 微博（审批流）
baoyu-post-to-x         → X (Twitter)
xiaohongshu-auto        → 小红书
douyin-upload-skill     → 抖音
```

### Brief 环节升级说明

**新系统（推荐）**：`dasheng-stage-brief-ai`
- ✅ AI 理解事件因果关系
- ✅ 生成自然语言标题（不是模板拼接）
- ✅ 推荐写作框架和内容增强策略
- ✅ 提供完整的论证和证据需求
- ✅ 候选选题数量：10-15 个（vs 旧系统的 5 个）

**旧系统（备份）**：`phase2_rebuilder.py`
- 保留作为回退方案
- 仅在 AI 系统失败时使用

**使用方式**：
```bash
# 通过 Claude Code 或 OpenClaw 调用
# 输入：产物/01_内容采集/{run_id}/
# 输出：产物/02_Brief/{run_id}/selected_topics.json
```

## 入口校验

执行前先检查：

- `${DASHENG_WORKSPACE}/引擎/03_全链路SOP工作流/STAGE_INTERFACES.md`
- `${DASHENG_WORKSPACE}/skills/dasheng-media-sop/SKILL.md`

## 每日首跑自检（强制）

首次运行当天任务前，先执行一次最小自检并记录：

- 自检提示词：`SMOKE_PROMPTS.md` 的“全链路最小自检”
- 交付：`smoke_report.md`（仅状态、风险、阻塞，不产出正式稿件）
