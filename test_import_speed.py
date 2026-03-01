#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试各个模块的导入速度
"""

import time
import sys

def test_import(module_name, import_statement):
    """测试单个模块的导入时间"""
    start = time.time()
    try:
        exec(import_statement)
        elapsed = time.time() - start
        print(f"✓ {module_name:40s} {elapsed*1000:8.2f} ms")
        return elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ {module_name:40s} {elapsed*1000:8.2f} ms (错误: {e})")
        return elapsed

print("=" * 60)
print("模块导入速度测试")
print("=" * 60)
print()

total_time = 0

# 测试标准库
print("【标准库】")
total_time += test_import("os", "import os")
total_time += test_import("sys", "import sys")
total_time += test_import("subprocess", "import subprocess")
total_time += test_import("time", "import time")
total_time += test_import("datetime", "from datetime import datetime, timedelta")
total_time += test_import("threading", "import threading")
total_time += test_import("signal", "import signal")
print()

# 测试第三方库
print("【第三方库】")
total_time += test_import("yaml", "import yaml")
total_time += test_import("paramiko", "import paramiko")
total_time += test_import("scp", "from scp import SCPClient")
total_time += test_import("rich.console", "from rich.console import Console")
total_time += test_import("rich.panel", "from rich.panel import Panel")
total_time += test_import("rich.prompt", "from rich.prompt import Prompt")
total_time += test_import("rich.table", "from rich.table import Table")
total_time += test_import("rich.progress", "from rich.progress import Progress")
print()

# 测试项目模块
print("【项目模块 - common】")
total_time += test_import("common.log_utils", "from common.log_utils import log_info, log_warn, log_error")
total_time += test_import("common.path_utils", "from common.path_utils import expand_path")
total_time += test_import("common.ssh_client", "from common.ssh_client import SSHClient")
print()

print("【项目模块 - remote_deploy】")
total_time += test_import("remote_deploy.config_manager", "from remote_deploy.config_manager import ConfigManager")
total_time += test_import("remote_deploy.file_uploader", "from remote_deploy.file_uploader import FileUploader")
total_time += test_import("remote_deploy.command_executor", "from remote_deploy.command_executor import CommandExecutor")
total_time += test_import("remote_deploy.deploy_service", "from remote_deploy.deploy_service import RemoteDeployService")
print()

print("=" * 60)
print(f"总导入时间: {total_time*1000:.2f} ms ({total_time:.3f} s)")
print("=" * 60)
