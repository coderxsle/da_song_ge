#!/bin/bash

echo "=========================================="
echo "冷启动性能测试（清理缓存后）"
echo "=========================================="
echo ""

# 清理函数
clean_cache() {
    echo "🧹 清理缓存..."
    
    # 清理 PyInstaller 临时目录
    if [ -n "$TMPDIR" ]; then
        find "$TMPDIR" -name "_MEI*" -type d -exec rm -rf {} + 2>/dev/null
        echo "  ✓ 清理 TMPDIR: $TMPDIR"
    fi
    
    # 清理 /tmp 目录
    find /tmp -name "_MEI*" -type d -exec rm -rf {} + 2>/dev/null
    echo "  ✓ 清理 /tmp"
    
    # 清理 /var/folders (macOS)
    find /var/folders -name "_MEI*" -type d -exec rm -rf {} + 2>/dev/null
    echo "  ✓ 清理 /var/folders"
    
    # 清理系统缓存（可选，需要 sudo）
    # sudo purge
    
    echo "  ✓ 缓存清理完成"
    echo ""
    
    # 等待一下，确保清理完成
    sleep 1
}

# 测试函数
test_startup() {
    local test_name=$1
    echo "【$test_name】"
    echo "---"
    
    for i in {1..3}; do
        echo -n "第 $i 次: "
        
        # 清理缓存
        clean_cache > /dev/null 2>&1
        
        # 测试启动时间
        start=$(perl -MTime::HiRes=time -e 'print time')
        ./dist/lxs <<< "0" > /dev/null 2>&1
        end=$(perl -MTime::HiRes=time -e 'print time')
        
        runtime=$(echo "$end - $start" | bc)
        echo "${runtime}s"
        
        # 等待一下再进行下一次测试
        sleep 1
    done
    echo ""
}

test_option1() {
    local test_name=$1
    echo "【$test_name】"
    echo "---"
    
    for i in {1..3}; do
        echo "第 $i 次:"
        
        # 清理缓存
        clean_cache > /dev/null 2>&1
        
        # 测试选择1的时间
        start=$(perl -MTime::HiRes=time -e 'print time')
        { echo "1"; sleep 0.3; echo "0"; } | ./dist/lxs > /tmp/test_output_$i.log 2>&1
        end=$(perl -MTime::HiRes=time -e 'print time')
        
        runtime=$(echo "$end - $start" | bc)
        echo "  总时间: ${runtime}s"
        
        # 检查是否成功加载配置
        if grep -q "正在加载配置" /tmp/test_output_$i.log; then
            echo "  ✓ 成功加载配置"
        else
            echo "  ✗ 未看到配置加载"
        fi
        
        echo ""
        
        # 等待一下再进行下一次测试
        sleep 1
    done
}

# 执行测试
test_startup "测试1: 冷启动时间（选择0退出）"
test_option1 "测试2: 冷启动 + 选择1"

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "💡 说明："
echo "  - 每次测试前都清理了 PyInstaller 临时目录"
echo "  - 这模拟了用户首次运行的情况"
echo "  - 实际使用中，后续运行会更快（系统缓存）"
