#!/bin/bash

# ===========================================
# 直播带货AI助手 - 快速启动脚本
# ===========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示欢迎信息
show_banner() {
    echo ""
    echo "======================================"
    echo "  直播带货AI助手 - 快速启动"
    echo "======================================"
    echo ""
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_success "Python已安装: $PYTHON_VERSION"
    else
        log_error "未找到Python3，请先安装Python 3.12+"
        exit 1
    fi
}

# 检查.env文件
check_env_file() {
    log_info "检查环境变量配置..."
    
    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，正在从模板创建..."
        cp .env.example .env
        log_warning "请编辑 .env 文件并填写必要配置"
        log_info "必要配置项:"
        log_info "  - DATABASE_URL (PostgreSQL连接)"
        log_info "  - REDIS_HOST (Redis连接)"
        log_info "  - DOUYIN_APP_ID / DOUYIN_APP_SECRET (抖音API)"
        
        read -p "是否现在编辑 .env 文件? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ${EDITOR:-vim} .env
        else
            log_error "请先配置 .env 文件后再运行此脚本"
            exit 1
        fi
    else
        log_success ".env 文件已存在"
    fi
}

# 检查Redis服务
check_redis() {
    log_info "检查Redis服务..."
    
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            log_success "Redis服务正在运行"
        else
            log_warning "Redis服务未运行，尝试启动..."
            
            if command -v systemctl &> /dev/null; then
                sudo systemctl start redis-server || sudo systemctl start redis
            elif command -v brew &> /dev/null; then
                brew services start redis
            else
                log_error "无法自动启动Redis，请手动启动"
                log_info "启动命令: sudo systemctl start redis-server"
                exit 1
            fi
            
            sleep 2
            if redis-cli ping &> /dev/null; then
                log_success "Redis服务启动成功"
            else
                log_error "Redis服务启动失败"
                exit 1
            fi
        fi
    else
        log_warning "未安装Redis CLI"
        log_info "安装方法:"
        log_info "  Ubuntu/Debian: sudo apt install redis-server"
        log_info "  macOS: brew install redis"
        log_info "  或使用Docker: docker run -d -p 6379:6379 redis:5.0-alpine"
        exit 1
    fi
}

# 检查PostgreSQL服务
check_postgres() {
    log_info "检查PostgreSQL服务..."
    
    if command -v psql &> /dev/null; then
        if pg_isready &> /dev/null; then
            log_success "PostgreSQL服务正在运行"
        else
            log_warning "PostgreSQL服务未运行，尝试启动..."
            
            if command -v systemctl &> /dev/null; then
                sudo systemctl start postgresql
            elif command -v brew &> /dev/null; then
                brew services start postgresql@14
            else
                log_error "无法自动启动PostgreSQL，请手动启动"
                exit 1
            fi
            
            sleep 2
            if pg_isready &> /dev/null; then
                log_success "PostgreSQL服务启动成功"
            else
                log_error "PostgreSQL服务启动失败"
                exit 1
            fi
        fi
    else
        log_warning "未找到PostgreSQL CLI"
        log_info "如果使用Supabase，可以忽略此警告"
    fi
}

# 安装Python依赖
install_dependencies() {
    log_info "检查Python依赖..."
    
    if [ ! -d "venv" ]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
    fi
    
    log_info "激活虚拟环境..."
    source venv/bin/activate
    
    log_info "安装依赖包..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    log_success "依赖安装完成"
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    if [ -f "scripts/init_database.py" ]; then
        python scripts/init_database.py
        
        if [ $? -eq 0 ]; then
            log_success "数据库初始化完成"
        else
            log_warning "数据库初始化失败，请检查数据库配置"
        fi
    else
        log_warning "未找到数据库初始化脚本"
    fi
}

# 导入知识库（可选）
import_knowledge() {
    log_info "是否导入示例知识库数据? (y/n): "
    read -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "导入示例知识库..."
        python -m src.utils.knowledge_importer import_sample
        
        if [ $? -eq 0 ]; then
            log_success "知识库导入完成"
        else
            log_warning "知识库导入失败，可以稍后手动导入"
        fi
    fi
}

# 启动服务
start_service() {
    log_info "启动服务..."
    
    # 检查启动脚本
    if [ -f "scripts/run_prod.py" ]; then
        log_success "服务启动中..."
        log_info "访问地址:"
        log_info "  - 主服务: http://localhost:8000"
        log_info "  - API文档: http://localhost:8000/docs"
        log_info "  - 监控面板: http://localhost:8000/monitoring"
        log_info ""
        log_warning "按 Ctrl+C 停止服务"
        echo ""
        
        python scripts/run_prod.py
    else
        log_error "未找到启动脚本 scripts/run_prod.py"
        exit 1
    fi
}

# 主函数
main() {
    show_banner
    
    # 执行检查
    check_python
    check_env_file
    check_redis
    check_postgres
    install_dependencies
    init_database
    import_knowledge
    
    # 启动服务
    echo ""
    log_success "所有检查通过！"
    echo ""
    
    start_service
}

# 运行主函数
main
