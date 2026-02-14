"""
价格/库存核对工具
用于检测主播讲错价格或库存，并提供官方更正信息
"""

import json
import os
import re
from langchain.tools import tool, ToolRuntime
from langchain_core.messages import HumanMessage
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context

# 商品数据文件路径
PRODUCTS_FILE = "assets/products.json"


def _load_products():
    """加载商品数据"""
    if not os.path.exists(PRODUCTS_FILE):
        return []
    
    with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def _find_product_by_name(query: str, products: list) -> dict:
    """根据商品名称查找商品"""
    query_lower = query.lower()
    
    for product in products:
        # 搜索商品名称
        if query_lower in product['name'].lower():
            return product
        # 搜索SKU
        elif query_lower in product.get('sku', '').lower():
            return product
    
    return None


def _extract_price(text: str) -> float:
    """从文本中提取价格"""
    # 匹配价格格式：¥100、100元、100.5元等
    patterns = [
        r'¥(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*元',
        r'(\d+\.?\d*)\s*块钱',
        r'价格\s*(?:为|:|是)\s*(\d+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
    
    return None


def _extract_stock(text: str) -> int:
    """从文本中提取库存数量"""
    # 匹配库存格式：库存100、还有100件、100台等
    patterns = [
        r'库存\s*(?:为|:|是|有)\s*(\d+)',
        r'还有\s*(\d+)\s*(?:件|台|个|套)',
        r'(\d+)\s*(?:件|台|个|套)\s*(?:库存)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    
    return None


@tool
def verify_price(product_name: str, stated_price: float, runtime: ToolRuntime = None) -> str:
    """
    核对商品价格是否正确
    
    参数:
        product_name: 商品名称
        stated_price: 主播说的价格
    
    返回:
        核对结果，如果价格错误则提供更正信息
    """
    ctx = runtime.context if runtime else new_context(method="verify_price")
    
    try:
        products = _load_products()
        product = _find_product_by_name(product_name, products)
        
        if not product:
            return f"未找到商品: {product_name}，无法核对价格。"
        
        actual_price = float(product['price'])
        
        # 允许价格误差在1元以内（可能是四舍五入）
        price_diff = abs(stated_price - actual_price)
        
        if price_diff <= 1.0:
            return (
                f"✓ 价格核对正确\n"
                f"商品: {product['name']}\n"
                f"主播说的价格: ¥{stated_price:.2f}\n"
                f"实际价格: ¥{actual_price:.2f}\n"
                f"无需更正。"
            )
        else:
            # 价格错误，返回更正信息
            return (
                f"⚠ 【官方更正】价格错误！\n"
                f"商品: {product['name']}\n"
                f"主播说的价格: ¥{stated_price:.2f}\n"
                f"实际价格: ¥{actual_price:.2f}\n"
                f"差价: ¥{abs(stated_price - actual_price):.2f}\n\n"
                f"请主播注意：正确价格应该是 ¥{actual_price:.2f}！"
            )
    
    except Exception as e:
        return f"核对价格失败: {str(e)}"


@tool
def verify_stock(product_name: str, stated_stock: int, runtime: ToolRuntime = None) -> str:
    """
    核对商品库存是否正确
    
    参数:
        product_name: 商品名称
        stated_stock: 主播说的库存数量
    
    返回:
        核对结果，如果库存错误或不足则提供更正信息
    """
    ctx = runtime.context if runtime else new_context(method="verify_stock")
    
    try:
        products = _load_products()
        product = _find_product_by_name(product_name, products)
        
        if not product:
            return f"未找到商品: {product_name}，无法核对库存。"
        
        actual_stock = int(product['stock'])
        
        # 库存核对
        if stated_stock == actual_stock:
            stock_status = "有货" if actual_stock > 0 else "缺货"
            return (
                f"✓ 库存核对正确\n"
                f"商品: {product['name']}\n"
                f"主播说的库存: {stated_stock} 件\n"
                f"实际库存: {actual_stock} 件\n"
                f"状态: {stock_status}\n"
                f"无需更正。"
            )
        else:
            # 库存错误
            stock_status = "有货" if actual_stock > 0 else "缺货"
            
            return (
                f"⚠ 【官方更正】库存错误！\n"
                f"商品: {product['name']}\n"
                f"主播说的库存: {stated_stock} 件\n"
                f"实际库存: {actual_stock} 件\n"
                f"状态: {stock_status}\n\n"
                f"请主播注意：正确库存应该是 {actual_stock} 件！"
            )
    
    except Exception as e:
        return f"核对库存失败: {str(e)}"


@tool
def check_product_availability(product_name: str, runtime: ToolRuntime = None) -> str:
    """
    检查商品是否有货
    
    参数:
        product_name: 商品名称
    
    返回:
        商品库存状态
    """
    ctx = runtime.context if runtime else new_context(method="check_product_availability")
    
    try:
        products = _load_products()
        product = _find_product_by_name(product_name, products)
        
        if not product:
            return f"未找到商品: {product_name}。"
        
        stock = int(product['stock'])
        
        if stock == 0:
            return (
                f"⚠ 【库存提醒】\n"
                f"商品: {product['name']}\n"
                f"当前状态: 缺货\n"
                f"库存数量: 0\n\n"
                f"请主播注意：该商品已售罄，不要继续售卖！"
            )
        elif stock < 10:
            return (
                f"⚠ 【库存预警】\n"
                f"商品: {product['name']}\n"
                f"当前状态: 库存紧张\n"
                f"库存数量: {stock} 件\n\n"
                f"请主播注意：该商品库存不足，建议及时补货或提醒用户抢购！"
            )
        else:
            return (
                f"✓ 【库存状态】\n"
                f"商品: {product['name']}\n"
                f"当前状态: 有货\n"
                f"库存数量: {stock} 件\n"
                f"库存充足，可以放心销售。"
            )
    
    except Exception as e:
        return f"检查商品库存失败: {str(e)}"


@tool
def verify_anchor_speech(speech_text: str, runtime: ToolRuntime = None) -> str:
    """
    智能分析主播的语音内容，提取价格和库存信息进行核对
    
    参数:
        speech_text: 主播说的语音文本
    
    返回:
        核对结果，如果发现错误则提供更正
    """
    ctx = runtime.context if runtime else new_context(method="verify_anchor_speech")
    
    try:
        products = _load_products()
        
        # 提取价格和库存
        stated_price = _extract_price(speech_text)
        stated_stock = _extract_stock(speech_text)
        
        # 尝试识别商品名称（简单的关键词匹配）
        found_product = None
        for product in products:
            if product['name'].lower() in speech_text.lower():
                found_product = product
                break
        
        results = []
        
        # 核对价格
        if stated_price and found_product:
            actual_price = float(found_product['price'])
            price_diff = abs(stated_price - actual_price)
            
            if price_diff > 1.0:
                results.append(
                    f"⚠ 【官方更正】价格错误！\n"
                    f"商品: {found_product['name']}\n"
                    f"主播说的价格: ¥{stated_price:.2f}\n"
                    f"实际价格: ¥{actual_price:.2f}\n"
                    f"差价: ¥{price_diff:.2f}\n\n"
                    f"正确价格应该是 ¥{actual_price:.2f}！"
                )
        
        # 核对库存
        if stated_stock and found_product:
            actual_stock = int(found_product['stock'])
            
            if stated_stock != actual_stock:
                stock_status = "有货" if actual_stock > 0 else "缺货"
                results.append(
                    f"⚠ 【官方更正】库存错误！\n"
                    f"商品: {found_product['name']}\n"
                    f"主播说的库存: {stated_stock} 件\n"
                    f"实际库存: {actual_stock} 件\n"
                    f"状态: {stock_status}\n\n"
                    f"正确库存应该是 {actual_stock} 件！"
                )
            
            # 如果库存为0，额外提醒
            if actual_stock == 0:
                results.append(
                    f"⚠ 【紧急提醒】\n"
                    f"商品: {found_product['name']}\n"
                    f"当前已售罄！请主播立即停止售卖！"
                )
        
        if results:
            return "\n\n" + "\n\n".join(results)
        else:
            return "✓ 主播说的信息核对无误，无需更正。"
    
    except Exception as e:
        return f"分析主播语音失败: {str(e)}"
