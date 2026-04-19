# Publish 技能矩阵

更新时间：`2026-04-14`

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
| `xiaohongshu-ops` | 小红书运营动作 | 正式集成 | 小红书发布后运营辅助 |
| `douyin-upload-skill` | 抖音官方上传 / fallback | 正式集成 | 抖音执行器 |
| `zhihu-post` | 知乎专栏 / 想法发布 | 正式集成 | 知乎执行器（按需启用） |
| `wechat-public-cli` | 公众号本地 CLI 发布 | 正式集成 | 公众号补充执行器 |
| `publish-guard` | 发布后验真、限流、凭据审计 | 正式集成 | `Publish Guard` |

## 已核实的外部 skill 来源

| Skill | 来源路径 | 结论 |
| --- | --- | --- |
| `xiaohongshu-auto` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/xiaohongshu-auto/SKILL.md` | 正式发布执行器，支持图文/视频笔记 |
| `xiaohongshu-ops` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/xiaohongshu-ops/SKILL.md` | 运营辅助 skill，可做发布前巡检/运营动作，不算正式发布执行器 |
| `douyin-upload-skill` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/douyin-upload-skill/SKILL.md` | 正式发布执行器，支持 `doctor / auth / prepare / publish / fallback` |
| `bilibili-youtube-watcher` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/bilibili-youtube-watcher/SKILL.md` | 仅视频转录/摘要辅助，不是 B 站投稿执行器 |
| `zhihu-post` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/zhihu-post/SKILL.md` | 知乎专栏/想法执行器，可作为补充渠道 |
| `wechat-public-cli` | `/Volumes/PSSD/Projects/OpenClawInstaller/skills/default/wechat-public-cli/skill.md` | 公众号本地 CLI 执行器，适合凭据已配置环境 |

## 吸收后降级

| Skill | 当前状态 | 处理方式 |
| --- | --- | --- |
| `dasheng-stage-distribute` | 历史 skill | 平台路由与分发知识已并入 `publish`，不再作为正式入口 |

## 当前能力缺口

| 平台/能力 | 现状 | Publish 策略 |
| --- | --- | --- |
| 微信视频号 | 暂无正式执行 skill | 只导出素材包与待人工发布清单 |
| B站发布 | 暂无正式执行 skill | 只导出视频包、标题、简介与封面；如需辅助理解视频内容，可调用 `bilibili-youtube-watcher` |
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
2. Dasheng `publish` 负责“选什么发、何时发、发哪版、怎么验真”，并将可选辅助 skill 写入 `publish_skill_stack`。
3. 没有 `publish-guard` 验真，不算完成。
4. 平台 skill 失败时必须写回 `channel_execution_manifest.json`，不能只输出终端日志。
5. B站与视频号当前不得标记为“自动发布完成”；只能标记为 `manual_only / export_only`。
6. `channel_execution_manifest.json` 必须包含 `executor_invocation` 与 `helper_invocations`，确保每个渠道包下一步可直接调用或人工执行。
