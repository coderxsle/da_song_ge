#!/bin/bash
set -e


# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 函数定义 ====================

# 打印带颜色的信息
function print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

function print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

function print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

function print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}


# 本地编译
function build_project() {
    print_info "开始编译项目..."
    cd "$PROJECT_ROOT"
    
    if [ ! -f "pom.xml" ]; then
        print_error "未找到 pom.xml 文件，请确认项目路径: $PROJECT_ROOT"
        exit 1
    fi
    
    print_info "执行 Maven 打包: mvn clean package $MAVEN_OPTS"
    if mvn clean package $MAVEN_OPTS; then
        print_success "项目编译成功"
    else
        print_error "项目编译失败"
        exit 1
    fi
    
    # 查找生成的 jar 包
    JAR_FILE=$(find "$PROJECT_ROOT" -name "${PROJECT_NAME}*.jar" -not -path "*/original-*" | head -n 1)
    
    if [ -z "$JAR_FILE" ]; then
        print_error "未找到编译后的 jar 包"
        exit 1
    fi
    
    print_success "找到 jar 包: $JAR_FILE"
}

# 创建服务器目录结构
function create_server_directories() {
    print_info "创建服务器目录结构..."
    
    ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_BASE_PATH/{build,backup,heapError,logs}"
    
    print_success "服务器目录创建完成"
}


# 显示部署信息
function show_deploy_info() {
    printf "\n"
    print_info "=========================================="
    print_info "           部署信息"
    print_info "=========================================="
    print_info "项目名称: $PROJECT_NAME"
    print_info "项目路径: $PROJECT_ROOT"
    print_info "服务器地址: $SERVER_USER@$SERVER_HOST:$SERVER_PORT"
    print_info "部署路径: $SERVER_BASE_PATH"
    print_info "=========================================="
    printf "\n"
}

# 主函数
function main() {
    printf "\n"
    print_info "=========================================="
    print_info "      自动化部署脚本 v1.0"
    print_info "=========================================="
    printf "\n"
    
    printf "\n"
    print_info "=========================================="
    print_success "🎉 操作完成！"
    print_info "=========================================="
    printf "\n"
    print_info "查看服务器日志："
    print_info "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'tail -f $SERVER_BASE_PATH/logs/server_\$(date +%Y%m%d).log'"
    printf "\n"
    print_info "查看服务状态："
    print_info "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'cd $SERVER_BASE_PATH/bin && ./startup1.sh status'"
    printf "\n"
    print_info "停止服务："
    print_info "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'cd $SERVER_BASE_PATH/bin && ./startup1.sh stop'"
    printf "\n"
}

# 执行主函数
main

