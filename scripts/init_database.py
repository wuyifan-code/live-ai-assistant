"""
初始化数据库 - 导入商品数据到PostgreSQL
"""

import sys
import os

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.storage.database.supabase_client import get_supabase_client

def init_products():
    """初始化商品数据"""
    client = get_supabase_client()
    
    # 商品数据
    products = [
        {
            "name": "iPhone 15 Pro",
            "description": "苹果最新旗舰手机，A17 Pro芯片，钛金属边框",
            "price": 7999.00,
            "stock": 50,
            "category": "手机",
            "sku": "IP15PRO-256",
            "image_url": "https://example.com/iphone15pro.jpg",
            "is_active": True
        },
        {
            "name": "MacBook Air M3",
            "description": "轻薄笔记本，M3芯片，13.6英寸Liquid视网膜显示屏",
            "price": 8999.00,
            "stock": 30,
            "category": "电脑",
            "sku": "MBAIR-M3-13",
            "image_url": "https://example.com/macbookair.jpg",
            "is_active": True
        },
        {
            "name": "AirPods Pro 2",
            "description": "主动降噪耳机，空间音频，MagSafe充电盒",
            "price": 1899.00,
            "stock": 100,
            "category": "耳机",
            "sku": "APPRO-2-USB",
            "image_url": "https://example.com/airpodspro.jpg",
            "is_active": True
        },
        {
            "name": "iPad Air 5",
            "description": "10.9英寸平板电脑，M1芯片，支持Apple Pencil 2",
            "price": 4799.00,
            "stock": 0,
            "category": "平板",
            "sku": "IPAD-AIR-5-64",
            "image_url": "https://example.com/ipadair5.jpg",
            "is_active": True
        },
        {
            "name": "Apple Watch Series 9",
            "description": "智能手表，S9芯片，全天候视网膜显示屏",
            "price": 2999.00,
            "stock": 45,
            "category": "手表",
            "sku": "AW-S9-41",
            "image_url": "https://example.com/applewatch.jpg",
            "is_active": True
        }
    ]
    
    # 清空现有数据
    print("清空现有商品数据...")
    client.table('products').delete().neq('id', 0).execute()
    
    # 插入商品数据
    print("插入商品数据...")
    response = client.table('products').insert(products).execute()
    
    print(f"✅ 成功插入 {len(response.data)} 个商品")
    for product in response.data:
        print(f"  - {product['name']} (ID: {product['id']})")


if __name__ == "__main__":
    try:
        init_products()
        print("\n✅ 数据库初始化完成！")
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
