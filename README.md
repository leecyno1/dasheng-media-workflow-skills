# Dasheng Media Workflow Skills

⭐ **AI 驱动的媒体内容生产工作流套件** - 从内容采集到发布复盘的完整智能化流程

## 🎯 核心特性

### ⭐ 全面 AI 化（v2.0 最新升级）

- **Brief AI 化**：自然语言标题，告别模板拼接
- **Draft 框架驱动**：结构化初稿，应用内容增强策略
- **Material 智能优化**：AI 图表门控 + 精准素材检索

### 📊 工作流

```
Intake → Brief (AI) → Draft (框架) → Material (AI) → Rewrite → Publish → Distribute → Postmortem
```

### 🚀 关键改进

**Brief 环节**：
- ❌ 旧：”外交部、伊朗：事件升级之外，长期秩序成本在怎样上升”
- ✅ 新：”中东冲突如何重塑全球能源供应链”

**Draft 环节**：
- 根据推荐框架生成结构化初稿
- 应用 4 种内容增强策略
- 自动质量验证（字数、结构、引用）

**Material 环节**：
- AI 判断哪些数据需要可视化（减少 30-50% 不必要图表）
- AI 优化搜索关键词（提高 50-100% 素材命中率）

## 📦 技能清单

仓库内共 8 个技能：

1. **dasheng-sop-orchestrator**  
   全链路入口与调度器，负责阶段识别、路由和规则约束

2. **dasheng-stage-intake-brief-draft** ⭐ 已升级  
   负责 `intake/brief/draft` 三阶段，集成 AI brief 和框架驱动 draft

3. **dasheng-stage-brief-ai** ⭐ 新增  
   AI 驱动的选题生成，自然语言标题 + 框架推荐

4. **dasheng-stage-material-refill** ⭐ 已增强  
   素材生成与填充，集成 AI 图表门控和智能检索

5. **dasheng-stage-rewrite**  
   多渠道改写、多 DNA 风格与情绪档位适配

6. **dasheng-stage-publish-video**  
   发布前视频增强（动态图表 + motion 叙事）

7. **dasheng-stage-distribute** ⭐ 新增  
   多平台内容分发（微信/微博/X/小红书/抖音）

8. **dasheng-style-profiler**  
   风格 DNA 提取（14 维分析框架）

### 🔌 推荐集成的 ClawHub Skills

增强 distribute 阶段能力：

- **social-copy-generator**: 从单一输入生成 14 个平台的优化文案
- **wechat-video-publish**: 微信视频号发布支持
- **auto-publisher**: 多平台视频批量发布编排器

安装方法：
```bash
openclaw skills install social-copy-generator
openclaw skills install wechat-video-publish
openclaw skills install auto-publisher
```

## 🛠️ 快速开始

### 安装

```bash
# 默认安装到 ~/.openclaw/skills
bash install_to_openclaw.sh

# 自定义安装路径
bash install_to_openclaw.sh /your/openclaw/skills
```

### 环境配置

```bash
# 1. 复制环境模板
cp ENV_TEMPLATE.env ~/.openclaw/dasheng.env

# 2. 编辑配置文件，填入必要信息
# - DASHENG_WORKSPACE
# - FINANCE_MOTION_WORKSPACE
# - DASHENG_OUTPUT_ROOT
# - DASHENG_FEISHU_ROOT_URL
# - DASHENG_FEISHU_CHAT_ID
# - FEISHU_APP_ID / FEISHU_APP_SECRET
# - TUSHARE_TOKEN
# - 图片生成 provider keys

# 3. 加载环境变量
set -a; source ~/.openclaw/dasheng.env; set +a
```

### 运行工作流

```bash
cd “${DASHENG_WORKSPACE}”

# 1. Intake - 内容采集
python3 scripts/run_stage1_intake.py

# 2. Brief - AI 驱动的选题生成
# 使用 dasheng-stage-brief-ai skill

# 3. Draft - 框架驱动的初稿生成
python3 scripts/draft_with_framework.py \
  --brief-dir “产物/02_Brief/{run_id}_ai” \
  --output-dir “产物/03_Draft/{run_id}”

# 4. Material - AI 优化的素材准备
python3 scripts/material_execute_pack.py \
  --pack-root “<topic_pack_root>” \
  --steps charts,image_search,video_search,ai_prep

# 5. Rewrite - 平台特定改写
python3 scripts/rewrite_rerun_with_final_structure.py

# 6. Publish - 发布前视频增强
python3 scripts/publish_video_supplement.py
```

## 📚 核心文档

### 升级报告
- [完整升级报告](COMPLETE_UPGRADE_REPORT.md) - 两阶段升级的完整说明
- [Brief AI 测试报告](BRIEF_AI_TEST_REPORT.md) - Brief 环节的 AI 改造
- [Brief 新旧对比](BRIEF_AI_COMPARISON.md) - 详细的效果对比
- [第二阶段总结](PHASE2_UPGRADE_SUMMARY.md) - Draft 和 Material 的智能化

### 使用指南
- [项目说明](CLAUDE.md) - 完整的项目文档
- [Brief AI 生成指南](skills/dasheng-stage-brief-ai/references/ai-generation-guide.md)
- [选题评估框架](skills/dasheng-stage-brief-ai/references/topic-evaluation.md)
- [写作框架](skills/dasheng-stage-rewrite/references/frameworks.md)
- [内容增强策略](skills/dasheng-stage-rewrite/references/content-enhance.md)

## 🎨 写作框架和策略

### 7 种写作框架
- **痛点型**：问题-解决方案结构
- **故事型**：叙事结构
- **清单型**：列表结构
- **对比型**：A vs B 分析
- **热点解读型**：时事评论
- **纯观点型**：立场鲜明
- **复盘型**：事后分析

### 4 种内容增强策略
- **角度发现**：找到差异化视角
- **密度强化**：增加可操作细节
- **细节锚定**：用真实细节增强代入感
- **真实体感**：用真实用户声音

## 📈 预期效果

### 编辑工作量
- Brief 修改：减少 80%
- Draft 修改：减少 50%
- Material 筛选：减少 40%

### 生产效率
- Brief 生成：从 2 小时降至 30 分钟
- Draft 生成：从 4 小时降至 1 小时
- Material 准备：从 3 小时降至 1.5 小时

## 🔧 执行规则

### 关键约束
- 必须遵循固定主链顺序
- 不跨阶段提前产出正式交付
- 每阶段必须有"文档 + manifest"
- 多选题必须按题拆分（每题单独目录）

### 入口建议
优先从 `dasheng-sop-orchestrator` 进入，避免阶段错位

### 每日启动建议
使用 `SMOKE_PROMPTS.md` 先做一次最小自检，确认路径、凭据、接口齐全

## 🚦 版本管理

- 命名规范：`dasheng-media-workflow-skills-YYYYMMDD-vX`
- 同日多次迭代：v1, v2, v3
- 保留历史版本以支持回滚

## 📝 更新日志

### 2026-04-05 - v2.0 ⭐ 重大升级
- ✅ Brief 环节完全 AI 化
- ✅ Draft 环节集成框架系统
- ✅ Material 环节 AI 优化（图表门控 + 素材检索）
- ✅ 端到端智能化工作流

### 2026-04-04 - v1.5
- ✅ 创建 dasheng-stage-brief-ai skill
- ✅ 测试并验证 AI 生成效果
- ✅ 生成详细的对比报告

## 🤝 致谢

本项目整合了以下仓库的优秀实践：
- [wewrite](https://github.com/oaker-io/wewrite) - 选题评估框架
- [wechat-skills](https://github.com/gainubi/wechat-skills) - 写作框架和风格分析

---

**最后更新**：2026-04-05  
**当前版本**：v2.0  
**维护者**：Dasheng Media Team

