#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件验证脚本
用于验证 config.yaml 的配置是否正确
"""

import sys
from pathlib import Path
from typing import Optional

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from remote_deploy.config_manager import ConfigManager
from common.log_utils import log_error
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


def show_servers_table(servers: list, title: Optional[str] = None):
    """
    显示服务器配置表格
    
    Args:
        servers: 服务器配置列表
        title: 表格标题（可选）
    """
    if title is None:
        title = f"✨ 共找到 {len(servers)} 个服务器配置 ✨"
    
    # 创建服务器配置表格
    table = Table(
        title=title,
        box=box.ROUNDED,
        title_style="bold magenta",
        border_style="bright_blue",
        show_header=True,
        header_style="bold cyan",
        show_lines=True
    )
    
    table.add_column("序号", justify="center", style="bold yellow", width=4, vertical="middle")
    table.add_column("服务器名称", style="bold green", width=16, vertical="middle")
    table.add_column("地址", style="cyan", width=20, vertical="middle")
    table.add_column("用户", style="white", width=10, vertical="middle")
    table.add_column("认证类型", style="magenta", width=8, vertical="middle")
    table.add_column("密码状态", style="yellow", width=12, vertical="middle")
    table.add_column("应用类型", style="blue", width=18, vertical="middle")
    table.add_column("命令组", style="green", width=18, vertical="middle")
    
    for idx, server in enumerate(servers, 1):
        # 获取认证信息
        auth = server['auth']
        auth_type = auth['type']
        
        # 检查密码状态
        if auth['type'] == 'ssh_key':
            if 'password' in auth and auth['password']:
                password_status = "🔑 密钥+密码"
            else:
                password_status = "🔑 仅密钥"
        elif auth['type'] == 'password':
            if 'password' in auth and auth['password']:
                password_status = "✓ 已配置"
            else:
                password_status = "⚠ 未配置"
        else:
            password_status = "-"
        
        # 检查上传配置
        if 'upload' in server:
            upload_types = ', '.join(list(server['upload'].keys()))
        else:
            upload_types = "[yellow]⚠ 未配置[/yellow]"
        
        # 检查命令配置
        if 'commands' in server:
            command_groups = ', '.join(list(server['commands'].keys()))
        else:
            command_groups = "[yellow]⚠ 未配置[/yellow]"
        
        # 添加表格行
        table.add_row(
            str(idx),
            server['name'],
            f"{server['host']}:{server['port']}",
            server['username'],
            auth_type,
            password_status,
            upload_types,
            command_groups
        )
    
    console.print(table)

def validate_config(config_path: str):
    """验证配置文件"""
    console.print()
    console.print(Panel.fit(
        "[bold yellow]配置文件验证工具[/bold yellow]\n"
        f"[cyan]配置文件: {config_path}[/cyan]",
        border_style="magenta",
        title="🔍 配置验证"
    ))
    console.print()
    
    # 创建配置管理器
    config_manager = ConfigManager(config_path)
    
    # 加载并验证配置
    if not config_manager.load_config():
        console.print(Panel.fit(
            "[bold red]❌ 配置验证失败！[/bold red]",
            border_style="red"
        ))
        return False
    
    console.print(Panel.fit(
        "[bold green]✓ 配置验证通过！[/bold green]",
        border_style="green"
    ))
    console.print()
    
    # 显示服务器列表
    servers = config_manager.get_servers()
    show_servers_table(servers)
    
    return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='配置文件验证工具')
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help=f'配置文件路径 (默认: {ConfigManager.DEFAULT_CONFIG_PATH})'
    )
    
    args = parser.parse_args()
    
    try:
        # 如果没有指定配置文件，使用默认路径
        config_path = args.config if args.config else str(ConfigManager.DEFAULT_CONFIG_PATH)
        
        success = validate_config(config_path)
        
        if success:
            console.print(Panel.fit(
                "[bold green]🎉 验证完成！[/bold green]",
                border_style="green"
            ))
        
        return 0 if success else 1
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 验证被用户中断[/yellow]")
        return 1
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ 验证过程出错: {e}[/bold red]",
            border_style="red"
        ))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

