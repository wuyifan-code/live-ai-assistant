"""
商品信息查询工具 v2.0
使用PostgreSQL数据库和Redis缓存
"""

import logging
from typing import Optional
from langchain.tools import tool, ToolRuntime
from coze_coding_utils.runtime_ctx.context import new_context

from src.storage.database.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# 延迟导入Redis相关函数，以避免循环导入
def _get_redis_func(func_name: str):
    """延迟导入Redis缓存函数"""
    from src.storage.redis_cache import (
        get_cache,
        cache_product,
        get_cached_product,
        cache_product_price,
        get_cached_product_price,
        cache_product_stock,
        get_cached_product_stock
    )
    return {
        'get_cache': get_cache,
        'cache_product': cache_product,
        'get_cached_product': get_cached_product,
        'cache_product_price': cache_product_price,
        'get_cached_product_price': get_cached_product_price,
        'cache_product_stock': cache_product_stock,
        'get_cached_product_stock': get_cached_product_stock,
    }[func_name]


def _search_product_by_name(query: str, client) -> Optional[dict]:
    """根据商品名称或SKU搜索商品"""
    query_lower = query.lower()
    
    # 先尝试精确匹配SKU
    response = client.table('products').select('*').eq('sku', query).execute()
    if response.data:
        return response.data[0]
    
    # 模糊搜索商品名称
    response = client.table('products').select('*').ilike('name', f'%{query}%').execute()
    if response.data:
        return response.data[0]
    
    return None


@tool
def query_product_v2(product_name: str, runtime: ToolRuntime = None) -> str:
    """
    查询商品信息（使用数据库和缓存）
    
    参数:
        product_name: 商品名称或SKU（如"iPhone 15 Pro"、"IP15PRO-256"）
    
    返回:
        商品详细信息，包括名称、价格、库存、描述等
    """
    ctx = runtime.context if runtime else new_context(method="query_product_v2")
    
    try:
        client = get_supabase_client()
        cache = _get_redis_func('get_cache')
        
        # 先从缓存查询
        cached_result = cache.get(f"search:{product_name}")
        if cached_result:
            logger.info(f"✅ 从缓存获取商品: {product_name}")
            return cached_result
        
        # 从数据库查询
        product = _search_product_by_name(product_name, client)
        
        if not product:
            return f"未找到商品: {product_name}。请尝试其他关键词。"
        
        # 检查商品是否上架
        if not product.get('is_active', True):
            return f"商品已下架: {product['name']}"
        
        # 获取价格（优先从缓存）
        get_cached_product_price_func = _get_redis_func('get_cached_product_price')
        cache_product_price_func = _get_redis_func('cache_product_price')
        
        price = get_cached_product_price_func(product['id'])
        if price is None:
            price = float(product['price'])
            cache_product_price_func(product['id'], price)
        
        # 获取库存（优先从缓存）
        get_cached_product_stock_func = _get_redis_func('get_cached_product_stock')
        cache_product_stock_func = _get_redis_func('cache_product_stock')
        
        stock = get_cached_product_stock_func(product['id'])
        if stock is None:
            stock = int(product['stock'])
            cache_product_stock_func(product['id'], stock)
        
        stock_status = "有货" if stock > 0 else "缺货"
        
        response = (
            f"【商品信息】\n"
            f"商品名称: {product['name']}\n"
            f"SKU: {product['sku']}\n"
            f"价格: ¥{price:.2f}\n"
            f"库存: {stock} 件 ({stock_status})\n"
            f"分类: {product['category']}\n"
            f"描述: {product['description']}\n"
            f"状态: {'上架中' if product['is_active'] else '已下架'}"
        )
        
        # 缓存查询结果（2分钟）
        cache.set(f"search:{product_name}", response, ttl=120)
        
        return response
    
    except Exception as e:
        logger.error(f"查询商品失败: {str(e)}")
        return f"查询商品信息失败: {str(e)}"


@tool
def query_product_list_v2(category: str = "", limit: int = 20, runtime: ToolRuntime = None) -> str:
    """
    查询商品列表（使用数据库和缓存）
    
    参数:
        category: 商品分类（可选，如"手机"、"电脑"等）
        limit: 返回数量限制，默认20
    
    返回:
        商品列表，包含名称、价格、库存等信息
    """
    ctx = runtime.context if runtime else new_context(method="query_product_list_v2")
    
    try:
        client = get_supabase_client()
        cache = _get_redis_func('get_cache')
        
        # 生成缓存键
        cache_key = f"product_list:{category}:{limit}"
        
        # 先从缓存查询
        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info(f"✅ 从缓存获取商品列表: {category}")
            return cached_result
        
        # 构建查询
        query = client.table('products').select('*').eq('is_active', True)
        
        # 如果指定了分类，进行过滤
        if category:
            query = query.ilike('category', f'%{category}%')
        
        # 执行查询
        response = query.limit(limit).execute()
        products = response.data
        
        if not products:
            return "没有找到相关商品。"
        
        get_cached_product_stock_func = _get_redis_func('get_cached_product_stock')
        cache_product_stock_func = _get_redis_func('cache_product_stock')
        
        response_parts = [f"共找到 {len(products)} 个商品:\n"]
        
        for product in products:
            stock = get_cached_product_stock_func(product['id'])
            if stock is None:
                stock = int(product['stock'])
                cache_product_stock_func(product['id'], stock)
            
            stock_status = "有货" if stock > 0 else "缺货"
            response_parts.append(
                f"\n{product['id']}. {product['name']}\n"
                f"   价格: ¥{float(product['price']):.2f} | "
                f"库存: {stock} ({stock_status}) | "
                f"SKU: {product['sku']}"
            )
        
        result = "\n".join(response_parts)
        
        # 缓存查询结果（3分钟）
        cache.set(cache_key, result, ttl=180)
        
        return result
    
    except Exception as e:
        logger.error(f"查询商品列表失败: {str(e)}")
        return f"查询商品列表失败: {str(e)}"


@tool
def get_product_by_sku_v2(sku: str, runtime: ToolRuntime = None) -> str:
    """
    根据SKU查询商品（使用数据库和缓存）
    
    参数:
        sku: 商品SKU代码
    
    返回:
        商品详细信息
    """
    ctx = runtime.context if runtime else new_context(method="get_product_by_sku_v2")
    
    try:
        client = get_supabase_client()
        cache = _get_redis_func('get_cache')
        
        # 先从缓存查询
        cached_result = cache.get(f"sku:{sku}")
        if cached_result:
            logger.info(f"✅ 从缓存获取SKU商品: {sku}")
            return cached_result
        
        # 从数据库查询
        response = client.table('products').select('*').eq('sku', sku).execute()
        
        if not response.data:
            return f"未找到SKU为 {sku} 的商品。"
        
        product = response.data[0]
        
        # 获取价格和库存（优先从缓存）
        get_cached_product_price_func = _get_redis_func('get_cached_product_price')
        cache_product_price_func = _get_redis_func('cache_product_price')
        get_cached_product_stock_func = _get_redis_func('get_cached_product_stock')
        cache_product_stock_func = _get_redis_func('cache_product_stock')
        
        price = get_cached_product_price_func(product['id'])
        if price is None:
            price = float(product['price'])
            cache_product_price_func(product['id'], price)
        
        stock = get_cached_product_stock_func(product['id'])
        if stock is None:
            stock = int(product['stock'])
            cache_product_stock(product['id'], stock)
        
        stock_status = "有货" if stock > 0 else "缺货"
        
        response = (
            f"【商品信息】\n"
            f"商品名称: {product['name']}\n"
            f"SKU: {product['sku']}\n"
            f"价格: ¥{price:.2f}\n"
            f"库存: {stock} 件 ({stock_status})\n"
            f"分类: {product['category']}\n"
            f"描述: {product['description']}\n"
            f"状态: {'上架中' if product['is_active'] else '已下架'}"
        )
        
        # 缓存查询结果（5分钟）
        cache.set(f"sku:{sku}", response, ttl=300)
        
        return response
    
    except Exception as e:
        logger.error(f"根据SKU查询商品失败: {str(e)}")
        return f"根据SKU查询商品失败: {str(e)}"


@tool
def update_product_stock(product_id: int, new_stock: int, runtime: ToolRuntime = None) -> str:
    """
    更新商品库存并刷新缓存
    
    参数:
        product_id: 商品ID
        new_stock: 新的库存数量
    
    返回:
        更新结果
    """
    ctx = runtime.context if runtime else new_context(method="update_product_stock")
    
    try:
        client = get_supabase_client()
        
        # 更新数据库
        response = client.table('products').update({'stock': new_stock}).eq('id', product_id).execute()
        
        if not response.data:
            return f"未找到ID为 {product_id} 的商品。"
        
        product = response.data[0]
        
        # 刷新缓存
        cache_product_stock(product_id, new_stock)
        
        return f"✅ 商品库存更新成功：{product['name']} -> {new_stock} 件"
    
    except Exception as e:
        logger.error(f"更新商品库存失败: {str(e)}")
        return f"更新商品库存失败: {str(e)}"
