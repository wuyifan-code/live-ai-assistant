"""
商品信息查询工具
用于查询商品的价格、库存、详情等信息
"""

import json
import os
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context

# 商品数据文件路径
PRODUCTS_FILE = "assets/products.json"

def _load_products():
    """加载商品数据"""
    if not os.path.exists(PRODUCTS_FILE):
        # 如果文件不存在，创建示例数据
        sample_products = [
            {
                "id": 1,
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
                "id": 2,
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
                "id": 3,
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
                "id": 4,
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
                "id": 5,
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
        
        # 确保assets目录存在
        os.makedirs(os.path.dirname(PRODUCTS_FILE), exist_ok=True)
        
        with open(PRODUCTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(sample_products, f, ensure_ascii=False, indent=2)
        
        return sample_products
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _search_product_by_name(query: str, products: list) -> list:
    """根据商品名称搜索"""
    query_lower = query.lower()
    results = []
    
    for product in products:
        # 搜索商品名称
        if query_lower in product['name'].lower():
            results.append(product)
        # 搜索SKU
        elif query_lower in product.get('sku', '').lower():
            results.append(product)
    
    return results


@tool
def query_product(product_name: str, runtime: ToolRuntime = None) -> str:
    """
    查询商品信息
    
    参数:
        product_name: 商品名称或SKU（如"iPhone 15 Pro"、"IP15PRO-256"）
    
    返回:
        商品详细信息，包括名称、价格、库存、描述等
    """
    ctx = runtime.context if runtime else new_context(method="query_product")
    
    try:
        products = _load_products()
        results = _search_product_by_name(product_name, products)
        
        if not results:
            return f"未找到商品: {product_name}。请尝试其他关键词。"
        
        # 如果有多个结果，返回所有匹配的商品
        if len(results) > 1:
            response_parts = [f"找到 {len(results)} 个匹配的商品:\n"]
            for product in results:
                stock_status = "有货" if product['stock'] > 0 else "缺货"
                response_parts.append(
                    f"\n- 商品: {product['name']}\n"
                    f"  SKU: {product['sku']}\n"
                    f"  价格: ¥{product['price']:.2f}\n"
                    f"  库存: {product['stock']} ({stock_status})\n"
                    f"  描述: {product['description'][:50]}..."
                )
            return "\n".join(response_parts)
        
        # 只有一个结果，返回详细信息
        product = results[0]
        stock_status = "有货" if product['stock'] > 0 else "缺货"
        
        response = (
            f"【商品信息】\n"
            f"商品名称: {product['name']}\n"
            f"SKU: {product['sku']}\n"
            f"价格: ¥{product['price']:.2f}\n"
            f"库存: {product['stock']} 件 ({stock_status})\n"
            f"分类: {product['category']}\n"
            f"描述: {product['description']}\n"
            f"状态: {'上架中' if product['is_active'] else '已下架'}"
        )
        
        return response
    
    except Exception as e:
        return f"查询商品信息失败: {str(e)}"


@tool
def query_product_list(category: str = "", runtime: ToolRuntime = None) -> str:
    """
    查询商品列表
    
    参数:
        category: 商品分类（可选，如"手机"、"电脑"等）
    
    返回:
        商品列表，包含名称、价格、库存等信息
    """
    ctx = runtime.context if runtime else new_context(method="query_product_list")
    
    try:
        products = _load_products()
        
        # 如果指定了分类，进行过滤
        if category:
            products = [p for p in products if category.lower() in p.get('category', '').lower()]
        
        if not products:
            return "没有找到相关商品。"
        
        response_parts = [f"共找到 {len(products)} 个商品:\n"]
        
        for product in products:
            stock_status = "有货" if product['stock'] > 0 else "缺货"
            response_parts.append(
                f"\n{product['id']}. {product['name']}\n"
                f"   价格: ¥{product['price']:.2f} | 库存: {product['stock']} ({stock_status}) | SKU: {product['sku']}"
            )
        
        return "\n".join(response_parts)
    
    except Exception as e:
        return f"查询商品列表失败: {str(e)}"


@tool
def get_product_by_sku(sku: str, runtime: ToolRuntime = None) -> str:
    """
    根据SKU查询商品
    
    参数:
        sku: 商品SKU代码
    
    返回:
        商品详细信息
    """
    ctx = runtime.context if runtime else new_context(method="get_product_by_sku")
    
    try:
        products = _load_products()
        
        for product in products:
            if product.get('sku', '').lower() == sku.lower():
                stock_status = "有货" if product['stock'] > 0 else "缺货"
                
                response = (
                    f"【商品信息】\n"
                    f"商品名称: {product['name']}\n"
                    f"SKU: {product['sku']}\n"
                    f"价格: ¥{product['price']:.2f}\n"
                    f"库存: {product['stock']} 件 ({stock_status})\n"
                    f"分类: {product['category']}\n"
                    f"描述: {product['description']}\n"
                    f"状态: {'上架中' if product['is_active'] else '已下架'}"
                )
                return response
        
        return f"未找到SKU为 {sku} 的商品。"
    
    except Exception as e:
        return f"根据SKU查询商品失败: {str(e)}"
