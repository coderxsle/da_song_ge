#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器
负责读取、解析和验证配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from common.log_utils import log_info, log_warn, log_error
from common.path_utils import expand_path, validate_path
from rich.console import Console

console = Console()

class ConfigManager:
    """配置管理器类"""
    
    # 默认配置文件路径（类变量）
    DEFAULT_CONFIG_PATH = Path(__file__).parent / 'config.yaml'
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径（可选，默认使用 DEFAULT_CONFIG_PATH）
        """
        if config_path is None:
            config_path = str(self.DEFAULT_CONFIG_PATH)
        
        self.config_path = expand_path(config_path)
        self.config: Optional[Dict[str, Any]] = None
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            # 检查配置文件是否存在
            if not os.path.exists(self.config_path):
                log_error(f"配置文件不存在: {self.config_path}")
                return False
            
            # 读取配置文件
            console.print(f"[blue]✲ 正在加载配置文件:[/blue] {self.config_path}")
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            # 检查配置是否为空
            if self.config is None:
                log_error("配置文件为空")
                return False
            
            console.print("[green]✓ 配置文件加载成功[/green]")
            
            # 验证配置
            return self.validate_config()
            
        except yaml.YAMLError as e:
            log_error(f"配置文件格式错误: {e}")
            return False
        except Exception as e:
            log_error(f"加载配置文件失败: {e}")
            return False
    
    def validate_config(self) -> bool:
        """
        验证配置的合法性
        
        Returns:
            bool: 验证是否通过
        """
        if not self.config:
            log_error("配置为空")
            return False
        
        # 检查 servers 字段
        if 'servers' not in self.config:
            log_error("配置文件缺少 'servers' 字段")
            return False
        
        servers = self.config['servers']
        
        # 检查 servers 是否为列表
        if not isinstance(servers, list):
            log_error("'servers' 必须是列表类型")
            return False
        
        # 检查 servers 是否为空
        if len(servers) == 0:
            log_error("'servers' 列表不能为空")
            return False
        
        # 验证每个服务器配置
        server_names = set()
        for idx, server in enumerate(servers):
            if not self._validate_server_config(server, idx):
                return False
            
            # 检查服务器名称唯一性
            server_name = server['name']
            if server_name in server_names:
                log_error(f"服务器名称重复: {server_name}")
                return False
            server_names.add(server_name)
        
        console.print("[green]✓ 配置文件验证通过[/green]")
        console.print()
        return True
    
    def _validate_server_config(self, server: Dict[str, Any], idx: int) -> bool:
        """
        验证单个服务器配置
        
        Args:
            server: 服务器配置字典
            idx: 服务器索引
            
        Returns:
            bool: 验证是否通过
        """
        # 必填字段
        required_fields = ['name', 'host', 'port', 'username', 'auth']
        
        # 检查必填字段
        for field in required_fields:
            if field not in server:
                log_error(f"服务器 #{idx} 缺少必填字段: {field}")
                return False
        
        # 验证字段类型
        if not isinstance(server['name'], str):
            log_error(f"服务器 #{idx} 的 'name' 必须是字符串")
            return False
        
        if not isinstance(server['host'], str):
            log_error(f"服务器 '{server['name']}' 的 'host' 必须是字符串")
            return False
        
        if not isinstance(server['port'], int):
            log_error(f"服务器 '{server['name']}' 的 'port' 必须是整数")
            return False
        
        if not isinstance(server['username'], str):
            log_error(f"服务器 '{server['name']}' 的 'username' 必须是字符串")
            return False
        
        # 验证端口范围
        if not (1 <= server['port'] <= 65535):
            log_error(f"服务器 '{server['name']}' 的端口号无效: {server['port']} (必须在 1-65535 之间)")
            return False
        
        # 验证认证配置
        if not self._validate_auth_config(server['auth'], server['name']):
            return False
        
        # 验证上传配置（可选）
        if 'upload' in server:
            if not isinstance(server['upload'], dict):
                log_error(f"服务器 '{server['name']}' 的 'upload' 必须是字典类型")
                return False
            
            if not self._validate_upload_config(server['upload'], server['name']):
                return False
        
        # 验证命令配置（可选）
        if 'commands' in server:
            if not isinstance(server['commands'], dict):
                log_error(f"服务器 '{server['name']}' 的 'commands' 必须是字典类型")
                return False
            
            if not self._validate_commands_config(server['commands'], server['name']):
                return False
        
        return True
    
    def _validate_auth_config(self, auth: Any, server_name: str) -> bool:
        """
        验证认证配置
        
        Args:
            auth: 认证配置
            server_name: 服务器名称
            
        Returns:
            bool: 验证是否通过
        """
        if not isinstance(auth, dict):
            log_error(f"服务器 '{server_name}' 的 'auth' 必须是字典类型")
            return False
        
        # 检查必填字段
        if 'type' not in auth:
            log_error(f"服务器 '{server_name}' 的认证配置缺少 'type' 字段")
            return False
        
        # 验证认证类型
        if auth['type'] not in ['ssh_key', 'password']:
            log_error(f"服务器 '{server_name}' 的认证类型无效: {auth['type']} (支持: ssh_key, password)")
            return False
        
        # 根据认证类型验证必填字段
        if auth['type'] == 'ssh_key':
            # SSH 密钥认证：需要 key_path，password 可选
            if 'key_path' not in auth:
                log_error(f"服务器 '{server_name}' 的 SSH 密钥认证需要 'key_path' 字段")
                return False
            
            key_path = expand_path(auth['key_path'])
            if not os.path.exists(key_path):
                log_warn(f"服务器 '{server_name}' 的 SSH 密钥文件不存在: {key_path}")
                # 注意：这里只是警告，不返回 False，因为密钥文件可能在运行时才创建
        
        elif auth['type'] == 'password':
            # 密码认证：password 可选，如果不提供将在连接时提示输入
            pass
        
        return True
    
    def _validate_upload_config(self, upload: Dict[str, Any], server_name: str) -> bool:
        """
        验证上传配置
        
        Args:
            upload: 上传配置
            server_name: 服务器名称
            
        Returns:
            bool: 验证是否通过
        """
        for upload_type, upload_items in upload.items():
            if not isinstance(upload_items, list):
                log_error(f"服务器 '{server_name}' 的应用类型 '{upload_type}' 必须是列表")
                return False
            
            for idx, item in enumerate(upload_items):
                if not isinstance(item, dict):
                    log_error(f"服务器 '{server_name}' 的应用类型 '{upload_type}' 的第 {idx} 项必须是字典")
                    return False
                
                # 检查必填字段
                if 'local_path' not in item:
                    log_error(f"服务器 '{server_name}' 的应用类型 '{upload_type}' 的第 {idx} 项缺少 'local_path'")
                    return False
                
                if 'remote_path' not in item:
                    log_error(f"服务器 '{server_name}' 的应用类型 '{upload_type}' 的第 {idx} 项缺少 'remote_path'")
                    return False
                
                # 验证上传模式（可选）
                if 'mode' in item:
                    if item['mode'] not in ['sync', 'copy']:
                        log_error(f"服务器 '{server_name}' 的上传模式无效: {item['mode']} (支持: sync, copy)")
                        return False
                
                # 验证 delete_extra（可选）
                if 'delete_extra' in item:
                    if not isinstance(item['delete_extra'], bool):
                        log_error(f"服务器 '{server_name}' 的 'delete_extra' 必须是布尔类型")
                        return False
        
        return True
    
    def _validate_commands_config(self, commands: Dict[str, Any], server_name: str) -> bool:
        """
        验证命令配置
        
        Args:
            commands: 命令配置
            server_name: 服务器名称
            
        Returns:
            bool: 验证是否通过
        """
        for command_group, command_list in commands.items():
            if not isinstance(command_list, list):
                log_error(f"服务器 '{server_name}' 的命令组 '{command_group}' 必须是列表")
                return False
            
            for idx, command in enumerate(command_list):
                if not isinstance(command, str):
                    log_error(f"服务器 '{server_name}' 的命令组 '{command_group}' 的第 {idx} 项必须是字符串")
                    return False
        
        return True
    
    def get_servers(self) -> List[Dict[str, Any]]:
        """
        获取所有服务器配置
        
        Returns:
            List[Dict]: 服务器配置列表
        """
        return self.config.get('servers', []) if self.config else []
    
    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取服务器配置
        
        Args:
            name: 服务器名称
            
        Returns:
            Optional[Dict]: 服务器配置，如果未找到则返回 None
        """
        for server in self.get_servers():
            if server['name'] == name:
                return server
        return None
    
    def get_license_key(self) -> Optional[str]:
        """
        获取授权密钥
        
        Returns:
            Optional[str]: 授权密钥，如果未配置则返回 None
        """
        return self.config.get('license_key') if self.config else None
    
    @staticmethod
    def expand_path(path: str) -> str:
        """
        展开路径（~ 转换为用户主目录）
        
        Args:
            path: 原始路径
            
        Returns:
            str: 展开后的路径
        """
        return expand_path(path)


def main():
    """主函数 - 用于测试配置管理器"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='配置管理器测试工具')
    parser.add_argument(
        '-c', '--config',
        type=str,
        default=None,
        help=f'配置文件路径 (默认: {ConfigManager.DEFAULT_CONFIG_PATH})'
    )
    
    args = parser.parse_args()
    
    # 直接调用 validate_config 模块的功能，避免重复代码
    try:
        from remote_deploy.validate_config import validate_config
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        # 如果没有指定配置文件，使用默认路径
        config_path = args.config if args.config else str(ConfigManager.DEFAULT_CONFIG_PATH)
        
        success = validate_config(config_path)
        
        if success:
            console.print(Panel.fit(
                "[bold green]🎉 配置管理器测试完成！[/bold green]",
                border_style="green"
            ))
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 测试被用户中断[/yellow]")
        return 1
    except Exception as e:
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        console.print(Panel.fit(
            f"[bold red]❌ 发生错误: {e}[/bold red]",
            border_style="red"
        ))
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())

