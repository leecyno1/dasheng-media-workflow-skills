---
name: dasheng-stage-rewrite
description: Use when generating the 4-variant rewrite set per topic with hard word-count validation, final-structure inheritance, and optional personal style DNA injection.
---

# Dasheng Stage: Rewrite

## 默认路径

- `DASHENG_WORKSPACE=${DASHENG_WORKSPACE:-/Volumes/PSSD/Projects/公众号文章}`

## 阶段目标

每题生成 4 版改写，并继承终稿框架：

- wechat + luxun + hot
- wechat + lemon + normal
- xhs_video + luxun + hot
- xhs_video + lemon + normal

## 推荐命令

### 使用预设 DNA（默认）

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/rewrite_rerun_with_final_structure.py
node scripts/feishu_rewrite_push.js "$(date +%F)"
```

### 使用个人风格 DNA

```bash
cd "${DASHENG_WORKSPACE}"
python3 scripts/rewrite_with_personal_dna.py --dna-path "${DASHENG_WORKSPACE}/风格库/{作者}/风格画像.md"
node scripts/feishu_rewrite_push.js "$(date +%F)"
```

## DNA 选择策略

### 预设 DNA（luxun/lemon）
- **luxun**：犀利、数据驱动、强观点、适合财经/行业分析
- **lemon**：温和、叙事性强、情感共鸣、适合生活/文化内容
- **适用场景**：首次使用、通用场景、快速产出

### 个人风格 DNA
- 从用户历史文章提取的定制化风格（需先运行 `dasheng-style-profiler`）
- 包含 14 维风格分析、段落配方、叙述方法体系等
- **适用场景**：已有 10+ 篇历史文章、需要强化个人品牌识别度

## 写作框架与内容增强

改写阶段可选择应用写作框架和内容增强策略（见 `references/frameworks.md` 和 `references/content-enhance.md`）：

### 7 种写作框架
1. **痛点型**：解决问题、提供方案
2. **故事型**：人物、事件、趋势
3. **清单型**：盘点、推荐、方法论
4. **对比型**：A vs B、优劣分析
5. **热点解读型**：时事评论、趋势分析
6. **纯观点型**：立场鲜明、论证充分
7. **复盘型**：事后分析、经验总结

### 4 种内容增强策略
- **角度发现**：适用于热点解读型/纯观点型，找到差异化切入点
- **密度强化**：适用于痛点型/清单型，提升可操作性
- **细节锚定**：适用于故事型/复盘型，用真实细节增强代入感
- **真实体感**：适用于对比型，用真实用户声音替代抽象分析

## 字数硬阈值

- 公众号两版：`>=4000`（且不应无故超过 `8000`）
- 小红书视频两版：`>=1800`

## 强约束

1. 公众号改写必须继承终稿一级结构，不得强制改成固定三段论。
2. 不同题目必须独立目录、独立 bundle、独立 meta。
3. 字数未达标不得推送飞书。
4. 使用个人 DNA 时，必须严格遵循风格画像中的段落配方、叙述方法体系、标点符号偏好。

## 交付要求

- `<topic>__rewrite_bundle.md`
- `meta.json`（需包含使用的 DNA 类型和框架类型）
- `rewrite_manifest.json`

## 学习飞轮（可选）

改写完成后，可以让系统学习人工修改：

```bash
# 在飞书中修改后，同步回本地并学习
python3 scripts/learn_edits_from_feishu.py --date "$(date +%F)"
```

学习记录会保存到 `${DASHENG_WORKSPACE}/lessons/` 目录，下次改写时自动应用。

