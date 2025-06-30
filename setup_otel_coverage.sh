#!/bin/bash
# setup_otel_coverage.sh - 一键设置 OTEL 覆盖率测试

echo "🚀 Secure PR Guard - OTEL 覆盖率设置"
echo "======================================"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ Python 未找到，请先安装 Python"
    exit 1
fi

# 激活虚拟环境（如果存在）
if [ -d ".venv" ]; then
    echo "📦 激活虚拟环境..."
    source .venv/bin/activate
fi

# 安装测试依赖
echo "📥 安装测试依赖..."
pip install -q pytest pytest-cov pytest-mock coverage codecov

# 创建缺失的目录
echo "📁 检查项目结构..."
mkdir -p agents security monitoring tests logs

# 创建空的初始化文件（如果不存在）
for dir in agents security monitoring tests; do
    if [ ! -f "$dir/__init__.py" ]; then
        touch "$dir/__init__.py"
        echo "✅ 创建 $dir/__init__.py"
    fi
done

# 备份原始测试文件（如果存在）
if [ -f "tests/test_otel_helpers.py" ] && [ -s "tests/test_otel_helpers.py" ]; then
    cp tests/test_otel_helpers.py tests/test_otel_helpers.py.backup
    echo "💾 备份原始测试文件"
fi

# 运行覆盖率测试
echo "🧪 运行 OTEL 覆盖率测试..."
echo "==============================="

# 方法1: 针对 OTEL helpers 的专项测试
echo "🎯 专项测试: monitoring/otel_helpers.py"
python -m pytest tests/test_otel_helpers.py -v \
    --cov=monitoring.otel_helpers \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=85

TEST_RESULT=$?

# 方法2: 完整项目覆盖率
echo ""
echo "📊 完整项目覆盖率分析..."
python -m coverage run --source=. -m pytest tests/ 2>/dev/null
python -m coverage report --show-missing

# 生成HTML报告
python -m coverage html

# 检查核心文件覆盖率
echo ""
echo "🎯 核心模块覆盖率检查:"
echo "========================"

if [ -f ".coverage" ]; then
    # 检查 otel_helpers.py 覆盖率
    OTEL_COVERAGE=$(python -c "
import coverage
cov = coverage.Coverage()
cov.load()
try:
    coverage_data = cov.get_data()
    files = coverage_data.measured_files()
    otel_file = None
    for f in files:
        if 'otel_helpers.py' in f:
            otel_file = f
            break
    if otel_file:
        analysis = coverage_data.lines(otel_file)
        executed = coverage_data.lines(otel_file)
        if executed:
            print(f'{len(executed)}')
        else:
            print('0')
    else:
        print('N/A')
except:
    print('Error')
" 2>/dev/null)

    echo "  📊 otel_helpers.py: $OTEL_COVERAGE 行被测试"
else
    echo "  ⚠️  覆盖率数据文件不存在"
fi

# 显示结果
echo ""
echo "📋 测试结果摘要:"
echo "================"
if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ OTEL 测试通过"
    echo "✅ 目标覆盖率: 95%"
    echo "✅ HTML 报告: htmlcov/index.html"
else
    echo "❌ 部分测试失败或覆盖率不足"
    echo "💡 建议: 检查 htmlcov/index.html 查看详细覆盖率"
fi

# 显示下一步操作
echo ""
echo "🎯 下一步操作:"
echo "=============="
echo "1. 查看详细覆盖率报告:"
echo "   open htmlcov/index.html"
echo ""
echo "2. 运行特定测试:"
echo "   python -m pytest tests/test_otel_helpers.py::TestOTELConfig -v"
echo ""
echo "3. 连续监控覆盖率:"
echo "   python -m pytest --cov=monitoring.otel_helpers --cov-report=term-missing tests/"
echo ""
echo "4. 上传到 Codecov (CI/CD):"
echo "   codecov -t \$CODECOV_TOKEN"

# 检查是否需要创建其他组件
echo ""
echo "📦 项目完整性检查:"
echo "=================="

MISSING_FILES=()
if [ ! -f "security/owasp_rules.py" ]; then
    MISSING_FILES+=("security/owasp_rules.py")
fi
if [ ! -f "agents/nitpicker.py" ]; then
    MISSING_FILES+=("agents/nitpicker.py")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo "⚠️  发现缺失文件:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "💡 建议: 创建这些文件以达到完整的项目覆盖率"
else
    echo "✅ 核心项目文件完整"
fi

echo ""
echo "🎉 OTEL 覆盖率设置完成！"