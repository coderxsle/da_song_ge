#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Python 项目工具集主界面
提供部署工具、示例程序等功能的统一入口
"""

import os
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich import box
from rich.text import Text

console = Console()


def show_banner():
    """显示欢迎横幅"""
    banner = Text()
    banner.append("╔═══════════════════════════════════════════╗\n", style="bold cyan")
    banner.append("║                                           ║\n", style="bold cyan")
    banner.append("║         ", style="bold cyan")
    banner.append("🚀  李雪松工具集", style="bold yellow")
    banner.append("                  ║\n", style="bold cyan")
    banner.append("║                                           ║\n", style="bold cyan")
    banner.append("╚═══════════════════════════════════════════╝", style="bold cyan")
    
    console.print()
    console.print(banner, justify="left")
    console.print()


def show_menu():
    """显示功能菜单"""
    table = Table(
        title="✨ 功能菜单 ✨",
        box=box.ROUNDED,
        title_style="bold magenta",
        border_style="bright_blue",
        show_header=True,
        header_style="bold cyan"
    )
    
    table.add_column("序号", justify="center", style="bold yellow", width=4)
    table.add_column("功能名称", style="bold green", width=25)
    table.add_column("描述", style="white", width=40)
    
    table.add_row("1", "🚀 远程部署", "远程服务器部署功能")
    table.add_row("2", "🐳 部署工具", "Docker镜像构建、打包和部署")
    table.add_row("3", "📊 进度条示例", "查看各种进度条库的演示效果")
    table.add_row("4", "📝 项目信息", "查看项目详细信息和配置")
    table.add_row("5", "🔧 运行脚本", "执行自定义脚本")
    table.add_row("0", "❌ 退出程序", "退出工具集")
    
    console.print(table)
    console.print()


def run_remote_deploy():
    """运行远程部署"""
    # 延迟导入，避免启动时加载所有模块
    from remote_deploy.deploy_service import RemoteDeployService
    from rich.console import Console
    
    console = Console()
    console.clear()
    
    try:
        # 执行部署
        RemoteDeployService.deploy()
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 操作已取消[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    console.print()
    input("按回车键继续...")


def run_deploy_tool():
    """运行部署工具"""
    console.print(Panel.fit(
        "🐳 启动部署工具...",
        border_style="green",
        title="部署工具"
    ))
    console.print()
    
    try:
        # 运行部署工具
        subprocess.run([sys.executable, "deploy_tool/run.py"], check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ 运行失败: {e}[/red]")
    except FileNotFoundError:
        console.print("[red]❌ 找不到部署工具文件[/red]")
    
    console.print()
    input("按回车键继续...")


def show_progress_examples():
    """显示进度条示例菜单"""
    console.clear()
    console.print(Panel.fit(
        "📊 进度条示例程序",
        border_style="magenta",
        title="示例选择"
    ))
    console.print()
    
    examples_table = Table(box=box.ROUNDED, border_style="magenta")
    examples_table.add_column("序号", justify="center", style="bold yellow", width=8)
    examples_table.add_column("示例名称", style="bold cyan", width=20)
    examples_table.add_column("描述", style="white", width=40)
    
    examples_table.add_row("1", "Rich 进度条", "最全面的终端美化库，pip 使用的库")
    examples_table.add_row("2", "Tqdm 进度条", "最简单易用，性能好，开销小")
    examples_table.add_row("3", "Halo 加载动画", "专注于加载动画，预设效果丰富")
    examples_table.add_row("4", "Alive Progress", "动画效果丰富，音乐播放器风格")
    examples_table.add_row("5", "Yaspin 旋转器", "轻量级旋转器，简单易用")
    examples_table.add_row("0", "返回主菜单", "返回上一级")
    
    console.print(examples_table)
    console.print()
    
    choice = Prompt.ask(
        "请选择要运行的示例",
        choices=["0", "1", "2", "3", "4", "5"],
        default="0"
    )
    
    examples_map = {
        "1": "examples/progress/rich_demo.py",
        "2": "examples/progress/tqdm_demo.py",
        "3": "examples/progress/spinners_demo.py",
        "4": "examples/progress/alive_demo.py",
        "5": "examples/progress/yaspin_demo.py",
    }
    
    if choice != "0" and choice in examples_map:
        console.print()
        console.print(f"[green]▶ 运行示例: {examples_map[choice]}[/green]")
        console.print()
        
        try:
            subprocess.run([sys.executable, examples_map[choice]], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ 运行失败: {e}[/red]")
        except FileNotFoundError:
            console.print(f"[red]❌ 找不到文件: {examples_map[choice]}[/red]")
        
        console.print()
        input("按回车键继续...")


def show_project_info():
    """显示项目信息"""
    console.clear()
    
    info_panel = Panel.fit(
        "[bold cyan]项目名称:[/bold cyan] deploy-tool\n"
        "[bold cyan]版本:[/bold cyan] 1.0.0\n"
        "[bold cyan]描述:[/bold cyan] Docker镜像构建、打包和部署的自动化工具\n"
        "[bold cyan]Python版本:[/bold cyan] >= 3.12\n\n"
        "[bold yellow]主要功能:[/bold yellow]\n"
        "  • Docker 镜像构建\n"
        "  • Docker 镜像打包\n"
        "  • 远程部署\n"
        "  • 多环境配置支持\n\n"
        "[bold green]主要依赖:[/bold green]\n"
        "  • PyYAML - 配置文件解析\n"
        "  • Paramiko - SSH 连接\n"
        "  • Docker - Docker SDK\n"
        "  • Rich - 终端美化\n"
        "  • Typer - CLI 框架",
        title="📝 项目信息",
        border_style="blue",
        padding=(1, 2)
    )
    
    console.print(info_panel)
    console.print()
    input("按回车键继续...")


def run_custom_script():
    """运行自定义脚本"""
    console.clear()
    console.print(Panel.fit(
        "🔧 运行自定义脚本",
        border_style="yellow",
        title="脚本执行"
    ))
    console.print()
    
    if os.path.exists("script.py"):
        console.print("[green]找到 script.py，正在执行...[/green]")
        console.print()
        
        try:
            subprocess.run([sys.executable, "script.py"], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"[red]❌ 运行失败: {e}[/red]")
    else:
        console.print("[yellow]⚠ 未找到 script.py 文件[/yellow]")
    
    console.print()
    input("按回车键继续...")


def main():
    """主程序入口"""
    while True:
        console.clear()
        show_banner()
        show_menu()
        
        choice = Prompt.ask(
            "请选择功能",
            choices=["0", "1", "2", "3", "4", "5"],
            default="0"
        )
        
        if choice == "0":
            console.print()
            console.print(Panel.fit(
                "👋 感谢使用，再见！",
                border_style="green",
                title="退出"
            ))
            console.print()
            break
        elif choice == "1":
            console.clear()
            run_remote_deploy()
        elif choice == "2":
            console.clear()
            run_deploy_tool()
        elif choice == "3":
            show_progress_examples()
        elif choice == "4":
            show_project_info()
        elif choice == "5":
            run_custom_script()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 程序被用户中断[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
        sys.exit(1)
