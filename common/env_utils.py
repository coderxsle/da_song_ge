#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境变量工具模块
提供环境变量的读取功能
"""

import os
from typing import Optional


class EnvUtils:
    """环境变量工具类"""

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """
        获取环境变量
        
        参数:
            key: 环境变量名
            default: 默认值
            
        返回:
            环境变量值，如果不存在则返回默认值
        """
        return os.getenv(key, default)

    @staticmethod
    def set(key: str, value: str) -> None:
        """
        设置环境变量
        
        参数:
            key: 环境变量名
            value: 环境变量值
        """
        os.environ[key] = value

