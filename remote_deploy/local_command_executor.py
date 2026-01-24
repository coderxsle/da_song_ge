#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
本地命令执行器
负责在本地执行命令（如编译、打包等）
"""

import os
import subprocess
from typing import List, Tuple, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class LocalCommandExecutor:
    """本地命令执行器类"""
    
    def __init__(self, working_dir: Optional[str] = None):
        """
        初始化本地命令执行器
        
        Args:
            working_dir: 工作目录（可选，默认为当前目录）
        """
        self.working_dir = working_dir or os.getcwd()
    
    def execute_command_group(self, commands: List[str], group_name: str, 
                             working_dir: Optional[str] = None,
                             stop_on_error: bool = True) -> bool:
        """
        执行本地命令组
        
        Args:
            commands: 命令列表
            group_name: 命令组名称
            working_dir: 工作目录（可选，覆盖初始化时的工作目录）
            stop_on_error: 遇到错误是否停止（默认 True）
            
        Returns:
            bool: 执行是否成功
        """
        if not commands:
            console.print("[yellow]⚠ 命令组为空，跳过执行[/yellow]")
            return True
        
        # 确定工作目录
        work_dir = working_dir or self.working_dir
        work_dir = os.path.expanduser(work_dir)
        
        if not os.path.exists(work_dir):
            console.print(Panel.fit(
                f"[bold red]❌ 工作目录不存在: {work_dir}[/bold red]",
                border_style="red"
            ))
            return False
        
        console.print(f"[cyan]📂 工作目录:[/cyan] {work_dir}")
        console.print(f"[cyan]📋 命令数量:[/cyan] {len(commands)}")
        console.print()
        
        # 执行每条命令
        for idx, command in enumerate(commands, 1):
            console.print(f"[bold yellow]▶ [{idx}/{len(commands)}] 执行命令:[/bold yellow] [cyan]{command}[/cyan]")
            
            success, output, exit_code = self._execute_single_command(
                command, 
                work_dir
            )
            
            if not success:
                self._handle_command_failure(command, exit_code, output)
                
                if stop_on_error:
                    console.print(Panel.fit(
                        f"[bold red]❌ 命令组 '{group_name}' 执行失败（第 {idx} 条命令）[/bold red]",
                        border_style="red"
                    ))
                    return False
                else:
                    console.print(f"[yellow]⚠ 命令失败但继续执行后续命令[/yellow]")
            else:
                console.print(f"[green]✓ 命令执行成功[/green]")
                
            console.print()
        
        console.print(Panel.fit(
            f"[bold green]✓ 命令组 '{group_name}' 执行成功[/bold green]",
            border_style="green"
        ))
        console.print()
        
        return True
    
    def _execute_single_command(self, command: str, working_dir: str) -> Tuple[bool, str, int]:
        """
        执行单条命令（实时输出）
        
        Args:
            command: 要执行的命令
            working_dir: 工作目录
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 输出, 退出码)
        """
        try:
            import sys
            import select
            import pty
            import fcntl
            import termios
            import struct
            import time
            
            console.print("[dim]" + "─" * 60 + "[/dim]")
            
            # 使用 pty 创建伪终端，让命令认为它在真实终端中运行
            master_fd, slave_fd = pty.openpty()
            
            # 设置终端大小（避免输出换行问题）
            winsize = struct.pack('HHHH', 24, 80, 0, 0)
            fcntl.ioctl(slave_fd, termios.TIOCSWINSZ, winsize)
            
            # 启动进程
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=working_dir,
                stdout=slave_fd,
                stderr=slave_fd,
                stdin=slave_fd,
                close_fds=True,
                preexec_fn=os.setsid
            )
            
            # 关闭子进程端的文件描述符
            os.close(slave_fd)
            
            # 设置非阻塞模式
            flags = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            
            # 实时读取并输出
            output_lines = []
            no_data_count = 0
            
            while True:
                # 检查进程是否结束
                poll_result = process.poll()
                
                # 使用 select 等待数据
                try:
                    readable, _, _ = select.select([master_fd], [], [], 0.1)
                    
                    if readable:
                        try:
                            data = os.read(master_fd, 4096)
                            if data:
                                text = data.decode('utf-8', errors='replace')
                                # 直接输出到终端（保留所有控制字符）
                                sys.stdout.write(text)
                                sys.stdout.flush()
                                output_lines.append(text)
                                no_data_count = 0
                            else:
                                # 没有数据了
                                no_data_count += 1
                        except OSError as e:
                            # 读取结束
                            if e.errno == 5:  # Input/output error
                                break
                            no_data_count += 1
                    else:
                        no_data_count += 1
                    
                    # 如果进程已结束
                    if poll_result is not None:
                        # 再尝试读取几次，确保所有数据都读完
                        if no_data_count > 3:
                            break
                        time.sleep(0.05)
                        
                except Exception:
                    break
            
            # 等待进程结束
            exit_code = process.wait()
            
            # 关闭主端文件描述符
            try:
                os.close(master_fd)
            except:
                pass
            
            print()  # 确保最后有换行
            console.print("[dim]" + "─" * 60 + "[/dim]")
            
            # 判断是否成功
            success = exit_code == 0
            
            # 合并输出
            output = ''.join(output_lines)
            
            return success, output, exit_code
            
        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]❌ 命令执行异常: {e}[/bold red]",
                border_style="red"
            ))
            import traceback
            traceback.print_exc()
            return False, str(e), -1
    
    def _handle_command_failure(self, command: str, exit_code: int, output: str):
        """
        处理命令执行失败
        
        Args:
            command: 失败的命令
            exit_code: 退出码
            output: 输出信息
        """
        console.print()
        console.print("[bold red]" + "=" * 60 + "[/bold red]")
        console.print("[bold red]命令执行失败[/bold red]")
        console.print("[bold red]" + "=" * 60 + "[/bold red]")
        console.print(f"[red]命令:[/red] {command}")
        console.print(f"[red]退出码:[/red] {exit_code}")
        
        if output and output.strip():
            console.print("[red]错误输出:[/red]")
            console.print("[dim]" + "-" * 60 + "[/dim]")
            console.print(output.strip())
            console.print("[dim]" + "-" * 60 + "[/dim]")
        
        console.print()
    
    @staticmethod
    def test_command_available(command: str) -> bool:
        """
        测试命令是否可用
        
        Args:
            command: 命令名称（如 'mvn', 'npm', 'python'）
            
        Returns:
            bool: 命令是否可用
        """
        try:
            # 使用 which 命令检查（Unix/Linux/macOS）
            result = subprocess.run(
                ['which', command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False


if __name__ == '__main__':
    """测试本地命令执行器"""
    
    # 创建执行器
    executor = LocalCommandExecutor()
    
    # 测试命令
    test_commands = [
        "echo '测试命令 1'",
        "pwd",
        "ls -la",
        "echo '测试命令 2'"
    ]
    
    # 执行命令组
    success = executor.execute_command_group(
        commands=test_commands,
        group_name="测试命令组"
    )
    
    if success:
        console.print("[bold green]✓ 测试成功[/bold green]")
    else:
        console.print("[bold red]✗ 测试失败[/bold red]")

