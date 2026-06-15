# Dasheng Media Workflow Skills

**6阶段自媒体内容创作自动化系统**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

端到端的中文社交媒体内容创作自动化系统，支持微信公众号、小红书、微博等多平台内容生产与分发。

## 快速开始

### 安装

```bash
git clone https://github.com/leecyno1/dasheng-media-workflow-skills.git
cd dasheng-media-workflow-skills
./scripts/install.sh
```

### 配置API密钥

```bash
# 创建.env文件
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
```

### 运行第一个工作流

```bash
# Stage 1: 内容采集
python3 scripts/run_stage1_intake.py

# 查看采集结果
ls 产物/01_内容采集/
```

详细安装指南请参考 [INSTALLATION.md](INSTALLATION.md)

## 核心特性

- ✅ **6阶段标准化工作流** - Intake → Brief → Draft → Transwrite → Publish → Postmortem
- ✅ **HITL质量门** - 关键节点保留人工审核机制
- ✅ **多平台适配** - 支持微信公众号、小红书、微博、抖音、B站
- ✅ **AI驱动** - 基于Claude 4.6的智能内容生成与优化
- ✅ **DNA系统** - 可配置的风格、结构、质量标准
- ✅ **完整测试覆盖** - 87个单元测试 + 集成测试 + E2E测试
- ✅ **飞书协作** - 与飞书深度集成，支持团队协作

## 工作流概览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Stage 1    │───▶│  Stage 2    │───▶│  Stage 3    │
│   Intake    │    │   Brief     │    │   Draft     │
│  内容采集    │    │  选题分析    │    │  正文/HTML   │
└─────────────┘    └─────────────┘    └─────────────┘
                                                │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Stage 6    │◀───│  Stage 5    │◀───│  Stage 4    │◀─────────────┘
│ Postmortem  │    │  Publish    │    │ Transwrite  │
│  分析复盘    │    │  发布执行    │    │  转写生产    │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Stage 1: Intake（内容采集）
从多个数据源采集每日热点内容，进行去重、聚类、排序。

### Stage 2: Brief（选题分析）
AI生成5-10个选题候选，编辑确认后进入初稿阶段。

### Stage 3: Draft（初稿生成）
基于选题生成正文、数据图表、配图和可编辑自包含 HTML，支持人工迭代修改。

### Stage 4: Transwrite（转写生产）
将确认后的 Draft 转为公众号文章、口播视频和播客生产包，负责 DNA/humanize、封面、视频视觉层和播客 API 请求体。

### Stage 5: Publish（发布执行）
验收转写包，生成发布包，推草稿或导出人工发布包，并回收发布链接。

### Stage 6: Postmortem（分析复盘）
回收发布数据并回写选题、证据、结构和渠道经验。

## 文档

- [安装指南](INSTALLATION.md) - 详细安装步骤
- [快速开始](docs/guides/quick-start.md) - 5分钟快速上手
- [阶段详解](docs/guides/stage-by-stage.md) - 6个阶段的详细说明
- [架构设计](docs/technical/architecture.md) - 系统架构与设计决策
- [阶段接口](docs/STAGE_INTERFACES.md) - 各阶段输入输出规范
- [完整文档](docs/README_FULL.md) - 原完整README
- [贡献指南](CONTRIBUTING.md) - 如何参与开发

## 系统要求

- Python 3.10+
- Node.js 18+
- 8GB RAM
- 5GB 磁盘空间

## 技术栈

- **AI模型**: Claude 4.6 (Opus/Sonnet)
- **语言**: Python 3.10+, Node.js 18+
- **数据**: Tushare (金融数据), AkShare (市场数据)
- **协作**: 飞书API
- **测试**: pytest, jest
- **图像**: DALL-E 3, Stable Diffusion

## 测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 检查系统健康
python3 scripts/workflow_doctor.py

# 验证安装
python3 scripts/verify_installation.py
```

## 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目开发。

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本历史和变更记录。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/leecyno1/dasheng-media-workflow-skills/issues)
- **功能建议**: [GitHub Discussions](https://github.com/leecyno1/dasheng-media-workflow-skills/discussions)

---

**注意**: 本项目仅供学习和研究使用。使用本系统生成的内容需遵守各平台的内容政策和法律法规。
