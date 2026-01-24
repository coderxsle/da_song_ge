#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from rich.console import Console

console = Console(force_terminal=True)

def log_success(message: str) -> None:
    """输出成功日志"""
    console.print(f"[green]✓ {message}[/green]")

def log_info(message: str) -> None:
    """输出信息日志"""
    console.print(message)

def log_error(message: str) -> None:
    """输出错误日志"""
    console.print(f"[red]❌ {message}[/red]")

def log_warn(message: str) -> None:
    """输出警告日志"""
    console.print(f"[yellow]⚠️  {message}[/yellow]")