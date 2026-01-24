#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
快速测试脚本
用于测试远程部署工具的基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from remote_deploy.config_manager import ConfigManager
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def test_config_manager():
    """测试配置管理器"""
    console.print()
    console.print(Panel.fit(
        "[bold yellow]测试配置管理器[/bold yellow]",
        border_style="magenta",
        title="🧪 配置测试"
    ))
    console.print()
    
    # 测试加载配置（使用默认配置路径）
    config_manager = ConfigManager()
    
    if not config_manager.load_config():
        console.print(Panel.fit(
            "[bold red]❌ 配置加载失败[/bold red]",
            border_style="red"
        ))
        return False
    
    console.print("[green]✓ 配置加载成功[/green]")
    console.print()
    
    # 显示服务器列表
    servers = config_manager.get_servers()
    
    # 创建服务器列表表格
    table = Table(
        title=f"✨ 找到 {len(servers)} 个服务器配置 ✨",
        box=box.ROUNDED,
        title_style="bold magenta",
        border_style="bright_blue",
        show_header=True,
        header_style="bold cyan",
        show_lines=True
    )
    
    table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
    table.add_column("服务器名称", style="bold green", width=25, vertical="middle")
    table.add_column("地址", style="cyan", width=30, vertical="middle")
    
    for idx, server in enumerate(servers, 1):
        table.add_row(
            str(idx),
            server['name'],
            f"{server['host']}:{server['port']}"
        )
    
    console.print(table)
    console.print()
    
    return True


def test_path_utils():
    """测试路径工具"""
    console.print(Panel.fit(
        "[bold yellow]测试路径工具[/bold yellow]",
        border_style="magenta",
        title="🔧 工具测试"
    ))
    console.print()
    
    from common.path_utils import expand_path, validate_path, format_file_size
    
    # 测试路径展开
    test_path = "~/test"
    expanded = expand_path(test_path)
    console.print(f"[green]✓[/green] 路径展开: [cyan]{test_path}[/cyan] -> [yellow]{expanded}[/yellow]")
    
    # 测试文件大小格式化
    console.print()
    console.print("[bold cyan]文件大小格式化测试:[/bold cyan]")
    
    table = Table(
        box=box.ROUNDED,
        border_style="bright_blue",
        show_header=True,
        header_style="bold cyan",
        show_lines=True
    )
    
    table.add_column("原始大小 (bytes)", justify="right", style="yellow", width=20, vertical="middle")
    table.add_column("格式化后", style="green", width=20, vertical="middle")
    
    sizes = [1024, 1048576, 1073741824]
    for size in sizes:
        formatted = format_file_size(size)
        table.add_row(f"{size:,}", formatted)
    
    console.print(table)
    console.print()
    
    return True


def main():
    """主函数"""
    console.clear()
    console.print()
    console.print(Panel.fit(
        "[bold yellow]远程部署工具 - 快速测试[/bold yellow]",
        border_style="magenta",
        title="🚀 快速测试"
    ))
    console.print()
    
    # 测试配置管理器
    if not test_config_manager():
        return 1
    
    # 测试路径工具
    if not test_path_utils():
        return 1
    
    console.print(Panel.fit(
        "[bold green]✓ 所有测试通过！[/bold green]",
        border_style="green"
    ))
    console.print()
    
    # 显示下一步提示
    next_steps = Panel(
        "[bold cyan]下一步:[/bold cyan]\n\n"
        "[yellow]1.[/yellow] 确保配置文件 [cyan]scripts/config.yaml[/cyan] 已正确配置\n"
        "[yellow]2.[/yellow] 设置 [cyan]SSH_PASSWORD[/cyan] 环境变量（如果使用密码认证）\n"
        "[yellow]3.[/yellow] 运行: [green]cd scripts && python remote_deploy.py[/green]",
        title="📋 操作指南",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(next_steps)
    console.print()
    
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 测试被用户中断[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)

