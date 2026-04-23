# 视频模板风格定义

本文档定义 5 套标准视频模板的视觉风格、调色板和使用场景。

---

## 模板概览

| 模板名称 | 适用场景 | 主色调 | 特点 |
|---------|---------|--------|------|
| Claude Purple | 科技、AI、创新 | 紫色+粉色 | 科技感、渐变、粒子动画 |
| Cyberpunk | 科技、未来、趋势 | 青色+品红+黄色 | 故障效果、霓虹、扫描线 |
| Finance Business | 财经、商务、数据 | 金色+白色 | 专业、稳重、数据强调 |
| Medical Lancet | 医学、学术、研究 | 深红+深蓝 | 学术、简洁、高对比 |
| Anime Light | 生活、文化、轻松 | 柔和彩色 | 可爱、圆角、柔和阴影 |

---

## 1. Claude Purple（Claude 紫色风格）

### 视觉特征

**调色板**：
- 主色：紫色 `#a855f7`
- 次色：粉色 `#ec4899`
- 背景：深紫色渐变 `#1a0b2e` → `#2d1b4e`
- 文字：白色 `#ffffff`
- 强调：亮紫 `#c084fc`

**排版**：
- 标题字体：Inter Bold, 64-80px
- 正文字体：Inter Regular, 32-48px
- 数据字体：Inter SemiBold, 48-72px
- 行高：1.4-1.6

**视觉元素**：
- 渐变文字效果（紫色到粉色）
- 粒子动画背景
- 发光边框和阴影
- 毛玻璃效果（backdrop-blur）

**动画风格**：
- 进入：淡入 + 上滑（easeOutCubic）
- 强调：脉冲发光效果
- 转场：渐变溶解
- 数据：绘制动画（draw）

### 适用场景

✅ **推荐**：
- AI 和人工智能相关内容
- 科技创新和趋势分析
- 创业和投资主题
- 未来展望和预测

❌ **不推荐**：
- 传统行业分析
- 严肃学术内容
- 政策解读

### Finance Motion 8787 配置

```json
{
  "style": "neon",
  "palette": "custom",
  "customPalette": {
    "primary": "#a855f7",
    "secondary": "#ec4899",
    "background": "#1a0b2e",
    "text": "#ffffff"
  },
  "animation": {
    "enter": {
      "type": "fade",
      "durationMs": 1000,
      "easing": "easeOutCubic"
    },
    "emphasis": {
      "effect": "glow"
    }
  }
}
```

### Remotion 组件

文件：`/Users/lichengyin/clawd/remotion-video-starter/src/templates/ClaudePurple.jsx`

已实现（基于 FinanceNewsXhs 组件）

---

## 2. Cyberpunk（赛博朋克风格）

### 视觉特征

**调色板**：
- 主色：青色 `#00ffff`
- 次色：品红 `#ff00ff`
- 强调：黄色 `#ffff00`
- 背景：深蓝黑渐变 `#0a0a1a` → `#1a1a2e`
- 文字：白色 `#ffffff` + 青色发光

**排版**：
- 标题字体：Orbitron Bold, 64-80px
- 正文字体：Rajdhani Medium, 32-48px
- 数据字体：Orbitron ExtraBold, 56-88px
- 行高：1.3-1.5
- 字母间距：0.05em

**视觉元素**：
- 霓虹网格背景
- 故障效果（glitch）
- 扫描线动画
- 霓虹边框和发光
- 数字雨效果（可选）

**动画风格**：
- 进入：故障闪现 + 扫描线
- 强调：霓虹闪烁
- 转场：数字化分解
- 数据：脉冲扫描

### 适用场景

✅ **推荐**：
- 科技趋势和未来预测
- 区块链和加密货币
- 游戏和电竞行业
- 黑客和网络安全

❌ **不推荐**：
- 传统金融分析
- 医疗健康内容
- 政策和法规解读

### Finance Motion 8787 配置

```json
{
  "style": "neon",
  "palette": "custom",
  "customPalette": {
    "primary": "#00ffff",
    "secondary": "#ff00ff",
    "accent": "#ffff00",
    "background": "#0a0a1a",
    "text": "#ffffff"
  },
  "animation": {
    "enter": {
      "type": "glitch",
      "durationMs": 800,
      "easing": "easeInOutCubic"
    },
    "emphasis": {
      "effect": "pulse"
    }
  }
}
```

### Remotion 组件

文件：`/Users/lichengyin/clawd/remotion-video-starter/src/templates/Cyberpunk.jsx`

待创建

---

## 3. Finance Business（金融商务风格）

### 视觉特征

**调色板**：
- 主色：金色 `#ffd700`
- 次色：白色 `#ffffff`
- 强调：浅金 `#ffe55c`
- 背景：深蓝色 `#0a1929` → `#1a2332`
- 文字：白色 `#ffffff` + 金色点缀

**排版**：
- 标题字体：Playfair Display Bold, 56-72px
- 正文字体：Lato Regular, 28-40px
- 数据字体：Lato Bold, 48-64px
- 行高：1.5-1.7

**视觉元素**：
- 金色分割线和边框
- 数据图表强调
- 专业图标和符号
- 微妙的渐变和阴影
- 网格背景（可选）

**动画风格**：
- 进入：淡入 + 缩放（easeOutQuad）
- 强调：金色高亮
- 转场：推入/推出
- 数据：平滑增长动画

### 适用场景

✅ **推荐**：
- 财经分析和市场解读
- 投资策略和理财建议
- 企业财报和业绩分析
- 经济政策解读

❌ **不推荐**：
- 娱乐和生活内容
- 科技创新（太传统）
- 年轻化内容

### Finance Motion 8787 配置

```json
{
  "style": "broadcast",
  "palette": "financeBlue",
  "customAccent": "#ffd700",
  "animation": {
    "enter": {
      "type": "grow",
      "durationMs": 1200,
      "easing": "easeOutQuad"
    },
    "emphasis": {
      "effect": "highlight"
    }
  },
  "config": {
    "showGrid": true,
    "motionIntensity": "low"
  }
}
```

### Remotion 组件

文件：`/Users/lichengyin/clawd/remotion-video-starter/src/templates/FinanceBusiness.jsx`

待创建

---

## 4. Medical Lancet（医学柳叶刀风格）

### 视觉特征

**调色板**：
- 主色：深红 `#8b0000`
- 次色：深蓝 `#003366`
- 强调：中红 `#c41e3a`
- 背景：白色 `#ffffff` + 浅灰渐变 `#f5f5f5`
- 文字：深灰 `#333333`

**排版**：
- 标题字体：Merriweather Bold, 48-64px
- 正文字体：Source Sans Pro Regular, 24-36px
- 数据字体：Source Sans Pro SemiBold, 40-56px
- 行高：1.6-1.8
- 段落间距：较大

**视觉元素**：
- 简洁的线条和边框
- 高对比度文字
- 学术图表和图示
- 引用框和注释
- 最小化装饰

**动画风格**：
- 进入：淡入（easeInOutSine）
- 强调：下划线或边框
- 转场：淡入淡出
- 数据：线性增长

### 适用场景

✅ **推荐**：
- 医疗健康分析
- 学术研究解读
- 临床数据报告
- 公共卫生政策

❌ **不推荐**：
- 娱乐和生活内容
- 科技创新（太严肃）
- 商业营销

### Finance Motion 8787 配置

```json
{
  "style": "editorial",
  "palette": "custom",
  "customPalette": {
    "primary": "#8b0000",
    "secondary": "#003366",
    "background": "#ffffff",
    "text": "#333333"
  },
  "animation": {
    "enter": {
      "type": "fade",
      "durationMs": 1500,
      "easing": "easeInOutSine"
    },
    "emphasis": {
      "effect": "none"
    }
  },
  "config": {
    "showGrid": false,
    "motionIntensity": "low"
  }
}
```

### Remotion 组件

文件：`/Users/lichengyin/clawd/remotion-video-starter/src/templates/MedicalLancet.jsx`

待创建

---

## 5. Anime Light（浅色动漫风格）

### 视觉特征

**调色板**：
- 主色：柔和粉 `#ffb3d9`
- 次色：柔和蓝 `#b3d9ff`
- 强调：柔和黄 `#ffffb3`
- 背景：浅色渐变 `#fff9f0` → `#ffe6f0`
- 文字：深灰 `#4a4a4a`

**排版**：
- 标题字体：Nunito ExtraBold, 56-72px
- 正文字体：Nunito Regular, 28-40px
- 数据字体：Nunito Bold, 44-60px
- 行高：1.5-1.7
- 圆角：所有元素

**视觉元素**：
- 圆角矩形和卡片
- 柔和阴影
- 可爱图标和插画
- 彩色标签和徽章
- 波浪形装饰

**动画风格**：
- 进入：弹跳（easeOutBack）
- 强调：轻微摇晃
- 转场：滑动 + 淡入
- 数据：弹性增长

### 适用场景

✅ **推荐**：
- 生活方式和文化内容
- 教育和知识分享
- 轻松的科普内容
- 年轻化品牌

❌ **不推荐**：
- 严肃财经分析
- 学术研究
- 政策解读

### Finance Motion 8787 配置

```json
{
  "style": "zen",
  "palette": "custom",
  "customPalette": {
    "primary": "#ffb3d9",
    "secondary": "#b3d9ff",
    "accent": "#ffffb3",
    "background": "#fff9f0",
    "text": "#4a4a4a"
  },
  "animation": {
    "enter": {
      "type": "slide",
      "durationMs": 1000,
      "easing": "easeOutBack"
    },
    "emphasis": {
      "effect": "pulse"
    }
  },
  "config": {
    "showGrid": false,
    "motionIntensity": "medium"
  }
}
```

### Remotion 组件

文件：`/Users/lichengyin/clawd/remotion-video-starter/src/templates/AnimeLight.jsx`

待创建

---

## 风格选择决策树

```
内容类型是什么？
├─ AI/科技创新 → Claude Purple
├─ 未来趋势/区块链 → Cyberpunk
├─ 财经/商务 → Finance Business
├─ 医疗/学术 → Medical Lancet
└─ 生活/文化 → Anime Light

目标受众是谁？
├─ 专业投资者 → Finance Business
├─ 科技从业者 → Claude Purple 或 Cyberpunk
├─ 学术研究者 → Medical Lancet
└─ 年轻用户 → Anime Light

内容调性如何？
├─ 严肃专业 → Finance Business 或 Medical Lancet
├─ 科技前沿 → Claude Purple 或 Cyberpunk
└─ 轻松活泼 → Anime Light
```

---

## 在 Dasheng 工作流中的应用

### 自动风格推荐

在 `rewrite` 阶段，系统会根据以下因素推荐风格：

1. **选题关键词**
   - 包含 "AI", "人工智能", "创新" → Claude Purple
   - 包含 "区块链", "加密", "元宇宙" → Cyberpunk
   - 包含 "投资", "财报", "市场" → Finance Business
   - 包含 "医疗", "健康", "研究" → Medical Lancet
   - 包含 "生活", "文化", "教育" → Anime Light

2. **内容框架**
   - 数据密集型 → Finance Business
   - 趋势预测型 → Claude Purple 或 Cyberpunk
   - 学术分析型 → Medical Lancet
   - 知识科普型 → Anime Light

3. **目标平台**
   - B站（科技区）→ Claude Purple 或 Cyberpunk
   - B站（知识区）→ Medical Lancet 或 Anime Light
   - 小红书 → Anime Light
   - 抖音 → Claude Purple 或 Anime Light

### 手动指定风格

在 `publish_video_supplement.py` 中可以手动指定：

```bash
python3 scripts/publish_video_supplement.py \
  --run-id 2026-04-05_075240_ai \
  --style claude-purple  # 或 cyberpunk, finance-business, medical-lancet, anime-light
```

---

## 相关文档

- [Motion 系统整合指南](/Volumes/PSSD/Projects/dasheng-media-workflow-skills/docs/MOTION_INTEGRATION_GUIDE.md)
- [平台元数据规则](/Volumes/PSSD/Projects/dasheng-media-workflow-skills/skills/dasheng-stage-rewrite/references/platform-metadata.md)
- [Publish 阶段说明](/Volumes/PSSD/Projects/dasheng-media-workflow-skills/skills/dasheng-stage-publish-video/SKILL.md)

---

**最后更新**：2026-04-06  
**维护者**：Dasheng Media Team
