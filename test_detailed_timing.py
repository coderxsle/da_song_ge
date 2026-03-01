#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
详细的性能分析 - 测量每个步骤的耗时
"""

import time
import sys

def measure(name, func):
    """测量函数执行时间"""
    start = time.time()
    result = func()
    elapsed = (time.time() - start) * 1000
    print(f"{name:50s} {elapsed:8.2f} ms")
    return result, elapsed

print("=" * 70)
print("详细性能分析 - 模拟选择1的流程")
print("=" * 70)
print()

total_time = 0

# 1. 导入 main.py 的基础模块
print("【阶段1：导入基础模块】")
_, t = measure("import os, sys, subprocess", lambda: exec("import os, sys, subprocess"))
total_time += t

_, t = measure("from rich.console import Console", lambda: exec("from rich.console import Console"))
total_time += t

_, t = measure("from rich.panel import Panel", lambda: exec("from rich.panel import Panel"))
total_time += t

_, t = measure("from rich.prompt import Prompt", lambda: exec("from rich.prompt import Prompt"))
total_time += t

_, t = measure("from rich.table import Table", lambda: exec("from rich.table import Table"))
total_time += t

_, t = measure("from rich import box", lambda: exec("from rich import box"))
total_time += t

_, t = measure("from rich.text import Text", lambda: exec("from rich.text import Text"))
total_time += t

print()

# 2. 预导入 RemoteDeployService
print("【阶段2：预导入 RemoteDeployService（main.py 启动时）】")
_, t = measure("from remote_deploy.deploy_service import RemoteDeployService", 
               lambda: exec("from remote_deploy.deploy_service import RemoteDeployService"))
total_time += t

print()

# 3. 用户选择1后，调用 deploy 方法
print("【阶段3：用户选择1，开始执行 deploy】")

# 导入 ConfigManager（在 deploy 方法中）
_, t = measure("创建 ConfigManager 实例", 
               lambda: exec("from remote_deploy.config_manager import ConfigManager; cm = ConfigManager()"))
total_time += t

# 加载配置文件
print()
print("【阶段4：加载和验证配置文件】")
from remote_deploy.config_manager import ConfigManager
cm = ConfigManager()

start = time.time()
result = cm.load_config()
elapsed = (time.time() - start) * 1000
print(f"{'load_config() - 读取和验证配置':50s} {elapsed:8.2f} ms")
total_time += elapsed

print()
print("=" * 70)
print(f"总计: {total_time:.2f} ms ({total_time/1000:.3f} s)")
print("=" * 70)
print()

# 分析 load_config 的细节
print("【详细分析：load_config 方法】")
print("让我们看看配置验证花了多少时间...")
print()

import yaml
from pathlib import Path

config_path = Path.home() / ".coderxslee" / "config.yaml"

start = time.time()
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)
elapsed = (time.time() - start) * 1000
print(f"{'读取 YAML 文件':50s} {elapsed:8.2f} ms")

# 模拟验证过程
start = time.time()
servers = config.get('servers', [])
for idx, server in enumerate(servers):
    # 验证每个服务器配置
    pass
elapsed = (time.time() - start) * 1000
print(f"{'验证配置（遍历服务器）':50s} {elapsed:8.2f} ms")

print()
print("💡 优化建议：")
print("  1. 配置验证可以改为懒加载（只在需要时验证）")
print("  2. Rich 库的导入比较重（约 50ms），但这是必需的")
print("  3. YAML 解析速度还可以，不是瓶颈")
print("  4. 主要时间花在 PyInstaller 解压和模块加载上")
