#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
common/progress.py 使用示例程序
演示如何使用 Progress 工具类的各种功能
"""

import time
import random
from common.progress import Progress
from rich.console import Console
from rich.panel import Panel

console = Console()


def demo_status():
    """演示状态消息显示"""
    console.print(Panel.fit("1️⃣  状态消息演示", style="bold cyan"))
    console.print()
    
    progress = Progress()
    
    with progress.status("[bold green]正在连接服务器...") as status:
        time.sleep(2)
        status.update("[bold yellow]正在上传文件...")
        time.sleep(2)
        status.update("[bold blue]正在处理数据...")
        time.sleep(2)
    
    console.print("[green]✓ 状态消息演示完成![/green]\n")


def demo_basic_progress():
    """演示基础进度条"""
    console.print(Panel.fit("2️⃣  基础进度条演示", style="bold cyan"))
    console.print()
    
    progress = Progress()
    task = progress.show("正在处理任务...")
    
    # 模拟任务执行
    time.sleep(3)
    
    console.print("[green]✓ 基础进度条演示完成![/green]\n")


def demo_multiple_files():
    """演示多文件进度"""
    console.print(Panel.fit("3️⃣  多文件进度演示", style="bold cyan"))
    console.print()
    
    progress = Progress()
    
    # 定义多个文件
    files = [
        ("config.yaml", 1024 * 50),      # 50 KB
        ("docker-compose.yaml", 1024 * 30),  # 30 KB
        ("nginx.conf", 1024 * 20),       # 20 KB
        (".env.production", 1024 * 10),  # 10 KB
    ]
    
    console.print("[yellow]正在上传配置文件...[/yellow]\n")
    
    from rich.progress import Progress as RichProgress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, FileSizeColumn, TransferSpeedColumn
    
    with RichProgress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green"),
        FileSizeColumn(),
        TransferSpeedColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    ) as rich_progress:
        tasks = {}
        for name, size in files:
            tasks[name] = rich_progress.add_task(f"[cyan]上传 {name}...", total=size)
        
        # 模拟文件上传
        processed = {name: 0 for name, _ in files}
        
        while not rich_progress.finished:
            for name, size in files:
                if processed[name] < size:
                    # 随机上传速度
                    chunk = min(random.randint(1024, 5120), size - processed[name])
                    rich_progress.update(tasks[name], advance=chunk)
                    processed[name] += chunk
            
            time.sleep(0.05)
    
    console.print("\n[green]✓ 多文件进度演示完成![/green]\n")


def demo_single_file_unknown_size():
    """演示未知大小的单文件进度"""
    console.print(Panel.fit("4️⃣  未知大小任务演示", style="bold cyan"))
    console.print()
    
    console.print("[yellow]正在加载 Docker 镜像...[/yellow]\n")
    
    Progress.show_single(None, "加载镜像中...")
    
    console.print("\n[green]✓ 未知大小任务演示完成![/green]\n")


def demo_single_file_known_size():
    """演示已知大小的单文件进度"""
    console.print(Panel.fit("5️⃣  已知大小任务演示", style="bold cyan"))
    console.print()
    
    console.print("[yellow]正在上传 Docker 镜像...[/yellow]\n")
    
    # 模拟 30MB 的文件
    total_size = 1024 * 1024 * 30
    Progress.show_single(total_size, "上传 my-app-v1.0.0.tar")
    
    console.print("\n[green]✓ 已知大小任务演示完成![/green]\n")


def demo_deployment_scenario():
    """演示实际部署场景"""
    console.print(Panel.fit("6️⃣  实际部署场景演示", style="bold cyan"))
    console.print()
    
    progress = Progress()
    
    # 步骤1: 连接服务器
    with progress.status("[bold green]🔌 正在连接远程服务器..."):
        time.sleep(1.5)
    console.print("[green]✓ 服务器连接成功[/green]")
    
    # 步骤2: 上传配置文件
    console.print("\n[yellow]📤 上传配置文件...[/yellow]")
    files = [
        ("docker-compose.yaml", 1024 * 25),
        (".env.production", 1024 * 8),
    ]
    
    from rich.progress import Progress as RichProgress, TextColumn, BarColumn, TaskProgressColumn, FileSizeColumn, TransferSpeedColumn
    
    with RichProgress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green"),
        FileSizeColumn(),
        TransferSpeedColumn(),
        TaskProgressColumn(),
    ) as rich_progress:
        for name, size in files:
            task = rich_progress.add_task(f"[cyan]{name}", total=size)
            processed = 0
            while processed < size:
                chunk = min(random.randint(2048, 8192), size - processed)
                rich_progress.update(task, advance=chunk)
                processed += chunk
                time.sleep(0.02)
    
    console.print("[green]✓ 配置文件上传完成[/green]")
    
    # 步骤3: 部署服务
    with progress.status("[bold blue]🚀 正在部署服务..."):
        time.sleep(2)
    console.print("[green]✓ 服务部署成功[/green]")
    
    # 步骤4: 验证部署
    with progress.status("[bold yellow]🔍 正在验证部署结果..."):
        time.sleep(1.5)
    console.print("[green]✓ 部署验证通过[/green]")
    
    console.print("\n[bold green]🎉 部署完成！[/bold green]\n")


def main():
    """主函数"""
    console.clear()
    
    console.print()
    console.print(Panel.fit(
        "[bold yellow]Common Progress 工具类使用示例[/bold yellow]\n"
        "[cyan]演示 Progress 类的各种功能[/cyan]",
        border_style="magenta",
        title="📊 Progress Demo"
    ))
    console.print()
    
    # 运行所有演示
    demo_status()
    time.sleep(1)
    
    demo_basic_progress()
    time.sleep(1)
    
    demo_multiple_files()
    time.sleep(1)
    
    demo_single_file_unknown_size()
    time.sleep(1)
    
    demo_single_file_known_size()
    time.sleep(1)
    
    demo_deployment_scenario()
    
    console.print(Panel.fit(
        "[bold green]✨ 所有演示完成！[/bold green]",
        border_style="green"
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 演示被用户中断[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ 发生错误: {e}[/red]")
