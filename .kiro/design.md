# 远程服务器管理与自动化部署脚本 - 设计文档

## 文档版本
- **版本**: v1.0
- **创建日期**: 2026-01-21
- **最后更新**: 2026-01-21

---

## 目录
1. [系统架构设计](#1-系统架构设计)
2. [模块设计](#2-模块设计)
3. [类设计](#3-类设计)
4. [数据结构设计](#4-数据结构设计)
5. [核心流程设计](#5-核心流程设计)
6. [接口设计](#6-接口设计)
7. [错误处理设计](#7-错误处理设计)
8. [日志设计](#8-日志设计)
9. [配置管理设计](#9-配置管理设计)
10. [文件上传策略设计](#10-文件上传策略设计)

---

## 1. 系统架构设计

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI 入口层                              │
│                  (remote_deploy.py)                         │
│  - 命令行参数解析                                             │
│  - 交互式用户界面                                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    业务逻辑层                                 │
│                 (RemoteDeployService)                       │
│  - 部署流程控制                                               │
│  - 服务器选择                                                 │
│  - 上传任务管理                                               │
│  - 命令执行管理                                               │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    配置管理模块           │  │    SSH 连接模块          │
│  (ConfigManager)         │  │   (SSHClient)           │
│  - 配置文件解析           │  │  - SSH 连接管理          │
│  - 配置验证               │  │  - 文件上传 (SFTP)       │
│  - 路径展开               │  │  - 命令执行              │
└──────────────────────────┘  └──────────────────────────┘
                │                       │
                ▼                       ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│    文件上传模块           │  │    命令执行模块          │
│  (FileUploader)          │  │  (CommandExecutor)      │
│  - sync 模式上传          │  │  - 命令组执行            │
│  - copy 模式上传          │  │  - 输出捕获              │
│  - 进度显示               │  │  - 状态码检查            │
└──────────────────────────┘  └──────────────────────────┘
                │                       │
                ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    工具层                                     │
│  - 日志工具 (log_utils)                                       │
│  - 路径工具 (path_utils)                                      │
│  - 环境变量工具 (env_utils)                                   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈
- **语言**: Python 3.12+
- **SSH 库**: paramiko, fabric
- **配置解析**: PyYAML
- **进度显示**: rich
- **命令行**: argparse

### 1.3 目录结构

```
PythonProject/
├── scripts/
│   ├── remote_deploy.py          # 主入口脚本
│   ├── config.yaml                # 配置文件
│   ├── requirements.md            # 需求文档
│   └── design.md                  # 设计文档（本文件）
├── common/
│   ├── __init__.py
│   ├── ssh_client.py              # SSH 客户端（复用现有）
│   ├── log_utils.py               # 日志工具（复用现有）
│   ├── env_utils.py               # 环境变量工具（复用现有）
│   └── path_utils.py              # 路径工具（新增）
└── remote_deploy/
    ├── __init__.py
    ├── config_manager.py          # 配置管理器
    ├── deploy_service.py          # 部署服务
    ├── file_uploader.py           # 文件上传器
    └── command_executor.py        # 命令执行器
```

---

## 2. 模块设计

### 2.1 配置管理模块 (ConfigManager)

**职责**:
- 读取和解析 YAML 配置文件
- 验证配置的合法性
- 提供配置查询接口
- 路径展开（`~` 转换为用户主目录）

**主要方法**:
```python
class ConfigManager:
    def __init__(self, config_path: str)
    def load_config(self) -> bool
    def validate_config(self) -> bool
    def get_servers(self) -> List[Dict]
    def get_server_by_name(self, name: str) -> Optional[Dict]
    def expand_path(self, path: str) -> str
```

### 2.2 部署服务模块 (RemoteDeployService)

**职责**:
- 控制整个部署流程
- 管理服务器选择
- 协调文件上传和命令执行
- 输出部署结果摘要

**主要方法**:
```python
class RemoteDeployService:
    def __init__(self, config_manager: ConfigManager)
    @staticmethod
    def deploy(server_name: str, upload_type: str, command_group: str) -> bool
    def _select_server_interactive(self) -> Optional[str]
    def _select_upload_type_interactive(self, server_config: Dict) -> Optional[str]
    def _select_command_group_interactive(self, server_config: Dict) -> Optional[str]
    def _execute_deployment(self, server_config: Dict, upload_type: str, command_group: str) -> bool
    def _show_deployment_summary(self, results: Dict)
```

### 2.3 文件上传模块 (FileUploader)

**职责**:
- 实现 sync 和 copy 两种上传模式
- 显示上传进度
- 处理目录递归上传
- 管理远程目录创建

**主要方法**:
```python
class FileUploader:
    def __init__(self, ssh_client: SSHClient)
    def upload_files(self, upload_configs: List[Dict], mode: str = 'copy') -> bool
    def _upload_single_file(self, local_path: str, remote_path: str) -> bool
    def _upload_directory(self, local_path: str, remote_path: str, mode: str) -> bool
    def _sync_directory(self, local_path: str, remote_path: str, delete_extra: bool) -> bool
    def _copy_directory(self, local_path: str, remote_path: str) -> bool
    def _ensure_remote_directory(self, remote_path: str) -> bool
    def _get_remote_files(self, remote_path: str) -> List[str]
    def _delete_remote_files(self, files: List[str]) -> bool
```

### 2.4 命令执行模块 (CommandExecutor)

**职责**:
- 执行远程命令组
- 捕获命令输出
- 检查命令执行状态
- 处理命令失败情况

**主要方法**:
```python
class CommandExecutor:
    def __init__(self, ssh_client: SSHClient)
    def execute_command_group(self, commands: List[str], group_name: str) -> bool
    def _execute_single_command(self, command: str) -> Tuple[bool, str, int]
    def _handle_command_failure(self, command: str, exit_code: int, output: str)
```

---

## 3. 类设计

### 3.1 ConfigManager 类

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置管理器
负责读取、解析和验证配置文件
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from common.log_utils import log_info, log_warn, log_error

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_path: str):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config: Optional[Dict] = None
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if not os.path.exists(self.config_path):
                log_error(f"配置文件不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            log_info(f"配置文件加载成功: {self.config_path}")
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
        
        if 'servers' not in self.config:
            log_error("配置文件缺少 'servers' 字段")
            return False
        
        servers = self.config['servers']
        if not isinstance(servers, list) or len(servers) == 0:
            log_error("'servers' 必须是非空列表")
            return False
        
        # 验证每个服务器配置
        for idx, server in enumerate(servers):
            if not self._validate_server_config(server, idx):
                return False
        
        log_info("配置验证通过")
        return True
    
    def _validate_server_config(self, server: Dict, idx: int) -> bool:
        """验证单个服务器配置"""
        required_fields = ['name', 'host', 'port', 'username', 'auth']
        
        for field in required_fields:
            if field not in server:
                log_error(f"服务器 #{idx} 缺少必填字段: {field}")
                return False
        
        # 验证认证配置
        auth = server['auth']
        if 'type' not in auth or 'key_path' not in auth:
            log_error(f"服务器 '{server['name']}' 的认证配置不完整")
            return False
        
        return True
    
    def get_servers(self) -> List[Dict]:
        """获取所有服务器配置"""
        return self.config.get('servers', []) if self.config else []
    
    def get_server_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取服务器配置"""
        for server in self.get_servers():
            if server['name'] == name:
                return server
        return None
    
    @staticmethod
    def expand_path(path: str) -> str:
        """
        展开路径（~ 转换为用户主目录）
        
        Args:
            path: 原始路径
            
        Returns:
            str: 展开后的路径
        """
        return os.path.expanduser(path)
```


### 3.2 RemoteDeployService 类

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
远程部署服务
负责控制整个部署流程
"""

import sys
from typing import Optional, Dict, List
from common.ssh_client import SSHClient
from common.log_utils import log_info, log_warn, log_error
from remote_deploy.config_manager import ConfigManager
from remote_deploy.file_uploader import FileUploader
from remote_deploy.command_executor import CommandExecutor

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
    
    @staticmethod
    def deploy(config_path: str = 'config.yaml', 
               server_name: Optional[str] = None,
               upload_type: Optional[str] = None,
               command_group: Optional[str] = None,
               dry_run: bool = False) -> bool:
        """
        部署入口方法
        
        Args:
            config_path: 配置文件路径
            server_name: 服务器名称（可选）
            upload_type: 上传类型（可选）
            command_group: 命令组名称（可选）
            dry_run: 是否模拟执行
            
        Returns:
            bool: 部署是否成功
        """
        # 加载配置
        config_manager = ConfigManager(config_path)
        if not config_manager.load_config():
            return False
        
        # 创建部署服务实例
        service = RemoteDeployService(config_manager)
        
        # 选择服务器（交互式或参数指定）
        if not server_name:
            server_name = service._select_server_interactive()
            if not server_name:
                log_error("未选择服务器")
                return False
        
        server_config = config_manager.get_server_by_name(server_name)
        if not server_config:
            log_error(f"未找到服务器: {server_name}")
            return False
        
        # 选择上传类型
        if not upload_type:
            upload_type = service._select_upload_type_interactive(server_config)
            if not upload_type:
                log_warn("未选择上传类型，跳过文件上传")
        
        # 选择命令组
        if not command_group:
            command_group = service._select_command_group_interactive(server_config)
            if not command_group:
                log_warn("未选择命令组，跳过命令执行")
        
        # 执行部署
        if dry_run:
            log_info("=== 模拟执行模式 ===")
            service._show_dry_run_info(server_config, upload_type, command_group)
            return True
        
        return service._execute_deployment(server_config, upload_type, command_group)
    
    def _select_server_interactive(self) -> Optional[str]:
        """交互式选择服务器"""
        servers = self.config_manager.get_servers()
        
        log_info("=== 可用服务器列表 ===")
        for idx, server in enumerate(servers, 1):
            print(f"{idx}. {server['name']} ({server['host']}:{server['port']})")
        
        try:
            choice = input("\n请选择服务器编号: ").strip()
            idx = int(choice) - 1
            
            if 0 <= idx < len(servers):
                return servers[idx]['name']
            else:
                log_error("无效的选择")
                return None
        except (ValueError, KeyboardInterrupt):
            log_error("选择已取消")
            return None
    
    def _select_upload_type_interactive(self, server_config: Dict) -> Optional[str]:
        """交互式选择上传类型"""
        upload_config = server_config.get('upload', {})
        
        if not upload_config:
            log_warn("该服务器未配置上传任务")
            return None
        
        upload_types = list(upload_config.keys())
        
        log_info("=== 可用上传类型 ===")
        for idx, upload_type in enumerate(upload_types, 1):
            print(f"{idx}. {upload_type}")
        print(f"{len(upload_types) + 1}. 跳过文件上传")
        
        try:
            choice = input("\n请选择上传类型编号: ").strip()
            idx = int(choice) - 1
            
            if idx == len(upload_types):
                return None
            elif 0 <= idx < len(upload_types):
                return upload_types[idx]
            else:
                log_error("无效的选择")
                return None
        except (ValueError, KeyboardInterrupt):
            log_error("选择已取消")
            return None
    
    def _select_command_group_interactive(self, server_config: Dict) -> Optional[str]:
        """交互式选择命令组"""
        commands_config = server_config.get('commands', {})
        
        if not commands_config:
            log_warn("该服务器未配置命令")
            return None
        
        command_groups = list(commands_config.keys())
        
        log_info("=== 可用命令组 ===")
        for idx, group in enumerate(command_groups, 1):
            print(f"{idx}. {group}")
        print(f"{len(command_groups) + 1}. 跳过命令执行")
        
        try:
            choice = input("\n请选择命令组编号: ").strip()
            idx = int(choice) - 1
            
            if idx == len(command_groups):
                return None
            elif 0 <= idx < len(command_groups):
                return command_groups[idx]
            else:
                log_error("无效的选择")
                return None
        except (ValueError, KeyboardInterrupt):
            log_error("选择已取消")
            return None
    
    def _execute_deployment(self, server_config: Dict, 
                           upload_type: Optional[str],
                           command_group: Optional[str]) -> bool:
        """执行部署"""
        log_info("=== 开始部署 ===")
        log_info(f"服务器: {server_config['name']}")
        log_info(f"地址: {server_config['host']}:{server_config['port']}")
        
        # 建立 SSH 连接
        if not self._connect_to_server(server_config):
            return False
        
        results = {
            'upload_success': False,
            'command_success': False,
            'upload_skipped': upload_type is None,
            'command_skipped': command_group is None
        }
        
        try:
            # 上传文件
            if upload_type:
                results['upload_success'] = self._upload_files(server_config, upload_type)
                if not results['upload_success']:
                    log_error("文件上传失败，终止部署")
                    return False
            
            # 执行命令
            if command_group:
                results['command_success'] = self._execute_commands(server_config, command_group)
                if not results['command_success']:
                    log_error("命令执行失败")
                    return False
            
            # 显示部署摘要
            self._show_deployment_summary(server_config, results)
            
            return True
            
        finally:
            # 关闭连接
            if self.ssh_client:
                self.ssh_client.disconnect()
    
    def _connect_to_server(self, server_config: Dict) -> bool:
        """连接到服务器"""
        log_info("正在建立 SSH 连接...")
        
        try:
            # 设置环境变量（复用现有 SSHClient 的逻辑）
            import os
            os.environ['SERVER_IP'] = server_config['host']
            os.environ['SERVER_USER'] = server_config['username']
            
            # 处理认证
            auth_config = server_config['auth']
            if auth_config['type'] == 'ssh_key':
                key_path = self.config_manager.expand_path(auth_config['key_path'])
                if not os.path.exists(key_path):
                    log_error(f"SSH 密钥文件不存在: {key_path}")
                    return False
                # 注意：这里需要根据实际 SSHClient 的实现来设置密钥
                # 当前 SSHClient 使用密码认证，需要扩展支持密钥认证
                log_warn("当前 SSHClient 实现使用密码认证，需要扩展支持密钥认证")
                # 临时方案：假设密码已设置
                os.environ['SSH_PASSWORD'] = os.environ.get('SSH_PASSWORD', '')
            
            self.ssh_client = SSHClient()
            self.file_uploader = FileUploader(self.ssh_client)
            self.command_executor = CommandExecutor(self.ssh_client)
            
            log_info("SSH 连接建立成功")
            return True
            
        except Exception as e:
            log_error(f"连接服务器失败: {e}")
            return False
    
    def _upload_files(self, server_config: Dict, upload_type: str) -> bool:
        """上传文件"""
        log_info(f"=== 开始上传文件 ({upload_type}) ===")
        
        upload_config = server_config.get('upload', {}).get(upload_type, [])
        if not upload_config:
            log_error(f"未找到上传配置: {upload_type}")
            return False
        
        return self.file_uploader.upload_files(upload_config)
    
    def _execute_commands(self, server_config: Dict, command_group: str) -> bool:
        """执行命令"""
        log_info(f"=== 开始执行命令 ({command_group}) ===")
        
        commands = server_config.get('commands', {}).get(command_group, [])
        if not commands:
            log_error(f"未找到命令组: {command_group}")
            return False
        
        return self.command_executor.execute_command_group(commands, command_group)
    
    def _show_deployment_summary(self, server_config: Dict, results: Dict):
        """显示部署摘要"""
        log_info("=== 部署摘要 ===")
        log_info(f"服务器: {server_config['name']}")
        
        if not results['upload_skipped']:
            status = "✓ 成功" if results['upload_success'] else "✗ 失败"
            log_info(f"文件上传: {status}")
        else:
            log_info("文件上传: - 已跳过")
        
        if not results['command_skipped']:
            status = "✓ 成功" if results['command_success'] else "✗ 失败"
            log_info(f"命令执行: {status}")
        else:
            log_info("命令执行: - 已跳过")
    
    def _show_dry_run_info(self, server_config: Dict, 
                          upload_type: Optional[str],
                          command_group: Optional[str]):
        """显示模拟执行信息"""
        log_info(f"服务器: {server_config['name']}")
        log_info(f"地址: {server_config['host']}:{server_config['port']}")
        
        if upload_type:
            log_info(f"上传类型: {upload_type}")
            upload_config = server_config.get('upload', {}).get(upload_type, [])
            for item in upload_config:
                log_info(f"  - {item['local_path']} -> {item['remote_path']}")
        
        if command_group:
            log_info(f"命令组: {command_group}")
            commands = server_config.get('commands', {}).get(command_group, [])
            for cmd in commands:
                log_info(f"  - {cmd}")
```


### 3.3 FileUploader 类

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件上传器
负责文件和目录的上传，支持 sync 和 copy 两种模式
"""

import os
from pathlib import Path
from typing import List, Dict, Set
from common.ssh_client import SSHClient
from common.log_utils import log_info, log_warn, log_error

class FileUploader:
    """文件上传器类"""
    
    def __init__(self, ssh_client: SSHClient):
        """
        初始化文件上传器
        
        Args:
            ssh_client: SSH 客户端实例
        """
        self.ssh_client = ssh_client
    
    def upload_files(self, upload_configs: List[Dict]) -> bool:
        """
        上传文件（支持多个上传配置）
        
        Args:
            upload_configs: 上传配置列表
            
        Returns:
            bool: 上传是否成功
        """
        for config in upload_configs:
            local_path = os.path.expanduser(config['local_path'])
            remote_path = config['remote_path']
            mode = config.get('mode', 'copy')
            delete_extra = config.get('delete_extra', False)
            
            # 检查本地路径是否存在
            if not os.path.exists(local_path):
                log_error(f"本地路径不存在: {local_path}")
                return False
            
            # 确保远程目录存在
            if not self._ensure_remote_directory(remote_path):
                return False
            
            # 判断是文件还是目录
            if os.path.isfile(local_path):
                if not self._upload_single_file(local_path, remote_path):
                    return False
            else:
                if mode == 'sync':
                    if not self._sync_directory(local_path, remote_path, delete_extra):
                        return False
                else:
                    if not self._copy_directory(local_path, remote_path):
                        return False
        
        log_info("所有文件上传成功")
        return True
    
    def _upload_single_file(self, local_path: str, remote_path: str) -> bool:
        """
        上传单个文件
        
        Args:
            local_path: 本地文件路径
            remote_path: 远程路径（可以是目录或文件）
            
        Returns:
            bool: 上传是否成功
        """
        log_info(f"上传文件: {local_path} -> {remote_path}")
        
        # 如果远程路径是目录，则使用本地文件名
        if remote_path.endswith('/'):
            remote_file = remote_path + os.path.basename(local_path)
        else:
            remote_file = remote_path
        
        return self.ssh_client.put(local_path, remote_file)
    
    def _copy_directory(self, local_path: str, remote_path: str) -> bool:
        """
        复制模式上传目录（仅上传本地文件，不删除远程文件）
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            
        Returns:
            bool: 上传是否成功
        """
        log_info(f"复制目录: {local_path} -> {remote_path}")
        
        # 遍历本地目录
        for root, dirs, files in os.walk(local_path):
            # 计算相对路径
            rel_path = os.path.relpath(root, local_path)
            
            # 构建远程目录路径
            if rel_path == '.':
                remote_dir = remote_path
            else:
                remote_dir = os.path.join(remote_path, rel_path).replace('\\', '/')
            
            # 确保远程目录存在
            if not self._ensure_remote_directory(remote_dir):
                return False
            
            # 上传文件
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_dir, file).replace('\\', '/')
                
                if not self.ssh_client.put(local_file, remote_file):
                    log_error(f"上传文件失败: {local_file}")
                    return False
        
        return True
    
    def _sync_directory(self, local_path: str, remote_path: str, delete_extra: bool) -> bool:
        """
        同步模式上传目录（服务器目录完全同步本地目录）
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            delete_extra: 是否删除服务器上多余的文件
            
        Returns:
            bool: 上传是否成功
        """
        log_info(f"同步目录: {local_path} -> {remote_path}")
        
        # 获取本地文件列表
        local_files = self._get_local_files(local_path)
        
        # 获取远程文件列表
        remote_files = self._get_remote_files(remote_path)
        
        # 上传本地文件
        for rel_path in local_files:
            local_file = os.path.join(local_path, rel_path)
            remote_file = os.path.join(remote_path, rel_path).replace('\\', '/')
            
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_file)
            if not self._ensure_remote_directory(remote_dir):
                return False
            
            # 上传文件
            if not self.ssh_client.put(local_file, remote_file):
                log_error(f"上传文件失败: {local_file}")
                return False
        
        # 删除远程多余的文件
        if delete_extra:
            extra_files = remote_files - local_files
            if extra_files:
                log_info(f"删除 {len(extra_files)} 个多余的远程文件")
                if not self._delete_remote_files(remote_path, extra_files):
                    log_warn("删除部分远程文件失败")
        
        return True
    
    def _get_local_files(self, local_path: str) -> Set[str]:
        """
        获取本地文件列表（相对路径）
        
        Args:
            local_path: 本地目录路径
            
        Returns:
            Set[str]: 文件相对路径集合
        """
        files = set()
        for root, dirs, filenames in os.walk(local_path):
            for filename in filenames:
                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, local_path)
                files.add(rel_path.replace('\\', '/'))
        return files
    
    def _get_remote_files(self, remote_path: str) -> Set[str]:
        """
        获取远程文件列表（相对路径）
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            Set[str]: 文件相对路径集合
        """
        files = set()
        
        # 使用 find 命令获取远程文件列表
        cmd = f"find {remote_path} -type f 2>/dev/null || true"
        result = self.ssh_client.run(cmd, hide=True)
        
        if result:
            for line in result.split('\n'):
                line = line.strip()
                if line and line.startswith(remote_path):
                    rel_path = line[len(remote_path):].lstrip('/')
                    files.add(rel_path)
        
        return files
    
    def _delete_remote_files(self, remote_path: str, files: Set[str]) -> bool:
        """
        删除远程文件
        
        Args:
            remote_path: 远程目录路径
            files: 要删除的文件相对路径集合
            
        Returns:
            bool: 删除是否成功
        """
        for file in files:
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            cmd = f"rm -f {remote_file}"
            
            if not self.ssh_client.run(cmd, hide=True):
                log_warn(f"删除远程文件失败: {remote_file}")
                return False
        
        return True
    
    def _ensure_remote_directory(self, remote_path: str) -> bool:
        """
        确保远程目录存在
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            bool: 操作是否成功
        """
        cmd = f"mkdir -p {remote_path}"
        result = self.ssh_client.run(cmd, hide=True)
        
        if not result:
            log_error(f"创建远程目录失败: {remote_path}")
            return False
        
        return True
```

### 3.4 CommandExecutor 类

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
命令执行器
负责在远程服务器上执行命令
"""

from typing import List, Tuple
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
    
    def execute_command_group(self, commands: List[str], group_name: str) -> bool:
        """
        执行命令组
        
        Args:
            commands: 命令列表
            group_name: 命令组名称
            
        Returns:
            bool: 执行是否成功
        """
        log_info(f"执行命令组: {group_name}")
        
        for idx, command in enumerate(commands, 1):
            log_info(f"[{idx}/{len(commands)}] 执行命令: {command}")
            
            success, output, exit_code = self._execute_single_command(command)
            
            if not success:
                self._handle_command_failure(command, exit_code, output)
                return False
            
            # 显示命令输出
            if output:
                print(output)
        
        log_info(f"命令组 '{group_name}' 执行成功")
        return True
    
    def _execute_single_command(self, command: str) -> Tuple[bool, str, int]:
        """
        执行单条命令
        
        Args:
            command: 要执行的命令
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 输出, 退出码)
        """
        try:
            result = self.ssh_client.run(command, hide=False)
            
            if result is None:
                return False, "", -1
            
            # 如果 result 是字符串，说明命令成功
            if isinstance(result, str):
                return True, result, 0
            
            # 如果 result 是 True，说明命令成功但无输出
            if result is True:
                return True, "", 0
            
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
        log_error(f"命令执行失败: {command}")
        log_error(f"退出码: {exit_code}")
        
        if output:
            log_error(f"错误输出:\n{output}")
```

---

## 4. 数据结构设计

### 4.1 配置文件数据结构

```yaml
servers:
  - name: string                    # 服务器名称
    host: string                    # 服务器 IP
    port: int                       # SSH 端口
    username: string                # SSH 用户名
    auth:
      type: string                  # 认证类型 (ssh_key)
      key_path: string              # 密钥路径
    upload:                         # 上传配置（可选）
      <upload_type>:                # 上传类型名称（自定义）
        - local_path: string        # 本地路径
          remote_path: string       # 远程路径
          mode: string              # 上传模式 (sync/copy)
          delete_extra: bool        # 是否删除多余文件
    commands:                       # 命令配置（可选）
      <command_group>:              # 命令组名称（自定义）
        - string                    # 命令列表
```

### 4.2 内部数据结构

```python
# 服务器配置
ServerConfig = {
    'name': str,
    'host': str,
    'port': int,
    'username': str,
    'auth': {
        'type': str,
        'key_path': str
    },
    'upload': {
        str: [  # upload_type
            {
                'local_path': str,
                'remote_path': str,
                'mode': str,
                'delete_extra': bool
            }
        ]
    },
    'commands': {
        str: [str]  # command_group: [commands]
    }
}

# 部署结果
DeploymentResult = {
    'upload_success': bool,
    'command_success': bool,
    'upload_skipped': bool,
    'command_skipped': bool
}
```

---

## 5. 核心流程设计

### 5.1 主流程图

```
开始
  │
  ├─> 解析命令行参数
  │
  ├─> 加载配置文件
  │     ├─> 读取 YAML
  │     ├─> 验证配置
  │     └─> 展开路径
  │
  ├─> 选择服务器
  │     ├─> 命令行参数指定？
  │     │     ├─> 是：使用指定服务器
  │     │     └─> 否：交互式选择
  │     └─> 获取服务器配置
  │
  ├─> 选择上传类型
  │     ├─> 命令行参数指定？
  │     │     ├─> 是：使用指定类型
  │     │     └─> 否：交互式选择
  │     └─> 获取上传配置
  │
  ├─> 选择命令组
  │     ├─> 命令行参数指定？
  │     │     ├─> 是：使用指定命令组
  │     │     └─> 否：交互式选择
  │     └─> 获取命令列表
  │
  ├─> 模拟执行？
  │     ├─> 是：显示执行信息并退出
  │     └─> 否：继续
  │
  ├─> 建立 SSH 连接
  │     ├─> 设置环境变量
  │     ├─> 加载 SSH 密钥
  │     └─> 连接服务器
  │
  ├─> 上传文件（如果选择了上传类型）
  │     ├─> 检查本地路径
  │     ├─> 确保远程目录
  │     ├─> 判断上传模式
  │     │     ├─> sync：同步上传
  │     │     └─> copy：复制上传
  │     └─> 显示上传进度
  │
  ├─> 执行命令（如果选择了命令组）
  │     ├─> 遍历命令列表
  │     ├─> 执行每条命令
  │     ├─> 捕获输出
  │     ├─> 检查退出码
  │     └─> 失败则终止
  │
  ├─> 关闭 SSH 连接
  │
  ├─> 显示部署摘要
  │
结束
```


### 5.2 文件上传流程（sync 模式）

```
开始上传 (sync 模式)
  │
  ├─> 获取本地文件列表
  │     └─> 递归遍历本地目录
  │
  ├─> 获取远程文件列表
  │     └─> 执行 find 命令
  │
  ├─> 比对文件列表
  │     ├─> 本地有，远程无：需要上传
  │     ├─> 本地有，远程有：需要上传（覆盖）
  │     └─> 本地无，远程有：需要删除（如果 delete_extra=true）
  │
  ├─> 上传本地文件
  │     ├─> 遍历本地文件
  │     ├─> 确保远程目录存在
  │     ├─> 上传文件
  │     └─> 显示进度
  │
  ├─> 删除多余文件（如果 delete_extra=true）
  │     ├─> 计算多余文件列表
  │     └─> 执行删除命令
  │
结束上传
```

### 5.3 文件上传流程（copy 模式）

```
开始上传 (copy 模式)
  │
  ├─> 递归遍历本地目录
  │     ├─> 获取所有文件和子目录
  │     └─> 计算相对路径
  │
  ├─> 上传每个文件
  │     ├─> 构建远程路径
  │     ├─> 确保远程目录存在
  │     ├─> 上传文件
  │     └─> 显示进度
  │
结束上传
```

### 5.4 命令执行流程

```
开始执行命令组
  │
  ├─> 遍历命令列表
  │     │
  │     ├─> 执行命令
  │     │     ├─> 调用 SSH 客户端
  │     │     ├─> 捕获标准输出
  │     │     └─> 捕获错误输出
  │     │
  │     ├─> 检查退出码
  │     │     ├─> 退出码 = 0：成功
  │     │     └─> 退出码 ≠ 0：失败
  │     │
  │     ├─> 显示输出
  │     │
  │     └─> 失败处理
  │           ├─> 记录错误日志
  │           └─> 终止后续命令
  │
结束执行
```

---

## 6. 接口设计

### 6.1 命令行接口

```bash
# 基本用法
python remote_deploy.py

# 指定配置文件
python remote_deploy.py -c /path/to/config.yaml

# 指定服务器
python remote_deploy.py -s "领航不良资产"

# 指定上传类型
python remote_deploy.py -s "领航不良资产" -u frontend_admin

# 指定命令组
python remote_deploy.py -s "领航不良资产" -g backend_api_server

# 完整参数
python remote_deploy.py -c config.yaml -s "领航不良资产" -u frontend_admin -g backend_api_server

# 模拟执行
python remote_deploy.py -s "领航不良资产" -u frontend_admin -d

# 显示帮助
python remote_deploy.py -h
```

### 6.2 Python API 接口

```python
from remote_deploy.deploy_service import RemoteDeployService

# 方式 1：使用静态方法
success = RemoteDeployService.deploy(
    config_path='config.yaml',
    server_name='领航不良资产',
    upload_type='frontend_admin',
    command_group='backend_api_server',
    dry_run=False
)

# 方式 2：使用实例方法
from remote_deploy.config_manager import ConfigManager

config_manager = ConfigManager('config.yaml')
config_manager.load_config()

service = RemoteDeployService(config_manager)
# ... 调用实例方法
```

---

## 7. 错误处理设计

### 7.1 错误分类

| 错误类型 | 错误码 | 处理策略 |
|---------|--------|---------|
| 配置文件不存在 | 1001 | 输出错误日志，退出程序 |
| 配置文件格式错误 | 1002 | 输出错误日志，退出程序 |
| 配置验证失败 | 1003 | 输出错误日志，退出程序 |
| SSH 连接失败 | 2001 | 输出错误日志，跳过该服务器 |
| SSH 认证失败 | 2002 | 输出错误日志，跳过该服务器 |
| 本地文件不存在 | 3001 | 输出错误日志，跳过该文件 |
| 远程目录创建失败 | 3002 | 输出错误日志，终止上传 |
| 文件上传失败 | 3003 | 输出错误日志，终止上传 |
| 命令执行失败 | 4001 | 输出错误日志，终止后续命令 |
| 用户取消操作 | 5001 | 输出提示信息，退出程序 |

### 7.2 异常处理策略

```python
# 配置加载异常
try:
    config_manager.load_config()
except FileNotFoundError:
    log_error("配置文件不存在")
    sys.exit(1)
except yaml.YAMLError as e:
    log_error(f"配置文件格式错误: {e}")
    sys.exit(1)

# SSH 连接异常
try:
    ssh_client = SSHClient()
except ConnectionError as e:
    log_error(f"SSH 连接失败: {e}")
    return False
except AuthenticationError as e:
    log_error(f"SSH 认证失败: {e}")
    return False

# 文件上传异常
try:
    ssh_client.put(local_path, remote_path)
except FileNotFoundError:
    log_error(f"本地文件不存在: {local_path}")
    return False
except PermissionError:
    log_error(f"远程目录无权限: {remote_path}")
    return False

# 命令执行异常
try:
    result = ssh_client.run(command)
    if result is None or exit_code != 0:
        log_error(f"命令执行失败: {command}")
        return False
except Exception as e:
    log_error(f"命令执行异常: {e}")
    return False
```

---

## 8. 日志设计

### 8.1 日志级别定义

```python
# 日志级别
LOG_LEVEL_INFO = "INFO"     # 正常流程信息
LOG_LEVEL_WARN = "WARN"     # 警告信息
LOG_LEVEL_ERROR = "ERROR"   # 错误信息

# 日志颜色
LOG_COLOR_INFO = "\033[32m"   # 绿色
LOG_COLOR_WARN = "\033[33m"   # 黄色
LOG_COLOR_ERROR = "\033[31m"  # 红色
LOG_COLOR_RESET = "\033[0m"   # 重置
```

### 8.2 日志格式

```python
# 日志格式
def log_info(message: str):
    print(f"{LOG_COLOR_INFO}[INFO]{LOG_COLOR_RESET} {message}")

def log_warn(message: str):
    print(f"{LOG_COLOR_WARN}[WARN]{LOG_COLOR_RESET} {message}")

def log_error(message: str):
    print(f"{LOG_COLOR_ERROR}[ERROR]{LOG_COLOR_RESET} {message}")
```

### 8.3 日志内容示例

```
[INFO] 配置文件加载成功: config.yaml
[INFO] 配置验证通过
[INFO] === 可用服务器列表 ===
[INFO] 正在建立 SSH 连接...
[INFO] SSH 连接建立成功
[INFO] === 开始上传文件 (frontend_admin) ===
[INFO] 上传文件: /path/to/local/file -> /path/to/remote/file
[INFO] 所有文件上传成功
[INFO] === 开始执行命令 (backend_api_server) ===
[INFO] [1/2] 执行命令: cd /home/admin/web_projects/dccw/server-api/bin
[INFO] [2/2] 执行命令: sh startup1.sh
[INFO] 命令组 'backend_api_server' 执行成功
[INFO] === 部署摘要 ===
[INFO] 服务器: 领航不良资产
[INFO] 文件上传: ✓ 成功
[INFO] 命令执行: ✓ 成功
```

---

## 9. 配置管理设计

### 9.1 配置文件位置

```
默认配置文件位置：
1. 当前目录下的 config.yaml
2. 脚本所在目录下的 config.yaml
3. 用户主目录下的 .remote_deploy/config.yaml

优先级：命令行参数 > 当前目录 > 脚本目录 > 用户主目录
```

### 9.2 配置验证规则

```python
# 必填字段验证
REQUIRED_SERVER_FIELDS = ['name', 'host', 'port', 'username', 'auth']
REQUIRED_AUTH_FIELDS = ['type', 'key_path']

# 字段类型验证
FIELD_TYPES = {
    'name': str,
    'host': str,
    'port': int,
    'username': str,
    'auth': dict,
    'upload': dict,
    'commands': dict
}

# 字段值验证
def validate_port(port: int) -> bool:
    return 1 <= port <= 65535

def validate_auth_type(auth_type: str) -> bool:
    return auth_type in ['ssh_key', 'password']

def validate_upload_mode(mode: str) -> bool:
    return mode in ['sync', 'copy']
```

### 9.3 配置示例

```yaml
servers:
  # 示例服务器 1
  - name: 领航不良资产
    host: 192.168.1.10
    port: 5555
    username: deploy
    auth:
      type: ssh_key
      key_path: ~/.ssh/id_rsa
    upload:
      frontend_admin:
        - local_path: ~/workspace/ling_hang/ling_hang_admin/dist-prod/
          remote_path: /home/admin/web_projects/dccw/server-backui/
          mode: sync
          delete_extra: true
      backend_api_server:
        - local_path: ~/workspace/ling_hang/ling_hang_server/yudao-server/target/yudao-server.jar
          remote_path: /home/admin/web_projects/dccw/server-api/
        - local_path: ~/workspace/ling_hang/ling_hang_server/script/shell/startup1.sh
          remote_path: /home/admin/web_projects/dccw/server-api/bin
    commands:
      backend_api_server:
        - cd /home/admin/web_projects/dccw/server-api/bin
        - sh startup1.sh
```

---

## 10. 文件上传策略设计

### 10.1 sync 模式详细设计

**目标**: 使远程目录完全同步本地目录

**步骤**:
1. 获取本地文件列表（递归遍历）
2. 获取远程文件列表（使用 `find` 命令）
3. 比对文件列表，计算差异
4. 上传本地新增或修改的文件
5. 删除远程多余的文件（如果 `delete_extra=true`）

**优点**:
- 确保远程目录与本地完全一致
- 自动清理过期文件

**缺点**:
- 需要额外的文件列表比对
- 可能误删重要文件（需谨慎使用 `delete_extra`）

**适用场景**:
- 前端静态资源部署
- 需要清理旧版本文件的场景

### 10.2 copy 模式详细设计

**目标**: 仅上传本地文件，不删除远程文件

**步骤**:
1. 递归遍历本地目录
2. 逐个上传文件到远程目录
3. 保留远程已存在的其他文件

**优点**:
- 简单快速
- 不会误删文件

**缺点**:
- 远程目录可能积累过期文件

**适用场景**:
- 后端 JAR 包部署
- 配置文件上传
- 不需要清理旧文件的场景

### 10.3 上传优化策略

```python
# 1. 文件大小检查（跳过空文件）
if os.path.getsize(local_path) == 0:
    log_warn(f"跳过空文件: {local_path}")
    continue

# 2. 文件修改时间比对（可选）
local_mtime = os.path.getmtime(local_path)
remote_mtime = get_remote_mtime(remote_path)
if local_mtime <= remote_mtime:
    log_info(f"文件未修改，跳过: {local_path}")
    continue

# 3. 文件哈希比对（可选，更精确但更慢）
local_hash = calculate_file_hash(local_path)
remote_hash = get_remote_file_hash(remote_path)
if local_hash == remote_hash:
    log_info(f"文件内容相同，跳过: {local_path}")
    continue

# 4. 批量上传（使用 put_multiple）
file_list = [(local1, remote1), (local2, remote2), ...]
ssh_client.put_multiple(file_list)
```

---

## 11. 安全性设计

### 11.1 SSH 密钥管理

```python
# 1. 密钥文件权限检查
def check_key_permission(key_path: str) -> bool:
    stat_info = os.stat(key_path)
    mode = stat_info.st_mode & 0o777
    
    if mode != 0o600:
        log_warn(f"SSH 密钥文件权限不安全: {oct(mode)}")
        log_warn(f"建议执行: chmod 600 {key_path}")
        return False
    
    return True

# 2. 密钥文件存在性检查
def check_key_exists(key_path: str) -> bool:
    if not os.path.exists(key_path):
        log_error(f"SSH 密钥文件不存在: {key_path}")
        return False
    return True
```

### 11.2 敏感信息保护

```python
# 1. 不在日志中输出密码
def log_connection_info(host: str, username: str):
    log_info(f"连接服务器: {username}@{host}")
    # 不输出密码或密钥内容

# 2. 配置文件权限检查
def check_config_permission(config_path: str):
    stat_info = os.stat(config_path)
    mode = stat_info.st_mode & 0o777
    
    if mode & 0o004:  # 其他用户可读
        log_warn(f"配置文件权限过于宽松: {oct(mode)}")
        log_warn(f"建议执行: chmod 600 {config_path}")
```

### 11.3 命令注入防护

```python
# 1. 路径参数转义
import shlex

def escape_path(path: str) -> str:
    return shlex.quote(path)

# 使用示例
remote_path = escape_path(user_input_path)
cmd = f"mkdir -p {remote_path}"

# 2. 命令参数验证
def validate_command(command: str) -> bool:
    # 禁止危险命令
    dangerous_patterns = [
        r'rm\s+-rf\s+/',  # 删除根目录
        r':\(\)\{.*\};:',  # fork 炸弹
        r'dd\s+if=/dev/zero',  # 磁盘填充
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, command):
            log_error(f"检测到危险命令: {command}")
            return False
    
    return True
```

---

## 12. 性能优化设计

### 12.1 并发上传

```python
# 使用线程池并发上传多个文件
from concurrent.futures import ThreadPoolExecutor

def upload_files_concurrent(file_list: List[Tuple[str, str]], max_workers: int = 4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for local_path, remote_path in file_list:
            future = executor.submit(ssh_client.put, local_path, remote_path)
            futures.append(future)
        
        # 等待所有上传完成
        for future in futures:
            future.result()
```

### 12.2 断点续传（可选）

```python
# 记录上传进度
def upload_with_resume(local_path: str, remote_path: str):
    # 获取远程文件大小
    remote_size = get_remote_file_size(remote_path)
    local_size = os.path.getsize(local_path)
    
    if remote_size > 0 and remote_size < local_size:
        # 从断点处继续上传
        log_info(f"从 {remote_size} 字节处继续上传")
        upload_from_offset(local_path, remote_path, remote_size)
    else:
        # 全新上传
        ssh_client.put(local_path, remote_path)
```

### 12.3 压缩传输（可选）

```python
# 压缩后上传，远程解压
def upload_with_compression(local_dir: str, remote_dir: str):
    # 本地压缩
    tar_file = f"{local_dir}.tar.gz"
    os.system(f"tar -czf {tar_file} -C {os.path.dirname(local_dir)} {os.path.basename(local_dir)}")
    
    # 上传压缩包
    ssh_client.put(tar_file, f"{remote_dir}.tar.gz")
    
    # 远程解压
    ssh_client.run(f"tar -xzf {remote_dir}.tar.gz -C {os.path.dirname(remote_dir)}")
    
    # 清理压缩包
    os.remove(tar_file)
    ssh_client.run(f"rm -f {remote_dir}.tar.gz")
```

---

## 13. 测试设计

### 13.1 单元测试

```python
# test_config_manager.py
def test_load_config():
    config_manager = ConfigManager('test_config.yaml')
    assert config_manager.load_config() == True

def test_validate_config():
    config_manager = ConfigManager('invalid_config.yaml')
    assert config_manager.validate_config() == False

def test_get_server_by_name():
    config_manager = ConfigManager('test_config.yaml')
    config_manager.load_config()
    server = config_manager.get_server_by_name('test_server')
    assert server is not None
    assert server['host'] == '192.168.1.10'
```

### 13.2 集成测试

```python
# test_deploy_service.py
def test_full_deployment():
    # 准备测试环境
    setup_test_server()
    
    # 执行部署
    success = RemoteDeployService.deploy(
        config_path='test_config.yaml',
        server_name='test_server',
        upload_type='test_upload',
        command_group='test_commands'
    )
    
    # 验证结果
    assert success == True
    assert check_remote_files_exist()
    assert check_command_executed()
    
    # 清理测试环境
    cleanup_test_server()
```

---

## 14. 部署与维护

### 14.1 依赖安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 14.2 requirements.txt

```
paramiko>=2.11.0
fabric>=2.7.0
PyYAML>=6.0
rich>=12.0.0
scp>=0.14.0
```

### 14.3 使用文档

```markdown
# 远程部署工具使用指南

## 快速开始

1. 配置服务器信息（编辑 config.yaml）
2. 运行部署脚本：`python remote_deploy.py`
3. 按提示选择服务器、上传类型和命令组

## 常见问题

Q: SSH 连接失败怎么办？
A: 检查服务器 IP、端口、用户名和密钥文件是否正确

Q: 文件上传失败怎么办？
A: 检查本地文件是否存在，远程目录是否有写权限

Q: 命令执行失败怎么办？
A: 检查命令是否正确，远程环境是否满足要求
```

---

## 15. 总结

本设计文档详细描述了远程服务器管理与自动化部署脚本的架构、模块、类、数据结构、流程、接口、错误处理、日志、配置管理、文件上传策略、安全性、性能优化和测试等方面的设计。

### 15.1 设计亮点

1. **模块化设计**: 清晰的模块划分，职责明确
2. **灵活的配置**: 支持多服务器、多上传类型、多命令组
3. **两种上传模式**: sync 和 copy 满足不同场景需求
4. **完善的错误处理**: 分类明确，处理策略清晰
5. **友好的用户界面**: 支持交互式和命令行参数两种方式
6. **安全性考虑**: SSH 密钥管理、敏感信息保护、命令注入防护
7. **性能优化**: 并发上传、断点续传、压缩传输（可选）

### 15.2 后续优化方向

1. 支持密码认证
2. 支持并行执行多台服务器
3. 支持文件备份和回滚
4. 提供 Web 界面
5. 添加部署历史记录
6. 支持部署通知（邮件、钉钉、企业微信等）

---

**文档结束**
