#!/bin/bash
# 雅典娜生产环境部署脚本
# 用法: ./deploy.sh [init|start|stop|restart|update|backup]

set -e

PROJECT_DIR="/home/vitiana/Athena/api"
COMPOSE_FILE="docker-compose.prod.yml"
BACKUP_DIR="./backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查环境
check_environment() {
    log_info "检查环境..."
    
    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    # 检查 .env 文件
    if [ ! -f "$PROJECT_DIR/.env" ]; then
        log_error ".env 文件不存在，请复制 .env.production.example 并配置"
        exit 1
    fi
    
    # 检查 GPU
    if ! command -v nvidia-smi &> /dev/null; then
        log_warn "nvidia-smi 未找到，GPU 功能可能不可用"
    else
        log_info "GPU 检测: $(nvidia-smi --query-gpu=name --format=csv,noheader)"
    fi
    
    log_info "环境检查通过"
}

# 初始化数据目录
init_directories() {
    log_info "初始化数据目录..."
    
    # SSD 目录
    sudo mkdir -p /home/vitiana/Athena/data_ssd/{pg_data,valkey_data,hf_cache}
    sudo chown -R 1000:1000 /home/vitiana/Athena/data_ssd/
    
    # HDD 目录
    sudo mkdir -p /data/athena/{minio_data,calibre_books,calibre_config}
    sudo chown -R 1000:1000 /data/athena/
    
    # 备份目录
    mkdir -p "$BACKUP_DIR"
    
    log_info "数据目录初始化完成"
}

# 初始化 PostgreSQL
init_postgres() {
    log_info "初始化 PostgreSQL..."
    
    # 启动 PostgreSQL
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" up -d postgres
    
    log_info "等待 PostgreSQL 启动..."
    sleep 10
    
    # 创建 PowerSync 复制槽和发布
    log_info "创建 PowerSync 复制槽和发布..."
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U athena -d athena <<EOF
-- 创建复制槽
SELECT pg_create_logical_replication_slot('athena_powersync', 'pgoutput');

-- 创建发布
CREATE PUBLICATION athena_publication FOR TABLE 
  books, 
  reading_progress, 
  reading_sessions, 
  notes, 
  highlights, 
  bookmarks, 
  shelves, 
  shelf_books, 
  user_settings;
EOF
    
    log_info "PostgreSQL 初始化完成"
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    
    cd "$PROJECT_DIR"
    
    # 构建 API 镜像
    log_info "构建 API 镜像..."
    docker build -f Dockerfile.prod -t athena-api:latest --build-arg SKIP_HEAVY=true .
    
    # 构建 OCR 镜像
    log_info "构建 OCR 镜像..."
    docker build -f Dockerfile.ocr.prod -t athena-ocr:latest .
    
    # 构建 Embedding 镜像
    log_info "构建 Embedding 镜像..."
    docker build -f Dockerfile.prod -t athena-embedding:latest --build-arg SKIP_HEAVY=false .
    
    log_info "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" up -d
    
    log_info "等待服务启动..."
    sleep 15
    
    # 显示服务状态
    docker compose -f "$COMPOSE_FILE" ps
    
    log_info "服务启动完成"
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" down
    
    log_info "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" restart
    
    log_info "服务已重启"
}

# 更新部署
update_deployment() {
    log_info "更新部署..."
    
    # 拉取最新代码
    cd /home/vitiana/Athena
    git pull origin main
    
    # 重新构建镜像
    build_images
    
    # 滚动更新
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" up -d --no-deps --build api
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    docker compose -f "$COMPOSE_FILE" exec api alembic upgrade head
    
    log_info "更新完成"
}

# 备份数据库
backup_database() {
    log_info "备份数据库..."
    
    BACKUP_FILE="$BACKUP_DIR/athena_$(date +%Y%m%d_%H%M%S).backup"
    
    cd "$PROJECT_DIR"
    docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U athena -d athena -F c -b -v > "$BACKUP_FILE"
    
    log_info "数据库备份完成: $BACKUP_FILE"
    
    # 压缩备份
    gzip "$BACKUP_FILE"
    log_info "备份已压缩: ${BACKUP_FILE}.gz"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # API 健康检查
    if curl -f http://localhost:48000/health > /dev/null 2>&1; then
        log_info "✓ API 健康"
    else
        log_error "✗ API 不健康"
    fi
    
    # PowerSync 健康检查
    if curl -f http://localhost:48090/health > /dev/null 2>&1; then
        log_info "✓ PowerSync 健康"
    else
        log_error "✗ PowerSync 不健康"
    fi
    
    # GPU 检查
    if nvidia-smi > /dev/null 2>&1; then
        log_info "✓ GPU 可用"
        nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv
    else
        log_warn "✗ GPU 不可用"
    fi
}

# 主菜单
case "${1:-}" in
    init)
        check_environment
        init_directories
        build_images
        init_postgres
        start_services
        log_info "初始化完成！请运行数据库迁移: docker compose -f $COMPOSE_FILE exec api alembic upgrade head"
        ;;
    start)
        check_environment
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    update)
        check_environment
        update_deployment
        ;;
    backup)
        backup_database
        ;;
    health)
        health_check
        ;;
    *)
        echo "用法: $0 {init|start|stop|restart|update|backup|health}"
        echo ""
        echo "  init    - 首次部署（初始化目录、构建镜像、启动服务）"
        echo "  start   - 启动服务"
        echo "  stop    - 停止服务"
        echo "  restart - 重启服务"
        echo "  update  - 更新部署（拉取代码、重新构建、滚动更新）"
        echo "  backup  - 备份数据库"
        echo "  health  - 健康检查"
        exit 1
        ;;
esac
