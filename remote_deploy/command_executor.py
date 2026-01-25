#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令执行器
负责在远程服务器上执行命令
"""

from typing import List, Tuple, Any
from common.ssh_client import SSHClient
from common.log_utils import log_info, log_warn, log_error


class CommandExecutor:
    """命令执行器类"""
    
    def __init__(self, ssh_client: SSHClient):
        """
        初始化命令执行器
        
        Args:
            ssh_client: SSH 客户端实例
        """
        self.ssh_client = ssh_client
    
    def execute_command_group(self, commands: List[str], group_name: str, keep_session: bool = True) -> bool:
        """
        执行命令组
        
        Args:
            commands: 命令列表
            group_name: 命令组名称
            keep_session: 是否保持会话状态（将多条命令合并为一条执行）
            
        Returns:
            bool: 执行是否成功
        """
        if not commands:
            log_warn(f"命令组 '{group_name}' 为空，跳过执行")
            return True
        
        log_info(f"执行命令组: {group_name} (共 {len(commands)} 条命令)")
        
        # 如果启用保持会话，将所有命令合并为一条执行
        if keep_session and len(commands) > 1:
            return self._execute_commands_in_session(commands, group_name)
        
        # 否则逐条执行
        for idx, command in enumerate(commands, 1):
            log_info(f"[{idx}/{len(commands)}] 执行命令: {command}")
            
            # hide=False 会实时显示输出
            success, output, exit_code = self._execute_single_command(command, hide=False)
            
            if not success:
                self._handle_command_failure(command, exit_code, output)
                return False
        
        log_info(f"命令组 '{group_name}' 执行成功")
        return True
    
    def _execute_commands_in_session(self, commands: List[str], group_name: str) -> bool:
        """
        在同一个会话中执行多条命令（使用 && 连接）
        
        Args:
            commands: 命令列表
            group_name: 命令组名称
            
        Returns:
            bool: 执行是否成功
        """
        # 显示每条命令
        for idx, command in enumerate(commands, 1):
            log_info(f"[{idx}/{len(commands)}] 执行命令: {command}")
        
        # 将命令用 && 连接（任何一条失败就停止）
        combined_command = " && ".join(commands)
        
        log_info("在同一会话中执行所有命令...")
        
        # hide=False 会实时显示输出，所以不需要再 print(output)
        success, output, exit_code = self._execute_single_command(combined_command, hide=False)
        
        if not success:
            self._handle_command_failure(combined_command, exit_code, output)
            return False
        
        log_info(f"命令组 '{group_name}' 执行成功")
        return True
    
    def _execute_single_command(self, command: str, hide: bool = False) -> Tuple[bool, str, int]:
        """
        执行单条命令
        
        Args:
            command: 要执行的命令
            hide: 是否隐藏输出（True 时不实时显示，False 时实时显示）
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 输出, 退出码)
        """
        try:
            # 执行命令
            result = self.ssh_client.run(command, hide=hide)
            
            # 处理返回结果
            if result is None:
                return False, "", -1
            
            # 如果 result 是字符串，说明命令成功
            if isinstance(result, str):
                return True, result, 0
            
            # 如果 result 是 True，说明命令成功但无输出
            if result is True:
                return True, "", 0
            
            # 其他情况视为失败
            return False, "", -1
            
        except Exception as e:
            log_error(f"命令执行异常: {e}")
            return False, str(e), -1
    
    def _handle_command_failure(self, command: str, exit_code: int, output: str):
        """
        处理命令执行失败
        
        Args:
            command: 失败的命令
            exit_code: 退出码
            output: 输出信息
        """
        log_error("=" * 60)
        log_error("命令执行失败")
        log_error("=" * 60)
        log_error(f"命令: {command}")
        log_error(f"退出码: {exit_code}")
        
        if output and output.strip():
            log_error("错误输出:")
            log_error("-" * 60)
            print(output)
            log_error("-" * 60)
        
        log_error("后续命令将不会执行")

