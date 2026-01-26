# 🔧 Windows 闪退问题修复

## ❌ 问题描述

Windows 版本启动后立即闪退，错误信息：
```
ModuleNotFoundError: No module named 'rich._unicode_data.unicode17_0_0'
```

## 🔍 原因分析

`rich` 库在 Windows 上需要 Unicode 数据文件，但 PyInstaller 默认不会打包这些文件。

## ✅ 修复方案

已在打包配置中添加：

```python
--hidden-import rich._unicode_data
--hidden-import rich._unicode_data.unicode17_0_0
--collect-all rich
```

这会确保 `rich` 库的所有数据文件都被打包。

## 📤 推送修复到 GitHub

### 方法一：等待 Gitee 自动同步

如果您配置了 Gitee 到 GitHub 的自动同步：
- ⏳ 等待几分钟
- 🔄 Gitee 会自动同步到 GitHub
- ✅ 然后在 GitHub Actions 重新运行

### 方法二：在 GitHub 网页上手动修改

#### 1. 修改 build.yml

访问：`https://github.com/coderxsle/da_song_ge/edit/master/.github/workflows/build.yml`

找到 Windows 构建部分（约第 26 行），替换为：

```yaml
      - name: Build Windows executable
        run: |
          python -m PyInstaller --name 李雪松工具集 --onefile --console --clean --noconfirm \
            --add-data "remote_deploy;remote_deploy" \
            --add-data "common;common" \
            --add-data "examples;examples" \
            --hidden-import rich \
            --hidden-import rich._unicode_data \
            --hidden-import rich._unicode_data.unicode17_0_0 \
            --hidden-import yaml \
            --hidden-import paramiko \
            --hidden-import scp \
            --hidden-import fabric \
            --hidden-import typer \
            --hidden-import docker \
            --hidden-import pydantic \
            --hidden-import dotenv \
            --collect-all rich \
            main.py
        shell: bash
```

#### 2. 修改 build.py

访问：`https://github.com/coderxsle/da_song_ge/edit/master/build.py`

找到隐藏导入部分（约第 70 行），替换为：

```python
        # 隐藏导入（确保所有依赖都被打包）
        "--hidden-import", "rich",
        "--hidden-import", "rich._unicode_data",
        "--hidden-import", "rich._unicode_data.unicode17_0_0",
        "--hidden-import", "yaml",
        "--hidden-import", "paramiko",
        "--hidden-import", "scp",
        "--hidden-import", "fabric",
        "--hidden-import", "typer",
        "--hidden-import", "docker",
        "--hidden-import", "pydantic",
        "--hidden-import", "dotenv",
        "--collect-all", "rich",
```

## 🚀 重新构建

修复推送后：

1. **访问 Actions 页面：**
   ```
   https://github.com/coderxsle/da_song_ge/actions
   ```

2. **点击 "Build Executables"**

3. **点击 "Run workflow"**
   - 选择 "master" 分支
   - 点击绿色的 "Run workflow" 按钮

4. **等待构建完成**（约 5-10 分钟）

5. **下载新的 Windows 版本测试**

## 📊 预期结果

修复后，Windows 版本应该能够正常启动：

```
╔═══════════════════════════════════════════╗
║                                           ║
║         🚀  李雪松工具集                  ║
║                                           ║
╚═══════════════════════════════════════════╝

                  ✨ 功能菜单 ✨
╭──────┬───────────────────────────┬────────╮
│ 序号 │ 功能名称                  │ 描述   │
├──────┼───────────────────────────┼────────┤
│  1   │ 🚀 远程部署               │ ...    │
│  2   │ 🐳 部署工具               │ ...    │
...
```

## 🔍 其他可能的问题

如果修复后仍然闪退，可能需要：

### 1. 添加更多 rich 相关的隐藏导入

```python
--hidden-import rich.console
--hidden-import rich.panel
--hidden-import rich.table
--hidden-import rich.prompt
--hidden-import rich.text
--hidden-import rich.box
--hidden-import rich.progress
```

### 2. 使用 --onedir 模式测试

将 `--onefile` 改为 `--onedir`，这样可以看到更详细的错误信息。

### 3. 检查 Windows 控制台编码

确保 Windows 控制台支持 UTF-8：
```cmd
chcp 65001
```

## 💡 调试技巧

如果需要查看详细错误信息：

1. **创建批处理文件 `run.bat`：**
   ```batch
   @echo off
   chcp 65001
   李雪松工具集.exe
   pause
   ```

2. **双击运行 `run.bat`**
   - 这样程序退出后窗口不会关闭
   - 可以看到完整的错误信息

## 📝 本地测试

如果您想在本地测试修复：

```bash
cd /Users/coderxslee/workspace/tools/da_song_ge

# 使用修复后的配置打包
python build.py

# 将生成的文件复制到 Windows 测试
```

---

## 🎯 总结

**问题：** Windows 版本缺少 rich 库的 Unicode 数据文件

**修复：** 添加 `--collect-all rich` 和相关隐藏导入

**下一步：**
1. 等待 Gitee 同步到 GitHub（或手动推送）
2. 在 GitHub Actions 重新运行 workflow
3. 下载新的 Windows 版本测试
4. 确认问题已解决

---

**修复已完成！等待同步后重新构建即可！** 🎉

