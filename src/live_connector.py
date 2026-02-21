"""
直播间连接器
处理不同直播平台的WebSocket连接和弹幕处理
"""

import asyncio
import json
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    DANMAKU = "danmaku"           # 弹幕
    GIFT = "gift"                 # 礼物
    LIKE = "like"                 # 点赞
    ENTER = "enter"               # 进入
    FOLLOW = "follow"             # 关注
    SHARE = "share"               # 分享


class LiveConnector:
    """
    直播间连接器基类
    
    支持WebSocket连接到不同的直播平台
    """
    
    def __init__(
        self,
        websocket_url: str,
        on_message_callback: Optional[Callable] = None,
        on_error_callback: Optional[Callable] = None
    ):
        """
        参数:
            websocket_url: WebSocket连接地址
            on_message_callback: 消息回调函数
            on_error_callback: 错误回调函数
        """
        self.websocket_url = websocket_url
        self.on_message = on_message_callback
        self.on_error = on_error_callback
        self.is_connected = False
        self.ws = None
        self.room_id = None
    
    async def connect(self):
        """建立WebSocket连接"""
        try:
            import websockets
            
            logger.info(f"🔌 连接直播间: {self.websocket_url}")
            
            self.ws = await websockets.connect(self.websocket_url)
            self.is_connected = True
            
            logger.info("✅ 直播间连接成功")
            
            # 开始接收消息
            await self._receive_loop()
            
        except Exception as e:
            logger.error(f"❌ 连接失败: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _receive_loop(self):
        """消息接收循环"""
        try:
            async for message in self.ws:
                try:
                    data = json.loads(message)
                    await self._handle_message(data)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析消息: {message}")
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
                    
        except Exception as e:
            logger.error(f"接收消息异常: {str(e)}")
            self.is_connected = False
    
    async def _handle_message(self, data: Dict[str, Any]):
        """处理收到的消息"""
        # 解析消息类型
        msg_type = data.get("type", "danmaku")
        
        if msg_type == "danmaku":
            danmaku_data = {
                "user_id": data.get("user_id", ""),
                "username": data.get("username", "匿名用户"),
                "content": data.get("content", ""),
                "timestamp": data.get("timestamp", datetime.now().isoformat()),
                "room_id": self.room_id
            }
            
            if self.on_message:
                await self.on_message(danmaku_data)
    
    async def send_message(self, message: str, is_official: bool = False):
        """
        发送消息到直播间
        
        注意：实际发送需要通过HTTP API，WebSocket主要用于接收
        
        参数:
            message: 消息内容
            is_official: 是否为官方消息（会添加特殊标记）
        """
        if is_official:
            message = f"【官方更正】{message}"
        
        # 标记消息状态
        status = "📢 [官方]" if is_official else "📤 [AI]"
        logger.info(f"{status} 发送消息: {message[:50]}...")
        
        # 实际发送需要子类实现
        # 例如 DouyinLiveConnector 会调用抖音API
        pass
    
    async def disconnect(self):
        """断开连接"""
        if self.ws:
            await self.ws.close()
            self.is_connected = False
            logger.info("👋 已断开直播间连接")


class DanmakuAIBridge:
    """
    弹幕与AI助手的桥接器
    
    处理弹幕消息并将其传递给AI助手，再将AI回复发送回直播间
    """
    
    def __init__(self, connector: LiveConnector, agent):
        """
        参数:
            connector: 直播间连接器
            agent: AI Agent实例
        """
        self.connector = connector
        self.agent = agent
        
        # 统计信息
        self.stats = {
            "total_danmaku": 0,
            "processed_danmaku": 0,
            "ai_responses": 0,
            "official_corrections": 0
        }
    
    async def start(self):
        """启动桥接器"""
        logger.info("🚀 启动AI助手桥接器...")
        
        # 设置消息回调
        self.connector.on_message = self._on_danmaku_received
        
        # 连接直播间
        await self.connector.connect()
    
    async def _on_danmaku_received(self, danmaku_data: Dict[str, Any]):
        """收到弹幕的处理回调"""
        self.stats["total_danmaku"] += 1
        
        try:
            username = danmaku_data.get("username", "用户")
            content = danmaku_data.get("content", "")
            
            logger.info(f"📥 [{username}]: {content}")
            
            # 调用AI Agent处理
            response = await self._process_with_ai(username, content)
            
            # 发送AI回复
            if response:
                is_official = "更正" in response or "错误" in response
                
                await self.connector.send_message(response, is_official)
                
                self.stats["ai_responses"] += 1
                if is_official:
                    self.stats["official_corrections"] += 1
            
            self.stats["processed_danmaku"] += 1
            
        except Exception as e:
            logger.error(f"处理弹幕失败: {str(e)}")
    
    async def _process_with_ai(self, username: str, content: str) -> Optional[str]:
        """
        使用AI处理弹幕
        
        参数:
            username: 用户名
            content: 弹幕内容
        
        返回:
            AI回复内容
        """
        try:
            # 构建输入
            user_input = f"用户【{username}】说：{content}"
            
            # 调用Agent
            config = {"configurable": {"thread_id": f"live_{username}"}}
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            )
            
            # 提取AI回复
            if result and "messages" in result:
                last_message = result["messages"][-1]
                return last_message.content
            
            return None
            
        except Exception as e:
            logger.error(f"AI处理失败: {str(e)}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats.copy()
    
    async def stop(self):
        """停止桥接器"""
        await self.connector.disconnect()
        logger.info(f"📊 统计: {self.stats}")
