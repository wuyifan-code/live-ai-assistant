"""
视觉识别工具
实时OCR、商品识别、画中画同步检测
"""

import json
import logging
import base64
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from langchain.tools import tool, ToolRuntime
from coze_coding_dev_sdk import LLMClient
from coze_coding_utils.runtime_ctx.context import new_context
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)


@tool
def extract_text_from_screen(image_url: str, runtime: ToolRuntime = None) -> str:
    """
    从直播间画面中提取文字（OCR）
    
    可识别：
    - 背景看板上的促销信息（如"限时秒杀"、"买一送一"）
    - 商品吊牌、标签
    - 商品包装上的文字
    - 字幕、弹幕等
    
    参数:
        image_url: 图片URL（直播间截图）
    
    返回:
        提取的所有文字内容
    """
    ctx = runtime.context if runtime else new_context(method="visual_ocr")
    
    try:
        client = LLMClient(ctx=ctx)
        
        messages = [
            SystemMessage(content="""你是一个专业的OCR文字识别助手。
你的任务是从直播间截图中提取所有可见的文字。

请按以下格式输出：
{
  "texts": [
    {
      "content": "识别的文字内容",
      "location": "位置描述（如：左上角看板、商品标签、字幕等）",
      "confidence": 0.95
    }
  ],
  "promotions": ["识别到的促销信息"],
  "product_labels": ["识别到的商品标签"]
}

注意：
1. 准确识别所有文字，包括中文、英文、数字
2. 标注文字所在位置
3. 特别关注促销关键词（秒杀、特价、限时等）
4. 如果图片模糊或文字不清，请标注"不清晰"并尽力识别"""),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": "请识别这张直播间截图中的所有文字内容。"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ])
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-vision-250815",
            temperature=0.1
        )
        
        # 安全提取文本内容
        if isinstance(response.content, str):
            result_text = response.content
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            result_text = " ".join(text_parts)
        else:
            result_text = str(response.content)
        
        logger.info(f"✅ OCR识别完成: {len(result_text)} 字符")
        
        return result_text
        
    except Exception as e:
        logger.error(f"❌ OCR识别失败: {str(e)}")
        return f"OCR识别失败: {str(e)}"


@tool
def detect_product_in_scene(image_url: str, runtime: ToolRuntime = None) -> str:
    """
    检测直播间当前展示的商品
    
    可以识别：
    - 商品类型（手机、服装、食品等）
    - 商品颜色、尺寸等属性
    - 商品在画面中的位置
    
    参数:
        image_url: 图片URL（直播间截图）
    
    返回:
        检测到的商品信息，包括类型、属性、位置
    """
    ctx = runtime.context if runtime else new_context(method="product_detection")
    
    try:
        client = LLMClient(ctx=ctx)
        
        messages = [
            SystemMessage(content="""你是一个专业的商品识别助手。
你的任务是从直播间截图中识别主播正在展示的商品。

请按以下格式输出：
{
  "main_product": {
    "type": "商品类型",
    "name": "商品名称（如果能识别）",
    "attributes": {
      "color": "颜色",
      "size": "尺寸",
      "other": "其他属性"
    },
    "position": {
      "topLeftX": x_min,
      "topLeftY": y_min,
      "bottomRightX": x_max,
      "bottomRightY": y_max
    }
  },
  "other_objects": ["其他可见物品"],
  "confidence": 0.85
}

注意：
1. 坐标为相对值（0-1000），(0,0)为左上角
2. 重点识别主播手持或展示的商品
3. 描述商品的关键特征
4. 如果同时有多个商品，标注最主要的一个"""),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": "请识别这张直播间截图中主播正在展示的商品。"
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ])
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-vision-250815",
            temperature=0.2
        )
        
        # 安全提取文本内容
        if isinstance(response.content, str):
            result_text = response.content
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            result_text = " ".join(text_parts)
        else:
            result_text = str(response.content)
        
        logger.info(f"✅ 商品检测完成")
        
        return result_text
        
    except Exception as e:
        logger.error(f"❌ 商品检测失败: {str(e)}")
        return f"商品检测失败: {str(e)}"


@tool
def analyze_scene_context(
    image_url: str,
    speech_text: str = "",
    danmaku_content: str = "",
    runtime: ToolRuntime = None
) -> str:
    """
    分析直播间场景上下文，检测画中画冲突
    
    场景示例：
    - 主播展示商品A，弹幕问商品B → 识别冲突，建议引导话术
    - 主播提到"限时秒杀"，画面显示促销信息 → 验证一致性
    - 主播说"最后10件"，画面库存显示"库存充足" → 检测矛盾
    
    参数:
        image_url: 图片URL（直播间截图）
        speech_text: 主播说的话（可选）
        danmaku_content: 弹幕内容（可选）
    
    返回:
        场景分析结果，包括一致性检查、冲突检测、建议话术
    """
    ctx = runtime.context if runtime else new_context(method="scene_analysis")
    
    try:
        client = LLMClient(ctx=ctx)
        
        # 构建分析提示
        analysis_prompt = f"""请分析这张直播间截图的场景上下文。

主播说的话：{speech_text if speech_text else "无"}
弹幕内容：{danmaku_content if danmaku_content else "无"}

请进行以下分析：
1. 视觉识别：画面中有哪些关键信息（商品、促销、文字等）
2. 一致性检查：主播说的话与画面内容是否一致
3. 冲突检测：主播展示的商品与弹幕询问的商品是否一致
4. 建议话术：如果有冲突或不一致，建议主播如何引导

输出格式：
{{
  "visual_info": {{
    "displayed_product": "画面展示的商品",
    "promotion_texts": ["画面中的促销文字"],
    "other_info": ["其他关键信息"]
  }},
  "consistency_check": {{
    "is_consistent": true/false,
    "inconsistencies": ["不一致的地方"]
  }},
  "conflict_detection": {{
    "has_conflict": true/false,
    "conflict_description": "冲突描述",
    "suggested_guidance": "建议的引导话术"
  }},
  "overall_assessment": "整体评估"
}}"""

        messages = [
            SystemMessage(content="你是一个专业的直播场景分析助手，擅长识别视觉和语音信息的一致性。"),
            HumanMessage(content=[
                {
                    "type": "text",
                    "text": analysis_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ])
        ]
        
        response = client.invoke(
            messages=messages,
            model="doubao-seed-1-6-vision-250815",
            temperature=0.3
        )
        
        # 安全提取文本内容
        if isinstance(response.content, str):
            result_text = response.content
        elif isinstance(response.content, list):
            text_parts = []
            for item in response.content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            result_text = " ".join(text_parts)
        else:
            result_text = str(response.content)
        
        logger.info(f"✅ 场景分析完成")
        
        return result_text
        
    except Exception as e:
        logger.error(f"❌ 场景分析失败: {str(e)}")
        return f"场景分析失败: {str(e)}"


class LiveStreamVisualMonitor:
    """直播间视觉监控器"""
    
    def __init__(self, capture_interval: int = 5):
        """
        参数:
            capture_interval: 截图间隔（秒）
        """
        self.capture_interval = capture_interval
        self.last_screenshot_url = None
        self.last_product_info = None
        self.last_ocr_result = None
        self.screenshot_count = 0
        self.inconsistency_count = 0
    
    async def capture_screenshot(self) -> Optional[str]:
        """
        捕获直播间截图
        
        注意：这是占位实现，实际需要对接直播平台API
        
        返回:
            截图URL
        """
        # TODO: 对接直播平台API获取实时截图
        # 例如：抖音开放平台、快手开放平台等
        
        logger.info(f"📸 捕获直播间截图...")
        
        # 模拟截图URL
        # 实际应该是：f"https://live-platform.com/screenshot/{room_id}/{timestamp}.jpg"
        self.screenshot_count += 1
        
        return None  # 需要实际实现
    
    async def monitor_loop(self):
        """
        持续监控循环
        
        定时截图并进行视觉分析
        """
        logger.info(f"🎥 启动视觉监控，间隔: {self.capture_interval}秒")
        
        while True:
            try:
                # 捕获截图
                screenshot_url = await self.capture_screenshot()
                
                if screenshot_url:
                    # 执行OCR
                    ocr_result = extract_text_from_screen(screenshot_url)
                    self.last_ocr_result = ocr_result
                    
                    # 检测商品
                    product_info = detect_product_in_scene(screenshot_url)
                    self.last_product_info = product_info
                    
                    logger.info(f"✅ 视觉分析完成")
                
                # 等待下一次
                await asyncio.sleep(self.capture_interval)
                
            except Exception as e:
                logger.error(f"❌ 视觉监控异常: {str(e)}")
                await asyncio.sleep(self.capture_interval)


# 全局视觉监控实例
visual_monitor = LiveStreamVisualMonitor()


# 需要导入asyncio
import asyncio
