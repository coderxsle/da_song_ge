#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
授权验证器
负责验证授权密钥的有效性
"""

import os
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()


class LicenseValidator:
    """授权验证器类"""
    
    # 验证接口 URL
    VERIFY_URL = "https://a.app.hbsjzhyyy.com/license/license/verify"
    
    # 缓存文件路径（存储在用户主目录）
    CACHE_DIR = Path.home() / ".remote_deploy_cache"
    CACHE_FILE = CACHE_DIR / "license_cache.json"
    
    # 缓存有效期（24小时）
    CACHE_VALIDITY_HOURS = 24
    
    # 请求超时时间（秒）
    REQUEST_TIMEOUT = 10
    
    def __init__(self, license_key: str):
        """
        初始化授权验证器
        
        Args:
            license_key: 授权密钥
        """
        self.license_key = license_key
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not self.CACHE_DIR.exists():
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def validate(self, force_refresh: bool = False) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        验证授权密钥
        
        Args:
            force_refresh: 是否强制刷新（忽略缓存）
            
        Returns:
            Tuple[bool, Optional[Dict], Optional[str]]: 
                (是否有效, 授权数据, 错误信息)
        """
        # 检查缓存
        if not force_refresh:
            cached_data = self._load_cache()
            if cached_data:
                console.print("[cyan]✓ 使用缓存的授权验证结果[/cyan]")
                return True, cached_data, None
        
        # 调用验证接口
        console.print("[cyan]⏳ 正在验证授权密钥...[/cyan]")
        
        try:
            response = requests.get(
                self.VERIFY_URL,
                params={"license_code": self.license_key},
                timeout=self.REQUEST_TIMEOUT
            )
            
            # 检查 HTTP 状态码
            if response.status_code != 200:
                error_msg = f"验证接口返回错误状态码: {response.status_code}"
                return False, None, error_msg
            
            # 解析 JSON 响应
            result = response.json()
            
            # 检查返回的 code 字段
            if result.get("code") != 0:
                error_msg = result.get("message", "授权验证失败")
                return False, None, error_msg
            
            # 获取授权数据
            data = result.get("data")
            if not data:
                return False, None, "授权数据为空"
            
            # 检查授权状态
            status = data.get("status")
            valid = data.get("valid")
            
            # 状态检查：0-未激活 1-已激活 2-已过期 3-已禁用
            if status != 1:
                status_text = data.get("status_text", "未知状态")
                error_msg = f"授权密钥状态异常: {status_text}"
                return False, data, error_msg
            
            if not valid:
                error_msg = "授权密钥无效"
                return False, data, error_msg
            
            # 验证成功，保存缓存
            self._save_cache(data)
            
            return True, data, None
            
        except requests.exceptions.Timeout:
            error_msg = f"验证接口请求超时（{self.REQUEST_TIMEOUT}秒）"
            return False, None, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "无法连接到验证服务器，请检查网络连接"
            return False, None, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求失败: {e}"
            return False, None, error_msg
        except json.JSONDecodeError:
            error_msg = "验证接口返回的数据格式错误"
            return False, None, error_msg
        except Exception as e:
            error_msg = f"授权验证异常: {e}"
            return False, None, error_msg
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """
        加载缓存的授权数据
        
        Returns:
            Optional[Dict]: 授权数据，如果缓存无效则返回 None
        """
        try:
            if not self.CACHE_FILE.exists():
                return None
            
            with open(self.CACHE_FILE, 'r', encoding='utf-8') as f:
                cache = json.load(f)
            
            # 检查缓存的授权密钥是否匹配
            if cache.get("license_code") != self.license_key:
                return None
            
            # 检查缓存时间
            cached_time_str = cache.get("cached_time")
            if not cached_time_str:
                return None
            
            cached_time = datetime.fromisoformat(cached_time_str)
            now = datetime.now()
            
            # 检查缓存是否过期
            if now - cached_time > timedelta(hours=self.CACHE_VALIDITY_HOURS):
                return None
            
            # 返回授权数据
            return cache.get("data")
            
        except Exception:
            # 缓存加载失败，忽略错误
            return None
    
    def _save_cache(self, data: Dict[str, Any]):
        """
        保存授权数据到缓存
        
        Args:
            data: 授权数据
        """
        try:
            cache = {
                "license_code": self.license_key,
                "cached_time": datetime.now().isoformat(),
                "data": data
            }
            
            with open(self.CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
                
        except Exception:
            # 缓存保存失败，忽略错误（不影响主流程）
            pass
    
    def show_license_info(self, data: Optional[Dict[str, Any]]):
        """
        显示授权信息
        
        Args:
            data: 授权数据
        """
        # 如果数据为空，不显示
        if not data:
            return
        
        console.print()
        
        # 创建授权信息表格
        table = Table(
            box=box.ROUNDED,
            border_style="bright_green",
            show_header=False,
            # show_lines=True,
            padding=(0, 2)
        )
        
        table.add_column("项目", style="bold cyan", width=20)
        table.add_column("值", style="white", width=50)
        
        # 添加授权信息
        table.add_row("授权密钥", data.get("license_code", "-"))
        table.add_row("产品名称", data.get("product_name", "-"))
        table.add_row("状态", f"[green]{data.get('status_text', '-')}[/green]")
        table.add_row("有效期开始", data.get("valid_start_time", "-"))
        table.add_row("有效期结束", data.get("valid_end_time", "-"))
        
        remaining_days = data.get("remaining_days", 0)
        if remaining_days > 365000:  # 永久授权
            remaining_text = "[green]永久有效[/green]"
        elif remaining_days > 30:
            remaining_text = f"[green]{remaining_days} 天[/green]"
        elif remaining_days > 7:
            remaining_text = f"[yellow]{remaining_days} 天[/yellow]"
        else:
            remaining_text = f"[red]{remaining_days} 天[/red]"
        
        table.add_row("剩余天数", remaining_text)
        
        if data.get("remark"):
            table.add_row("备注", data.get("remark"))
        
        console.print(Panel(
            table,
            title="[bold green]✓ 授权验证成功[/bold green]",
            border_style="green",
            padding=(1, 2)
        ))
        
        # 如果即将过期，显示警告
        if 0 < remaining_days <= 30:
            console.print(Panel.fit(
                f"[bold yellow]⚠ 警告: 授权密钥将在 {remaining_days} 天后过期，请及时续期！[/bold yellow]",
                border_style="yellow"
            ))
        
        console.print()
    
    def show_error(self, error_msg: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        """
        显示错误信息
        
        Args:
            error_msg: 错误信息（可选）
            data: 授权数据（可选）
        """
        console.print()
        
        # 如果没有提供错误信息，使用默认信息
        if error_msg is None:
            error_msg = "授权验证失败"
        
        error_lines = [
            f"[bold red]❌ {error_msg}[/bold red]",
            "",
            f"[yellow]授权密钥:[/yellow] {self.license_key}"
        ]
        
        if data:
            error_lines.append("")
            error_lines.append("[yellow]详细信息:[/yellow]")
            error_lines.append(f"  • 状态: {data.get('status_text', '未知')}")
            
            if data.get("valid_end_time"):
                error_lines.append(f"  • 有效期: {data.get('valid_start_time', '-')} ~ {data.get('valid_end_time', '-')}")
            
            if data.get("remark"):
                error_lines.append(f"  • 备注: {data.get('remark')}")
        
        console.print(Panel(
            "\n".join(error_lines),
            title="[bold red]授权验证失败[/bold red]",
            border_style="red",
            padding=(1, 2)
        ))
        console.print()


def main():
    """主函数 - 用于测试授权验证器"""
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description='授权验证器测试工具')
    parser.add_argument(
        '-k', '--key',
        type=str,
        required=True,
        help='授权密钥'
    )
    parser.add_argument(
        '-f', '--force',
        action='store_true',
        help='强制刷新（忽略缓存）'
    )
    
    args = parser.parse_args()
    
    try:
        validator = LicenseValidator(args.key)
        success, data, error_msg = validator.validate(force_refresh=args.force)
        
        if success:
            validator.show_license_info(data)
            return 0
        else:
            validator.show_error(error_msg, data)
            return 1
            
    except KeyboardInterrupt:
        console.print("\n\n[yellow]⚠ 验证被用户中断[/yellow]")
        return 1
    except Exception as e:
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

