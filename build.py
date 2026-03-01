#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
打包脚本 - 用于将项目打包成可执行文件
支持 Windows 和 macOS 平台
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# 设置 Windows 控制台编码为 UTF-8
if platform.system() == 'Windows':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def get_platform_name():
    """获取当前平台名称"""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    elif system == "linux":
        return "linux"
    else:
        return system

def install_pyinstaller():
    """安装 PyInstaller"""
    print("📦 检查 PyInstaller...")
    try:
        import PyInstaller
        print("✅ PyInstaller 已安装")
    except ImportError:
        print("📥 正在安装 PyInstaller...")
        
        # 尝试使用 uv pip install
        try:
            subprocess.run(["uv", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller 安装完成（使用 uv）")
        except (subprocess.CalledProcessError, FileNotFoundError):
            # 如果 uv 不可用，尝试使用 pip
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
                print("✅ PyInstaller 安装完成（使用 pip）")
            except subprocess.CalledProcessError:
                print("❌ 无法安装 PyInstaller")
                print("请手动运行: uv pip install pyinstaller")
                sys.exit(1)

def build_executable():
    """构建可执行文件"""
    platform_name = get_platform_name()
    print(f"\n🚀 开始为 {platform_name} 平台打包...")
    
    # 基础配置
    app_name = "李雪松工具集"
    main_script = "main.py"
    
    # 获取 pyinstaller 路径
    pyinstaller_cmd = os.path.join(os.path.dirname(sys.executable), "pyinstaller")
    if not os.path.exists(pyinstaller_cmd):
        pyinstaller_cmd = "pyinstaller"  # 尝试使用 PATH 中的
    
    # PyInstaller 命令参数
    cmd = [
        pyinstaller_cmd,
        "--name", app_name,
        "--onedir",  # 使用目录模式，显著提升启动速度（避免 onefile 每次解压）
        "--console",  # 使用控制台模式（命令行工具）
        "--clean",  # 清理临时文件
        "--noconfirm",  # 不询问确认
        
        # 添加数据文件
        "--add-data", f"remote_deploy{os.pathsep}remote_deploy",
        "--add-data", f"common{os.pathsep}common",
        "--add-data", f"examples{os.pathsep}examples",
        
        # 隐藏导入（仅保留 Rich 的 Unicode 数据，避免过度打包）
        "--hidden-import", "rich",
        "--hidden-import", "rich._unicode_data",
        "--hidden-import", "rich._unicode_data.unicode17_0_0",
        "--collect-all", "rich",
        
        # 主脚本
        main_script
    ]
    
    # 如果有图标文件，添加图标
    icon_path = Path("icon.ico" if platform_name == "windows" else "icon.icns")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])
    
    print(f"\n执行命令: {' '.join(cmd)}\n")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ 打包成功！")
        print(f"📁 可执行文件位置: dist/{app_name}")
        
        # 显示文件大小
        if platform_name == "windows":
            exe_path = Path(f"dist/{app_name}.exe")
        else:
            exe_path = Path(f"dist/{app_name}")
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📊 文件大小: {size_mb:.2f} MB")
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 打包失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("=" * 60)
    print("🎯 Python 项目打包工具")
    print("=" * 60)
    
    # 检查是否在项目根目录
    if not Path("main.py").exists():
        print("❌ 错误: 请在项目根目录运行此脚本")
        sys.exit(1)
    
    # 安装 PyInstaller
    install_pyinstaller()
    
    # 构建可执行文件
    build_executable()
    
    print("\n" + "=" * 60)
    print("🎉 打包完成！")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  打包被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

