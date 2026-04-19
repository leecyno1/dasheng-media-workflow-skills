# Rewrite 技能取舍结论

更新时间：`2026-03-26`

本结论基于本机已安装 skills 的 `SKILL.md` 比较得出。

## 一、比较对象

- `doc-coauthoring`
- `content-strategy`
- `social-content`
- `baoyu-format-markdown`
- `baoyu-markdown-to-html`
- `wechat-title-generator`
- `wechat-draft-writer`
- `wechat-topic-outline-planner`
- `wechat-style-profiler`

## 二、结论表

| Skill | 核心职责 | 主要重叠点 | 建议位置 | 结论 |
| --- | --- | --- | --- | --- |
| `doc-coauthoring` | 通用文档共创流程 | 与大纲规划、分段写作轻度重叠 | rewrite 前/兜底 | 降级 |
| `content-strategy` | 内容战略与选题/支柱规划 | 与结构规划、渠道规划重叠 | rewrite 前 | 移出 |
| `social-content` | 社媒内容改编与分发 | 与渠道适配、标题钩子轻度重叠 | rewrite 后 | 移出 |
| `baoyu-format-markdown` | 只做 markdown 排版与小修正 | 与 HTML 转换衔接 | rewrite 后 | 降级 |
| `baoyu-markdown-to-html` | markdown 转 HTML | 与发布转换层重叠 | 发布前 | 移出 |
| `wechat-title-generator` | 公众号标题生成 | 与正文排版有轻微交叉 | rewrite 后半段 | 保留 |
| `wechat-draft-writer` | 基于 confirmed outline + material + DNA 写高保真稿 | 与通用写作流程重叠，但更契约化 | rewrite 核心 | 保留 |
| `wechat-topic-outline-planner` | 公众号文章结构规划 | 与内容战略、结构搭建重叠 | rewrite 前 | 保留但前置 |
| `wechat-style-profiler` | 从样文提炼文风 DNA | 与正文风格执行互补，不替代 | rewrite 前 | 保留但前置 |

## 三、最终取舍

### rewrite 前

- `wechat-style-profiler`
- `wechat-topic-outline-planner`

### rewrite 中

- `wechat-draft-writer`

### rewrite 后

- `wechat-title-generator`
- `baoyu-format-markdown`（可选）

### 移出 rewrite

- `content-strategy`
- `social-content`
- `baoyu-markdown-to-html`

## 四、最小链路

`wechat-style-profiler` -> `wechat-topic-outline-planner` -> `wechat-draft-writer` -> `wechat-title-generator` -> `baoyu-format-markdown`

发布环节再接：

`baoyu-markdown-to-html` / `md2wechat` / `baoyu-post-to-wechat`
