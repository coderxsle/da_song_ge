#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SSH 客户端模块
提供 SSH 连接和操作的基础功能。
"""

import os
import time
from typing import Optional, Any, Callable, List, Dict, Tuple
from fabric import Connection
from rich.progress import Progress, TaskID, BarColumn, TimeElapsedColumn, SpinnerColumn, TextColumn, DownloadColumn
import paramiko
from scp import SCPClient
import concurrent.futures
from .env_utils import EnvUtils
from .log_utils import log_info, log_error

class SSHClient:
    """SSH 客户端类，提供连接和命令执行功能"""
    
    _instance = None  # 类变量，用于存储单例实例

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(SSHClient, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'conn'):  # 确保只初始化一次
            self.conn: Optional[Connection] = None

    def disconnect(self):
        """关闭远程连接"""
        if self.conn:
            self.conn.close()
            log_info("远程连接已关闭")
            self.conn = None

    def run(self, command: str, hide: bool = False) -> Any:
        """
        执行 SSH 命令
        参数:
            command: 要执行的命令
            hide: 是否隐藏输出
        返回:
            命令执行结果
        """
        if not self.__check_connection():
            return None
        try:
            # print(f"执行命令: {command}")
            result = self.conn.run(command, hide=hide)
            return result.stdout.strip() if result.stdout else True
        except Exception as e:
            log_error(f"执行命令失败: {e}")
            return None


    def local_run(self, command: str, hide: bool = False) -> Any:
        """
        在本地执行命令
        参数:
            command: 要执行的命令
            hide: 是否隐藏输出
        返回:
            命令执行结果
        """
        try:
            # print(f"在本地执行命令: {command}")
            # 创建一个新的连接实例，指向 localhost
            local_conn = Connection("localhost")
            result = local_conn.local(command, hide=hide, pty=True)  # 使用 Fabric 的 run 方法
            
            return result.stdout.strip() if result.stdout else True
            
        except Exception as e:
            log_error(f"本地命令执行失败: {e}")
            return None
        

       
    
    def put(self, local_path: str, remote_path: str, progress_callback: Optional[Callable] = None) -> bool:
        """
        上传单个文件（底层传输方法）
        
        参数:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            progress_callback: 进度回调函数 (filename, size, sent)
            
        返回:
            上传是否成功
        """
        if not self.__check_connection():
            return False
            
        try:
            # 如果没有进度回调，使用简单的 fabric put
            if progress_callback is None:
                self.conn.put(local_path, remote_path)
                return True
            
            # 如果有进度回调，使用 fabric 的底层 paramiko 连接
            # 复用已有的连接，避免重新建立连接
            try:
                # 从 fabric 的 Connection 对象获取底层的 paramiko 连接
                transport = self.conn.client.get_transport()
                
                # 使用 SCP 上传文件（复用连接）
                with SCPClient(transport, progress=progress_callback) as scp:
                    scp.put(local_path, remote_path)
                
                return True
            except Exception as e:
                log_error(f"使用已有连接上传失败: {e}")
                return False
            
        except Exception as e:
            log_error(f"文件传输失败: {e}")
            return False
    



    def __create_connection(self) -> Optional[Connection]:
        """创建 SSH 连接"""
        try:
            server_ip = EnvUtils.get('SERVER_IP')
            server_port = EnvUtils.get('SERVER_PORT')  # 新增：获取端口
            server_user = EnvUtils.get('SERVER_USER')
            ssh_password = EnvUtils.get('SSH_PASSWORD')
            ssh_key_path = EnvUtils.get('SSH_KEY_PATH')  # 新增：SSH 密钥路径

            if not all([server_ip, server_user]):
                log_error("缺少必要的连接信息")
                return None
            
            # 端口默认为 22
            port = int(server_port) if server_port else 22

            # 创建连接配置
            connect_kwargs = {
                "banner_timeout": 60,
                "timeout": 30,
            }
            
            # 优先使用 SSH 密钥认证，失败后尝试密码认证
            connection_established = False
            
            if ssh_key_path and os.path.exists(ssh_key_path):
                try:
                    log_info(f"尝试使用 SSH 密钥认证: {ssh_key_path}")
                    key_kwargs = connect_kwargs.copy()
                    key_kwargs["key_filename"] = ssh_key_path
                    # 如果有密码，作为密钥的 passphrase
                    if ssh_password:
                        key_kwargs["passphrase"] = ssh_password
                    
                    # 创建链接
                    log_info(f"正在创建与服务器 {server_ip}:{port} 的链接...")
                    self.conn = Connection(
                        host=server_ip,
                        port=port,
                        user=server_user,
                        connect_kwargs=key_kwargs
                    )
                    
                    # 测试连接
                    self.conn.run("echo 'Connection test'", hide=True)
                    log_info("SSH 密钥认证成功，远程连接建立成功")
                    connection_established = True
                    return self.conn
                    
                except Exception as key_error:
                    log_error(f"SSH 密钥认证失败: {key_error}")
                    self.conn = None
                    # 如果有密码，尝试密码认证
                    if ssh_password:
                        log_info("尝试使用密码认证...")
            
            # 如果密钥认证失败或没有密钥，尝试密码认证
            if not connection_established and ssh_password:
                try:
                    log_info("使用密码认证")
                    pwd_kwargs = connect_kwargs.copy()
                    pwd_kwargs["password"] = ssh_password
                    
                    # 创建链接
                    log_info(f"正在创建与服务器 {server_ip}:{port} 的链接...")
                    self.conn = Connection(
                        host=server_ip,
                        port=port,
                        user=server_user,
                        connect_kwargs=pwd_kwargs
                    )
                    
                    # 测试连接
                    self.conn.run("echo 'Connection test'", hide=True)
                    log_info("密码认证成功，远程连接建立成功")
                    connection_established = True
                    return self.conn
                    
                except Exception as pwd_error:
                    log_error(f"密码认证失败: {pwd_error}")
                    self.conn = None
            
            if not connection_established:
                log_error("所有认证方式均失败，缺少有效的认证信息（SSH 密钥或密码）")
                return None

        except Exception as e:
            log_error(f"建立连接失败: {str(e)}")
            return None


    def __check_connection(self) -> bool:
        """检查连接是否有效"""
        if self.conn is None:
            return self.__create_connection() is not None
        try:
            self.conn.run("echo 'Connection test'", hide=True)
            return True
        except Exception:
            log_error("连接已断开，重新建立连接")
            return self.__create_connection() is not None



