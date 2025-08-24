#!/bin/bash

# 烟雾测试运行脚本
# 用途: 快速验证系统基本功能是否正常

set -e  # 遇到错误立即退出

echo "🚀 开始运行烟雾测试..."
echo "时间: $(date)"
echo "================================"

# 检查后端服务器是否运行
echo "🔍 检查后端服务器状态..."
if curl -s http://localhost:5001/healthz > /dev/null; then
    echo "✅ 后端服务器正在运行"
else
    echo "❌ 后端服务器未运行，请先启动服务器"
    echo "启动命令: cd menziyi-server && python app.py"
    exit 1
fi

# 运行后端烟雾测试
echo ""
echo "🔍 运行后端烟雾测试..."
cd menziyi-server
if python test_smoke.py; then
    echo "✅ 后端烟雾测试通过"
else
    echo "❌ 后端烟雾测试失败"
    exit 1
fi
cd ..

echo ""
echo "🔍 检查iOS项目..."
if [ -d "ziyi" ]; then
    echo "✅ iOS项目存在"
    echo "📱 请在iOS模拟器或设备上运行应用，进入烟雾测试页面进行测试"
else
    echo "❌ iOS项目不存在"
    exit 1
fi

echo ""
echo "🔍 检查关键文件..."
critical_files=(
    "menziyi-server/app.py"
    "menziyi-server/requirements.txt"
    "ziyi/ContentView.swift"
    "ziyi/SmokeTestView.swift"
    "env.locked"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 不存在"
        exit 1
    fi
done

echo ""
echo "🎉 所有烟雾测试检查完成！"
echo "================================"
echo "📋 测试总结:"
echo "  - 后端服务器: ✅ 运行中"
echo "  - 后端API测试: ✅ 通过"
echo "  - iOS项目: ✅ 存在"
echo "  - 关键文件: ✅ 完整"
echo ""
echo "💡 下一步:"
echo "  1. 在iOS设备/模拟器上运行应用"
echo "  2. 进入烟雾测试页面"
echo "  3. 点击'运行烟雾测试'按钮"
echo "  4. 验证录音功能是否正常"
echo ""
echo "🔄 如需重新运行后端测试:"
echo "  cd menziyi-server && python test_smoke.py"
