#!/bin/bash
#
# verify_setup.sh - 验证雅典娜部署配置
# 用于检查 LAN 环境配置是否正确
#

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "  雅典娜部署配置验证"
echo "========================================"
echo ""

ERRORS=0
WARNINGS=0

# 检查函数
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

# 1. 检查 .env 文件
echo "【1】检查环境配置文件..."
if [ -f ".env" ]; then
    check_pass ".env 文件存在"
    
    # 检查关键变量
    if grep -q "MINIO_EXTERNAL_ENDPOINT" .env 2>/dev/null; then
        MINIO_EXT=$(grep "MINIO_EXTERNAL_ENDPOINT" .env | cut -d'=' -f2)
        check_pass "MINIO_EXTERNAL_ENDPOINT 已配置: $MINIO_EXT"
    else
        check_fail "MINIO_EXTERNAL_ENDPOINT 未配置"
    fi
    
    if grep -q "ENABLE_DOCS" .env 2>/dev/null; then
        ENABLE_DOCS=$(grep "ENABLE_DOCS" .env | cut -d'=' -f2)
        check_pass "ENABLE_DOCS 已配置: $ENABLE_DOCS"
    else
        check_warn "ENABLE_DOCS 未配置 (将使用默认值 true)"
    fi
    
    if grep -q "CORS_ORIGINS" .env 2>/dev/null; then
        check_pass "CORS_ORIGINS 已配置"
    else
        check_fail "CORS_ORIGINS 未配置"
    fi
    
    if grep -q "FRONTEND_URL" .env 2>/dev/null; then
        FRONTEND_URL=$(grep "FRONTEND_URL" .env | cut -d'=' -f2)
        check_pass "FRONTEND_URL 已配置: $FRONTEND_URL"
    else
        check_warn "FRONTEND_URL 未配置"
    fi
else
    check_fail ".env 文件不存在"
fi
echo ""

# 2. 检查 deploy.sh 配置
echo "【2】检查 deploy.sh 更新逻辑..."
if [ -f "deploy.sh" ]; then
    check_pass "deploy.sh 存在"
    
    SERVICES=("api" "celery-worker" "celery-beat" "celery-conversion-worker" "celery-metadata-worker" "celery-indexing-worker" "celery-ocr-worker")
    for svc in "${SERVICES[@]}"; do
        if grep -q "$svc" deploy.sh 2>/dev/null; then
            check_pass "deploy.sh 包含服务: $svc"
        else
            check_fail "deploy.sh 缺少服务: $svc"
        fi
    done
else
    check_fail "deploy.sh 不存在"
fi
echo ""

# 3. 检查 docker-compose.prod.yml
echo "【3】检查 docker-compose.prod.yml..."
if [ -f "docker-compose.prod.yml" ]; then
    check_pass "docker-compose.prod.yml 存在"
    
    if grep -q "MINIO_EXTERNAL_ENDPOINT" docker-compose.prod.yml 2>/dev/null; then
        check_pass "docker-compose 包含 MINIO_EXTERNAL_ENDPOINT"
    else
        check_fail "docker-compose 缺少 MINIO_EXTERNAL_ENDPOINT"
    fi
    
    if grep -q "ENABLE_DOCS" docker-compose.prod.yml 2>/dev/null; then
        check_pass "docker-compose 包含 ENABLE_DOCS"
    else
        check_fail "docker-compose 缺少 ENABLE_DOCS"
    fi
    
    if grep -q "FRONTEND_URL" docker-compose.prod.yml 2>/dev/null; then
        check_pass "docker-compose 包含 FRONTEND_URL"
    else
        check_warn "docker-compose 缺少 FRONTEND_URL"
    fi
else
    check_fail "docker-compose.prod.yml 不存在"
fi
echo ""

# 4. 检查 requirements-ocr.txt GPU 依赖
echo "【4】检查 OCR GPU 依赖..."
if [ -f "requirements-ocr.txt" ]; then
    check_pass "requirements-ocr.txt 存在"
    
    if grep -q "paddlepaddle-gpu" requirements-ocr.txt 2>/dev/null; then
        check_pass "paddlepaddle-gpu 已配置"
    else
        check_fail "缺少 paddlepaddle-gpu (当前使用 CPU 版本)"
    fi
else
    check_fail "requirements-ocr.txt 不存在"
fi
echo ""

# 5. 检查容器状态 (如果 Docker 可用)
echo "【5】检查容器状态..."
if command -v docker &> /dev/null; then
    if docker compose -f docker-compose.prod.yml ps --format json 2>/dev/null | head -1 | grep -q "Name"; then
        UNHEALTHY=$(docker compose -f docker-compose.prod.yml ps 2>/dev/null | grep -c "unhealthy" || true)
        RUNNING=$(docker compose -f docker-compose.prod.yml ps 2>/dev/null | grep -c "Up" || true)
        
        if [ "$UNHEALTHY" -gt 0 ]; then
            check_fail "发现 $UNHEALTHY 个不健康的容器"
        else
            check_pass "所有容器健康 ($RUNNING 个运行中)"
        fi
    else
        check_warn "Docker Compose 未运行或无容器"
    fi
else
    check_warn "Docker 不可用，跳过容器检查"
fi
echo ""

# 6. 测试 API 端点 (如果服务运行中)
echo "【6】测试 API 端点..."
API_URL="http://192.168.0.122:48000"

if curl -s --connect-timeout 2 "$API_URL/health" > /dev/null 2>&1; then
    check_pass "API 健康检查通过: $API_URL/health"
    
    # 检查 Swagger 文档
    DOCS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$API_URL/docs" 2>/dev/null || echo "000")
    if [ "$DOCS_STATUS" = "200" ]; then
        check_pass "Swagger 文档可访问: $API_URL/docs"
    else
        check_warn "Swagger 文档不可访问 (HTTP $DOCS_STATUS)"
    fi
else
    check_warn "API 服务未运行，跳过端点测试"
fi
echo ""

# 7. 测试 MinIO 端点
echo "【7】测试 MinIO 端点..."
MINIO_URL="http://192.168.0.122:49000"

if curl -s --connect-timeout 2 "$MINIO_URL/minio/health/live" > /dev/null 2>&1; then
    check_pass "MinIO 健康检查通过: $MINIO_URL"
else
    check_warn "MinIO 服务未运行或端口未暴露"
fi
echo ""

# 结果汇总
echo "========================================"
echo "  验证结果"
echo "========================================"
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}全部检查通过！${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}发现 $WARNINGS 个警告，无错误${NC}"
    exit 0
else
    echo -e "${RED}发现 $ERRORS 个错误，$WARNINGS 个警告${NC}"
    exit 1
fi
