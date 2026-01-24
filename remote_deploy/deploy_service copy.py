#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
远程部署服务
负责控制整个部署流程
"""

import os
import sys
from typing import Optional, Dict, List, Any
from common.ssh_client import SSHClient
from common.log_utils import log_error
from remote_deploy.config_manager import ConfigManager
from remote_deploy.file_uploader import FileUploader
from remote_deploy.command_executor import CommandExecutor
from remote_deploy.local_command_executor import LocalCommandExecutor
from remote_deploy.validate_config import show_servers_table
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich import box

console = Console()


class RemoteDeployService:
    """远程部署服务类"""
    
    def __init__(self, config_manager: ConfigManager):
        """
        初始化部署服务
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager
        self.ssh_client: Optional[SSHClient] = None
        self.file_uploader: Optional[FileUploader] = None
        self.command_executor: Optional[CommandExecutor] = None
        self.local_command_executor: Optional[LocalCommandExecutor] = None
    
    @staticmethod
    def deploy(config_path: str = None, 
               server_name: Optional[str] = None,
               upload_types: Optional[List[str]] = None,
               command_group: Optional[str] = None,
               dry_run: bool = False) -> bool:
        """
        部署入口方法
        
        Args:
            config_path: 配置文件路径（可选，默认使用 ConfigManager.DEFAULT_CONFIG_PATH）
            server_name: 服务器名称（可选）
            upload_types: 应用类型列表（可选，支持多个）
            command_group: 命令组名称（可选）
            dry_run: 是否模拟执行
            
        Returns:
            bool: 部署是否成功
        """
        console.clear()
        console.print(Panel.fit(
            "[bold yellow]远程服务器部署工具[/bold yellow]",
            border_style="magenta",
            title="🚀 部署工具"
        ))
        
        # 加载配置（如果没有指定配置文件，ConfigManager 会使用默认路径）
        config_manager = ConfigManager(config_path)
        if not config_manager.load_config():
            return False
        
        # 创建部署服务实例
        service = RemoteDeployService(config_manager)
        
        # 选择服务器（交互式或参数指定）
        if not server_name:
            server_name = service._select_server_interactive()
            if not server_name:
                console.print(Panel.fit(
                    "[bold red]❌ 未选择服务器[/bold red]",
                    border_style="red"
                ))
                return False
        
        server_config = config_manager.get_server_by_name(server_name)
        if not server_config:
            console.print(Panel.fit(
                f"[bold red]❌ 未找到服务器: {server_name}[/bold red]",
                border_style="red"
            ))
            return False
        
        # 选择应用类型（支持多选）
        if not upload_types:
            upload_types = service._select_upload_type_interactive(server_config)
            # upload_types 可以为 None（跳过上传）
        
        # 选择命令组
        if not command_group:
            command_group = service._select_command_group_interactive(server_config)
            # command_group 可以为 None（跳过命令执行）
        
        # 检查是否至少选择了一项任务
        if not upload_types and not command_group:
            console.print(Panel.fit(
                "[bold yellow]⚠ 未选择任何任务，退出[/bold yellow]",
                border_style="yellow"
            ))
            return False
        
        # 模拟执行
        if dry_run:
            console.print(Panel.fit(
                "[bold yellow]模拟执行模式（不会实际执行）[/bold yellow]",
                border_style="yellow",
                title="🔍 模拟执行"
            ))
            service._show_dry_run_info(server_config, upload_types, command_group)
            return True
        
        # 执行部署
        return service._execute_deployment(server_config, upload_types, command_group)
    
    def _select_server_interactive(self) -> Optional[str]:
        """交互式选择服务器"""
        servers = self.config_manager.get_servers()
        
        console.print(Panel.fit(
            "[bold yellow]可用服务器列表[/bold yellow]",
            border_style="magenta",
            title="🖥️  服务器选择"
        ))
        
        # 使用 validate_config 中的表格显示函数
        show_servers_table(servers, title=None)
        
        try:
            choice = Prompt.ask(
                "[bold cyan]请选择服务器编号[/bold cyan]",
                choices=[str(i) for i in range(1, len(servers) + 1)]
            )
            
            idx = int(choice) - 1
            selected = servers[idx]['name']
            console.print(f"[green]✓ 已选择服务器:[/green] [bold]{selected}[/bold]")
            console.print()
            return selected
                
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ 操作已取消[/yellow]")
            return None
    
    def _select_upload_type_interactive(self, server_config: Dict[str, Any]) -> Optional[List[str]]:
        """交互式选择应用类型（支持多选）"""
        upload_config = server_config.get('upload', {})
        
        if not upload_config:
            console.print(Panel.fit(
                "[bold yellow]⚠ 该服务器未配置上传任务[/bold yellow]",
                border_style="yellow"
            ))
            return None
        
        upload_types = list(upload_config.keys())
        
        console.print(Panel.fit(
            "[bold yellow]可选应用类型（支持多选）[/bold yellow]",
            border_style="magenta",
            title="📤 应用选择"
        ))
        
        # 创建应用类型表格
        table = Table(
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
        table.add_column("应用类型", style="bold green", width=30, vertical="middle")
        table.add_column("任务数量", style="cyan", width=15, vertical="middle")
        
        for idx, upload_type in enumerate(upload_types, 1):
            file_count = len(upload_config[upload_type])
            table.add_row(
                str(idx),
                upload_type,
                f"{file_count} 个任务"
            )
        
        # 添加全选和跳过选项
        table.add_row(
            "all",
            "[green]全部部署[/green]",
            f"{len(upload_types)} 个应用"
        )
        table.add_row(
            "0",
            "[yellow]跳过文件上传[/yellow]",
            "-"
        )
        
        console.print(table)
        console.print()
        
        # 循环直到用户输入有效选择或取消
        while True:
            try:
                choice = Prompt.ask(
                    "[bold cyan]请选择应用类型编号（多选用逗号或空格分隔，如: 1,2 或 1 2 或输入 all 全选）[/bold cyan]"
                )
                
                # 处理跳过
                if choice.strip() == '0':
                    console.print("[yellow]⚠ 已跳过文件上传[/yellow]")
                    return None
                
                # 处理全选
                if choice.strip().lower() == 'all':
                    console.print(f"[green]✓ 已选择部署应用:[/green] [bold]{', '.join(upload_types)}[/bold]")
                    return upload_types
                
                # 统一处理中英文逗号和空格分隔符
                # 将中文逗号替换为英文逗号，然后同时按逗号和空格分割
                choice = choice.replace('，', ',')  # 中文逗号转英文逗号
                # 先按逗号分割，再对每部分按空格分割
                parts = []
                for segment in choice.split(','):
                    parts.extend(segment.split())
                
                # 处理多选
                selected_indices = []
                invalid_inputs = []
                
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        idx = int(part)
                        if 1 <= idx <= len(upload_types):
                            selected_indices.append(idx)
                        else:
                            invalid_inputs.append(part)
                    except ValueError:
                        invalid_inputs.append(part)
                
                # 显示无效输入警告
                if invalid_inputs:
                    console.print(f"[yellow]⚠ 忽略无效输入: {', '.join(invalid_inputs)}[/yellow]")
                
                # 如果没有有效选择，提示重新输入
                if not selected_indices:
                    console.print("[red]❌ 未选择有效的应用类型，请重新输入[/red]")
                    console.print()
                    continue
                
                # 去重并排序
                selected_indices = sorted(set(selected_indices))
                selected_types = [upload_types[idx - 1] for idx in selected_indices]
                
                console.print(f"[green]✓ 已选择部署应用:[/green] [bold]{', '.join(selected_types)}[/bold]")
                return selected_types
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠ 操作已取消[/yellow]")
                return None
    
    def _select_command_group_interactive(self, server_config: Dict[str, Any]) -> Optional[str]:
        """交互式选择命令组"""
        commands_config = server_config.get('commands', {})
        
        if not commands_config:
            console.print(Panel.fit(
                "[bold yellow]⚠ 该服务器未配置命令[/bold yellow]",
                border_style="yellow"
            ))
            return None
        
        command_groups = list(commands_config.keys())
        
        console.print()
        console.print(Panel.fit(
            "[bold yellow]可用命令组[/bold yellow]",
            border_style="magenta",
            title="⚙️  命令选择"
        ))
        console.print()
        
        # 创建命令组表格
        table = Table(
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
        table.add_column("命令组", style="bold green", width=30, vertical="middle")
        table.add_column("命令数量", style="cyan", width=15, vertical="middle")
        
        for idx, group in enumerate(command_groups, 1):
            cmd_count = len(commands_config[group])
            table.add_row(
                str(idx),
                group,
                f"{cmd_count} 条命令"
            )
        
        # 添加跳过选项
        skip_option = len(command_groups) + 1
        table.add_row(
            str(skip_option),
            "[yellow]跳过命令执行[/yellow]",
            "-"
        )
        
        console.print(table)
        console.print()
        
        # 循环直到用户输入有效选择或取消
        while True:
            try:
                choice = Prompt.ask(
                    "[bold cyan]请选择命令组编号[/bold cyan]"
                )
                
                choice = choice.strip()
                if not choice:
                    console.print("[red]❌ 输入不能为空，请重新输入[/red]")
                    console.print()
                    continue
                
                try:
                    idx = int(choice)
                    
                    # 检查是否为跳过选项
                    if idx == skip_option:
                        console.print("[yellow]⚠ 已跳过命令执行[/yellow]")
                        return None
                    
                    # 检查是否为有效的命令组编号
                    if 1 <= idx <= len(command_groups):
                        selected = command_groups[idx - 1]
                        console.print(f"[green]✓ 已选择命令组:[/green] [bold]{selected}[/bold]")
                        return selected
                    else:
                        console.print(f"[red]❌ 无效的编号: {choice}，请输入 1-{skip_option} 之间的数字[/red]")
                        console.print()
                        continue
                        
                except ValueError:
                    console.print(f"[red]❌ 无效的输入: {choice}，请输入数字[/red]")
                    console.print()
                    continue
                    
            except KeyboardInterrupt:
                console.print("\n[yellow]⚠ 操作已取消[/yellow]")
                return None
    
    def _execute_deployment(self, server_config: Dict[str, Any], 
                           upload_types: Optional[List[str]],
                           command_group: Optional[str]) -> bool:
        """执行部署（支持多个应用类型）"""
        console.print()
        console.print(Panel.fit(
            f"[bold yellow]开始部署[/bold yellow]\n"
            f"[cyan]服务器:[/cyan] {server_config['name']}\n"
            f"[cyan]地址:[/cyan] {server_config['host']}:{server_config['port']}\n"
            f"[cyan]用户:[/cyan] {server_config['username']}",
            border_style="magenta",
            title="🚀 部署执行"
        ))
        console.print()
        
        # 初始化结果字典（支持多应用）
        results = {
            'local_commands': {},  # {app_type: success}
            'uploads': {},         # {app_type: success}
            'command_success': False,
            'command_skipped': command_group is None
        }
        
        # ========== 阶段 0: 执行本地命令（在连接服务器之前）==========
        if upload_types:
            console.print()
            console.print(Panel.fit(
                f"[bold yellow]阶段 0: 执行本地命令[/bold yellow]",
                border_style="blue",
                title="💻 本地命令"
            ))
            console.print()
            
            for idx, upload_type in enumerate(upload_types, 1):
                local_commands_config = server_config.get('local_commands', {}).get(upload_type)
                
                if local_commands_config:
                    console.print(f"[bold cyan]▶ [{idx}/{len(upload_types)}] 本地命令: {upload_type}[/bold cyan]")
                    console.print()
                    
                    success = self._execute_local_commands(
                        local_commands_config, 
                        upload_type
                    )
                    results['local_commands'][upload_type] = success
                    
                    if not success:
                        console.print(Panel.fit(
                            f"[bold red]❌ 本地命令执行失败 ({upload_type})，终止部署[/bold red]",
                            border_style="red"
                        ))
                        return False
                    
                    console.print(f"[green]✓ 本地命令执行成功 ({upload_type})[/green]")
                    console.print()
                else:
                    console.print(f"[yellow]⚠ 跳过本地命令 ({upload_type})：未配置[/yellow]")
                    console.print()
        
        # ========== 建立 SSH 连接（本地命令成功后才连接）==========
        console.print()
        if not self._connect_to_server(server_config):
            return False
        
        try:
            # ========== 阶段 1: 上传文件 ==========
            if upload_types:
                console.print()
                console.print(Panel.fit(
                    f"[bold yellow]阶段 1: 上传文件[/bold yellow]",
                    border_style="blue",
                    title="📤 文件上传"
                ))
                console.print()
                
                for idx, upload_type in enumerate(upload_types, 1):
                    console.print(f"[bold cyan]▶ [{idx}/{len(upload_types)}] 上传文件: {upload_type}[/bold cyan]")
                    console.print()
                    
                    success = self._upload_files(server_config, upload_type)
                    results['uploads'][upload_type] = success
                    
                    if not success:
                        console.print(Panel.fit(
                            f"[bold red]❌ 文件上传失败 ({upload_type})，终止部署[/bold red]",
                            border_style="red"
                        ))
                        return False
                    
                    console.print(f"[green]✓ 文件上传成功 ({upload_type})[/green]")
                    console.print()
            
            # ========== 阶段 2: 执行远程命令 ==========
            if command_group:
                console.print()
                console.print(Panel.fit(
                    f"[bold yellow]阶段 2: 执行远程命令 ({command_group})[/bold yellow]",
                    border_style="blue",
                    title="⚙️  命令执行"
                ))
                console.print()
                results['command_success'] = self._execute_commands(server_config, command_group)
                
                if not results['command_success']:
                    console.print(Panel.fit(
                        "[bold red]❌ 命令执行失败[/bold red]",
                        border_style="red"
                    ))
                    return False
            
            # 显示部署摘要
            self._show_deployment_summary(server_config, results, upload_types)
            
            return True
            
        finally:
            # 关闭连接
            if self.ssh_client:
                self.ssh_client.disconnect()
    
    def _connect_to_server(self, server_config: Dict[str, Any]) -> bool:
        """连接到服务器"""
        console.print()
        console.print("[bold green]🔌 正在建立 SSH 连接...[/bold green]")
        
        try:
            # 从配置文件设置环境变量（SSHClient 会从环境变量读取）
            os.environ['SERVER_IP'] = server_config['host']
            os.environ['SERVER_PORT'] = str(server_config['port'])  # 新增：设置端口
            os.environ['SERVER_USER'] = server_config['username']
            
            # 处理认证
            auth_config = server_config['auth']
            
            if auth_config['type'] == 'ssh_key':
                key_path = self.config_manager.expand_path(auth_config['key_path'])
                
                if not os.path.exists(key_path):
                    console.print(Panel.fit(
                        f"[bold red]❌ SSH 密钥文件不存在: {key_path}[/bold red]",
                        border_style="red"
                    ))
                    return False
                
                # 检查密钥文件权限（可选）
                self._check_key_permission(key_path)
                
                # 设置密钥路径到环境变量
                os.environ['SSH_KEY_PATH'] = key_path
                
                # 获取密码（可选，用作密钥的 passphrase）
                password = self._get_password(auth_config, server_config['name'], is_passphrase=True)
                if password:
                    os.environ['SSH_PASSWORD'] = password
                
                console.print("[cyan]使用 SSH 密钥认证[/cyan]")
            
            elif auth_config['type'] == 'password':
                # 密码认证
                password = self._get_password(auth_config, server_config['name'], is_passphrase=False)
                if password is None:
                    return False
                
                os.environ['SSH_PASSWORD'] = password
                # 清除密钥路径（如果有）
                if 'SSH_KEY_PATH' in os.environ:
                    del os.environ['SSH_KEY_PATH']
                
                console.print("[cyan]使用密码认证[/cyan]")
            
            else:
                console.print(Panel.fit(
                    f"[bold red]❌ 不支持的认证类型: {auth_config['type']}[/bold red]",
                    border_style="red"
                ))
                return False
            
            # 创建 SSH 客户端
            self.ssh_client = SSHClient()
            
            # 显式建立连接（测试连接）
            if not self.ssh_client.run("echo 'Connection test'", hide=True):
                console.print(Panel.fit(
                    "[bold red]❌ SSH 连接测试失败[/bold red]",
                    border_style="red"
                ))
                return False
            
            self.file_uploader = FileUploader(self.ssh_client)
            self.command_executor = CommandExecutor(self.ssh_client)
            
            console.print("[green]✓ SSH 连接建立成功[/green]")
            return True
            
        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]❌ 连接服务器失败: {e}[/bold red]",
                border_style="red"
            ))
            return False
    
    def _get_password(self, auth_config: Dict[str, Any], server_name: str, is_passphrase: bool = False) -> Optional[str]:
        """
        获取密码
        
        Args:
            auth_config: 认证配置
            server_name: 服务器名称
            is_passphrase: 是否是密钥的 passphrase（True 时密码可选）
            
        Returns:
            Optional[str]: 密码，如果获取失败则返回 None
        """
        # 如果配置文件中有密码，直接使用
        if 'password' in auth_config and auth_config['password']:
            return auth_config['password']
        
        # 如果是 passphrase 且没有配置，可以跳过（密钥可能没有密码保护）
        if is_passphrase:
            console.print("[cyan]SSH 密钥未设置 passphrase（或将尝试无密码连接）[/cyan]")
            return None
        
        # 否则提示用户输入
        try:
            import getpass
            console.print(f"[yellow]请输入服务器 '{server_name}' 的密码:[/yellow]")
            password = getpass.getpass("密码: ")
            
            if not password:
                console.print(Panel.fit(
                    "[bold red]❌ 密码不能为空[/bold red]",
                    border_style="red"
                ))
                return None
            
            return password
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ 操作已取消[/yellow]")
            return None
        except Exception as e:
            console.print(Panel.fit(
                f"[bold red]❌ 获取密码失败: {e}[/bold red]",
                border_style="red"
            ))
            return None
    
    def _check_key_permission(self, key_path: str):
        """检查密钥文件权限"""
        try:
            import stat
            st = os.stat(key_path)
            mode = st.st_mode & 0o777
            
            if mode != 0o600:
                console.print(f"[yellow]⚠ SSH 密钥文件权限不安全: {oct(mode)}[/yellow]")
                console.print(f"[yellow]建议执行: chmod 600 {key_path}[/yellow]")
        except Exception:
            pass
    
    def _execute_local_commands(self, local_commands_config: Dict[str, Any], upload_type: str) -> bool:
        """
        执行本地命令
        
        Args:
            local_commands_config: 本地命令配置
            upload_type: 应用类型
            
        Returns:
            bool: 执行是否成功
        """
        commands = local_commands_config.get('commands', [])
        working_dir = local_commands_config.get('working_dir')
        stop_on_error = local_commands_config.get('stop_on_error', True)
        
        if not commands:
            console.print(Panel.fit(
                f"[bold yellow]⚠ 本地命令配置为空: {upload_type}[/bold yellow]",
                border_style="yellow"
            ))
            return True
        
        # 展开工作目录中的 ~ 符号
        if working_dir:
            working_dir = self.config_manager.expand_path(working_dir)
        
        # 创建本地命令执行器
        self.local_command_executor = LocalCommandExecutor(working_dir)
        
        # 执行命令组
        return self.local_command_executor.execute_command_group(
            commands=commands,
            group_name=f"本地命令 ({upload_type})",
            working_dir=working_dir,
            stop_on_error=stop_on_error
        )
    
    def _upload_files(self, server_config: Dict[str, Any], upload_type: str) -> bool:
        """上传文件"""
        upload_config = server_config.get('upload', {}).get(upload_type, [])
        
        if not upload_config:
            console.print(Panel.fit(
                f"[bold red]❌ 未找到上传配置: {upload_type}[/bold red]",
                border_style="red"
            ))
            return False
        
        if not self.file_uploader:
            console.print(Panel.fit(
                "[bold red]❌ 文件上传器未初始化[/bold red]",
                border_style="red"
            ))
            return False
        
        return self.file_uploader.upload_files(upload_config)
    
    def _execute_commands(self, server_config: Dict[str, Any], command_group: str) -> bool:
        """执行命令"""
        commands = server_config.get('commands', {}).get(command_group, [])
        
        if not commands:
            console.print(Panel.fit(
                f"[bold red]❌ 未找到命令组: {command_group}[/bold red]",
                border_style="red"
            ))
            return False
        
        if not self.command_executor:
            console.print(Panel.fit(
                "[bold red]❌ 命令执行器未初始化[/bold red]",
                border_style="red"
            ))
            return False
        
        return self.command_executor.execute_command_group(commands, command_group)
    
    def _show_deployment_summary(self, server_config: Dict[str, Any], results: Dict[str, Any], upload_types: Optional[List[str]]):
        """显示部署摘要（支持多应用）"""
        console.print()
        console.print(Panel.fit(
            "[bold yellow]部署摘要[/bold yellow]",
            border_style="magenta",
            title="📊 摘要"
        ))
        console.print()
        
        # 创建摘要表格
        table = Table(
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        table.add_column("项目", style="bold yellow", width=25, vertical="middle")
        table.add_column("状态", style="white", width=40, vertical="middle")
        
        table.add_row("服务器", f"[cyan]{server_config['name']}[/cyan]")
        table.add_row("地址", f"[cyan]{server_config['host']}:{server_config['port']}[/cyan]")
        
        # 本地命令执行结果（多应用）
        if results['local_commands']:
            for app_type, success in results['local_commands'].items():
                status = "[green]✓ 成功[/green]" if success else "[red]✗ 失败[/red]"
                table.add_row(f"本地命令 ({app_type})", status)
        else:
            table.add_row("本地命令", "[yellow]- 已跳过[/yellow]")
        
        # 文件上传结果（多应用）
        if results['uploads']:
            for app_type, success in results['uploads'].items():
                status = "[green]✓ 成功[/green]" if success else "[red]✗ 失败[/red]"
                table.add_row(f"文件上传 ({app_type})", status)
        else:
            table.add_row("文件上传", "[yellow]- 已跳过[/yellow]")
        
        # 命令执行结果
        if not results['command_skipped']:
            status = "[green]✓ 成功[/green]" if results['command_success'] else "[red]✗ 失败[/red]"
            table.add_row("远程命令", status)
        else:
            table.add_row("远程命令", "[yellow]- 已跳过[/yellow]")
        
        console.print(table)
        console.print()
        
        console.print(Panel.fit(
            "[bold green]🎉 部署完成！[/bold green]",
            border_style="green"
        ))
        console.print()
    
    def _show_dry_run_info(self, server_config: Dict[str, Any], 
                          upload_types: Optional[List[str]],
                          command_group: Optional[str]):
        """显示模拟执行信息（支持多应用）"""
        # 创建基本信息表格
        table = Table(
            title="📋 服务器信息",
            box=box.ROUNDED,
            border_style="bright_blue",
            show_header=True,
            header_style="bold cyan",
            show_lines=True
        )
        
        table.add_column("项目", style="bold yellow", width=15, vertical="middle")
        table.add_column("值", style="cyan", width=50, vertical="middle")
        
        table.add_row("服务器", server_config['name'])
        table.add_row("地址", f"{server_config['host']}:{server_config['port']}")
        table.add_row("用户", server_config['username'])
        
        console.print(table)
        console.print()
        
        if upload_types:
            for idx, upload_type in enumerate(upload_types, 1):
                # 显示本地命令（如果有）
                local_commands_config = server_config.get('local_commands', {}).get(upload_type)
                
                if local_commands_config:
                    console.print(Panel.fit(
                        f"[bold yellow]本地命令 [{idx}/{len(upload_types)}]: {upload_type}[/bold yellow]",
                        border_style="blue",
                        title="💻 本地命令"
                    ))
                    console.print()
                    
                    commands = local_commands_config.get('commands', [])
                    working_dir = local_commands_config.get('working_dir', '当前目录')
                    
                    # 创建本地命令表格
                    local_cmd_table = Table(
                        box=box.ROUNDED,
                        border_style="bright_blue",
                        show_header=True,
                        header_style="bold cyan",
                        show_lines=True
                    )
                    
                    local_cmd_table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
                    local_cmd_table.add_column("命令", style="green", width=80, vertical="middle")
                    
                    for cmd_idx, cmd in enumerate(commands, 1):
                        local_cmd_table.add_row(str(cmd_idx), cmd)
                    
                    console.print(f"[cyan]工作目录:[/cyan] {working_dir}")
                    console.print()
                    console.print(local_cmd_table)
                    console.print()
                
                # 显示上传任务
                console.print(Panel.fit(
                    f"[bold yellow]应用类型 [{idx}/{len(upload_types)}]: {upload_type}[/bold yellow]",
                    border_style="blue",
                    title="📤 上传任务"
                ))
                console.print()
                
                upload_config = server_config.get('upload', {}).get(upload_type, [])
                
                # 创建上传任务表格
                upload_table = Table(
                    box=box.ROUNDED,
                    border_style="bright_blue",
                    show_header=True,
                    header_style="bold cyan",
                    show_lines=True
                )
                
                upload_table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
                upload_table.add_column("本地路径", style="cyan", width=35, vertical="middle")
                upload_table.add_column("远程路径", style="green", width=35, vertical="middle")
                upload_table.add_column("选项", style="magenta", width=20, vertical="middle")
                
                for item_idx, item in enumerate(upload_config, 1):
                    options = []
                    if 'mode' in item:
                        options.append(f"模式: {item['mode']}")
                    if item.get('delete_extra'):
                        options.append("删除多余文件")
                    
                    upload_table.add_row(
                        str(item_idx),
                        item['local_path'],
                        item['remote_path'],
                        "\n".join(options) if options else "-"
                    )
                
                console.print(upload_table)
                console.print()
        
        if command_group:
            console.print(Panel.fit(
                f"[bold yellow]命令组: {command_group}[/bold yellow]",
                border_style="blue",
                title="⚙️  命令任务"
            ))
            console.print()
            
            commands = server_config.get('commands', {}).get(command_group, [])
            
            # 创建命令表格
            cmd_table = Table(
                box=box.ROUNDED,
                border_style="bright_blue",
                show_header=True,
                header_style="bold cyan",
                show_lines=True
            )
            
            cmd_table.add_column("序号", justify="center", style="bold yellow", width=6, vertical="middle")
            cmd_table.add_column("命令", style="green", width=80, vertical="middle")
            
            for idx, cmd in enumerate(commands, 1):
                cmd_table.add_row(str(idx), cmd)
            
            console.print(cmd_table)
            console.print()
        
        console.print(Panel.fit(
            "[bold green]✓ 模拟执行完成（未实际执行）[/bold green]",
            border_style="green"
        ))
        console.print()


if __name__ == '__main__':
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='远程服务器管理与自动化部署脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 交互式模式（推荐）
  python remote_deploy/deploy_service.py
  
  # 指定配置文件
  python remote_deploy/deploy_service.py -c /path/to/config.yaml
  
  # 指定服务器
  python remote_deploy/deploy_service.py -s "领航不良资产"
  
  # 指定单个应用类型
  python remote_deploy/deploy_service.py -s "领航不良资产" -u frontend_admin
  
  # 指定多个应用类型（逗号分隔）
  python remote_deploy/deploy_service.py -s "领航不良资产" -u backend_api,frontend_admin
  
  # 指定命令组
  python remote_deploy/deploy_service.py -s "领航不良资产" -g backend_api_server
  
  # 完整参数
  python remote_deploy/deploy_service.py -c config.yaml -s "领航不良资产" -u backend_api,frontend_admin -g restart_all
  
  # 模拟执行（不实际上传和执行命令）
  python remote_deploy/deploy_service.py -s "领航不良资产" -u frontend_admin -d
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help=f'配置文件路径 (默认: {ConfigManager.DEFAULT_CONFIG_PATH})'
    )
    
    parser.add_argument(
        '-s', '--server',
        type=str,
        help='服务器名称'
    )
    
    parser.add_argument(
        '-u', '--upload-types',
        type=str,
        help='应用类型，支持多选（逗号分隔，如: backend_api,frontend_admin）'
    )
    
    parser.add_argument(
        '-g', '--command-group',
        type=str,
        help='命令组名称'
    )
    
    parser.add_argument(
        '-d', '--dry-run',
        action='store_true',
        help='模拟执行（不实际上传和执行命令）'
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 2.0.0'
    )
    
    try:
        args = parser.parse_args()
        
        # 处理多个应用类型（逗号分隔）
        upload_types = None
        if args.upload_types:
            upload_types = [t.strip() for t in args.upload_types.split(',') if t.strip()]
            if not upload_types:
                upload_types = None
        
        # 执行部署
        success = RemoteDeployService.deploy(
            config_path=args.config,
            server_name=args.server,
            upload_types=upload_types,
            command_group=args.command_group,
            dry_run=args.dry_run
        )
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 操作已取消[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(Panel.fit(
            f"[bold red]❌ 程序异常: {e}[/bold red]",
            border_style="red"
        ))
        import traceback
        traceback.print_exc()
        sys.exit(1)

