#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试同时上传多个文件并显示进度条
"""

import os
import sys
import tempfile
from pathlib import Path

from deploy_tool.utils.ssh_client import SSHClient
from deploy_tool.utils.env_utils import EnvUtils
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()

def create_test_file(name, size_mb):
    """创建测试文件"""
    path = os.path.join(tempfile.gettempdir(), name)
    console.print(f"[cyan]创建测试文件:[/cyan] {name} ([yellow]{size_mb}MB[/yellow])")
    with open(path, 'wb') as f:
        f.write(os.urandom(size_mb * 1024 * 1024))
    return path

def test_multiple_upload():
    """测试同时上传多个文件"""
    # 加载环境变量
    try:
        console.clear()
        console.print()
        console.print(Panel.fit(
            "[bold yellow]测试多文件上传功能[/bold yellow]\n"
            "[cyan]上传配置文件、环境变量、以及测试文件到云端服务器[/cyan]",
            border_style="magenta",
            title="📤 上传测试"
        ))
        console.print()
        
        # 从环境变量获取项目根目录、部署路径和服务器信息
        project_root = EnvUtils.get('PROJECT_ROOT')
        deploy_path = EnvUtils.get('DEPLOY_PATH')
        project_root_path = Path(project_root)
        
        # 创建SSH客户端
        ssh_client = SSHClient()
        
        # 准备文件列表
        files_to_upload = []
        
        console.print("[bold cyan]📋 准备上传文件列表...[/bold cyan]")
        console.print()
        
        # 添加配置文件
        console.print("[yellow]添加配置文件:[/yellow]")
        for config_file in ["docker-compose.yaml", "nginx.conf"]:
            local_path = f"{project_root_path.parent}/docker/{config_file}"
            remote_path = f"{deploy_path}/"
            if os.path.exists(local_path):
                files_to_upload.append((local_path, remote_path))
                console.print(f"  [green]✓[/green] {local_path}")
        console.print()
        
        # 添加环境变量文件
        console.print("[yellow]添加环境变量文件:[/yellow]")
        for env in ["production", "staging", "development"]:
            env_file_path = f"{project_root}/env/.env.{env}"
            if os.path.exists(env_file_path):
                files_to_upload.append((env_file_path, f"{deploy_path}/"))
                console.print(f"  [green]✓[/green] {env_file_path}")
        console.print()
        
        # 创建并添加一些测试文件
        console.print("[yellow]创建测试文件:[/yellow]")
        test_files = []
        test_files.append(create_test_file("test_file_10mb.bin", 10))
        test_files.append(create_test_file("test_file_20mb.bin", 20))
        test_files.append(create_test_file("test_file_5mb.bin", 5))
        test_files.append(create_test_file("test_file_15mb.bin", 15))
        console.print()
        
        for test_file in test_files:
            files_to_upload.append((test_file, f"{deploy_path}/"))
        
        # 使用 put_multiple 同时上传所有文件
        if not files_to_upload:
            console.print(Panel.fit(
                "[bold red]❌ 没有找到要上传的文件[/bold red]",
                border_style="red"
            ))
            return False
        
        # 创建文件列表表格
        table = Table(
            title=f"✨ 准备上传 {len(files_to_upload)} 个文件 ✨",
            box=box.ROUNDED,
            title_style="bold magenta",
            border_style="bright_blue",
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
        table.add_column("本地路径", style="cyan", width=50, vertical="middle")
        table.add_column("远程路径", style="green", width=30, vertical="middle")
        
        for idx, (local, remote) in enumerate(files_to_upload, 1):
            table.add_row(str(idx), local, remote)
        
        console.print(table)
        console.print()
        
        console.print("[bold green]🚀 开始上传文件...[/bold green]")
        console.print()
        
        # 使用 put_multiple 同时上传所有文件
        result = ssh_client.put_multiple(files_to_upload)
        
        console.print()
        
        # 删除测试文件
        console.print("[yellow]🧹 清理测试文件...[/yellow]")
        for test_file in test_files:
            try:
                os.remove(test_file)
                console.print(f"  [green]✓[/green] 删除: {test_file}")
            except Exception as e:
                console.print(f"  [red]✗[/red] 删除失败: {e}")
        
        console.print()
        
        if result:
            console.print(Panel.fit(
                "[bold green]✓ 所有文件上传成功！[/bold green]",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                "[bold red]❌ 文件上传失败[/bold red]",
                border_style="red"
            ))
        
        return result
        
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ 上传测试过程中出现错误: {e}[/bold red]",
            border_style="red"
        ))
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        # 执行测试
        test_multiple_upload()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 测试被用户中断[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1) 