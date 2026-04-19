# Skills 安装与 Rewrite 增强方案

更新时间：`2026-03-26`

## 一、已安装新增 Skills

### 1. WeChat 相关

- `wechat`
  - 来源：`huangdijia/wechat-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat`
  - 用途：macOS 桌面微信发消息/发图自动化

- `baoyu-post-to-wechat`
  - 来源：`JimLiu/baoyu-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/baoyu-post-to-wechat`
  - 用途：公众号文章/图文发布

### 2. 素材与视频

- `media-downloader`
  - 来源：`yizhiyanhua-ai/media-downloader`
  - 安装位置：`/Users/lichengyin/.codex/skills/media-downloader`
  - 用途：按描述搜索并下载图片/视频/YouTube 片段

- `remotion-best-practices`
  - 来源：本机已有 skill 镜像到 Codex
  - 安装位置：`/Users/lichengyin/.codex/skills/remotion-best-practices`
  - 用途：将文章改写成视频脚本、镜头、字幕、动画结构

### 3. Baoyu 内容产出与分发

- `baoyu-article-illustrator`
- `baoyu-cover-image`
- `baoyu-format-markdown`
- `baoyu-imagine`
- `baoyu-infographic`
- `baoyu-markdown-to-html`
- `baoyu-post-to-weibo`
- `baoyu-post-to-x`
- `baoyu-slide-deck`
- `baoyu-translate`
- `baoyu-xhs-images`

以上均安装在：`/Users/lichengyin/.codex/skills/`

### 4. 第二批微信专项 Skills

- `wechat-article-extractor-skill`
  - 来源：本地 `OpenClaw` skill
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-article-extractor-skill`
  - 用途：提取公众号文章元数据与正文内容

- `wechat-draft-writer`
  - 来源：本地 `clawd/wechat-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-draft-writer`
  - 用途：基于 Brief / Material / confirmed outline / 风格 DNA 生成公众号高保真初稿

- `wechat-multi-publisher`
  - 来源：本地 `OpenClaw` skill
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-multi-publisher`
  - 用途：多篇 Markdown 批量推送到公众号草稿箱

- `wechat-public-cli`
  - 来源：本地 `OpenClaw` skill
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-public-cli`
  - 用途：调用本地 CLI 进行公众号/百家号发布下载

- `wechat-search`
  - 来源：本地 `OpenClaw` skill
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-search`
  - 用途：搜公众号文章

- `wechat-style-profiler`
  - 来源：本地 `clawd/wechat-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-style-profiler`
  - 用途：建立公众号作者风格 DNA

- `wechat-title-generator`
  - 来源：本地 `clawd/wechat-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-title-generator`
  - 用途：基于 brief / outline / 初稿生成标题候选

- `wechat-topic-outline-planner`
  - 来源：本地 `clawd/wechat-skills`
  - 安装位置：`/Users/lichengyin/.codex/skills/wechat-topic-outline-planner`
  - 用途：基于 Brief / Material 规划公众号文章大纲

- `md2wechat`
  - 来源：`geekjourneyx/md2wechat-skill`
  - 安装位置：`/Users/lichengyin/.codex/skills/md2wechat`
  - 用途：Markdown 转公众号 HTML、上传草稿、图片生成、风格化处理

## 二、Rewrite 环节最有价值的 Skills

### S 级：直接定义公众号 Rewrite 工作流

1. `wechat-style-profiler`
   - 作用：把参考账号的文风 DNA 显式化
   - 价值：这是公众号 rewrite 能否“像”的前置资产，不是可选项

2. `wechat-topic-outline-planner`
   - 作用：把 Brief / Material 压成公众号可写大纲
   - 价值：如果前序大纲不是公众号导向，它能显著降低 rewrite 返工

3. `wechat-draft-writer`
   - 作用：在结构确认后生成公众号高保真初稿
   - 价值：这实际上覆盖了“标准初稿到公众号稿”的大段工作

4. `wechat-title-generator`
   - 作用：专门做公众号标题层
   - 价值：标题是公众号流量系统的一部分，最好从正文 rewrite 中剥离

### A 级：直接增强 Rewrite 主流程

1. `baoyu-format-markdown`
   - 作用：把改写后的正文整理成高可读 markdown 结构
   - 价值：不改观点，只做结构与排版整理，适合作为 rewrite 的最后一步

2. `content-strategy`
   - 作用：校正选题表达角度、受众导向、标题方向
   - 价值：适合在 rewrite 开始前确认“这稿子到底写给谁”

3. `doc-coauthoring`
   - 作用：把改写过程拆成目标、约束、读者感受、版本迭代
   - 价值：适合长稿、多轮打磨，尤其适合你的工作流

4. `social-content`
   - 作用：把主稿拆成适合公众号、小红书、X、短视频文案的多平台表达
   - 价值：虽然更接近发布，但也会反向约束 rewrite 的句式密度与节奏

5. `baoyu-translate`
   - 作用：输出英文或双语版本时保留结构
   - 价值：适合需要外网分发或英文摘要的稿件

6. `md2wechat`
   - 作用：把 rewrite 后的 Markdown 直接转公众号 HTML，并支持上传草稿
   - 价值：它把 rewrite 与实际公众号交付打通，但当前本机尚未安装 `md2wechat` CLI

### B 级：增强 Rewrite 的表达呈现

1. `baoyu-cover-image`
   - 作用：根据文章主判断生成封面概念
   - 价值：会倒逼 rewrite 更明确核心冲突和主标题

2. `baoyu-infographic`
   - 作用：把复杂段落抽成结构化信息图
   - 价值：可以反过来检验 rewrite 是否真的讲清楚了

3. `baoyu-article-illustrator`
   - 作用：为文中关键段落自动配图
   - 价值：适合大稿，能帮助安排“哪一段需要视觉锚点”

4. `baoyu-xhs-images`
   - 作用：把文章拆成小红书卡片
   - 价值：适合 rewrite 时提前控制句长、点位密度和钩子感

5. `baoyu-markdown-to-html`
   - 作用：把 markdown 主稿转换为 HTML 交付
   - 价值：是 rewrite 到发布之间的桥梁

6. `theme-factory`
   - 作用：统一视觉主题
   - 价值：适合长图、专题页、汇报稿，不是正文改写核心

### B+ 级：Rewrite 前后的素材与证据增强

1. `wechat-search`
   - 作用：补搜公众号相关文章
   - 价值：适合在 rewrite 前补样本和补观点来源

2. `wechat-article-extractor-skill`
   - 作用：把公众号 URL 结构化提取
   - 价值：适合做样本入库、风格学习、引用回查

3. `media-downloader`
   - 作用：补图、补视频、补 YouTube 片段
   - 价值：不直接改字句，但能强化 rewrite 之后的视觉表达

### C 级：Rewrite 后的下游增强

1. `baoyu-post-to-wechat`
2. `baoyu-post-to-weibo`
3. `baoyu-post-to-x`
4. `wechat`
5. `wechat-multi-publisher`
6. `wechat-public-cli`
7. `remotion-best-practices`

这些更偏发布、素材、视频化，不是正文 rewrite 本身的核心能力，但适合接在 rewrite 之后。

## 三、我建议的 Rewrite 新方案

把 rewrite 阶段拆成 5 个子动作：

### Step 0：公众号专用前置校准

使用：
- `wechat-style-profiler`
- `wechat-topic-outline-planner`

目标：
- 确认这篇文章是否要走“公众号专属表达”
- 把 L1 风格知识与当前题目对齐
- 在 rewrite 前定好公众号化结构，而不是边写边改

### Step 1：逻辑改写

使用：
- `doc-coauthoring`
- `content-strategy`

目标：
- 校正受众
- 校正文章主判断
- 校正结构顺序
- 删除背景噪音和重复论据

### Step 2：语言改写

人工主导，必要时调用：
- `wechat-draft-writer`

规则固定：
- 不改事实边界
- 不引入新证据
- 不风格化过度
- 只做节奏、句长、逻辑压缩、标题增强

### Step 3：版式整理

使用：
- `baoyu-format-markdown`
- `md2wechat`（仅当 CLI 可用时）

目标：
- 标题层级清晰
- 列表、加粗、引用、分节统一
- 为后续发布与视觉补料留结构锚点
- 若进入公众号交付，则同步产出 HTML 预览版本

### Step 4：渠道前适配检查

按目标渠道决定是否调用：
- `social-content`
- `baoyu-markdown-to-html`
- `baoyu-xhs-images`
- `baoyu-cover-image`
- `wechat-title-generator`

目标：
- 判断这篇稿是更像公众号稿、长图稿、卡片稿，还是可视频化稿
- 标题生成单独处理，不与正文 rewrite 混写

### Step 5：发布或草稿箱落地

按实际工具链选择：
- `baoyu-post-to-wechat`
- `wechat-multi-publisher`
- `wechat-public-cli`

目标：
- 不再重复人工复制粘贴
- 把 rewrite 成果直接落到公众号草稿箱或发布接口

## 四、我的结论

最值得嵌入公众号 rewrite 主流程的，不是全部已装 skill，而是这 7 个：

1. `wechat-style-profiler`
2. `wechat-topic-outline-planner`
3. `wechat-draft-writer`
4. `doc-coauthoring`
5. `content-strategy`
6. `baoyu-format-markdown`
7. `wechat-title-generator`

如果是你的这类深度稿，我建议默认工作方式为：

`标准初稿 -> wechat-style-profiler 对齐 DNA -> wechat-topic-outline-planner 校正公众号结构 -> doc-coauthoring/content-strategy 逻辑校正 -> wechat-draft-writer / 人工 rewrite -> baoyu-format-markdown 排版 -> wechat-title-generator 出标题 -> 视条件调用 md2wechat / baoyu-post-to-wechat`

## 五、待确认项

`wechat-skill` 我按最接近且可安装的仓库处理为：

- `wechat`：桌面微信消息自动化

如果你真正想要的是不同层面的微信生态能力，目前已分别具备：

- 公众号文章提取：`wechat-article-extractor-skill`
- 公众号搜索：`wechat-search`
- 公众号风格画像：`wechat-style-profiler`
- 公众号大纲规划：`wechat-topic-outline-planner`
- 公众号初稿写作：`wechat-draft-writer`
- 公众号标题生成：`wechat-title-generator`
- Markdown 转公众号 HTML：`md2wechat`
- 公众号草稿箱推送：`baoyu-post-to-wechat` / `wechat-multi-publisher` / `wechat-public-cli`
- 桌面微信发送：`wechat`

## 六、环境状态

- `bun`：已存在
- `npx`：已存在
- `node`：已存在
- `python3`：已存在

Baoyu 系列的基本运行前提已满足。

## 七、当前限制

- `md2wechat` **skill 已安装**，但 `md2wechat` **CLI 还不在 PATH**
- `wechat-public-cli` skill 已安装，但对应 `wechat-public-cli` 可执行程序是否已全局安装，仍需单独验证
- 这意味着：当前可以先把 rewrite 流程和模板固化，但真正的“自动上传公众号草稿箱”还需要补一次 CLI / 凭证配置
