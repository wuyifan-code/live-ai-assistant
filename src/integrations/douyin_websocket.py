"""
抖音直播间WebSocket连接器
实时弹幕监听和消息处理
"""

import asyncio
import json
import logging
import time
import gzip
from typing import Callable, Optional, Dict, Any
from datetime import datetime
import hashlib
import os

# 导入消息类型
from integrations.message_types import (
    DanmakuMessage, GiftMessage, LikeMessage, 
    EnterMessage, FollowMessage, ShareMessage,
    parse_message
)

logger = logging.getLogger(__name__)


class DouyinWebSocketConnector:
    """
    抖音直播间WebSocket连接器
    
    支持实时接收：
    - 弹幕消息
    - 礼物消息
    - 点赞消息
    - 进入直播间
    - 关注消息
    """
    
    # 抖音WebSocket地址
    WEBSOCKET_BASE = "wss://webcast.douyin.com/websocket/im/v1"
    
    # 消息类型
    MSG_TYPE_DANMAKU = 1          # 弹幕
    MSG_TYPE_GIFT = 2             # 礼物
    MSG_TYPE_LIKE = 3             # 点赞
    MSG_TYPE_ENTER = 4            # 进入
    MSG_TYPE_FOLLOW = 5           # 关注
    MSG_TYPE_SHARE = 6            # 分享
    MSG_TYPE_ROOM_INFO = 7        # 直播间信息
    MSG_TYPE_MEMBER = 8           # 成员变化
    
    def __init__(
        self,
        room_id: str,
        on_danmaku: Optional[Callable] = None,
        on_gift: Optional[Callable] = None,
        on_like: Optional[Callable] = None,
        on_enter: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        app_id: str = None,
        app_secret: str = None
    ):
        """
        参数:
            room_id: 直播间ID
            on_danmaku: 弹幕回调
            on_gift: 礼物回调
            on_like: 点赞回调
            on_enter: 进入回调
            on_error: 错误回调
            app_id: 应用ID（可选，用于签名验证）
            app_secret: 应用密钥（可选）
        """
        self.room_id = room_id
        self.on_danmaku = on_danmaku
        self.on_gift = on_gift
        self.on_like = on_like
        self.on_enter = on_enter
        self.on_error = on_error
        
        self.app_id = app_id or os.getenv("DOUYIN_APP_ID")
        self.app_secret = app_secret or os.getenv("DOUYIN_APP_SECRET")
        
        self.ws = None
        self.is_connected = False
        self.is_running = False
        
        # 心跳相关
        self.heartbeat_task = None
        self.heartbeat_interval = 10  # 心跳间隔（秒）
        
        # 统计
        self.stats = {
            "total_messages": 0,
            "danmaku_count": 0,
            "gift_count": 0,
            "like_count": 0,
            "enter_count": 0
        }
    
    def _generate_signature(self, timestamp: int) -> str:
        """
        生成WebSocket连接签名
        
        参数:
            timestamp: 时间戳
        
        返回:
            签名字符串
        """
        # 签名规则（示例，实际签名算法需要参考抖音文档）
        if self.app_id and self.app_secret:
            sign_str = f"{self.app_id}{self.room_id}{timestamp}{self.app_secret}"
            return hashlib.md5(sign_str.encode()).hexdigest()
        else:
            # 无签名模式（某些场景可能不需要签名）
            return ""
    
    def _build_websocket_url(self) -> str:
        """
        构建WebSocket连接URL
        
        返回:
            完整的WebSocket URL
        """
        timestamp = int(time.time())
        signature = self._generate_signature(timestamp)
        
        # 构建URL参数
        params = {
            "room_id": self.room_id,
            "app_id": self.app_id or "",
            "signature": signature,
            "timestamp": timestamp,
            "compress": "gzip"  # 启用gzip压缩
        }
        
        # 拼接URL
        param_str = "&".join(f"{k}={v}" for k, v in params.items() if v)
        ws_url = f"{self.WEBSOCKET_BASE}?{param_str}"
        
        return ws_url
    
    async def connect(self):
        """建立WebSocket连接"""
        try:
            import websockets
            
            ws_url = self._build_websocket_url()
            
            logger.info(f"🔌 连接抖音直播间: {self.room_id}")
            logger.debug(f"WebSocket URL: {ws_url}")
            
            # 建立连接
            self.ws = await websockets.connect(
                ws_url,
                ping_interval=None,  # 手动控制心跳
                ping_timeout=None,
                close_timeout=5
            )
            
            self.is_connected = True
            self.is_running = True
            
            logger.info("✅ WebSocket连接成功")
            
            # 启动心跳
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 开始接收消息
            await self._receive_loop()
            
        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {str(e)}")
            self.is_connected = False
            
            if self.on_error:
                await self.on_error(str(e))
            
            raise
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running and self.is_connected:
            try:
                # 发送心跳包
                await self._send_heartbeat()
                
                # 等待下次心跳
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"心跳失败: {str(e)}")
                break
    
    async def _send_heartbeat(self):
        """发送心跳包"""
        try:
            # 抖音心跳包格式（示例）
            heartbeat_data = {
                "type": "heartbeat",
                "timestamp": int(time.time() * 1000)
            }
            
            await self.ws.send(json.dumps(heartbeat_data))
            logger.debug("💓 心跳发送成功")
            
        except Exception as e:
            logger.error(f"发送心跳失败: {str(e)}")
    
    async def _receive_loop(self):
        """消息接收循环"""
        try:
            async for message in self.ws:
                try:
                    # 处理消息
                    await self._handle_message(message)
                    
                except Exception as e:
                    logger.error(f"处理消息失败: {str(e)}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ WebSocket连接已关闭")
            self.is_connected = False
            
        except Exception as e:
            logger.error(f"接收消息异常: {str(e)}")
            self.is_connected = False
    
    async def _handle_message(self, message: bytes):
        """
        处理接收到的消息
        
        参数:
            message: 原始消息数据
        """
        try:
            # 尝试解压gzip数据
            try:
                message = gzip.decompress(message)
            except:
                pass
            
            # 解析JSON
            data = json.loads(message)
            
            # 获取消息类型
            msg_type = data.get("type", 0)
            
            self.stats["total_messages"] += 1
            
            # 根据类型处理
            if msg_type == self.MSG_TYPE_DANMAKU:
                await self._handle_danmaku(data)
            elif msg_type == self.MSG_TYPE_GIFT:
                await self._handle_gift(data)
            elif msg_type == self.MSG_TYPE_LIKE:
                await self._handle_like(data)
            elif msg_type == self.MSG_TYPE_ENTER:
                await self._handle_enter(data)
            elif msg_type == self.MSG_TYPE_ROOM_INFO:
                await self._handle_room_info(data)
            else:
                logger.debug(f"未知消息类型: {msg_type}")
                
        except json.JSONDecodeError:
            logger.debug("非JSON消息，忽略")
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}")
    
    async def _handle_danmaku(self, data: Dict):
        """
        处理弹幕消息
        
        标准格式:
        {
            "type": "danmaku",
            "user_id": "123456789",
            "username": "用户昵称",
            "content": "iPhone 15 Pro多少钱？",
            "timestamp": "2024-01-01T12:00:00.000Z",
            "room_id": "room_001"
        }
        """
        try:
            self.stats["danmaku_count"] += 1
            
            # 使用消息类型解析
            message = parse_message(data)
            
            if isinstance(message, DanmakuMessage):
                logger.info(f"📥 [{message.username}]: {message.content}")
                
                if self.on_danmaku:
                    # 转换为字典格式传递给回调
                    danmaku_dict = message.to_dict()
                    await self.on_danmaku(danmaku_dict)
            else:
                # 兼容旧格式
                danmaku = {
                    "type": "danmaku",
                    "user_id": data.get("user_id", ""),
                    "username": data.get("nickname", data.get("username", "匿名用户")),
                    "content": data.get("content", ""),
                    "timestamp": data.get("timestamp", datetime.now().isoformat()),
                    "room_id": self.room_id
                }
                
                logger.info(f"📥 [{danmaku['username']}]: {danmaku['content']}")
                
                if self.on_danmaku:
                    await self.on_danmaku(danmaku)
                
        except Exception as e:
            logger.error(f"处理弹幕失败: {str(e)}")
    
    async def _handle_gift(self, data: Dict):
        """
        处理礼物消息
        
        标准格式:
        {
            "type": "gift",
            "user_id": "123456789",
            "username": "用户昵称",
            "gift_id": "gift_001",
            "gift_name": "小心心",
            "gift_count": 10,
            "gift_value": 100,
            "timestamp": "2024-01-01T12:00:00.000Z",
            "room_id": "room_001"
        }
        """
        try:
            self.stats["gift_count"] += 1
            
            # 使用消息类型解析
            message = parse_message(data)
            
            if isinstance(message, GiftMessage):
                logger.info(f"🎁 [{message.username}] 送出 {message.gift_name} x{message.gift_count}")
                
                if self.on_gift:
                    await self.on_gift(message.to_dict())
            else:
                # 兼容旧格式
                gift = {
                    "type": "gift",
                    "user_id": data.get("user_id", ""),
                    "username": data.get("nickname", "匿名用户"),
                    "gift_name": data.get("gift_name", ""),
                    "gift_count": data.get("gift_count", 1),
                    "gift_value": data.get("gift_value", 0),
                    "timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"🎁 [{gift['username']}] 送出 {gift['gift_name']} x{gift['gift_count']}")
                
                if self.on_gift:
                    await self.on_gift(gift)
                
        except Exception as e:
            logger.error(f"处理礼物失败: {str(e)}")
    
    async def _handle_like(self, data: Dict):
        """处理点赞消息"""
        try:
            self.stats["like_count"] += 1
            
            like = {
                "type": "like",
                "user_id": data.get("user_id", ""),
                "username": data.get("nickname", "匿名用户"),
                "like_count": data.get("like_count", 1),
                "timestamp": datetime.now().isoformat()
            }
            
            if self.on_like:
                await self.on_like(like)
                
        except Exception as e:
            logger.error(f"处理点赞失败: {str(e)}")
    
    async def _handle_enter(self, data: Dict):
        """处理进入直播间"""
        try:
            self.stats["enter_count"] += 1
            
            enter = {
                "type": "enter",
                "user_id": data.get("user_id", ""),
                "username": data.get("nickname", "匿名用户"),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.debug(f"👋 {enter['username']} 进入直播间")
            
            if self.on_enter:
                await self.on_enter(enter)
                
        except Exception as e:
            logger.error(f"处理进入消息失败: {str(e)}")
    
    async def _handle_room_info(self, data: Dict):
        """处理直播间信息更新"""
        logger.debug(f"直播间信息更新: {data}")
    
    async def send_message(self, message: str) -> bool:
        """
        发送消息到直播间
        
        参数:
            message: 消息内容
        
        返回:
            是否发送成功
        """
        if not self.is_connected or not self.ws:
            logger.warning("未连接到直播间")
            return False
        
        try:
            # 构建消息
            msg_data = {
                "type": "message",
                "content": message,
                "timestamp": int(time.time() * 1000)
            }
            
            await self.ws.send(json.dumps(msg_data))
            
            logger.info(f"📤 发送消息: {message}")
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        logger.info("👋 断开WebSocket连接...")
        
        self.is_running = False
        
        # 停止心跳
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # 关闭WebSocket
        if self.ws:
            await self.ws.close()
            self.ws = None
        
        self.is_connected = False
        
        # 打印统计
        logger.info(f"📊 统计: {json.dumps(self.stats, ensure_ascii=False)}")
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return self.stats.copy()


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    
    async def on_danmaku(danmaku: dict):
        """弹幕回调"""
        print(f"[{danmaku['username']}]: {danmaku['content']}")
    
    async def on_gift(gift: dict):
        """礼物回调"""
        print(f"🎁 {gift['username']} 送出 {gift['gift_name']}")
    
    async def on_error(error: str):
        """错误回调"""
        print(f"❌ 错误: {error}")
    
    # 创建连接器
    connector = DouyinWebSocketConnector(
        room_id="123456789",
        on_danmaku=on_danmaku,
        on_gift=on_gift,
        on_error=on_error
    )
    
    try:
        # 连接
        await connector.connect()
        
        # 运行一段时间
        await asyncio.sleep(60)
        
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        # 断开连接
        await connector.disconnect()


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
