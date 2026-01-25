# 打包指南

本文档说明如何将项目打包成 Windows 和 macOS 可执行文件。

## 📋 前置要求

1. Python 3.12 或更高版本
2. 已安装项目依赖：`uv sync` 或 `pip install -r requirements.txt`
3. PyInstaller（打包脚本会自动安装）

## 🚀 快速开始

### 方法一：使用自动打包脚本（推荐）

在项目根目录运行：

```bash
python build.py
```

这个脚本会：
- 自动检测当前操作系统
- 安装 PyInstaller（如果未安装）
- 打包成对应平台的可执行文件
- 输出文件位于 `dist/` 目录

### 方法二：使用 PyInstaller 命令

#### macOS 打包

```bash
# 安装 PyInstaller
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller build.spec

# 或者使用命令行参数
pyinstaller --name "李雪松工具集" \
    --onefile \
    --console \
    --clean \
    --add-data "remote_deploy:remote_deploy" \
    --add-data "common:common" \
    --add-data "examples:examples" \
    main.py
```

#### Windows 打包

在 Windows 系统上运行：

```cmd
# 安装 PyInstaller
pip install pyinstaller

# 使用 spec 文件打包
pyinstaller build.spec

# 或者使用命令行参数
pyinstaller --name "李雪松工具集" ^
    --onefile ^
    --console ^
    --clean ^
    --add-data "remote_deploy;remote_deploy" ^
    --add-data "common;common" ^
    --add-data "examples;examples" ^
    main.py
```

## 📦 输出文件

打包完成后，可执行文件位于：

- **macOS**: `dist/李雪松工具集` 或 `dist/李雪松工具集.app`
- **Windows**: `dist/李雪松工具集.exe`

## 🔧 高级配置

### 添加图标

1. 准备图标文件：
   - Windows: `icon.ico` (256x256 或更小)
   - macOS: `icon.icns` (包含多种尺寸)

2. 将图标文件放在项目根目录

3. 打包脚本会自动检测并使用图标

### 自定义打包选项

编辑 `build.spec` 文件来自定义打包行为：

```python
# 修改应用名称
name='你的应用名称'

# 添加更多数据文件
datas=[
    ('config', 'config'),
    ('assets', 'assets'),
]

# 添加隐藏导入
hiddenimports=[
    'your_module',
]

# 排除不需要的模块（减小文件大小）
excludes=[
    'tkinter',
    'matplotlib',
]
```

### 减小文件大小

1. **使用 UPX 压缩**（已在 spec 文件中启用）：
   ```bash
   # macOS/Linux
   brew install upx
   
   # Windows
   # 从 https://upx.github.io/ 下载
   ```

2. **排除不需要的模块**：
   在 `build.spec` 的 `excludes` 列表中添加不需要的模块

3. **使用虚拟环境**：
   在干净的虚拟环境中打包，只安装必需的依赖

## 🌐 跨平台打包

### 在 macOS 上打包 Windows 版本

PyInstaller 不支持真正的跨平台打包。要为 Windows 打包，您需要：

1. **使用 Windows 虚拟机或实体机**
2. **使用 GitHub Actions 自动化打包**（推荐）

### 使用 GitHub Actions 自动打包

创建 `.github/workflows/build.yml`：

```yaml
name: Build Executables

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build Windows executable
        run: python build.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: windows-executable
          path: dist/*.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build macOS executable
        run: python build.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: macos-executable
          path: dist/李雪松工具集
```

## 🐛 常见问题

### 1. 找不到模块错误

**问题**: 运行可执行文件时提示 `ModuleNotFoundError`

**解决方案**: 在 `build.spec` 的 `hiddenimports` 中添加缺失的模块

### 2. 配置文件找不到

**问题**: 程序无法读取配置文件

**解决方案**: 
- 确保配置文件在 `datas` 列表中
- 使用相对路径或 `sys._MEIPASS` 来定位资源文件

### 3. 文件太大

**问题**: 生成的可执行文件过大

**解决方案**:
- 安装并启用 UPX 压缩
- 排除不需要的模块
- 使用 `--onefile` 选项

### 4. macOS 安全警告

**问题**: macOS 提示"无法打开，因为无法验证开发者"

**解决方案**:
```bash
# 移除隔离属性
xattr -cr dist/李雪松工具集.app

# 或者在系统偏好设置中允许运行
```

### 5. Windows Defender 误报

**问题**: Windows Defender 将可执行文件标记为病毒

**解决方案**:
- 这是 PyInstaller 打包程序的常见问题
- 可以申请代码签名证书
- 或者提交到 Microsoft 进行白名单申请

## 📚 参考资源

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [PyInstaller 使用手册](https://pyinstaller.readthedocs.io/)
- [打包 Python 应用最佳实践](https://packaging.python.org/)

## 💡 提示

1. **测试**: 在目标平台上充分测试打包后的程序
2. **版本控制**: 不要将 `build/` 和 `dist/` 目录提交到 Git
3. **依赖管理**: 保持依赖版本的一致性
4. **文档**: 为用户提供清晰的安装和使用说明

