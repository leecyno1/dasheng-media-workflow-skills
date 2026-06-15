# Publish 平台自动化调研

更新时间：2026-06-14

## 目标

Transwrite 生成平台内容包后，Publish 能一键或半自动发布到：

- 微信公众号
- 小红书
- 抖音
- B站
- 微博
- X / Twitter
- 可选：知乎、视频号、快手、百家号、TikTok、YouTube

## 总体判断

最合适的路线不是从零写平台自动化，而是组合四层：

1. 本地已有 OpenClaw / Baoyu skills 作为主执行器。
2. API-first CLI / Skill / MCP 作为小红书、微博、抖音的优先路径。
3. `social-auto-upload` 作为国内视频平台统一上传参考或外部依赖。
4. `Postiz` 作为海外/通用社媒排程系统候选，但它不覆盖公众号、小红书、B站等中文平台。

Publish 仍必须保留人工确认和 Publish Guard。多数平台存在验证码、风控、账号安全、API 权限限制，不能承诺无人值守全自动。

## 优先接入矩阵

| 平台 | 主执行器 | 备选/参考 | 建议等级 |
| --- | --- | --- | --- |
| 微信公众号 | `baoyu-post-to-wechat`、`wechat-multi-publisher`、`wechat-public-cli` | `wechat-article-publisher-skill`、`wechat-publisher`、`wechat-pub-rs` | 直接集成 |
| 小红书 | `dasheng-xhs-publish-bridge` | `All-IN-ONE`、`XhsSkills`、`Spider_XHS`、`xiaohongshu-mcp`、`rednote-mcp`、`xiaohongshu-auto`、`social-auto-upload` | API-first + browser fallback |
| 抖音 | `douyin-upload-skill` | `social-auto-upload` | 直接集成 |
| B站 | 暂无本地正式投稿 skill | `social-auto-upload`、`biliup-rs`、`bilibiliupload`、`biliup-watcher` | 新增包装 skill |
| 微博 | `weibo-manager`、`baoyu-post-to-weibo` | `weibo-create-new-post`、`WeiboPilot`、Selenium/Puppeteer 项目 | 强审批集成 |
| X | `baoyu-post-to-x` | `xurl`、`x-cli`、`TweetCLI`、X API v2 media upload | 直接集成 |
| 知乎 | `zhihu-post` | 浏览器自动化 | 按需集成 |
| 视频号/快手/百家号/TikTok | 暂无本地主执行器 | `social-auto-upload` | 后续统一视频分发插件 |

## 关键外部项目

### social-auto-upload

地址：https://github.com/dreammis/social-auto-upload

价值：

- 覆盖抖音、Bilibili、小红书、快手、视频号、百家号、TikTok 等视频上传和定时发布。
- 适合作为国内视频分发统一外部依赖。

风险：

- 浏览器/UI 自动化可能受平台改版影响。
- 需要账号登录态、Cookie、反风控策略。
- 不直接解决公众号、微博长文、X Article。

建议：

- 不直接吞进仓库。
- 作为 `publish-video-uploader-bridge` 外部依赖调用。
- B站/视频号/快手优先通过它做第一版。

### B站上传工具

候选：

- `biliup/biliup-rs`：命令行投稿、登录、上传、追加、查看稿件。
- `bilibiliupload`：Python CLI/库式上传。
- `biliup-watcher`：监听目录并自动上传到 B站。

建议：

- 首选 `biliup-rs` 做 B站包装 skill。
- `social-auto-upload` 做多平台视频统一上传 fallback。

### 小红书自动化

候选：

- `cv-cat/All-IN-ONE`：小红书、微博、抖音统一 CLI & Agent Skill，覆盖搜索、详情、评论、上传、发布、蒲公英和千帆等命令，适合做 API-first 执行入口。
- `cv-cat/XhsSkills`：小红书接口 skill 包装，偏薄桥接，适合被 Dasheng skill 调度。
- `cv-cat/Spider_XHS`：底层 API 和签名源头，适合做接口变更时的 source-of-truth。
- `xpzouying/xiaohongshu-mcp`：Go/Rod MCP，支持搜索、详情、发布图文和视频，适合 MCP 化接入。
- `TimeCyber/mcp-xiaohongshu` / `rednote-mcp`：Node/Playwright MCP，支持搜索、详情、评论、图文发布，适合浏览器/MCP fallback。
- `JoeanAmier/XHS-Downloader`：强采集/下载工具，适合竞品素材采集，不适合发布主链。
- 本地 `xiaohongshu-auto`：发布笔记、管理内容，依赖登录 Cookie / 浏览器。
- 本地 `xiaohongshu-ops`：选题、发布前演练、发布后复盘和运营。
- `xiaohongshu-automation`：Playwright CDP 连接 OpenClaw 浏览器，支持发布、搜索、评论、用户资料。
- `xhs_ai_publisher`：PyQt/FastAPI/Playwright，复用登录态和预览发布。
- `Autoxhs`：生成图片、标题、内容、标签并发布。

建议：

- Publish 主执行器改为 `dasheng-xhs-publish-bridge`，桥内优先 API-first / CLI / MCP。
- 优先级：`All-IN-ONE` → `XhsSkills/Spider_XHS` → `xiaohongshu-mcp/rednote-mcp` → `xiaohongshu-auto/browser fallback`。
- `XHS-Downloader` 只进入 intake / 竞品监控 / 素材抓取，不进入发布主链。
- 发布前运营校验和发布后维护可继续利用 `xiaohongshu-ops`。

### 微信公众号

候选：

- 本地 `baoyu-post-to-wechat`：HTML/Markdown/图文，API 或 Chrome CDP。
- 本地 `wechat-multi-publisher`：多篇 Markdown 推草稿箱。
- 本地 `wechat-public-cli`：CLI 发布/草稿。
- `wechat-article-publisher-skill`：Markdown/HTML 发布到公众号草稿。
- `wechat-publisher`：OpenClaw skill，Markdown + 图片上传 + 转 WeChat HTML + 草稿箱。
- `wechat-pub-rs`：Rust SDK，上传文章和管理草稿。

建议：

- 主路径：`baoyu-post-to-wechat`。
- 批量主副文：`wechat-multi-publisher`。
- CLI fallback：`wechat-public-cli`。
- API 权限不足时走浏览器/CDP，默认推草稿不直接群发。

### 微博

候选：

- 本地 `weibo-manager`：Puppeteer + Feishu 审批，强制 Request -> Approve -> Execute。
- 本地 `baoyu-post-to-weibo`：微博图文/头条文章半自动。
- `weibo-create-new-post`：Selenium 自动发微博。
- `WeiboPilot`：微博账号管理、批量发帖、定时发布、自动评论的 Electron 工具。

建议：

- 短微博必须用 `weibo-manager` 的审批流。
- 长文/头条文章走 `baoyu-post-to-weibo`。
- 不接入自动评论/自动私信，避免风控和运营风险。

### X / Twitter

候选：

- 本地 `baoyu-post-to-x`：文本、图片、视频、X Articles，支持 Chrome 插件/Computer Use/CDP。
- `xdevplatform/xurl`：X 官方 CLI，可走 API v2，支持媒体上传流程。
- `Infatoshi/x-cli`：X/Twitter API v2 CLI。
- `TweetCLI`：简单 CLI，文本与媒体附件。
- `Postiz`：开源社媒排程工具，支持 X 等海外平台。

建议：

- 主路径：`baoyu-post-to-x`，因为它已经适配本地 Chrome 和 X Article。
- API fallback：`xurl` / `x-cli`。
- 如果未来需要海外社媒统一日历和排程，再接 `Postiz`。

### Postiz

地址：https://github.com/gitroomhq/postiz-app

价值：

- 开源、自托管、社媒排程。
- 支持 X、Bluesky、Mastodon、Discord、TikTok、YouTube、Instagram、LinkedIn 等。

限制：

- 不覆盖公众号、小红书、B站、微博这类中文核心平台。
- 更适合海外平台排程和团队日历，不适合直接替代 Dasheng Publish。

建议：

- 作为海外平台排程候选，不作为当前主链核心。

## Publish 集成方案

### 1. 平台适配包

每个 channel pack 固定输出：

- `channel_pack.json`
- `README.md`
- `assets/`
- `execution_request.json`
- `verification_request.json`

### 1.1 持久化浏览器登录态

所有浏览器型发布必须走发布专用持久化 Profile：

- 配置：`configs/publish/browser_profiles.json`
- 打开：`python3 scripts/open_publish_browser.py <channel>`
- 默认目录：`~/Library/Application Support/DashengPublishProfiles/<platform>`

禁止使用 Chrome DevTools MCP 临时 profile、一次性自动化 profile、项目目录或 `skills/` 目录保存平台 cookies。Agent 只允许复用 profile 目录，不允许读取、导出、复制或提交 cookies。

当前映射：

| 渠道 | Profile |
| --- | --- |
| `wechat_article` | `~/Library/Application Support/DashengPublishProfiles/wechat` |
| `xiaohongshu_video` | `~/Library/Application Support/DashengPublishProfiles/xiaohongshu` |
| `douyin_video` | `~/Library/Application Support/DashengPublishProfiles/douyin` |

### 2. 执行模式

- `api_official`：官方 API，如抖音、X、公众号部分 API。
- `browser_confirm`：浏览器填充，用户确认发布。
- `approval_required`：微博这类必须 Request -> Approve -> Execute。
- `manual_package`：B站/视频号在没有稳定执行器前导出人工包。
- `fallback_export`：官方 API 或浏览器失败时导出 outbox。

### 2.1 Dry-run 预演入口

不依赖具体内容包的发布通路体检：

```bash
python3 scripts/run_mainline_stage.py doctor --publish
python3 scripts/run_mainline_stage.py doctor --publish --channel wechat_article --channel xiaohongshu_video
```

`doctor --publish` 只检查本地 skill、外部依赖根目录、CLI 二进制和持久化浏览器 Profile 配置，不打开浏览器、不读取 cookies、不触发真实发布。

正式执行前先跑：

```bash
python3 scripts/run_mainline_stage.py publish \
  --transwrite-manifest 产物/06_转写生产/<run_id>/transwrite_manifest.json \
  --publish-decision 产物/07_发布执行/<run_id>/publish_decision.json \
  --dry-run
```

该命令只做三件事：

- 生成平台 `channel_pack.json`、`execution_request.json`、`verification_request.json`。
- 调用 `prepare_publish_execution.py` 为每个渠道选择可用执行路线。
- 写出机器可读的 `publish_dry_run_report.json` 和人工审核用的 `publish_preflight_report.md`，等待人工确认后才进入真实执行。

### 3. 统一验真

平台执行器统一输入：

```bash
python3 scripts/build_publish_payload.py \
  --channel-pack 产物/07_发布执行/<run_id>/channel_packs/<topic_id>/<channel>/channel_pack.json
```

`publish_payload.json` 只负责把 `channel_pack.json` 转成平台 skill/CLI 可消费的标准输入，不会触发发布。

安全执行入口：

```bash
python3 scripts/execute_publish_request.py \
  --execution-request 产物/07_发布执行/<run_id>/channel_packs/<topic_id>/<channel>/execution_request.json
```

默认只做 dry-run；只有当前会话明确确认后才允许追加 `--confirm-execute`。即便确认执行，也只允许 `skill_draft_push` 类型的本地草稿推送路线；浏览器、人工包、外部 CLI、MCP 和 API-first 路线仍只输出下一步命令，不自动执行。

发布后必须回填：

- `platform_url`
- `platform_post_id` / `draft_id`
- `account`
- `published_at`
- `screenshot`
- `verification_status`
- `error`

标准回填入口：

```bash
python3 scripts/record_publish_result.py \
  --channel-pack 产物/07_发布执行/<run_id>/channel_packs/<topic_id>/<channel>/channel_pack.json \
  --success true \
  --status draft \
  --draft-id <draft_id> \
  --verification-status verified \
  --account <account_name>
```

该入口会同步更新：

- `channel_packs/<topic_id>/<channel>/publish_result.json`
- `channel_packs/<topic_id>/<channel>/publish_result.md`
- `channel_pack.json`
- `channel_execution_manifest.json`
- `publish_verification_report.json`
- `publish_manifest.json`

没有验真不得写 `published`。

批次验收入口：

```bash
python3 scripts/publish_guard.py \
  --publish-manifest 产物/07_发布执行/<run_id>/publish_manifest.json
```

该入口默认在同目录写出 `publish_guard_report.json` / `publish_guard_report.md`，并把报告路径、状态和验收时间回写到 `publish_manifest.publish_guard`。它只校验批次结果，不上传、不发布、不打开浏览器、不读取 cookies。

## 下一步落地

已完成：

- 更新 `publish-skill-matrix.md`。
- 新增 `social-auto-upload-bridge` skill。
- 新增 `bilibili-upload-bridge` skill。
- 新增上游仓库登记表：`configs/publish/upstream_repos.json`。
- 新增上游检查脚本：`scripts/check_publish_upstreams.py`。
- 新增发布结果回填脚本：`scripts/record_publish_result.py`。

下一步：

1. 扩展真实执行层：`prepare_publish_execution.py` 已能从任意渠道 `execution_request.json` 生成安全 dry-run 计划，下一步才允许进入确认后执行。
2. 小红书兼容入口：`prepare_xhs_publish_execution.py` 保留为通用脚本薄包装。
3. 实现 B站桥执行脚本，优先调用 `biliup-rs`，fallback 到 `social-auto-upload`。
4. 为公众号、抖音、B站补更细的账号预检：登录态、API key、上传权限、每日限额；不得读取或导出 cookies。
