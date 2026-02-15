"""
直播间连接器 - 通用WebSocket方案
支持接收弹幕和发送消息到直播间
"""

import json
import asyncio
import websockets
from typing import Callable, Optional
from datetime import datetime


class LiveConnector:
    """直播间连接器基类"""
    
    def __init__(
        self,
        websocket_url: str,
        on_message_callback: Callable,
        on_error_callback: Optional[Callable] = None
    ):
        self.websocket_url = websocket_url
        self.on_message = on_message_callback
        self.on_error = on_error_callback
        self.websocket = None
        self.is_connected = False
    
    async def connect(self):
        """连接到直播间"""
        try:
            print(f"正在连接直播间: {self.websocket_url}")
            self.websocket = await websockets.connect(self.websocket_url)
            self.is_connected = True
            print("✅ 直播间连接成功")
            
            # 开始接收消息
            await self._listen_messages()
            
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _listen_messages(self):
        """监听弹幕消息"""
        try:
            while self.is_connected and self.websocket:
                message = await self.websocket.recv()
                await self._handle_message(message)
        except Exception as e:
            print(f"❌ 消息接收错误: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _handle_message(self, raw_message: str):
        """处理收到的消息"""
        try:
            # 解析消息
            message = json.loads(raw_message)
            
            # 提取弹幕信息
            if message.get("type") == "danmaku":
                danmaku_data = {
                    "user_id": message.get("user_id"),
                    "username": message.get("username"),
                    "content": message.get("content", ""),
                    "timestamp": message.get("timestamp", datetime.now().isoformat()),
                    "room_id": message.get("room_id")
                }
                
                # 调用回调函数处理弹幕
                if self.on_message:
                    await self.on_message(danmaku_data)
        
        except Exception as e:
            print(f"❌ 消息处理错误: {str(e)}")
    
    async def send_message(self, message: str, is_official: bool = False):
        """
        发送消息到直播间
        
        参数:
            message: 消息内容
            is_official: 是否为官方消息（用于更正信息）
        """
        if not self.is_connected or not self.websocket:
            print("⚠️ 未连接到直播间")
            return
        
        try:
            payload = {
                "type": "chat",
                "content": message,
                "is_official": is_official,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.websocket.send(json.dumps(payload))
            print(f"📤 已发送消息: {message}")
        
        except Exception as e:
            print(f"❌ 发送消息失败: {str(e)}")
    
    async def send_correction(self, message: str):
        """发送官方更正消息（高优先级显示）"""
        await self.send_message(message, is_official=True)
    
    async def disconnect(self):
        """断开连接"""
        self.is_connected = False
        if self.websocket:
            await self.websocket.close()
            print("🔌 已断开直播间连接")


class DanmakuAIBridge:
    """弹幕AI桥接器 - 连接直播间和AI助手"""
    
    def __init__(self, live_connector: LiveConnector, agent):
        self.connector = live_connector
        self.agent = agent
        self.message_queue = asyncio.Queue()
    
    async def on_danmaku(self, danmaku_data: dict):
        """
        收到弹幕时的处理函数
        
        参数:
            danmaku_data: 弹幕数据
                {
                    "user_id": "123",
                    "username": "用户A",
                    "content": "iPhone 15 Pro多少钱？",
                    "timestamp": "2024-01-01T12:00:00",
                    "room_id": "room_001"
                }
        """
        print(f"\n📥 收到弹幕 [{danmaku_data['username']}]: {danmaku_data['content']}")
        
        # 将弹幕放入处理队列
        await self.message_queue.put(danmaku_data)
    
    async def process_danmaku_loop(self):
        """持续处理弹幕队列"""
        print("🔄 开始处理弹幕...")
        
        while True:
            # 从队列获取弹幕
            danmaku_data = await self.message_queue.get()
            
            try:
                # 调用AI助手生成回复
                user_input = f"用户发弹幕：{danmaku_data['content']}"
                
                # 使用Agent的invoke方法
                config = {"configurable": {"thread_id": danmaku_data["user_id"]}}
                result = await self.agent.ainvoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config=config
                )
                
                # 提取AI回复
                ai_response = result["messages"][-1].content
                
                print(f"\n🤖 AI回复: {ai_response}")
                
                # 发送回复到直播间
                await self.connector.send_message(ai_response)
                
            except Exception as e:
                print(f"❌ 处理弹幕失败: {str(e)}")
    
    async def start(self):
        """启动AI桥接器"""
        # 连接直播间
        await self.connector.connect()
        
        # 启动弹幕处理循环
        asyncio.create_task(self.process_danmaku_loop())
    
    async def send_anchor_correction(self, correction_message: str):
        """
        发送主播更正消息
        
        参数:
            correction_message: 更正消息内容
        """
        print(f"\n⚠️ 发送官方更正: {correction_message}")
        await self.connector.send_correction(correction_message)
