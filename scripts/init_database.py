"""
数据库初始化脚本
创建表结构并导入初始数据
"""

import sys
import os
import asyncio
import logging

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SQL 创建表语句
CREATE_TABLES_SQL = """
-- 商品表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100),
    sku VARCHAR(100) UNIQUE NOT NULL,
    image_url TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    platform VARCHAR(50),
    room_id VARCHAR(255),
    messages JSONB DEFAULT '[]'::jsonb,
    context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 直播记录表
CREATE TABLE IF NOT EXISTS live_sessions (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(255) NOT NULL,
    anchor_name VARCHAR(255),
    platform VARCHAR(50),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    stats JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 弹幕记录表
CREATE TABLE IF NOT EXISTS danmaku_records (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    username VARCHAR(255),
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sentiment VARCHAR(50),
    is_processed BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 商品销售记录表
CREATE TABLE IF NOT EXISTS sales_records (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    user_id VARCHAR(255),
    room_id VARCHAR(255),
    sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 人工接管记录表
CREATE TABLE IF NOT EXISTS human_takeovers (
    id SERIAL PRIMARY KEY,
    room_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    trigger_reason TEXT,
    trigger_confidence DECIMAL(3, 2),
    danmaku_content TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    handler VARCHAR(255),
    handle_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 知识库文档表
CREATE TABLE IF NOT EXISTS knowledge_documents (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) UNIQUE NOT NULL,
    product_id VARCHAR(255),
    product_name VARCHAR(500),
    content TEXT NOT NULL,
    chunk_type VARCHAR(50),
    chunk_index INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_danmaku_room_id ON danmaku_records(room_id);
CREATE INDEX IF NOT EXISTS idx_danmaku_timestamp ON danmaku_records(timestamp);
CREATE INDEX IF NOT EXISTS idx_sales_product_id ON sales_records(product_id);
CREATE INDEX IF NOT EXISTS idx_takeovers_status ON human_takeovers(status);

-- 启用pgvector扩展（如果使用向量搜索）
CREATE EXTENSION IF NOT EXISTS vector;

-- 向量嵌入表（如果使用向量搜索）
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id SERIAL PRIMARY KEY,
    doc_id VARCHAR(255) REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
    embedding VECTOR(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建向量索引
CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
ON knowledge_embeddings 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""


async def create_tables():
    """创建数据库表结构"""
    try:
        from sqlalchemy import create_engine, text
        from dotenv import load_dotenv
        
        # 加载环境变量
        load_dotenv()
        
        # 获取数据库连接URL
        database_url = os.getenv("DATABASE_URL")
        
        if not database_url:
            logger.error("❌ 未配置 DATABASE_URL 环境变量")
            logger.info("请在 .env 文件中配置数据库连接信息")
            return False
        
        logger.info(f"📡 连接数据库...")
        
        # 创建数据库引擎
        engine = create_engine(database_url)
        
        # 执行SQL语句
        with engine.connect() as conn:
            # 分割SQL语句并逐个执行
            statements = [s.strip() for s in CREATE_TABLES_SQL.split(';') if s.strip()]
            
            for statement in statements:
                try:
                    conn.execute(text(statement))
                    conn.commit()
                except Exception as e:
                    # 忽略已存在的错误
                    if "already exists" not in str(e).lower():
                        logger.warning(f"执行SQL警告: {str(e)}")
        
        logger.info("✅ 数据库表结构创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建表结构失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def init_products():
    """初始化商品数据"""
    try:
        from storage.database.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        
        # 商品数据
        products = [
            {
                "name": "iPhone 15 Pro",
                "description": "苹果最新旗舰手机，A17 Pro芯片，钛金属边框，支持USB-C",
                "price": 7999.00,
                "stock": 50,
                "category": "手机",
                "sku": "IP15PRO-256",
                "image_url": "https://example.com/iphone15pro.jpg",
                "is_active": True
            },
            {
                "name": "MacBook Air M3",
                "description": "轻薄笔记本，M3芯片，13.6英寸Liquid视网膜显示屏，续航18小时",
                "price": 8999.00,
                "stock": 30,
                "category": "电脑",
                "sku": "MBAIR-M3-13",
                "image_url": "https://example.com/macbookair.jpg",
                "is_active": True
            },
            {
                "name": "AirPods Pro 2",
                "description": "主动降噪耳机，空间音频，MagSafe充电盒，续航6小时",
                "price": 1899.00,
                "stock": 100,
                "category": "耳机",
                "sku": "APPRO-2-USB",
                "image_url": "https://example.com/airpodspro.jpg",
                "is_active": True
            },
            {
                "name": "iPad Air 5",
                "description": "10.9英寸平板电脑，M1芯片，支持Apple Pencil 2，全层压显示屏",
                "price": 4799.00,
                "stock": 0,
                "category": "平板",
                "sku": "IPAD-AIR-5-64",
                "image_url": "https://example.com/ipadair5.jpg",
                "is_active": True
            },
            {
                "name": "Apple Watch Series 9",
                "description": "智能手表，S9芯片，全天候视网膜显示屏，健康监测",
                "price": 2999.00,
                "stock": 45,
                "category": "手表",
                "sku": "AW-S9-41",
                "image_url": "https://example.com/applewatch.jpg",
                "is_active": True
            },
            {
                "name": "智能保温杯",
                "description": "316不锈钢内胆，智能温控，保温12小时，APP远程控制",
                "price": 199.00,
                "stock": 200,
                "category": "家居",
                "sku": "CUP-SMART-500",
                "image_url": "https://example.com/smartcup.jpg",
                "is_active": True
            },
            {
                "name": "无线蓝牙耳机",
                "description": "主动降噪，蓝牙5.3，续航30小时，IPX5防水",
                "price": 299.00,
                "stock": 150,
                "category": "耳机",
                "sku": "BT-HEADSET-PRO",
                "image_url": "https://example.com/btheadset.jpg",
                "is_active": True
            },
            {
                "name": "有机坚果礼盒",
                "description": "精选6种有机坚果，无添加无漂白，独立小包装",
                "price": 168.00,
                "stock": 80,
                "category": "食品",
                "sku": "NUT-GIFT-600",
                "image_url": "https://example.com/nuts.jpg",
                "is_active": True
            }
        ]
        
        # 清空现有数据
        logger.info("🗑️  清空现有商品数据...")
        try:
            client.table('products').delete().neq('id', 0).execute()
        except:
            pass
        
        # 插入商品数据
        logger.info("📦 插入商品数据...")
        response = client.table('products').insert(products).execute()
        
        logger.info(f"✅ 成功插入 {len(response.data)} 个商品")
        for product in response.data:
            status = "✅" if product['stock'] > 0 else "❌"
            logger.info(f"  {status} {product['name']} (ID: {product['id']}, 库存: {product['stock']})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 初始化商品数据失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_connection():
    """测试数据库连接"""
    try:
        from storage.database.supabase_client import get_supabase_client
        
        client = get_supabase_client()
        
        # 测试查询
        response = client.table('products').select('count', count='exact').execute()
        
        count = response.count if hasattr(response, 'count') else 0
        logger.info(f"✅ 数据库连接正常，当前商品数量: {count}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {str(e)}")
        return False


async def main():
    """主函数"""
    logger.info("="*60)
    logger.info("🚀 直播带货AI助手 - 数据库初始化")
    logger.info("="*60)
    
    # 步骤1: 创建表结构
    logger.info("\n📋 步骤1: 创建数据库表结构...")
    if not await create_tables():
        logger.error("❌ 表结构创建失败，请检查数据库配置")
        return False
    
    # 步骤2: 测试数据库连接
    logger.info("\n📋 步骤2: 测试数据库连接...")
    if not await test_database_connection():
        logger.error("❌ 数据库连接失败，请检查环境变量配置")
        return False
    
    # 步骤3: 导入商品数据
    logger.info("\n📋 步骤3: 导入初始商品数据...")
    if not await init_products():
        logger.error("❌ 商品数据导入失败")
        return False
    
    logger.info("\n" + "="*60)
    logger.info("✅ 数据库初始化完成！")
    logger.info("="*60)
    logger.info("\n📝 后续步骤:")
    logger.info("  1. 配置 Redis 服务（必需）")
    logger.info("  2. 配置直播平台 API 凭证（必需）")
    logger.info("  3. 配置告警通知渠道（推荐）")
    logger.info("  4. 运行知识库导入脚本（可选）")
    logger.info("  5. 启动服务: python scripts/run_prod.py")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
