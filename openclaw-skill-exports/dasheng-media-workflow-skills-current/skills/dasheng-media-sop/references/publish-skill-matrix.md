# Publish 技能矩阵

更新时间：`2026-04-13`

## 保留并正式集成

| Skill | 用途 | 集成决策 | 在 Publish 中的角色 |
| --- | --- | --- | --- |
| `dasheng-stage-publish-video` | 图表动效视频 + 叙事动效视频 | 保留能力，吸收口径 | `Video Supplement` |
| `baoyu-post-to-wechat` | 公众号文章发布 / 草稿 / 浏览器/API | 正式集成 | 公众号单篇执行器 |
| `wechat-multi-publisher` | 多篇公众号草稿箱推送 | 正式集成 | 批量草稿执行器 |
| `md2wechat` | Markdown 转公众号 HTML、封面、信息图 | 正式集成 | 发布前预处理器 |
| `weibo-manager` | 微博短帖审批流发布 | 正式集成 | 微博短帖主执行器 |
| `baoyu-post-to-weibo` | 微博图文 / 视频 / 头条文章 | 正式集成 | 微博长文/半自动执行器 |
| `baoyu-post-to-x` | X 图文 / 视频 / 长文 | 正式集成 | X 执行器 |
| `xiaohongshu-auto` | 小红书图文 / 视频自动发布 | 正式集成 | 小红书执行器 |
| `douyin-upload-skill` | 抖音官方上传 / fallback | 正式集成 | 抖音执行器 |
| `publish-guard` | 发布后验真、限流、凭据审计 | 正式集成 | `Publish Guard` |

## 吸收后降级

| Skill | 当前状态 | 处理方式 |
| --- | --- | --- |
| `dasheng-stage-distribute` | 历史 skill | 平台路由与分发知识已并入 `publish`，不再作为正式入口 |

## 当前能力缺口

| 平台/能力 | 现状 | Publish 策略 |
| --- | --- | --- |
| 微信视频号 | 暂无正式执行 skill | 只导出素材包与待人工发布清单 |
| B站发布 | 暂无正式执行 skill | 只导出视频包、标题、简介与封面 |
| 多平台统一验真 | 依赖外部 skill 分散实现 | 统一收口到 `publish-guard` + `publish_manifest.json` |

## 自动化等级

| 等级 | 平台 |
| --- | --- |
| 自动 | 小红书、抖音 |
| 半自动 | 公众号、微博头条、X |
| 强审批 | 微博短帖 |
| 手动导出 | 微信视频号、B站等缺执行器平台 |

## 集成原则

1. 平台执行 skill 只负责“发”。
2. Dasheng `publish` 负责“选什么发、何时发、发哪版、怎么验真”。
3. 没有 `publish-guard` 验真，不算完成。
4. 平台 skill 失败时必须写回 `channel_execution_manifest.json`，不能只输出终端日志。
