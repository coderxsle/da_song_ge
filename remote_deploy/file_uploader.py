#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文件上传器
负责文件和目录的上传，支持 sync 和 copy 两种模式
"""

import os
from pathlib import Path
from typing import List, Dict, Set, Any
from common.ssh_client import SSHClient
from common.log_utils import log_info, log_warn, log_error
from common.path_utils import expand_path, validate_path, get_relative_path, normalize_path


class FileUploader:
    """文件上传器类"""
    
    def __init__(self, ssh_client: SSHClient):
        """
        初始化文件上传器
        
        Args:
            ssh_client: SSH 客户端实例
        """
        self.ssh_client = ssh_client
    
    def upload_files(self, upload_configs: List[Dict[str, Any]]) -> bool:
        """
        上传文件（支持多个上传配置）
        
        Args:
            upload_configs: 上传配置列表
            
        Returns:
            bool: 上传是否成功
        """
        if not upload_configs:
            log_warn("没有需要上传的文件")
            return True
        
        # 第一步：收集所有需要上传的文件
        all_files_to_upload = []
        directory_tasks = []  # 需要特殊处理的目录任务（sync 模式）
        
        for idx, config in enumerate(upload_configs, 1):
            log_info(f"[{idx}/{len(upload_configs)}] 分析上传任务...")
            
            local_path = expand_path(config['local_path'])
            remote_path = config['remote_path']
            mode = config.get('mode', 'copy')
            delete_extra = config.get('delete_extra', False)
            
            # 检查本地路径是否存在
            if not os.path.exists(local_path):
                log_error(f"本地路径不存在: {local_path}")
                return False
            
            # 确保远程目录存在
            if os.path.isfile(local_path):
                # 如果是文件，远程目录是 remote_path 的父目录（除非 remote_path 以 / 结尾）
                if remote_path.endswith('/'):
                    remote_dir = remote_path.rstrip('/')
                else:
                    remote_dir = os.path.dirname(remote_path)
            else:
                # 如果是目录，remote_path 本身就是目标目录
                remote_dir = remote_path.rstrip('/')
            
            if remote_dir and not self._ensure_remote_directory(remote_dir):
                return False
            
            # 判断是文件还是目录
            if os.path.isfile(local_path):
                # 单个文件：直接添加到上传列表
                if remote_path.endswith('/'):
                    remote_file = remote_path + os.path.basename(local_path)
                else:
                    remote_file = remote_path
                all_files_to_upload.append((local_path, remote_file))
                
            else:
                # 目录：收集目录中的所有文件
                if mode == 'sync':
                    # sync 模式需要特殊处理（删除多余文件）
                    directory_tasks.append({
                        'local_path': local_path,
                        'remote_path': remote_path,
                        'delete_extra': delete_extra
                    })
                
                # 收集目录中的所有文件
                files_in_dir = self._collect_directory_files(local_path, remote_path)
                all_files_to_upload.extend(files_in_dir)
        
        # 第二步：批量上传所有文件（带进度条）
        if all_files_to_upload:
            log_info(f"共收集到 {len(all_files_to_upload)} 个文件")
            if not self._upload_multiple_with_progress(all_files_to_upload):
                log_error("批量上传文件失败")
                return False
        else:
            log_warn("没有文件需要上传")
        
        # 第三步：处理 sync 模式的目录（删除多余文件）
        for task in directory_tasks:
            if task['delete_extra']:
                log_info(f"处理 sync 模式: {task['local_path']}")
                if not self._handle_sync_delete(task['local_path'], task['remote_path']):
                    log_warn("删除部分远程文件失败，但不影响部署")
        
        log_info("所有文件上传成功")
        return True
    
    def _collect_directory_files(self, local_path: str, remote_path: str) -> List[tuple]:
        """
        收集目录中的所有文件
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            
        Returns:
            List[tuple]: 文件列表，每个元素是 (本地路径, 远程路径) 元组
        """
        files_to_upload = []
        
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
                continue
            
            # 收集文件
            for file in files:
                local_file = os.path.join(root, file)
                remote_file = os.path.join(remote_dir, file).replace('\\', '/')
                files_to_upload.append((local_file, remote_file))
        
        return files_to_upload
    
    def _handle_sync_delete(self, local_path: str, remote_path: str) -> bool:
        """
        处理 sync 模式的删除操作
        
        Args:
            local_path: 本地目录路径
            remote_path: 远程目录路径
            
        Returns:
            bool: 删除是否成功
        """
        log_warn("启用 delete_extra，将删除服务器上多余的文件")
        
        # 获取本地文件列表
        log_info("扫描本地文件...")
        local_files = self._get_local_files(local_path)
        log_info(f"本地文件数量: {len(local_files)}")
        
        # 获取远程文件列表
        log_info("扫描远程文件...")
        remote_files = self._get_remote_files(remote_path)
        log_info(f"远程文件数量: {len(remote_files)}")
        
        # 删除远程多余的文件
        extra_files = remote_files - local_files
        if extra_files:
            log_info(f"发现 {len(extra_files)} 个多余的远程文件")
            if not self._delete_remote_files(remote_path, extra_files):
                return False
        else:
            log_info("没有多余的远程文件需要删除")
        
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
        log_info(f"上传文件: {local_path}")
        log_info(f"目标路径: {remote_path}")
        
        # 如果远程路径是目录（以 / 结尾），则使用本地文件名
        if remote_path.endswith('/'):
            remote_file = remote_path + os.path.basename(local_path)
        else:
            remote_file = remote_path
        
        # 使用 SSH 客户端上传文件（不带进度条）
        result = self.ssh_client.put(local_path, remote_file)
        
        if not result:
            log_error(f"文件上传失败: {local_path}")
            return False
        
        log_info(f"文件上传成功: {os.path.basename(local_path)}")
        return True
    
    def _upload_multiple_with_progress(self, file_list: List[tuple]) -> bool:
        """
        批量上传文件并显示进度条（并行上传，所有进度条同时显示和更新）
        
        Args:
            file_list: 文件列表，每个元素是 (本地路径, 远程路径) 元组
            
        Returns:
            bool: 上传是否成功
        """
        import time
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, FileSizeColumn, TransferSpeedColumn, TimeRemainingColumn
        from rich.console import Console
        
        console = Console()
        
        # 检查所有文件是否存在并获取文件大小
        files_info = []
        for local_path, remote_path in file_list:
            if not os.path.exists(local_path):
                log_error(f"文件不存在: {local_path}")
                return False
            
            file_size = os.path.getsize(local_path)
            file_name = os.path.basename(local_path)
            files_info.append((local_path, remote_path, file_name, file_size))
        
        log_info(f"准备并行上传 {len(files_info)} 个文件...")
        
        # 使用 Rich 进度条显示上传进度
        with Progress(
            TextColumn("[bold blue]{task.description:<30}"),
            BarColumn(complete_style="green"),
            FileSizeColumn(),
            TransferSpeedColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            # 第一步：先创建所有任务（所有进度条同时显示）
            tasks = {}
            for local_path, remote_path, file_name, file_size in files_info:
                task_id = progress.add_task(f"上传 {file_name}...", total=file_size)
                tasks[file_name] = task_id
            
            # 用于存储上传结果
            upload_results = {}
            upload_lock = threading.Lock()
            
            # 上传单个文件的函数
            def upload_file(local_path, remote_path, file_name, file_size):
                task_id = tasks[file_name]
                last_update_time = [time.time()]
                
                # 进度回调函数
                def progress_callback(filename, size, sent):
                    current_time = time.time()
                    elapsed = current_time - last_update_time[0]
                    
                    if elapsed > 0.1:  # 每0.1秒更新一次
                        progress.update(task_id, completed=sent)
                        last_update_time[0] = current_time
                    else:
                        progress.update(task_id, completed=sent)
                
                try:
                    # 使用 SSH 客户端上传文件（带进度回调）
                    result = self.ssh_client.put(local_path, remote_path, progress_callback)
                    
                    # 确保进度条完成
                    progress.update(task_id, completed=file_size)
                    
                    with upload_lock:
                        upload_results[file_name] = result
                    
                    return result
                except Exception as e:
                    log_error(f"文件上传异常: {file_name}, 错误: {e}")
                    with upload_lock:
                        upload_results[file_name] = False
                    return False
            
            # 第二步：使用线程池并行上传所有文件
            max_workers = min(len(files_info), 4)  # 最多4个并发上传
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # 提交所有上传任务
                futures = []
                for local_path, remote_path, file_name, file_size in files_info:
                    future = executor.submit(upload_file, local_path, remote_path, file_name, file_size)
                    futures.append(future)
                
                # 等待所有任务完成
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        log_error(f"上传任务异常: {e}")
            
            # 检查所有文件是否上传成功
            for file_name, result in upload_results.items():
                if not result:
                    log_error(f"文件上传失败: {file_name}")
                    return False
        
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
                # 统一使用正斜杠
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
        # 添加 2>/dev/null 忽略错误，|| true 确保命令总是成功
        cmd = f"find {remote_path} -type f 2>/dev/null || true"
        result = self.ssh_client.run(cmd, hide=True)
        
        if result:
            for line in result.split('\n'):
                line = line.strip()
                if line and line.startswith(remote_path):
                    # 计算相对路径
                    rel_path = line[len(remote_path):].lstrip('/')
                    if rel_path:
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
        log_info(f"删除 {len(files)} 个多余的远程文件...")
        
        success = True
        for file in files:
            remote_file = os.path.join(remote_path, file).replace('\\', '/')
            cmd = f"rm -f '{remote_file}'"
            
            if not self.ssh_client.run(cmd, hide=True):
                log_warn(f"删除远程文件失败: {remote_file}")
                success = False
        
        if success:
            log_info("所有多余文件删除成功")
        
        return success
    
    def _ensure_remote_directory(self, remote_path: str) -> bool:
        """
        确保远程目录存在
        
        Args:
            remote_path: 远程目录路径
            
        Returns:
            bool: 操作是否成功
        """
        if not remote_path or remote_path == '/':
            return True
        
        # 先检查路径是否已存在且是目录
        is_dir_cmd = f"[ -d '{remote_path}' ] && echo 'is_dir' || echo 'not_dir'"
        is_dir_result = self.ssh_client.run(is_dir_cmd, hide=True)
        
        # 确保返回值是字符串
        is_dir_str = str(is_dir_result) if is_dir_result else ''
        
        if 'is_dir' in is_dir_str:
            # 已经是目录，直接返回成功
            return True
        
        # 检查路径是否存在但不是目录（可能是文件）
        exists_cmd = f"[ -e '{remote_path}' ] && echo 'exists' || echo 'not_exists'"
        exists_result = self.ssh_client.run(exists_cmd, hide=True)
        
        # 确保返回值是字符串
        exists_str = str(exists_result) if exists_result else ''
        
        if 'exists' in exists_str and 'not_exists' not in exists_str:
            # 存在但不是目录，获取详细信息
            ls_cmd = f"ls -la '{remote_path}' 2>&1"
            ls_result = self.ssh_client.run(ls_cmd, hide=False)
            
            log_error(f"路径 '{remote_path}' 已存在但不是目录，无法创建")
            log_error(f"请在服务器上删除该文件: rm -f '{remote_path}'")
            log_error(f"或者修改配置文件中的 remote_path")
            return False
        
        # 路径不存在，创建目录（包括父目录）
        log_info(f"创建远程目录: {remote_path}")
        cmd = f"mkdir -p '{remote_path}'"
        result = self.ssh_client.run(cmd, hide=True)
        
        # 验证目录是否创建成功
        verify_cmd = f"[ -d '{remote_path}' ] && echo 'created' || echo 'failed'"
        verify_result = self.ssh_client.run(verify_cmd, hide=True)
        verify_str = str(verify_result) if verify_result else ''
        
        if 'created' in verify_str:
            return True
        else:
            log_error(f"创建远程目录失败: {remote_path}")
            return False

