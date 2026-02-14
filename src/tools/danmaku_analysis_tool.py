"""
弹幕分析工具
用于分析弹幕内容，识别用户意图，并生成合适的回复
"""

import json
from langchain.tools import tool, ToolRuntime
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage


@tool
def analyze_danmaku(danmaku_text: str, runtime: ToolRuntime = None) -> str:
    """
    分析弹幕内容，识别用户意图和语言类型
    
    参数:
        danmaku_text: 弹幕内容
    
    返回:
        分析结果，包括：
        - 用户意图（询问价格/库存/产品详情/售后/其他）
        - 语言类型（普通话/方言/外语）
        - 是否包含商品名称
        - 建议回复策略
    """
    ctx = runtime.context if runtime else new_context(method="analyze_danmaku")
    
    try:
        client = LLMClient(ctx=ctx)
        
        system_prompt = """你是一个直播弹幕分析专家。你的任务是分析弹幕内容，提取关键信息。

请分析以下弹幕内容，并以JSON格式返回分析结果：

{
  "intent": "用户意图类型",
  "intent_detail": "意图详细说明",
  "language": "语言类型（普通话/粤语/闽南语/英语/日语/其他）",
  "has_product_name": true/false,
  "product_name": "识别到的商品名称（如果有）",
  "keywords": ["关键词1", "关键词2"],
  "reply_strategy": "回复策略建议",
  "needs_tool_call": true/false
}

意图类型包括：
- price_query: 询问价格
- stock_query: 询问库存
- product_detail: 询问产品详情
- after_sales: 售后问题
- greeting: 问候
- complaint: 投诉
- other: 其他

如果弹幕包含商品相关询问（价格/库存/产品详情），needs_tool_call 应该设为 true。"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"弹幕内容: {danmaku_text}\n\n请分析这条弹幕。")
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-251015",
            temperature=0.3
        )
        
        # 提取文本内容
        content = response.content
        if isinstance(content, list):
            content = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        
        # 尝试解析JSON
        try:
            analysis = json.loads(content)
            
            result = (
                f"【弹幕分析结果】\n"
                f"弹幕内容: {danmaku_text}\n"
                f"用户意图: {analysis.get('intent', 'unknown')} - {analysis.get('intent_detail', '')}\n"
                f"语言类型: {analysis.get('language', '普通话')}\n"
                f"包含商品名: {'是' if analysis.get('has_product_name') else '否'}\n"
                f"商品名称: {analysis.get('product_name', '未识别')}\n"
                f"关键词: {', '.join(analysis.get('keywords', []))}\n"
                f"回复策略: {analysis.get('reply_strategy', '')}\n"
                f"需要调用工具: {'是' if analysis.get('needs_tool_call') else '否'}"
            )
            
            return result
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回原始内容
            return f"弹幕分析结果: {content}"
    
    except Exception as e:
        return f"分析弹幕失败: {str(e)}"


@tool
def generate_reply(danmaku_text: str, product_info: str = "", runtime: ToolRuntime = None) -> str:
    """
    生成弹幕回复
    
    参数:
        danmaku_text: 弹幕内容
        product_info: 商品信息（可选，如果涉及商品查询）
    
    返回:
        建议的回复内容
    """
    ctx = runtime.context if runtime else new_context(method="generate_reply")
    
    try:
        client = LLMClient(ctx=ctx)
        
        system_prompt = """你是一个专业的直播AI助手。你的任务是生成友好、专业、及时的弹幕回复。

回复要求：
1. 语气友好、热情，符合直播场景
2. 回复简洁明了，不超过100字
3. 如果用户说方言或外语，用相同语言/方言回复
4. 如果涉及商品信息，基于提供的商品信息回答
5. 回复要能解决用户的疑问或痛点
6. 保持品牌调性，体现专业性

生成回复时，请直接输出回复内容，不要解释。"""

        user_prompt = f"弹幕内容: {danmaku_text}\n"
        if product_info:
            user_prompt += f"商品信息: {product_info}\n"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt + "\n\n请生成一个合适的回复。")
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-8-251228",
            temperature=0.8
        )
        
        # 提取文本内容
        content = response.content
        if isinstance(content, list):
            content = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        
        # 如果是JSON格式，尝试提取回复内容
        try:
            parsed = json.loads(content)
            if isinstance(parsed, dict) and "reply" in parsed:
                content = parsed["reply"]
        except:
            pass
        
        return f"【建议回复】\n{content}"
    
    except Exception as e:
        return f"生成回复失败: {str(e)}"


@tool
def detect_language_and_suggest(danmaku_text: str, runtime: ToolRuntime = None) -> str:
    """
    检测弹幕的语言类型，并建议回复语言
    
    参数:
        danmaku_text: 弹幕内容
    
    返回:
        语言检测结果和回复语言建议
    """
    ctx = runtime.context if runtime else new_context(method="detect_language_and_suggest")
    
    try:
        client = LLMClient(ctx=ctx)
        
        system_prompt = """你是一个语言检测专家。你的任务是检测弹幕的语言类型，并建议回复语言。

请以JSON格式返回检测结果：

{
  "detected_language": "检测到的语言（普通话/粤语/闽南语/四川话/英语/日语/韩语/其他）",
  "confidence": "置信度（高/中/低）",
  "reply_language_suggestion": "建议回复的语言",
  "reply_style_tips": "回复风格建议",
  "example_reply": "示例回复"
}

支持的语言：
- 普通话：标准中文
- 方言：粤语、闽南语、四川话、东北话等
- 外语：英语、日语、韩语等"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"弹幕内容: {danmaku_text}\n\n请检测语言并提供建议。")
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-251015",
            temperature=0.3
        )
        
        # 提取文本内容
        content = response.content
        if isinstance(content, list):
            content = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        
        # 尝试解析JSON
        try:
            result = json.loads(content)
            
            return (
                f"【语言检测】\n"
                f"弹幕内容: {danmaku_text}\n"
                f"检测语言: {result.get('detected_language', '未知')}\n"
                f"置信度: {result.get('confidence', '中')}\n"
                f"建议回复语言: {result.get('reply_language_suggestion', '普通话')}\n"
                f"回复风格建议: {result.get('reply_style_tips', '')}\n"
                f"示例回复: {result.get('example_reply', '')}"
            )
        except json.JSONDecodeError:
            return f"语言检测结果: {content}"
    
    except Exception as e:
        return f"检测语言失败: {str(e)}"


@tool
def categorize_user_question(danmaku_text: str, runtime: ToolRuntime = None) -> str:
    """
    对用户问题进行分类，便于优先级排序
    
    参数:
        danmaku_text: 弹幕内容
    
    返回:
        问题分类和优先级
    """
    ctx = runtime.context if runtime else new_context(method="categorize_user_question")
    
    try:
        client = LLMClient(ctx=ctx)
        
        system_prompt = """你是一个问题分类专家。你的任务是对用户问题进行分类和优先级排序。

请以JSON格式返回分类结果：

{
  "category": "问题分类",
  "priority": "优先级（高/中/低）",
  "urgency": "紧急程度（紧急/一般/不紧急）",
  "needs_immediate_reply": true/false,
  "suggested_action": "建议操作",
  "estimated_reply_time": "建议回复时间（立即/1分钟内/3分钟内/稍后）"
}

问题分类：
- price_inquiry: 价格询问
- stock_inquiry: 库存询问
- product_info: 产品信息
- shipping: 物流配送
- after_sales: 售后服务
- complaint: 投诉
- technical: 技术问题
- greeting: 问候
- other: 其他

优先级规则：
- 高优先级：投诉、技术问题、重要售后
- 中优先级：价格询问、库存询问、产品信息
- 低优先级：问候、一般聊天

回复紧急程度：
- 紧急：投诉、技术问题
- 一般：价格询问、库存询问
- 不紧急：问候"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"用户问题: {danmaku_text}\n\n请分类该问题。")
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-251015",
            temperature=0.3
        )
        
        # 提取文本内容
        content = response.content
        if isinstance(content, list):
            content = " ".join([item.get("text", "") if isinstance(item, dict) else str(item) for item in content])
        
        # 尝试解析JSON
        try:
            result = json.loads(content)
            
            priority_emoji = {
                "高": "🔴",
                "中": "🟡",
                "低": "🟢"
            }
            
            urgency_emoji = {
                "紧急": "⚡",
                "一般": "⏱️",
                "不紧急": "🕐"
            }
            
            return (
                f"【问题分类】\n"
                f"用户问题: {danmaku_text}\n"
                f"分类: {result.get('category', 'other')}\n"
                f"优先级: {priority_emoji.get(result.get('priority', '中'), '🟡')} {result.get('priority', '中')}\n"
                f"紧急程度: {urgency_emoji.get(result.get('urgency', '一般'), '⏱️')} {result.get('urgency', '一般')}\n"
                f"需要立即回复: {'是' if result.get('needs_immediate_reply') else '否'}\n"
                f"建议操作: {result.get('suggested_action', '')}\n"
                f"建议回复时间: {result.get('estimated_reply_time', '立即')}"
            )
        except json.JSONDecodeError:
            return f"分类结果: {content}"
    
    except Exception as e:
        return f"分类问题失败: {str(e)}"
