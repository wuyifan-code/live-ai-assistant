"""
WebSocket重连监控
实时监控WebSocket连接状态，自动重连，异常告警
"""

import asyncio
import logging
import time
import os
from enum import Enum
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import websockets
import json

from .error_handler import handle_error_async, ErrorCategory

logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """连接状态"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ConnectionMetrics:
    """连接指标"""
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    last_ping: Optional[datetime] = None
    last_pong: Optional[datetime] = None
    reconnect_count: int = 0
    messages_received: int = 0
    messages_sent: int = 0
    bytes_received: int = 0
    bytes_sent: int = 0
    
    def get_uptime(self) -> float:
        """获取连接时长（秒）"""
        if self.connected_at and self.last_pong:
            return (self.last_pong - self.connected_at).total_seconds()
        return 0
    
    def get_avg_latency(self) -> float:
        """获取平均延迟（秒）"""
        if self.last_ping and self.last_pong:
            return (self.last_pong - self.last_ping).total_seconds()
        return 0


class WebSocketMonitor:
    """WebSocket连接监控器"""
    
    def __init__(
        self,
        url: str,
        max_retries: int = 5,
        retry_delay: int = 3,
        heartbeat_interval: int = 30,
        on_message_callback: Optional[Callable] = None,
        on_state_change_callback: Optional[Callable] = None
    ):
        """
        参数:
            url: WebSocket URL
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            heartbeat_interval: 心跳间隔（秒）
            on_message_callback: 消息回调
            on_state_change_callback: 状态变化回调
        """
        self.url = url
        self.max_retries = int(os.getenv("WEBSOCKET_MAX_RETRIES", max_retries))
        self.retry_delay = int(os.getenv("WEBSOCKET_RETRY_DELAY", retry_delay))
        self.heartbeat_interval = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", heartbeat_interval))
        
        self.on_message = on_message_callback
        self.on_state_change = on_state_change_callback
        
        self.state = ConnectionState.DISCONNECTED
        self.metrics = ConnectionMetrics()
        self.websocket = None
        self.is_running = False
        self.reconnect_task = None
        self.heartbeat_task = None
        
    async def connect(self):
        """连接到WebSocket服务器"""
        self.state = ConnectionState.CONNECTING
        self._notify_state_change()
        
        try:
            logger.info(f"🔌 连接到WebSocket: {self.url}")
            
            extra_headers = {
                "User-Agent": "LiveAI-Assistant/2.0"
            }
            
            self.websocket = await websockets.connect(
                self.url,
                extra_headers=extra_headers,
                ping_interval=self.heartbeat_interval,
                ping_timeout=self.heartbeat_interval * 2
            )
            
            self.state = ConnectionState.CONNECTED
            self.metrics.connected_at = datetime.now()
            self.metrics.reconnect_count = 0
            self._notify_state_change()
            
            logger.info(f"✅ WebSocket连接成功")
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 启动消息接收循环
            await self._message_loop()
        
        except Exception as e:
            logger.error(f"❌ WebSocket连接失败: {str(e)}")
            self.state = ConnectionState.FAILED
            self._notify_state_change()
            
            await handle_error_async(
                e,
                f"WebSocket连接失败: {self.url}",
                {"url": self.url, "state": self.state.value}
            )
            
            # 尝试重连
            await self.reconnect()
    
    async def _message_loop(self):
        """消息接收循环"""
        try:
            async for message in self.websocket:
                self.metrics.messages_received += 1
                self.metrics.bytes_received += len(str(message))
                self.metrics.last_pong = datetime.now()
                
                # 调用消息回调
                if self.on_message:
                    try:
                        await self.on_message(message)
                    except Exception as e:
                        logger.error(f"❌ 消息处理失败: {str(e)}")
                        await handle_error_async(
                            e,
                            "消息处理失败",
                            {"message_type": type(message).__name__}
                        )
        
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"⚠️ WebSocket连接已关闭: {e}")
            self.state = ConnectionState.DISCONNECTED
            self._notify_state_change()
            
            # 自动重连
            await self.reconnect()
        
        except Exception as e:
            logger.error(f"❌ 消息循环异常: {str(e)}")
            self.state = ConnectionState.FAILED
            self._notify_state_change()
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        try:
            while self.state == ConnectionState.CONNECTED:
                await asyncio.sleep(self.heartbeat_interval)
                
                if self.websocket and not self.websocket.closed:
                    self.metrics.last_ping = datetime.now()
                    # 发送ping
                    pong_waiter = await self.websocket.ping()
                    await pong_waiter
                    self.metrics.last_pong = datetime.now()
                    
                    latency = self.metrics.get_avg_latency()
                    logger.debug(f"💓 心跳成功, 延迟: {latency:.3f}s")
                else:
                    logger.warning("⚠️ WebSocket连接已断开")
                    break
        
        except Exception as e:
            logger.error(f"❌ 心跳失败: {str(e)}")
    
    async def reconnect(self):
        """重连"""
        if self.metrics.reconnect_count >= self.max_retries:
            logger.error(f"❌ 已达到最大重试次数: {self.max_retries}")
            self.state = ConnectionState.FAILED
            self._notify_state_change()
            
            await handle_error_async(
                Exception("Max retries exceeded"),
                f"WebSocket重连失败，已达到最大重试次数: {self.max_retries}",
                {"url": self.url, "reconnect_count": self.metrics.reconnect_count}
            )
            return
        
        self.state = ConnectionState.RECONNECTING
        self._notify_state_change()
        
        # 指数退避
        delay = self.retry_delay * (2 ** self.metrics.reconnect_count)
        delay = min(delay, 60)  # 最大60秒
        
        logger.info(f"🔄 {delay}秒后重连... (第{self.metrics.reconnect_count + 1}次)")
        
        await asyncio.sleep(delay)
        self.metrics.reconnect_count += 1
        
        # 清理旧连接
        if self.websocket and not self.websocket.closed:
            try:
                await self.websocket.close()
            except:
                pass
        
        # 重新连接
        await self.connect()
    
    async def send(self, message: Any):
        """
        发送消息
        
        参数:
            message: 消息内容（可以是字符串、字典等）
        """
        if not self.websocket or self.websocket.closed:
            logger.warning("⚠️ WebSocket未连接，无法发送消息")
            return False
        
        try:
            # 如果是字典，转换为JSON字符串
            if isinstance(message, dict):
                message = json.dumps(message, ensure_ascii=False)
            
            await self.websocket.send(message)
            
            self.metrics.messages_sent += 1
            self.metrics.bytes_sent += len(str(message))
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 发送消息失败: {str(e)}")
            
            await handle_error_async(
                e,
                "发送消息失败",
                {"message": str(message)[:100]}
            )
            
            return False
    
    def _notify_state_change(self):
        """通知状态变化"""
        if self.on_state_change:
            try:
                self.on_state_change(self.state, self.metrics)
            except Exception as e:
                logger.error(f"❌ 状态变化回调失败: {str(e)}")
    
    async def disconnect(self):
        """断开连接"""
        self.is_running = False
        self.state = ConnectionState.DISCONNECTED
        self._notify_state_change()
        
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        
        if self.websocket and not self.websocket.closed:
            await self.websocket.close()
        
        logger.info("🔌 WebSocket已断开")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计"""
        return {
            "state": self.state.value,
            "url": self.url,
            "uptime": self.metrics.get_uptime(),
            "latency": self.metrics.get_avg_latency(),
            "reconnect_count": self.metrics.reconnect_count,
            "messages_received": self.metrics.messages_received,
            "messages_sent": self.metrics.messages_sent,
            "bytes_received": self.metrics.bytes_received,
            "bytes_sent": self.metrics.bytes_sent,
            "connected_at": self.metrics.connected_at.isoformat() if self.metrics.connected_at else None,
            "last_pong": self.metrics.last_pong.isoformat() if self.metrics.last_pong else None
        }
    
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self.state == ConnectionState.CONNECTED and self.websocket and not self.websocket.closed


class WebSocketPool:
    """WebSocket连接池 - 管理多个连接"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocketMonitor] = {}
    
    async def add_connection(
        self,
        name: str,
        url: str,
        on_message_callback: Optional[Callable] = None,
        on_state_change_callback: Optional[Callable] = None
    ) -> WebSocketMonitor:
        """添加连接"""
        if name in self.connections:
            logger.warning(f"⚠️ 连接已存在: {name}")
            return self.connections[name]
        
        monitor = WebSocketMonitor(
            url=url,
            on_message_callback=on_message_callback,
            on_state_change_callback=on_state_change_callback
        )
        
        self.connections[name] = monitor
        
        # 启动连接
        asyncio.create_task(monitor.connect())
        
        logger.info(f"✅ 已添加连接: {name}")
        
        return monitor
    
    def get_connection(self, name: str) -> Optional[WebSocketMonitor]:
        """获取连接"""
        return self.connections.get(name)
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有连接的统计"""
        stats = {
            "total_connections": len(self.connections),
            "connected": 0,
            "disconnected": 0,
            "reconnecting": 0,
            "failed": 0,
            "connections": {}
        }
        
        for name, monitor in self.connections.items():
            stats["connections"][name] = monitor.get_stats()
            
            if monitor.state == ConnectionState.CONNECTED:
                stats["connected"] += 1
            elif monitor.state == ConnectionState.DISCONNECTED:
                stats["disconnected"] += 1
            elif monitor.state == ConnectionState.RECONNECTING:
                stats["reconnecting"] += 1
            elif monitor.state == ConnectionState.FAILED:
                stats["failed"] += 1
        
        return stats
    
    async def disconnect_all(self):
        """断开所有连接"""
        for name, monitor in self.connections.items():
            await monitor.disconnect()
        
        self.connections.clear()
        logger.info("🔌 所有WebSocket连接已断开")
    
    async def broadcast(self, message: Any):
        """广播消息到所有连接"""
        success_count = 0
        
        for name, monitor in self.connections.items():
            if await monitor.send(message):
                success_count += 1
        
        logger.info(f"📤 广播消息到 {success_count}/{len(self.connections)} 个连接")
        
        return success_count


# 全局WebSocket连接池
websocket_pool = WebSocketPool()
