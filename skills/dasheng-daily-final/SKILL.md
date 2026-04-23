---
name: dasheng-daily-final
description: Use only when replaying or debugging the legacy Dasheng finalization step; the standard mainline now splits this logic across rewrite, material, publish, and postmortem under dasheng-media-sop.
---

# dasheng-daily-final

## 状态

`historical module / 已退出主链`

## 当前定位

这个 skill 对应旧链路中的“强化版 / final”层。

它把多种能力混在一起：

- 复审
- 标题生成
- 多媒介适配
- 强化打包

这与当前新主链的分层方式冲突，因此已退出主链。

## 当前替代关系

- 复审与平台适配：进入 `rewrite`
- 素材与补图补视频：进入 `material`
- 发布包与渠道安排：进入 `publish`
- 数据回流：进入 `postmortem`

总控入口：

- `/Volumes/PSSD/Projects/公众号文章/skills/dasheng-media-sop/SKILL.md`

## 何时仍可使用

- 回看旧版“强化版”产物
- 调试旧飞书/群消息集成
- 对比新旧链路输出差异

默认不再作为对外工作流入口。
