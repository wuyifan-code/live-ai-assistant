import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver

# 导入工具
from tools.product_query_tool import (
    query_product,
    query_product_list,
    get_product_by_sku
)
from tools.price_stock_verify_tool import (
    verify_price,
    verify_stock,
    check_product_availability,
    verify_anchor_speech
)
from tools.danmaku_analysis_tool import (
    analyze_danmaku,
    generate_reply,
    detect_language_and_suggest,
    categorize_user_question
)
from tools.visual_awareness_tool import (
    extract_text_from_screen,
    detect_product_in_scene,
    analyze_scene_context
)
from tools.knowledge_base_tool import (
    rag_search_product_info
)

LLM_CONFIG = "config/agent_llm_config.json"

# 默认保留最近 20 轮对话 (40 条消息)
MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]  # type: ignore

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

def build_agent(ctx=None):
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)
    
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )
    
    # 导入所有工具
    tools = [
        # 商品查询工具
        query_product,
        query_product_list,
        get_product_by_sku,
        # 价格库存验证工具
        verify_price,
        verify_stock,
        check_product_availability,
        verify_anchor_speech,
        # 弹幕分析工具
        analyze_danmaku,
        generate_reply,
        detect_language_and_suggest,
        categorize_user_question,
        # 视觉识别工具
        extract_text_from_screen,
        detect_product_in_scene,
        analyze_scene_context,
        # 知识库工具
        rag_search_product_info
    ]
    
    return create_agent(
        model=llm,
        system_prompt=cfg.get("sp"),
        tools=tools,
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
