# Dasheng Media Workflow Skills

**7阶段自媒体内容创作自动化系统**

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

- ✅ **7阶段标准化工作流** - Intake → Brief → Draft → Material → Rewrite → Publish → Postmortem
- ✅ **6个HITL质量门** - 每个关键节点都有人工审核机制
- ✅ **多平台适配** - 支持微信公众号、小红书、微博、抖音、B站
- ✅ **AI驱动** - 基于Claude 4.6的智能内容生成与优化
- ✅ **DNA系统** - 可配置的风格、结构、质量标准
- ✅ **完整测试覆盖** - 87个单元测试 + 集成测试 + E2E测试
- ✅ **飞书协作** - 与飞书深度集成，支持团队协作

## 工作流概览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Stage 1    │───▶│  Stage 2    │───▶│  Stage 3    │───▶│  Stage 4    │
│   Intake    │    │   Brief     │    │   Draft     │    │  Material   │
│  内容采集    │    │  选题分析    │    │  初稿生成    │    │  素材收集    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                  │
┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  Stage 7    │◀───│  Stage 6    │◀───│  Stage 5    │◀─────────┘
│ Postmortem  │    │  Publish    │    │  Rewrite    │
│  分析复盘    │    │  渠道分发    │    │   改写      │
└─────────────┘    └─────────────┘    └─────────────┘
```

### Stage 1: Intake（内容采集）
从多个数据源采集每日热点内容，进行去重、聚类、排序。

### Stage 2: Brief（选题分析）
AI生成5-10个选题候选，编辑确认后进入初稿阶段。

### Stage 3: Draft（初稿生成）
基于选题生成标准初稿，支持人工迭代修改。

### Stage 4: Material（素材收集）
收集图表、图片、视频等素材，填充初稿中的证据缺口。

### Stage 5: Rewrite（改写）
生成4个平台版本（微信热文/常规、小红书热文/常规），严格控制字数和质量。

### Stage 6: Publish（渠道分发）
生成各平台发布包，包含标题候选、封面图、发布时机建议。

### Stage 7: Postmortem（分析复盘）
提取成功模式，更新知识库，持续优化。

## 文档

- [安装指南](INSTALLATION.md) - 详细安装步骤
- [快速开始](docs/guides/quick-start.md) - 5分钟快速上手
- [阶段详解](docs/guides/stage-by-stage.md) - 7个阶段的详细说明
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
