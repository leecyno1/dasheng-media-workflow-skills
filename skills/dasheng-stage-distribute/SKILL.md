---
name: dasheng-stage-distribute
description: Use when entering the distribute stage to publish rewritten content and videos across WeChat, Xiaohongshu, Douyin, Weibo, and X platforms using existing OpenClaw platform skills.
---

# Dasheng Stage: Distribute（多平台分发）

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`
- `OPENCLAW_SKILLS=${OPENCLAW_SKILLS:-/Users/lichengyin/.openclaw/skills}`

## 阶段目标

将 Stage 5（改写）和 Stage 6（视频补充）的产物，按平台规格适配后，依次分发至各渠道。

**本阶段不产生新内容**，只做三件事：
1. 内容路由（选哪个变体发哪个平台）
2. 格式适配（生成摘要、字幕、话题标签等）
3. 调用现有 skill 执行发布

---

## 输入依赖

| 来源阶段 | 文件 | 说明 |
|---------|------|------|
| Stage 5 Rewrite | `产物/06_改写/{run_id}/rewrite_manifest.json` | 8个改写变体的路径和元数据 |
| Stage 6 Publish | `产物/07_Publish/{run_id}/publish_video_supplement_manifest.json` | 视频文件路径 |

**如果 Stage 6 视频未就绪**，可先分发纯文字渠道（微信/微博/X），视频渠道（小红书/抖音）待视频完成后补发。

---

## 固定平台路由

```
微信公众号  ← wechat_luxun_hot.md（主推）或 wechat_lemon_normal.md（备选）
小红书      ← xhs_video_{style}.md 脚本 + Stage 6 生成的视频文件
抖音        ← Stage 6 视频文件 + AI 生成字幕（从 xhs 脚本提取）
微博        ← AI 生成 ≤140字摘要 + 封面图（可选）
X (Twitter) ← AI 生成推文串（中文主体 + 英文摘要可选）
```

用户在执行前确认路由选择，AI 不得擅自决定。

---

## 执行流程

### 步骤 0：读取输入

```bash
# 读取改写清单
cat 产物/06_改写/{run_id}/rewrite_manifest.json

# 读取视频清单（如已完成 Stage 6）
cat 产物/07_Publish/{run_id}/publish_video_supplement_manifest.json
```

### 步骤 1：展示分发计划，等待用户确认

在执行任何发布前，展示以下确认表：

```
═══════════════════════════════════════════════════
              分发计划 | {run_id}
═══════════════════════════════════════════════════
渠道          | 选题         | 变体                  | 视频
-------------|-------------|----------------------|------
微信公众号    | {topic_1}   | wechat_luxun_hot     | 无
微信公众号    | {topic_2}   | wechat_luxun_hot     | 无
小红书视频    | {topic_1}   | xhs_video_luxun_hot  | ✓
小红书视频    | {topic_2}   | xhs_video_luxun_hot  | ✓
抖音          | {topic_1}   | 视频文件             | ✓
微博          | 合并摘要     | AI生成              | ✓封面
X (Twitter)  | 合并推文串   | AI生成              | 无
═══════════════════════════════════════════════════
[确认继续 / 修改路由 / 跳过某渠道]
```

### 步骤 2：内容适配生成

在调用平台 skill 前，先在当前 session 生成各平台所需的适配内容：

**2a. 微博摘要（≤140字）**
从选定的微信文章中提取核心论点，压缩为微博可发布的摘要。
- 保留最强的1个数据点
- 保留最反直觉的1个论断
- 结尾附话题标签（#话题名#）

**2b. X 推文串**
- 主推文：用中文写，≤240字，包含核心角度
- 子推文1：核心数据
- 子推文2：对普通人的影响
- 子推文3：CTA（欢迎关注/转发）
- 可选：英文摘要单推（用于国际受众）

**2c. 抖音字幕脚本**
从 xhs_video 脚本中提取口播文本，格式化为抖音字幕格式（每段 ≤15字，标注时间轴）。

**2d. 小红书话题标签**
根据选题内容，生成5-8个小红书话题标签（#格式）。

### 步骤 3：按渠道依次发布

执行顺序：**先文字渠道（低风险），后视频渠道（高风险）**

#### 3a. 微信公众号

调用 `wechat-multi-publisher`：

```bash
cd ${OPENCLAW_SKILLS}/wechat-multi-publisher
node scripts/publish.mjs \
  "产物/06_改写/{run_id}/{topic_1}/wechat_luxun_hot.md" \
  "产物/06_改写/{run_id}/{topic_2}/wechat_luxun_hot.md"
```

- 每篇文章作为独立草稿保存
- 执行后检查 WeChat 草稿箱确认
- **注意**：微信 API 仅保存草稿，需要编辑在公众号后台手动发布

#### 3b. 微博

调用 `weibo-manager`（必须经过审批流程）：

```bash
cd ${OPENCLAW_SKILLS}/weibo-manager

# 发送审批请求（替换 {chat_id} 为飞书群 ID）
node src/request_publish.js "{DASHENG_FEISHU_CHAT_ID}" \
  "{微博摘要内容}" \
  "产物/04_Material/{run_id}/{封面图}.png"
```

- 审批人在飞书收到卡片后回复"同意"
- 收到同意后执行：
```bash
node src/approve_post.js "{DASHENG_FEISHU_CHAT_ID}" "{post_id}"
```

#### 3c. X (Twitter)

调用 `baoyu-post-to-x`：

```bash
cd ${OPENCLAW_SKILLS}/baoyu-post-to-x
npx -y bun scripts/x-browser.ts "{主推文内容}" --image "产物/04_Material/{run_id}/{封面图}.png"
```

- 浏览器打开后用户手动确认并发布
- 子推文需要在浏览器中手动回复主推文

#### 3d. 小红书

调用 `xiaohongshu-auto`：

```bash
cd ${OPENCLAW_SKILLS}/xiaohongshu-auto
# 需根据 xiaohongshu-auto 实际 CLI 格式调用
# 传入：标题、脚本文字（前300字作封面文案）、视频文件路径、话题标签
```

- 每日上限5篇，两篇之间随机间隔 5-30 分钟
- 先发一个选题，确认无误后再发第二个

#### 3e. 抖音

调用 `douyin-upload-skill`：

```bash
cd ${OPENCLAW_SKILLS}/douyin-upload-skill

# 检查依赖
node scripts/douyin.js doctor

# 准备视频（提取字幕）
node scripts/douyin.js prepare "产物/07_Publish/{run_id}/videos/motion_narrative/{topic}.mp4"

# 发布（需先在 chat 中确认字幕选项）
node scripts/douyin.js publish "产物/07_Publish/{run_id}/videos/motion_narrative/{topic}.mp4" \
  --text "{抖音字幕}" \
  --private-status 0 \
  --auto-confirm false
```

### 步骤 4：生成分发清单

所有平台执行完毕后，生成 `distribute_manifest.json`：

```json
{
  "run_id": "{run_id}",
  "generated_at": "{timestamp}",
  "stage": "distribute",
  "input_rewrite": "产物/06_改写/{run_id}/rewrite_manifest.json",
  "input_video": "产物/07_Publish/{run_id}/publish_video_supplement_manifest.json",
  "results": [
    {
      "platform": "wechat",
      "topic_id": "{topic_id}",
      "variant": "wechat_luxun_hot",
      "status": "draft_saved",
      "media_id": "{wechat_media_id}",
      "note": "草稿已保存，需编辑在后台手动发布"
    },
    {
      "platform": "weibo",
      "topic_id": "merged",
      "variant": "ai_summary",
      "status": "pending_approval",
      "post_id": "{post_id}",
      "note": "等待飞书审批"
    },
    {
      "platform": "x",
      "topic_id": "merged",
      "variant": "ai_thread",
      "status": "browser_opened",
      "note": "用户需手动确认发布"
    },
    {
      "platform": "xiaohongshu",
      "topic_id": "{topic_id}",
      "variant": "xhs_video_luxun_hot",
      "status": "published",
      "post_url": "{xhs_post_url}"
    },
    {
      "platform": "douyin",
      "topic_id": "{topic_id}",
      "variant": "video",
      "status": "published",
      "video_id": "{douyin_video_id}"
    }
  ],
  "summary": {
    "total_platforms": 5,
    "fully_automated": ["xiaohongshu", "douyin"],
    "semi_automated": ["wechat", "weibo", "x"],
    "pending_manual_action": ["wechat_publish", "weibo_approval", "x_confirm"]
  }
}
```

---

## 强约束

1. **发布前必须展示分发计划，用户确认后才执行**
2. **微博必须经过审批流程，不得绕过**
3. **X 发布需用户在浏览器中手动确认**
4. **微信草稿保存后，必须提醒用户到后台手动发布**
5. **小红书两篇之间必须间隔 ≥5 分钟**
6. **不得混题**：不同选题的内容不能发错平台账号
7. **视频未就绪时**：优先分发文字渠道，不得因等待视频而阻塞全流程

---

## 前置条件（首次使用）

各平台 skill 需要完成一次性的认证配置，详见：
`skills/dasheng-stage-distribute/references/setup-guide.md`

---

## 交付物

| 文件 | 说明 |
|------|------|
| `产物/08_Distribute/{run_id}/distribute_manifest.json` | 分发结果清单 |
| `产物/08_Distribute/{run_id}/adapted_content/weibo_summary.md` | 微博适配摘要 |
| `产物/08_Distribute/{run_id}/adapted_content/x_thread.md` | X 推文串 |
| `产物/08_Distribute/{run_id}/adapted_content/douyin_captions.md` | 抖音字幕脚本 |

---

## 调用的外部 Skills

| Skill | 路径 | 平台 |
|-------|------|------|
| `wechat-multi-publisher` | `~/.openclaw/skills/wechat-multi-publisher` | 微信公众号 |
| `weibo-manager` | `~/.openclaw/skills/weibo-manager` | 微博 |
| `baoyu-post-to-x` | `~/.openclaw/skills/baoyu-post-to-x` | X (Twitter) |
| `xiaohongshu-auto` | `~/.openclaw/skills/xiaohongshu-auto` | 小红书 |
| `douyin-upload-skill` | `~/.openclaw/skills/douyin-upload-skill` | 抖音 |
