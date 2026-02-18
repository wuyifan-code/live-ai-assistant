"""
实体提取工具
使用大模型从主播语音中提取结构化的商品信息、价格和库存
"""

import json
import logging
import re
from typing import Optional, Dict, Any
from langchain.tools import tool, ToolRuntime
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


@tool
def extract_anchor_entities(speech_text: str, runtime: ToolRuntime = None) -> str:
    """
    使用大模型从主播语音中提取商品信息、价格和库存
    
    相比正则表达式，这个工具具有更强的语义理解能力，可以：
    - 区分"原价99，现在只要19"中的实际售价
    - 识别"库存大概还有30、40台"中的模糊数量
    - 提取"iPhone 15 Pro"这样的复合商品名
    
    参数:
        speech_text: 主播说的话
    
    返回:
        提取的结构化信息，包括商品名、价格、库存、操作意图
    """
    ctx = runtime.context if runtime else new_context(method="extract_anchor_entities")
    
    try:
        client = LLMClient(ctx=ctx)
        
        system_prompt = """你是一个专业的直播语音实体提取专家。你的任务是从主播的语音中准确提取商品信息、价格和库存数量。

请以JSON格式返回提取结果：

{
  "product_name": "商品名称（如果有多个，返回最主要的商品）",
  "mentioned_price": {
    "value": 价格数字,
    "currency": "货币单位（CNY/USD）",
    "is_original_price": true/false,
    "is_sale_price": true/false,
    "confidence": "high/medium/low",
    "context": "价格语境说明"
  },
  "mentioned_stock": {
    "value": 库存数量（整数）",
    "unit": "单位（件/台/套）",
    "is_estimated": true/false,
    "confidence": "high/medium/low",
    "context": "库存语境说明"
  },
  "intent": "主播意图（introduce_product/update_price/update_stock/general）",
  "entities": [
    {"type": "product_name", "text": "iPhone 15 Pro", "start": 0, "end": 11},
    {"type": "price", "text": "7999元", "value": 7999, "start": 20, "end": 26}
  ],
  "summary": "简短总结主播说的话"
}

提取规则：
1. **价格提取**：
   - 优先提取"现在"、"只要"、"今天"等词汇后面的价格（这是当前售价）
   - 区分"原价"和"现价"，标注 is_original_price 和 is_sale_price
   - 如果有多个价格，标记所有价格并标注各自的含义
   - 价格单位默认为元（CNY）

2. **库存提取**：
   - 提取明确数字，如"库存30台" -> 30
   - 处理模糊表达，如"大概30、40台" -> 30（取最小值）
   - 标记 is_estimated 如果是模糊数字

3. **商品名提取**：
   - 优先提取完整的商品型号，如"iPhone 15 Pro 256G"
   - 如果只有品类名（如"这款手机"），product_name 设为 null

4. **置信度**：
   - high: 信息明确，数字准确
   - medium: 信息较明确，但可能有模糊之处
   - low: 信息模糊，不确定

5. **意图识别**：
   - introduce_product: 介绍新商品
   - update_price: 更新价格信息
   - update_stock: 更新库存信息
   - general: 一般性描述

示例：
输入："iPhone 15 Pro现在只要7999元，库存还有30台"
输出：
{
  "product_name": "iPhone 15 Pro",
  "mentioned_price": {"value": 7999, "currency": "CNY", "is_original_price": false, "is_sale_price": true, "confidence": "high", "context": "当前售价"},
  "mentioned_stock": {"value": 30, "unit": "台", "is_estimated": false, "confidence": "high", "context": "明确库存"},
  "intent": "update_price",
  "summary": "iPhone 15 Pro当前售价7999元，库存30台"
}

示例2：
输入："原价999，现在只要199，抢疯了"
输出：
{
  "product_name": null,
  "mentioned_price": {"value": 199, "currency": "CNY", "is_original_price": false, "is_sale_price": true, "confidence": "high", "context": "当前售价（对比原价999）"},
  "mentioned_stock": null,
  "intent": "update_price",
  "summary": "商品原价999元，现价199元"
}

只返回JSON，不要添加其他说明文字。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"主播说的话: {speech_text}\n\n请提取实体信息。")
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-thinking-250715",
            temperature=0.1
        )
        
        # 提取文本内容
        content = response.content
        if isinstance(content, list):
            content = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        
        # 尝试解析JSON
        try:
            entities = json.loads(content)
            
            # 格式化输出
            result_parts = ["【实体提取结果】"]
            result_parts.append(f"原话: {speech_text}")
            result_parts.append(f"意图: {entities.get('intent', 'general')}")
            result_parts.append(f"总结: {entities.get('summary', '')}")
            
            if entities.get('product_name'):
                result_parts.append(f"\n📦 商品: {entities['product_name']}")
            
            if entities.get('mentioned_price'):
                price_info = entities['mentioned_price']
                price_label = "原价" if price_info.get('is_original_price') else "现价"
                result_parts.append(f"\n💰 价格: {price_label} ¥{price_info['value']} ({price_info['confidence']})")
                result_parts.append(f"   语境: {price_info.get('context', '')}")
            
            if entities.get('mentioned_stock'):
                stock_info = entities['mentioned_stock']
                estimated = "约" if stock_info.get('is_estimated') else ""
                result_parts.append(f"\n📦 库存: {estimated}{stock_info['value']} {stock_info['unit']} ({stock_info['confidence']})")
                result_parts.append(f"   语境: {stock_info.get('context', '')}")
            
            if entities.get('entities'):
                result_parts.append(f"\n🔍 提取的实体:")
                for entity in entities['entities']:
                    result_parts.append(f"   - {entity['type']}: {entity['text']}")
            
            return "\n".join(result_parts)
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {str(e)}")
            # 如果JSON解析失败，返回原始内容
            return f"实体提取结果（未解析）:\n{content}"
    
    except Exception as e:
        logger.error(f"提取实体失败: {str(e)}")
        return f"提取实体失败: {str(e)}"


@tool
def smart_extract_price(speech_text: str, runtime: ToolRuntime = None) -> str:
    """
    智能提取价格（专门针对价格提取）
    
    相比正则表达式，可以准确识别：
    - "原价99，现在只要19" → 提取19（现价）
    - "今天特价199" → 提取199
    - "全场9.9元起" → 提取9.9
    
    参数:
        speech_text: 主播说的话
    
    返回:
        提取的价格及置信度
    """
    ctx = runtime.context if runtime else new_context(method="smart_extract_price")
    
    try:
        # 先尝试提取实体
        entity_result = extract_anchor_entities(speech_text=speech_text)
        
        # 解析结果
        if "价格:" in entity_result:
            return entity_result
        
        # 如果LLM提取失败，使用备用正则方法
        # 匹配：现价、只要、特价、等关键词后面的价格
        patterns = [
            r'(?:现在|只要|特价|售价|今天|当前)\s*(?:是)?\s*¥?(\d+\.?\d*)',
            r'¥?(\d+\.?\d*)\s*(?:元|块钱)(?!\s*原)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, speech_text)
            if matches:
                # 返回第一个匹配的价格
                price = float(matches[0])
                return f"提取到价格: ¥{price:.2f} (正则匹配，置信度medium)"
        
        return "未能从文本中提取到明确的价格信息"
    
    except Exception as e:
        logger.error(f"智能提取价格失败: {str(e)}")
        return f"提取价格失败: {str(e)}"


@tool
def smart_extract_stock(speech_text: str, runtime: ToolRuntime = None) -> str:
    """
    智能提取库存（专门针对库存提取）
    
    相比正则表达式，可以准确识别：
    - "库存还有30台" → 30
    - "大概50、60个" → 50（取最小值）
    - "最后100件" → 100
    
    参数:
        speech_text: 主播说的话
    
    返回:
        提取的库存数量及置信度
    """
    ctx = runtime.context if runtime else new_context(method="smart_extract_stock")
    
    try:
        # 先尝试提取实体
        entity_result = extract_anchor_entities(speech_text=speech_text)
        
        # 解析结果
        if "库存:" in entity_result:
            return entity_result
        
        # 如果LLM提取失败，使用备用正则方法
        # 匹配：库存、还有、最后、等关键词后面的数字
        patterns = [
            r'(?:库存|还有|剩|最后)\s*(?:是)?\s*(\d+)\s*(?:件|台|个|套|只)',
            r'(?:仅)\s*(\d+)\s*(?:件|台|个|套)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, speech_text)
            if matches:
                # 返回第一个匹配的库存
                stock = int(matches[0])
                return f"提取到库存: {stock} 件 (正则匹配，置信度medium)"
        
        return "未能从文本中提取到明确的库存信息"
    
    except Exception as e:
        logger.error(f"智能提取库存失败: {str(e)}")
        return f"提取库存失败: {str(e)}"
