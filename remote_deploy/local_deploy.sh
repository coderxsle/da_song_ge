#!/bin/bash
set -e

# ==================== 配置区域 ====================
# 服务器配置
SERVER_HOST="192.168.0.106"
SERVER_PORT="55555"  # SSH 端口，默认 22，如果不是请修改
SERVER_USER="admin"
SERVER_BASE_PATH="/home/admin/web_projects/dccw/server-api"

# 项目配置
PROJECT_NAME="yudao-server"
# 项目根目录（脚本所在目录的上上级）
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Maven 配置
MAVEN_OPTS="-Dmaven.test.skip=true"

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

# 检查 SSH 连接
function check_ssh_connection() {
    print_info "检查服务器连接: $SERVER_USER@$SERVER_HOST:$SERVER_PORT"
    
    if ssh -p $SERVER_PORT -o ConnectTimeout=10 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST 'echo connected' 2>&1 | grep -q "connected"; then
        print_success "服务器连接正常（SSH 免密登录）"
        return 0
    else
        print_error "无法连接到服务器，请检查："
        echo "  1. 服务器地址是否正确: $SERVER_HOST"
        echo "  2. SSH 端口是否正确: $SERVER_PORT"
        echo "  3. 用户名是否正确: $SERVER_USER"
        echo "  4. SSH 免密登录是否配置正确"
        echo "  5. 网络是否可达"
        echo ""
        echo "尝试手动连接测试："
        echo "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST"
        exit 1
    fi
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

# 上传文件到服务器
function upload_files() {
    print_info "上传文件到服务器..."
    
    # 上传 jar 包
    print_info "上传 jar 包: $(basename $JAR_FILE)"
    if scp -P $SERVER_PORT "$JAR_FILE" $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/build/$PROJECT_NAME.jar; then
        print_success "jar 包上传成功"
    else
        print_error "jar 包上传失败"
        exit 1
    fi
    
    # 上传 startup1.sh 脚本
    print_info "上传启动脚本: startup1.sh"
    if scp -P $SERVER_PORT "$SCRIPT_DIR/startup1.sh" $SERVER_USER@$SERVER_HOST:$SERVER_BASE_PATH/bin/startup1.sh; then
        print_success "启动脚本上传成功"
    else
        print_warning "启动脚本上传失败（如果服务器上已有脚本，可以忽略）"
    fi
}

# 备份旧版本
function backup_on_server() {
    print_info "开始备份旧版本..."
    
    ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "
        DATE=\$(date +%Y%m%d%H%M)
        if [ -f '$SERVER_BASE_PATH/yudao-server.jar' ]; then
            echo '[backup] 开始备份 yudao-server ...'
            cp $SERVER_BASE_PATH/yudao-server.jar $SERVER_BASE_PATH/backup/yudao-server-\$DATE.jar
            echo '[backup] 备份 yudao-server 完成'
        else
            echo '[backup] yudao-server.jar 不存在，跳过备份'
        fi
    "
    
    print_success "备份完成"
}

# 转移新 jar 包
function transfer_jar() {
    print_info "开始转移 jar 包..."
    
    ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "
        echo '[transfer] 开始转移 yudao-server.jar'
        
        if [ -f '$SERVER_BASE_PATH/yudao-server.jar' ]; then
            echo '[transfer] 移除 $SERVER_BASE_PATH/yudao-server.jar 完成'
            rm $SERVER_BASE_PATH/yudao-server.jar
        fi
        
        echo '[transfer] 从 $SERVER_BASE_PATH/build 中获取 yudao-server.jar 并迁移至 $SERVER_BASE_PATH'
        cp $SERVER_BASE_PATH/build/yudao-server.jar $SERVER_BASE_PATH/yudao-server.jar
        echo '[transfer] 转移 yudao-server.jar 完成'
    "
    
    print_success "jar 包转移完成"
}

# 使用服务器上的 startup1.sh 重启服务
function restart_service() {
    print_info "开始启动服务（使用 startup1.sh）..."
    
    ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST "
        # 加载环境变量（解决 java 命令找不到的问题）
        if [ -f ~/.bash_profile ]; then
            source ~/.bash_profile
        fi
        if [ -f ~/.bashrc ]; then
            source ~/.bashrc
        fi
        
        echo '[start] 开始启动'
        cd $SERVER_BASE_PATH/bin
        chmod +x startup1.sh
        ./startup1.sh restart
    "
    
    if [ $? -eq 0 ]; then
        print_success "服务启动成功！"
    else
        print_error "服务启动失败，请查看服务器日志"
        exit 1
    fi
}

# 显示部署信息
function show_deploy_info() {
    echo ""
    echo "=========================================="
    echo "           部署信息"
    echo "=========================================="
    echo "项目名称: $PROJECT_NAME"
    echo "项目路径: $PROJECT_ROOT"
    echo "服务器地址: $SERVER_USER@$SERVER_HOST:$SERVER_PORT"
    echo "部署路径: $SERVER_BASE_PATH"
    echo "=========================================="
    echo ""
}

# 主函数
function main() {
    echo ""
    echo "=========================================="
    echo "      自动化部署脚本 v1.0"
    echo "=========================================="
    echo ""
    
    show_deploy_info
    
    # 询问是否需要重新打包
    echo ""
    print_warning "请选择部署方式："
    echo "  1) 重新打包并部署（完整流程）"
    echo "  2) 仅重启服务（不打包，直接连接服务器重启）"
    echo ""
    read -p "请输入选项 (1/2): " -n 1 -r
    echo
    echo ""
    
    if [[ $REPLY == "1" ]]; then
        # 完整部署流程
        print_info "选择：重新打包并部署"
        
        # 执行完整部署流程
        build_project
        check_ssh_connection
        create_server_directories
        upload_files
        backup_on_server
        transfer_jar
        restart_service
        
    elif [[ $REPLY == "2" ]]; then
        # 仅重启服务
        print_info "选择：仅重启服务（跳过打包）"
        
        # 只检查连接和重启服务
        check_ssh_connection
        restart_service
        
    else
        print_error "无效的选项，部署已取消"
        exit 1
    fi
    
    echo ""
    echo "=========================================="
    print_success "🎉 操作完成！"
    echo "=========================================="
    echo ""
    echo "查看服务器日志："
    echo "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'tail -f $SERVER_BASE_PATH/logs/server_\$(date +%Y%m%d).log'"
    echo ""
    echo "查看服务状态："
    echo "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'cd $SERVER_BASE_PATH/bin && ./startup1.sh status'"
    echo ""
    echo "停止服务："
    echo "  ssh -p $SERVER_PORT $SERVER_USER@$SERVER_HOST 'cd $SERVER_BASE_PATH/bin && ./startup1.sh stop'"
    echo ""
}

# 执行主函数
main

