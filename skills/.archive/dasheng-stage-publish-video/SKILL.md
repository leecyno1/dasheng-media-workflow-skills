---
name: dasheng-stage-publish-video
description: Use when entering publish stage and needing the mandatory pre-publish video supplement, including interactive chart videos and motion narrative videos with style template selection.
---

# Dasheng Stage: Publish + Video Supplement

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`
- `FINANCE_MOTION_WORKSPACE=${FINANCE_MOTION_WORKSPACE:-/Volumes/PSSD/Projects/finance-motion-8787}`

## 阶段目标

发布前先补两类视频，再做渠道分发：

1. 互动图表视频（CSV -> finance-motion-8787 -> webm/mp4）
2. motion 叙事视频（改写稿框架精华 + 关键数据 -> 动画场景 -> webm/mp4）

⭐ **新增**：支持 5 套标准视频风格模板，根据内容类型自动选择或手动指定。

## 视频风格模板

系统支持 5 套专业风格模板：

1. **claude-purple** - Claude 紫色风格
   - 适用：AI、科技创新、创业投资
   - 特点：紫粉渐变、科技感、粒子动画

2. **cyberpunk** - 赛博朋克风格
   - 适用：未来趋势、区块链、游戏电竞
   - 特点：霓虹网格、故障效果、扫描线

3. **finance-business** - 金融商务风格
   - 适用：财经分析、市场解读、企业财报
   - 特点：金色点缀、专业稳重、数据强调

4. **medical-lancet** - 医学柳叶刀风格
   - 适用：医疗健康、学术研究、公共卫生
   - 特点：简洁学术、高对比度、最小化装饰

5. **anime-light** - 浅色动漫风格
   - 适用：生活文化、教育科普、年轻化内容
   - 特点：柔和彩色、圆角卡片、可爱风格

详见：`references/template-styles.md`

## 一键执行

```bash
cd "${DASHENG_WORKSPACE}"

# 使用默认风格（根据内容自动选择）
python3 scripts/publish_video_supplement.py

# 手动指定风格
python3 scripts/publish_video_supplement.py --style claude-purple
python3 scripts/publish_video_supplement.py --style cyberpunk
python3 scripts/publish_video_supplement.py --style finance-business
python3 scripts/publish_video_supplement.py --style medical-lancet
python3 scripts/publish_video_supplement.py --style anime-light
```

## 工作流程

### Step 1: 风格选择

系统会根据以下因素自动推荐风格：

1. **从 rewrite_manifest.json 读取选题关键词**
   - 包含 "AI", "人工智能" → claude-purple
   - 包含 "区块链", "加密" → cyberpunk
   - 包含 "投资", "财报" → finance-business
   - 包含 "医疗", "健康" → medical-lancet
   - 包含 "生活", "文化" → anime-light

2. **从 brief 阶段读取推荐框架**
   - 数据密集型 → finance-business
   - 趋势预测型 → claude-purple 或 cyberpunk
   - 学术分析型 → medical-lancet
   - 知识科普型 → anime-light

3. **用户可手动覆盖**
   - 使用 `--style` 参数指定

### Step 2: Finance Motion 预览（可选）

```bash
# 启动 Finance Motion 8787
cd /Volumes/PSSD/Projects/finance-motion-8787
npm run dev
# 访问 http://127.0.0.1:8787

# 在浏览器中预览和调整
# 满意后导出配置
npm run scenes:build
```

### Step 3: 转换为 Remotion 配置

```bash
cd /Volumes/PSSD/Projects/dasheng-media-workflow-skills

# 转换 Finance Motion 配置到 Remotion
python3 scripts/convert_finance_motion_to_remotion.py \
  --input /Volumes/PSSD/Projects/finance-motion-8787/dashboard/scenes.json \
  --output /Users/lichengyin/clawd/remotion-video-starter/src/compositions/generated-config.json \
  --style claude-purple
```

### Step 4: Remotion 渲染

```bash
cd /Users/lichengyin/clawd/remotion-video-starter

# 预览（可选）
npm start
# 访问 http://localhost:3000

# 渲染最终视频
npx remotion render FinanceNewsXhs out/video.mp4 --quality=100
```

## 线程对接

- `codex://threads/019d31c5-bb7f-7a40-a087-9d219e9bd6ab`

## 交付要求

- `publish_video_supplement_report.md`
- `publish_video_supplement_manifest.json`（包含使用的风格模板）
- 每题目录：
  - `videos/interactive_charts/*.webm|*.mp4`
  - `videos/motion_narrative/*.webm|*.mp4`
  - `videos/style_info.json`（记录使用的风格）

## 强约束

1. 视频补充未完成，不进入正式 publish 包。
2. 保证每题独立产物，不混题。
3. 失败必须写入 manifest（命令、错误、返回码）。
4. **风格选择必须记录到 manifest**，便于后续追溯和优化。

## 相关文档

- [视频模板风格定义](references/template-styles.md)
- [Motion 系统整合指南](/Volumes/PSSD/Projects/dasheng-media-workflow-skills/docs/MOTION_INTEGRATION_GUIDE.md)
- [Finance Motion 到 Remotion 转换器使用说明](/Volumes/PSSD/Projects/dasheng-media-workflow-skills/scripts/convert_finance_motion_to_remotion.py)

