# 安装指南

Dasheng Media Workflow Skills - 7阶段自媒体内容创作自动化系统

## 系统要求

### 必需
- **Python**: 3.10 或更高版本
- **Node.js**: 18.0 或更高版本
- **内存**: 至少 8GB RAM
- **磁盘空间**: 至少 5GB 可用空间

### 可选
- **Git**: 用于版本控制和更新
- **Docker**: 用于容器化部署（可选）

## 快速安装（推荐）

### 1. 克隆仓库

```bash
git clone https://github.com/leecyno1/dasheng-media-workflow-skills.git
cd dasheng-media-workflow-skills
```

### 2. 运行安装脚本

```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

安装脚本会自动：
- 检查系统要求
- 创建Python虚拟环境
- 安装所有依赖
- 创建必要的工作目录
- 生成配置文件模板
- 验证安装完整性

### 3. 验证安装

```bash
python3 scripts/verify_installation.py
```

如果看到所有检查项都显示 ✅，说明安装成功。

## 手动安装

如果自动安装脚本失败，可以按以下步骤手动安装：

### 1. 克隆仓库

```bash
git clone https://github.com/leecyno1/dasheng-media-workflow-skills.git
cd dasheng-media-workflow-skills
```

### 2. 创建Python虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows
```

### 3. 安装Python依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 安装Node.js依赖

```bash
npm install
```

### 5. 创建配置文件

```bash
cp configs/paths.default.yaml configs/paths.local.yaml
```

### 6. 创建工作目录

```bash
mkdir -p 素材 项目 产物
```

### 7. 验证安装

```bash
python3 scripts/verify_installation.py
```

## 配置

### 必需配置

#### 1. API密钥配置

创建 `.env` 文件（或设置环境变量）：

```bash
# Anthropic API密钥（用于AI生成）
ANTHROPIC_API_KEY=your_api_key_here

# Tushare Token（用于金融数据，可选）
TUSHARE_TOKEN=your_token_here
```

#### 2. 路径配置

编辑 `configs/paths.local.yaml`：

```yaml
# 项目根目录（通常无需修改，自动检测）
project_root: auto

# 工作目录（相对于project_root）
work_dirs:
  materials: "素材"
  projects: "项目"
  engines: "引擎"
  outputs: "产物"

# 外部依赖路径
external:
  feishu_config: "${FEISHU_CONFIG_PATH:-~/.config/feishu/api.conf}"
  openclaw_skills: "${OPENCLAW_SKILLS_DIR:-~/.openclaw/skills}"

# 数据源端点
data_sources:
  intake_5173: "${DASHENG_INTAKE_5173_BASE:-http://127.0.0.1:18000}"
  intake_reports: "${DASHENG_INTAKE_REPORTS_BASE:-http://45.197.148.64:8080}"
  intake_8001: "${DASHENG_INTAKE_8001_BASE:-http://45.197.148.64:8001}"
```

### 可选配置

#### 飞书集成（可选）

如果需要使用飞书协作功能，创建飞书配置文件：

```bash
mkdir -p ~/.config/feishu
cat > ~/.config/feishu/api.conf << EOF
APP_ID="your_app_id"
APP_SECRET="your_app_secret"
CHAT_ID="your_chat_id"
EOF
```

#### 图像生成服务（可选）

如果需要使用AI图像生成，配置图像生成服务：

```bash
# 编辑 configs/image_generation/providers.local.env
VIVIAI_IMAGE_API_KEY=your_key
VECTORENGINE_API_KEY=your_key
```

## 验证安装

运行以下命令验证各组件：

```bash
# 1. 验证路径解析
python3 core/path_resolver.py

# 2. 验证完整安装
python3 scripts/verify_installation.py

# 3. 运行测试套件
python3 -m pytest tests/ -v

# 4. 检查数据源健康
python3 scripts/check_data_sources.py
```

## 运行第一个工作流

安装完成后，运行Stage 1（内容采集）测试：

```bash
python3 scripts/run_stage1_intake.py
```

如果成功，会在 `产物/01_内容采集/` 目录下生成采集报告。

## Docker安装（可选）

### 使用Docker Compose

```bash
docker-compose up -d
docker-compose exec app python3 scripts/verify_installation.py
```

### 手动构建Docker镜像

```bash
docker build -t dasheng-workflow .
docker run -it dasheng-workflow python3 scripts/verify_installation.py
```

## 故障排除

### 问题1：Python版本过低

**错误**：`需要Python 3.10+，当前版本: 3.9.x`

**解决**：
```bash
# macOS (使用Homebrew)
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11

# 验证版本
python3 --version
```

### 问题2：Node.js版本过低

**错误**：`需要Node.js 18+`

**解决**：
```bash
# 使用nvm安装
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 18
nvm use 18
```

### 问题3：依赖安装失败

**错误**：`pip install` 或 `npm install` 失败

**解决**：
```bash
# 清理缓存
pip cache purge
npm cache clean --force

# 使用国内镜像（中国用户）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
npm install --registry=https://registry.npmmirror.com
```

### 问题4：路径解析失败

**错误**：`Cannot detect project root: CLAUDE.md not found`

**解决**：
- 确保在项目根目录运行命令
- 确保 `CLAUDE.md` 文件存在
- 或手动设置环境变量：
  ```bash
  export DASHENG_PROJECT_ROOT=/path/to/project
  ```

### 问题5：权限错误

**错误**：`Permission denied`

**解决**：
```bash
# 给脚本添加执行权限
chmod +x scripts/*.sh
chmod +x scripts/*.py

# 或使用sudo（不推荐）
sudo python3 scripts/install.sh
```

## 更新

### 更新到最新版本

```bash
git pull origin main
pip install -r requirements.txt --upgrade
npm install
python3 scripts/verify_installation.py
```

### 查看版本信息

```bash
cat VERSION
git log --oneline -5
```

## 卸载

```bash
# 删除虚拟环境
rm -rf .venv

# 删除Node模块
rm -rf node_modules

# 删除生成的数据（可选）
rm -rf 产物/* 素材/* 项目/*

# 删除项目目录
cd ..
rm -rf dasheng-media-workflow-skills
```

## 下一步

安装完成后，请阅读：

- [快速开始指南](docs/guides/quick-start.md) - 5分钟快速上手
- [阶段详解](docs/guides/stage-by-stage.md) - 了解7个工作流阶段
- [架构设计](docs/technical/architecture.md) - 深入理解系统架构
- [阶段接口规范](docs/STAGE_INTERFACES.md) - 各阶段输入输出接口定义
- [贡献指南](CONTRIBUTING.md) - 参与项目开发

## 获取帮助

- **文档**: [docs/](docs/)
- **问题反馈**: [GitHub Issues](https://github.com/leecyno1/dasheng-media-workflow-skills/issues)
- **更新日志**: [CHANGELOG.md](CHANGELOG.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
