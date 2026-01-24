# 本地命令执行功能使用说明

## 📖 功能介绍

本地命令执行功能允许你在上传文件到服务器之前，先在本地执行一些命令，比如：
- 编译前端项目（npm run build）
- 打包后端项目（mvn package）
- 运行测试
- 压缩文件
- 构建 Docker 镜像
- 等等...

## 🚀 快速开始

### 1. 配置文件结构

在 `config.yaml` 中添加 `local_commands` 配置：

```yaml
servers:
  - name: 我的服务器
    host: 192.168.1.100
    port: 22
    username: admin
    auth:
      type: ssh_key
      key_path: ~/.ssh/id_rsa

    # 本地命令配置
    local_commands:
      frontend_admin:  # 对应 upload 中的类型
        working_dir: ~/workspace/my_project/frontend  # 工作目录
        stop_on_error: true  # 遇到错误是否停止（默认 true）
        commands:
          - npm install
          - npm run build:prod

    # 上传配置
    upload:
      frontend_admin:
        - local_path: ~/workspace/my_project/frontend/dist/
          remote_path: /var/www/html/
```

### 2. 执行部署

```bash
# 交互式选择
python remote_deploy/deploy_service.py

# 或指定参数
python remote_deploy/deploy_service.py -s "我的服务器" -u frontend_admin
```

## 📝 配置说明

### 配置项详解

```yaml
local_commands:
  <upload_type>:  # 上传类型名称，必须与 upload 中的类型对应
    working_dir: <路径>  # 可选，命令执行的工作目录
    stop_on_error: <true|false>  # 可选，默认 true，遇到错误是否停止
    commands:  # 必填，要执行的命令列表
      - <命令1>
      - <命令2>
      - ...
```

### 配置项说明

| 配置项 | 类型 | 必填 | 默认值 | 说明 |
|--------|------|------|--------|------|
| `working_dir` | string | 否 | 当前目录 | 命令执行的工作目录，支持 `~` 符号 |
| `stop_on_error` | boolean | 否 | true | 遇到错误是否停止后续命令 |
| `commands` | list | 是 | - | 要执行的命令列表 |

## 💡 使用示例

### 示例 1：前端项目（Vue/React）

```yaml
local_commands:
  frontend_admin:
    working_dir: ~/workspace/vue-project
    commands:
      - npm install
      - npm run build:prod
```

### 示例 2：后端项目（Java Maven）

```yaml
local_commands:
  backend_api:
    working_dir: ~/workspace/java-project
    commands:
      - mvn clean package -Dmaven.test.skip=true
```

### 示例 3：多步骤构建

```yaml
local_commands:
  full_stack:
    working_dir: ~/workspace/my-project
    commands:
      - echo "清理旧文件..."
      - rm -rf dist/ build/
      - echo "编译前端..."
      - cd frontend && npm run build && cd ..
      - echo "编译后端..."
      - cd backend && mvn package && cd ..
      - echo "打包部署文件..."
      - tar -czf deploy.tar.gz frontend/dist backend/target/*.jar
```

### 示例 4：允许某些命令失败

```yaml
local_commands:
  backend_api:
    working_dir: ~/workspace/project
    stop_on_error: false  # 允许命令失败
    commands:
      - npm install || echo "npm install 失败，继续"
      - npm run build
```

## 🔄 执行流程

完整的部署流程如下：

```
1. 选择服务器
2. 选择上传类型
3. 选择命令组
   ↓
4. 执行本地命令 ← 新增步骤
   ↓
5. 建立 SSH 连接
   ↓
6. 上传文件
   ↓
7. 执行远程命令
   ↓
8. 显示部署摘要
```

## 📋 常见场景

### 场景 1：前端项目部署

```yaml
servers:
  - name: 前端服务器
    host: 192.168.1.100
    port: 22
    username: www
    auth:
      type: ssh_key
      key_path: ~/.ssh/id_rsa

    local_commands:
      frontend:
        working_dir: ~/workspace/vue3-admin
        commands:
          - npm install
          - npm run build:prod
    
    upload:
      frontend:
        - local_path: ~/workspace/vue3-admin/dist/
          remote_path: /var/www/html/
          mode: sync
          delete_extra: true
```

### 场景 2：Spring Boot 项目部署

```yaml
servers:
  - name: 后端服务器
    host: 192.168.1.101
    port: 22
    username: java
    auth:
      type: ssh_key
      key_path: ~/.ssh/id_rsa

    local_commands:
      backend:
        working_dir: ~/workspace/springboot-app
        commands:
          - mvn clean package -DskipTests
    
    upload:
      backend:
        - local_path: ~/workspace/springboot-app/target/app.jar
          remote_path: /opt/app/
    
    commands:
      backend:
        - cd /opt/app
        - sh restart.sh
```

### 场景 3：Docker 镜像部署

```yaml
servers:
  - name: Docker 服务器
    host: 192.168.1.102
    port: 22
    username: docker
    auth:
      type: ssh_key
      key_path: ~/.ssh/id_rsa

    local_commands:
      docker_app:
        working_dir: ~/workspace/my-app
        commands:
          - docker build -t myapp:latest .
          - docker save myapp:latest -o myapp.tar
    
    upload:
      docker_app:
        - local_path: ~/workspace/my-app/myapp.tar
          remote_path: /tmp/
    
    commands:
      docker_app:
        - docker load -i /tmp/myapp.tar
        - docker stop myapp || true
        - docker rm myapp || true
        - docker run -d --name myapp -p 8080:8080 myapp:latest
```

## ⚠️ 注意事项

1. **工作目录**：确保 `working_dir` 路径存在且有权限访问
2. **命令依赖**：确保本地已安装所需的命令工具（如 npm、mvn、docker 等）
3. **执行时间**：某些命令可能需要较长时间（如编译），请耐心等待
4. **错误处理**：建议保持 `stop_on_error: true`，避免错误被忽略
5. **路径问题**：使用 `~` 表示用户主目录，会自动展开

## 🐛 故障排查

### 问题 1：命令找不到

**错误信息**：`command not found: npm`

**解决方案**：
- 确保命令已安装：`which npm`
- 检查环境变量 PATH 是否正确
- 尝试使用完整路径：`/usr/local/bin/npm install`

### 问题 2：工作目录不存在

**错误信息**：`工作目录不存在: /path/to/dir`

**解决方案**：
- 检查路径是否正确
- 确保使用绝对路径或 `~` 开头的路径
- 手动创建目录：`mkdir -p /path/to/dir`

### 问题 3：权限不足

**错误信息**：`Permission denied`

**解决方案**：
- 检查文件/目录权限
- 确保当前用户有执行权限
- 必要时使用 `chmod` 修改权限

## 📚 更多示例

查看 `local_commands_example.yaml` 文件获取更多配置示例。

## 🔗 相关文档

- [配置文件说明](./config.yaml)
- [部署服务文档](./deploy_service.py)
- [本地命令执行器](./local_command_executor.py)

