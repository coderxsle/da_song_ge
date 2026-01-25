# 📦 打包指南

## 🎯 快速开始

### 在当前平台打包

直接运行打包脚本：

```bash
python build.py
```

这会自动：
- ✅ 检测当前操作系统（macOS/Windows）
- ✅ 安装 PyInstaller
- ✅ 打包成可执行文件
- ✅ 输出到 `dist/` 目录

### 打包结果

- **macOS**: `dist/李雪松工具集` 或 `dist/李雪松工具集.app`
- **Windows**: `dist/李雪松工具集.exe`

---

## 🔧 三种打包方式

### 方式一：自动打包脚本（最简单）

```bash
# 在 macOS 上
python build.py

# 在 Windows 上
python build.py
```

### 方式二：使用 spec 文件

```bash
# 1. 安装 PyInstaller
pip install pyinstaller

# 2. 使用 spec 文件打包
pyinstaller build.spec
```

### 方式三：GitHub Actions 自动化（推荐用于发布）

1. 将代码推送到 GitHub
2. 创建一个版本标签：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions 会自动为 Windows 和 macOS 打包
4. 在 GitHub Releases 页面下载打包好的文件

---

## 🌐 跨平台打包说明

### ⚠️ 重要提示

PyInstaller **不支持真正的跨平台打包**，这意味着：

- 在 macOS 上只能打包 macOS 版本
- 在 Windows 上只能打包 Windows 版本
- 在 Linux 上只能打包 Linux 版本

### 解决方案

#### 方案 1: 使用多台机器

- 在 Mac 上运行 `python build.py` 生成 macOS 版本
- 在 Windows 上运行 `python build.py` 生成 Windows 版本

#### 方案 2: 使用虚拟机

- 在 Mac 上使用 Parallels/VMware 运行 Windows 虚拟机
- 在 Windows 上使用 VirtualBox 运行 macOS 虚拟机（需要特殊配置）

#### 方案 3: 使用 GitHub Actions（推荐）

已经为您配置好了 `.github/workflows/build.yml`，它会：

1. 在 GitHub 的 Windows 服务器上打包 Windows 版本
2. 在 GitHub 的 macOS 服务器上打包 macOS 版本
3. 自动创建 Release 并上传两个版本

**使用步骤：**

```bash
# 1. 提交代码到 GitHub
git add .
git commit -m "准备发布 v1.0.0"
git push

# 2. 创建并推送标签
git tag v1.0.0
git push origin v1.0.0

# 3. 等待几分钟，GitHub Actions 会自动打包
# 4. 在 GitHub 仓库的 Releases 页面下载
```

---

## 📝 详细步骤

### 在 macOS 上打包

```bash
# 1. 确保在项目根目录
cd /Users/coderxslee/workspace/tools/da_song_ge

# 2. 激活虚拟环境（如果使用）
source .venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行打包脚本
python build.py

# 5. 测试可执行文件
./dist/李雪松工具集
```

### 在 Windows 上打包

```cmd
# 1. 确保在项目根目录
cd C:\path\to\da_song_ge

# 2. 激活虚拟环境（如果使用）
.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行打包脚本
python build.py

# 5. 测试可执行文件
dist\李雪松工具集.exe
```

---

## 🎨 自定义配置

### 添加应用图标

1. 准备图标文件：
   - **Windows**: `icon.ico`（256x256 像素）
   - **macOS**: `icon.icns`（包含多种尺寸）

2. 将图标文件放在项目根目录

3. 打包脚本会自动检测并使用

### 修改应用名称

编辑 `build.py` 文件：

```python
app_name = "你的应用名称"  # 修改这里
```

### 添加更多数据文件

编辑 `build.spec` 文件：

```python
datas = [
    ('remote_deploy', 'remote_deploy'),
    ('common', 'common'),
    ('examples', 'examples'),
    ('你的目录', '你的目录'),  # 添加新的数据目录
]
```

---

## 🐛 常见问题

### 1. ModuleNotFoundError

**问题**: 运行可执行文件时提示找不到模块

**解决方案**: 在 `build.spec` 的 `hiddenimports` 列表中添加缺失的模块：

```python
hiddenimports = [
    'rich',
    'yaml',
    '你缺失的模块',  # 添加这里
]
```

### 2. 文件太大

**问题**: 生成的可执行文件过大（>100MB）

**解决方案**:

```bash
# 安装 UPX 压缩工具
# macOS
brew install upx

# Windows
# 从 https://upx.github.io/ 下载并添加到 PATH
```

### 3. macOS 安全警告

**问题**: macOS 提示"无法打开，因为无法验证开发者"

**解决方案**:

```bash
# 移除隔离属性
xattr -cr dist/李雪松工具集.app

# 或者右键点击 -> 打开 -> 仍要打开
```

### 4. Windows Defender 误报

**问题**: Windows Defender 将可执行文件标记为病毒

**解决方案**:
- 这是 PyInstaller 的常见问题（误报）
- 添加到 Windows Defender 白名单
- 或者申请代码签名证书

---

## 📊 打包文件大小参考

| 平台 | 未压缩 | UPX 压缩后 |
|------|--------|-----------|
| macOS | ~50MB | ~20MB |
| Windows | ~40MB | ~15MB |

---

## 🚀 发布流程

### 本地发布

1. 在 Mac 上打包 macOS 版本
2. 在 Windows 上打包 Windows 版本
3. 将两个文件上传到发布平台

### GitHub 自动发布（推荐）

```bash
# 1. 更新版本号
# 编辑 pyproject.toml 中的 version

# 2. 提交更改
git add .
git commit -m "Release v1.0.0"
git push

# 3. 创建标签
git tag v1.0.0
git push origin v1.0.0

# 4. GitHub Actions 自动打包并创建 Release
# 访问 https://github.com/你的用户名/da_song_ge/releases
```

---

## 📚 更多信息

详细的打包指南请查看 `BUILD_GUIDE.md`

---

## ✅ 检查清单

打包前请确认：

- [ ] 所有依赖都在 `requirements.txt` 中
- [ ] 配置文件示例已创建（`config.yaml.example`）
- [ ] 测试过所有主要功能
- [ ] 更新了版本号
- [ ] 准备了图标文件（可选）
- [ ] 编写了用户使用文档

打包后请确认：

- [ ] 可执行文件能正常运行
- [ ] 所有功能都正常工作
- [ ] 配置文件能正确读取
- [ ] 文件大小合理
- [ ] 在目标平台上测试过

