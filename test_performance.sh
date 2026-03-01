#!/bin/bash

echo "=========================================="
echo "性能测试：李雪松工具集"
echo "=========================================="
echo ""

echo "【测试1】启动时间（选择0退出）"
echo "---"
for i in {1..3}; do
  echo -n "第 $i 次: "
  { time ./dist/lxs <<< "0" > /dev/null 2>&1; } 2>&1 | grep "total" | awk '{print $NF}'
done
echo ""

echo "【测试2】选择1后的响应时间"
echo "---"
for i in {1..3}; do
  echo -n "第 $i 次: "
  start=$(date +%s.%N)
  { echo "1"; sleep 0.3; echo "0"; } | ./dist/lxs > /tmp/test_output.log 2>&1
  end=$(date +%s.%N)
  runtime=$(echo "$end - $start" | bc)
  echo "${runtime}s"
  
  # 检查是否看到配置加载信息
  if grep -q "正在加载配置" /tmp/test_output.log; then
    echo "  ✓ 成功加载配置"
  else
    echo "  ✗ 未看到配置加载"
  fi
done
echo ""

echo "【测试3】查看选择1后到配置加载的时间差"
echo "---"
# 添加时间戳来测量
cat > /tmp/test_timing.sh << 'EOF'
#!/bin/bash
echo "开始时间: $(date +%s.%N)" > /tmp/timing.log
echo "1"
sleep 0.1
echo "输入1后: $(date +%s.%N)" >> /tmp/timing.log
sleep 0.5
echo "0"
EOF
chmod +x /tmp/test_timing.sh

/tmp/test_timing.sh | ./dist/lxs > /tmp/test_output2.log 2>&1

if [ -f /tmp/timing.log ]; then
  cat /tmp/timing.log
  if grep -q "正在加载配置" /tmp/test_output2.log; then
    echo "✓ 配置已加载"
  fi
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="
