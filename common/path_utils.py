#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
路径工具模块
提供路径处理、验证等功能
"""

import os
from pathlib import Path
from typing import Optional


def expand_path(path: str) -> str:
    """
    展开路径（~ 转换为用户主目录）
    
    Args:
        path: 原始路径
        
    Returns:
        str: 展开后的绝对路径
        
    Examples:
        >>> expand_path('~/workspace/project')
        '/Users/username/workspace/project'
    """
    # 展开用户主目录
    expanded = os.path.expanduser(path)
    # 展开环境变量
    expanded = os.path.expandvars(expanded)
    # 转换为绝对路径
    return os.path.abspath(expanded)


def validate_path(path: str, must_exist: bool = True, must_be_file: bool = False, 
                  must_be_dir: bool = False) -> bool:
    """
    验证路径是否有效
    
    Args:
        path: 要验证的路径
        must_exist: 路径必须存在
        must_be_file: 路径必须是文件
        must_be_dir: 路径必须是目录
        
    Returns:
        bool: 路径是否有效
        
    Examples:
        >>> validate_path('/path/to/file.txt', must_exist=True, must_be_file=True)
        True
    """
    if not path:
        return False
    
    expanded_path = expand_path(path)
    
    # 检查是否存在
    if must_exist and not os.path.exists(expanded_path):
        return False
    
    # 检查是否为文件
    if must_be_file and not os.path.isfile(expanded_path):
        return False
    
    # 检查是否为目录
    if must_be_dir and not os.path.isdir(expanded_path):
        return False
    
    return True


def ensure_directory(path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        path: 目录路径
        
    Returns:
        bool: 操作是否成功
        
    Examples:
        >>> ensure_directory('/path/to/new/directory')
        True
    """
    try:
        expanded_path = expand_path(path)
        Path(expanded_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        from .log_utils import log_error
        log_error(f"创建目录失败: {e}")
        return False


def get_file_size(path: str) -> Optional[int]:
    """
    获取文件大小（字节）
    
    Args:
        path: 文件路径
        
    Returns:
        Optional[int]: 文件大小，如果文件不存在则返回 None
        
    Examples:
        >>> get_file_size('/path/to/file.txt')
        1024
    """
    try:
        expanded_path = expand_path(path)
        if os.path.isfile(expanded_path):
            return os.path.getsize(expanded_path)
        return None
    except Exception:
        return None


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
        
    Examples:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"


def get_relative_path(path: str, base_path: str) -> str:
    """
    获取相对路径
    
    Args:
        path: 目标路径
        base_path: 基准路径
        
    Returns:
        str: 相对路径
        
    Examples:
        >>> get_relative_path('/home/user/project/file.txt', '/home/user')
        'project/file.txt'
    """
    expanded_path = expand_path(path)
    expanded_base = expand_path(base_path)
    return os.path.relpath(expanded_path, expanded_base)


def normalize_path(path: str) -> str:
    """
    规范化路径（统一使用正斜杠）
    
    Args:
        path: 原始路径
        
    Returns:
        str: 规范化后的路径
        
    Examples:
        >>> normalize_path('C:\\Users\\name\\file.txt')
        'C:/Users/name/file.txt'
    """
    return path.replace('\\', '/')

