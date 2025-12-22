#!/bin/bash
# 雅典娜生产环境配置验证脚本

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

echo "========================================"
echo "  雅典娜生产环境配置验证"
echo "========================================"
echo ""

# 1. 检查 .env 文件
echo "1. 检查配置文件..."
if [ -f ".env" ]; then
    check_pass ".env 文件存在"
    
    # 检查关键配置项
    source .env
    
    # 检查密码强度
    if [ ${#POSTGRES_PASSWORD} -lt 16 ]; then
        check_fail "POSTGRES_PASSWORD 长度不足（当前: ${#POSTGRES_PASSWORD}，建议: >=32）"
    else
        check_pass "POSTGRES_PASSWORD 长度充足"
    fi
    
    if [ ${#JWT_SECRET_KEY} -lt 32 ]; then
        check_fail "JWT_SECRET_KEY 长度不足（当前: ${#JWT_SECRET_KEY}，建议: >=64）"
    else
        check_pass "JWT_SECRET_KEY 长度充足"
    fi
    
    # 检查是否使用默认值
    if [ "$JWT_SECRET_KEY" == "your-super-secret-key-change-in-production" ]; then
        check_fail "JWT_SECRET_KEY 仍使用默认值！"
    else
        check_pass "JWT_SECRET_KEY 已自定义"
    fi
    
    if [ "$APP_ENV" != "production" ]; then
        check_warn "APP_ENV 不是 'production'（当前: $APP_ENV）"
    else
        check_pass "APP_ENV 设置为 production"
    fi
    
    if [ "$DEBUG" != "false" ]; then
        check_warn "DEBUG 未设置为 false（当前: $DEBUG）"
    else
        check_pass "DEBUG 已关闭"
    fi
else
    check_fail ".env 文件不存在！请复制 .env.production.example"
fi
echo ""

# 2. 检查数据目录
echo "2. 检查数据目录..."
if [ -d "/home/vitiana/Athena/data_ssd" ]; then
    check_pass "SSD 数据目录存在"
    
    # 检查权限
    if [ -w "/home/vitiana/Athena/data_ssd" ]; then
        check_pass "SSD 目录可写"
    else
        check_fail "SSD 目录不可写"
    fi
    
    # 检查磁盘空间
    SSD_AVAIL=$(df -BG /home/vitiana/Athena/data_ssd | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$SSD_AVAIL" -lt 50 ]; then
        check_warn "SSD 可用空间不足 50GB（当前: ${SSD_AVAIL}GB）"
    else
        check_pass "SSD 可用空间充足（${SSD_AVAIL}GB）"
    fi
else
    check_fail "SSD 数据目录不存在"
fi

if [ -d "/data/athena" ]; then
    check_pass "HDD 数据目录存在"
    
    if [ -w "/data/athena" ]; then
        check_pass "HDD 目录可写"
    else
        check_fail "HDD 目录不可写"
    fi
    
    # 检查磁盘空间
    HDD_AVAIL=$(df -BG /data/athena | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$HDD_AVAIL" -lt 500 ]; then
        check_warn "HDD 可用空间不足 500GB（当前: ${HDD_AVAIL}GB）"
    else
        check_pass "HDD 可用空间充足（${HDD_AVAIL}GB）"
    fi
else
    check_fail "HDD 数据目录不存在"
fi
echo ""

# 3. 检查 Docker
echo "3. 检查 Docker 环境..."
if command -v docker &> /dev/null; then
    check_pass "Docker 已安装"
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo "   版本: $DOCKER_VERSION"
    
    # 检查 Docker Compose
    if docker compose version &> /dev/null; then
        check_pass "Docker Compose 已安装"
        COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
        echo "   版本: $COMPOSE_VERSION"
    else
        check_fail "Docker Compose 未安装"
    fi
else
    check_fail "Docker 未安装"
fi
echo ""

# 4. 检查 GPU
echo "4. 检查 GPU 环境..."
if command -v nvidia-smi &> /dev/null; then
    check_pass "nvidia-smi 可用"
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader)
    GPU_MEM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits)
    echo "   GPU: $GPU_NAME"
    echo "   显存: ${GPU_MEM}MB"
    
    if [ "$GPU_MEM" -lt 8000 ]; then
        check_warn "GPU 显存不足 8GB，OCR 性能可能受限"
    else
        check_pass "GPU 显存充足"
    fi
    
    # 检查 nvidia-docker
    if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
        check_pass "nvidia-docker 可用"
    else
        check_fail "nvidia-docker 不可用"
    fi
else
    check_fail "nvidia-smi 未找到，GPU 功能不可用"
fi
echo ""

# 5. 检查网络端口
echo "5. 检查端口占用..."
check_port() {
    PORT=$1
    NAME=$2
    if netstat -tuln 2>/dev/null | grep -q ":$PORT "; then
        check_warn "端口 $PORT ($NAME) 已被占用"
    else
        check_pass "端口 $PORT ($NAME) 可用"
    fi
}

check_port 45432 "PostgreSQL"
check_port 46432 "PgBouncer"
check_port 46379 "Valkey"
check_port 48000 "API"
check_port 48090 "PowerSync"
check_port 49000 "MinIO"
echo ""

# 6. 检查系统资源
echo "6. 检查系统资源..."
# CPU
CPU_CORES=$(nproc)
if [ "$CPU_CORES" -lt 8 ]; then
    check_warn "CPU 核心数不足 8 核（当前: $CPU_CORES）"
else
    check_pass "CPU 核心数充足（$CPU_CORES 核）"
fi

# 内存
TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
if [ "$TOTAL_MEM" -lt 32 ]; then
    check_warn "系统内存不足 32GB（当前: ${TOTAL_MEM}GB）"
else
    check_pass "系统内存充足（${TOTAL_MEM}GB）"
fi

# 可用内存
AVAIL_MEM=$(free -g | awk '/^Mem:/{print $7}')
if [ "$AVAIL_MEM" -lt 16 ]; then
    check_warn "可用内存不足 16GB（当前: ${AVAIL_MEM}GB）"
else
    check_pass "可用内存充足（${AVAIL_MEM}GB）"
fi
echo ""

# 7. 检查 PowerSync 配置
echo "7. 检查 PowerSync 配置..."
if [ -f "powersync/powersync.yaml" ]; then
    check_pass "PowerSync 配置文件存在"
    
    if [ -f "powersync/sync-rules.yaml" ]; then
        check_pass "同步规则文件存在"
    else
        check_fail "同步规则文件不存在"
    fi
else
    check_fail "PowerSync 配置文件不存在"
fi
echo ""

# 总结
echo "========================================"
echo "  验证结果"
echo "========================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ 配置完美！可以开始部署${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ 有 $WARNINGS 个警告，建议修复后再部署${NC}"
    exit 0
else
    echo -e "${RED}✗ 有 $ERRORS 个错误和 $WARNINGS 个警告，必须修复后才能部署${NC}"
    exit 1
fi
