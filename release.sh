#!/bin/bash

# 发布新版本脚本

set -e

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 请提供版本号"
    echo "用法: ./release.sh v1.0.0"
    exit 1
fi

VERSION=$1

# 验证版本号格式
if [[ ! $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ 版本号格式错误"
    echo "正确格式: v1.0.0"
    exit 1
fi

echo "🚀 准备发布版本: $VERSION"
echo ""

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "📝 发现未提交的更改，正在提交..."
    git add .
    git commit -m "Release $VERSION"
else
    echo "✅ 没有未提交的更改"
fi

# 推送到远程
echo "📤 推送代码到 GitHub..."
git push origin main

# 检查标签是否已存在
if git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "⚠️  标签 $VERSION 已存在"
    read -p "是否删除并重新创建？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  删除旧标签..."
        git tag -d "$VERSION"
        git push origin --delete "$VERSION" 2>/dev/null || true
    else
        echo "❌ 取消发布"
        exit 1
    fi
fi

# 创建标签
echo "🏷️  创建标签 $VERSION..."
git tag -a "$VERSION" -m "Release $VERSION"

# 推送标签
echo "📤 推送标签到 GitHub..."
git push origin "$VERSION"

echo ""
echo "✅ 发布完成！"
echo ""
echo "📊 查看构建进度："
echo "   https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
echo ""
echo "📦 构建完成后，在这里下载："
echo "   https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/releases"
echo ""

