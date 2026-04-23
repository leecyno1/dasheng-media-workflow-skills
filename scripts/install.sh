#!/bin/bash
set -e

echo "=== Dasheng Media Workflow Skills 安装程序 ==="
echo ""

# 检测操作系统
OS=$(uname -s)
echo "检测到操作系统: $OS"

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到python3，请先安装Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Python版本: $PYTHON_VERSION"

# 简单版本比较（检查主版本号和次版本号）
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "❌ 错误: 需要Python 3.10+，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查Node.js版本
if ! command -v node &> /dev/null; then
    echo "⚠️  警告: 未找到node，部分功能可能不可用"
    echo "   建议安装Node.js 18+: https://nodejs.org/"
else
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo "Node.js版本: $NODE_VERSION"
fi

# 创建虚拟环境
echo ""
echo "创建Python虚拟环境..."
python3 -m venv .venv

# 激活虚拟环境
if [ "$OS" = "Darwin" ] || [ "$OS" = "Linux" ]; then
    source .venv/bin/activate
else
    echo "⚠️  警告: 未知操作系统，请手动激活虚拟环境"
    echo "   Windows: .venv\\Scripts\\activate"
    echo "   macOS/Linux: source .venv/bin/activate"
fi

# 安装Python依赖
echo ""
echo "安装Python依赖..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 安装Node.js依赖
if command -v npm &> /dev/null; then
    echo ""
    echo "安装Node.js依赖..."
    npm install --silent
fi

# 创建配置文件
echo ""
echo "创建配置文件..."
if [ ! -f configs/paths.local.yaml ]; then
    cp configs/paths.default.yaml configs/paths.local.yaml
    echo "✅ 已创建 configs/paths.local.yaml"
else
    echo "⚠️  configs/paths.local.yaml 已存在，跳过"
fi

# 创建必要目录
echo ""
echo "创建工作目录..."
mkdir -p "$BASE_DIR/素材" "$BASE_DIR/项目" "$BASE_DIR/产物"

# 运行验证
echo ""
echo "验证安装..."
python3 scripts/verify_installation.py

echo ""
echo "=== 安装完成 ==="
echo ""
echo "下一步："
echo "1. 配置API密钥:"
echo "   echo 'ANTHROPIC_API_KEY=your_key' > .env"
echo ""
echo "2. 运行测试:"
echo "   python3 -m pytest tests/ -v"
echo ""
echo "3. 运行第一个工作流:"
echo "   python3 scripts/run_stage1_intake.py"
echo ""
echo "详细文档: INSTALLATION.md"
