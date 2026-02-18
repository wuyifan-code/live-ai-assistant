"""
弹幕处理器
实现优先级队列和防刷去重机制
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class Priority(Enum):
    """问题优先级"""
    HIGH = 1    # 投诉、技术问题、售后
    MEDIUM = 2  # 价格询问、库存询问、产品信息
    LOW = 3     # 问候、一般聊天


@dataclass
class Danmaku:
    """弹幕数据结构"""
    user_id: str
    username: str
    content: str
    timestamp: datetime
    priority: Priority = Priority.MEDIUM
    category: str = "other"
    room_id: str = ""
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value < other.priority.value


class DanmakuDeduplicator:
    """弹幕去重器 - 防止刷屏"""
    
    def __init__(self, max_recent_messages: int = 5, time_window: int = 30):
        """
        参数:
            max_recent_messages: 每个用户最多保留最近N条消息
            time_window: 时间窗口（秒），超过此时间的消息可以重复
        """
        self.user_history: Dict[str, deque] = {}
        self.max_recent_messages = max_recent_messages
        self.time_window = time_window
    
    def is_duplicate(self, user_id: str, content: str) -> bool:
        """
        检查弹幕是否为重复消息
        
        参数:
            user_id: 用户ID
            content: 弹幕内容
        
        返回:
            True if duplicate, False otherwise
        """
        current_time = time.time()
        
        # 获取该用户的历史消息
        if user_id not in self.user_history:
            self.user_history[user_id] = deque(maxlen=self.max_recent_messages)
        
        history = self.user_history[user_id]
        
        # 清理过期消息
        while history and (current_time - history[0]['timestamp'] > self.time_window):
            history.popleft()
        
        # 检查是否有相同内容
        for msg in history:
            if msg['content'] == content:
                logger.debug(f"检测到重复弹幕: 用户[{user_id}] 内容[{content}]")
                return True
        
        # 添加新消息
        history.append({
            'content': content,
            'timestamp': current_time
        })
        
        return False


class PriorityDanmakuQueue:
    """优先级弹幕队列"""
    
    def __init__(self, max_queue_size: int = 100):
        """
        参数:
            max_queue_size: 队列最大长度
        """
        self.high_priority_queue = asyncio.Queue(maxsize=max_queue_size)
        self.medium_priority_queue = asyncio.Queue(maxsize=max_queue_size)
        self.low_priority_queue = asyncio.Queue(maxsize=max_queue_size)
        self.deduplicator = DanmakuDeduplicator()
        self.total_processed = 0
        self.total_dropped = 0
    
    async def add_danmaku(self, danmaku: Danmaku) -> bool:
        """
        添加弹幕到队列
        
        参数:
            danmaku: 弹幕对象
        
        返回:
            True if added, False if dropped
        """
        # 去重检查
        if self.deduplicator.is_duplicate(danmaku.user_id, danmaku.content):
            self.total_dropped += 1
            logger.info(f"🚫 丢弃重复弹幕: [{danmaku.username}] {danmaku.content}")
            return False
        
        # 根据优先级添加到对应队列
        try:
            if danmaku.priority == Priority.HIGH:
                self.high_priority_queue.put_nowait(danmaku)
            elif danmaku.priority == Priority.MEDIUM:
                self.medium_priority_queue.put_nowait(danmaku)
            else:
                self.low_priority_queue.put_nowait(danmaku)
            
            self.total_processed += 1
            logger.info(f"✅ 添加弹幕到队列: [{danmaku.username}] 优先级={danmaku.priority.name}")
            return True
        
        except asyncio.QueueFull:
            self.total_dropped += 1
            logger.warning(f"⚠️ 队列已满，丢弃弹幕: [{danmaku.username}]")
            return False
    
    async def get_danmaku(self) -> Optional[Danmaku]:
        """
        获取下一个弹幕（按优先级）
        
        优先级顺序: HIGH > MEDIUM > LOW
        """
        # 优先处理高优先级队列
        if not self.high_priority_queue.empty():
            return await self.high_priority_queue.get()
        
        # 其次处理中优先级队列
        if not self.medium_priority_queue.empty():
            return await self.medium_priority_queue.get()
        
        # 最后处理低优先级队列
        if not self.low_priority_queue.empty():
            return await self.low_priority_queue.get()
        
        return None
    
    def get_queue_stats(self) -> Dict:
        """获取队列统计信息"""
        return {
            "high_priority_size": self.high_priority_queue.qsize(),
            "medium_priority_size": self.medium_priority_queue.qsize(),
            "low_priority_size": self.low_priority_queue.qsize(),
            "total_processed": self.total_processed,
            "total_dropped": self.total_dropped,
            "total_in_queue": (
                self.high_priority_queue.qsize() +
                self.medium_priority_queue.qsize() +
                self.low_priority_queue.qsize()
            )
        }
    
    async def process_danmaku_loop(self, handler_func):
        """
        处理弹幕循环
        
        参数:
            handler_func: 处理弹幕的回调函数
        """
        logger.info("🔄 开始处理弹幕队列...")
        
        while True:
            try:
                danmaku = await self.get_danmaku()
                if danmaku:
                    logger.info(
                        f"📤 处理弹幕: [{danmaku.username}] "
                        f"优先级={danmaku.priority.name} "
                        f"内容={danmaku.content[:20]}..."
                    )
                    
                    # 调用处理函数
                    await handler_func(danmaku)
                else:
                    # 队列为空，稍作等待
                    await asyncio.sleep(0.1)
            
            except Exception as e:
                logger.error(f"❌ 处理弹幕失败: {str(e)}")
                await asyncio.sleep(1)


async def categorize_and_add_danmaku(queue: PriorityDanmakuQueue, user_data: dict, category_result: str):
    """
    对弹幕进行分类并添加到队列
    
    参数:
        queue: 优先级队列
        user_data: 用户弹幕数据
        category_result: 分类结果字符串
    """
    # 解析分类结果
    priority = Priority.MEDIUM
    category = "other"
    
    if "投诉" in category_result or "complaint" in category_result:
        priority = Priority.HIGH
        category = "complaint"
    elif "售后" in category_result or "after_sales" in category_result:
        priority = Priority.HIGH
        category = "after_sales"
    elif "技术" in category_result or "technical" in category_result:
        priority = Priority.HIGH
        category = "technical"
    elif "价格" in category_result or "price" in category_result:
        priority = Priority.MEDIUM
        category = "price_inquiry"
    elif "库存" in category_result or "stock" in category_result:
        priority = Priority.MEDIUM
        category = "stock_inquiry"
    elif "产品" in category_result or "product" in category_result:
        priority = Priority.MEDIUM
        category = "product_info"
    elif "问候" in category_result or "greeting" in category_result:
        priority = Priority.LOW
        category = "greeting"
    
    # 创建弹幕对象
    danmaku = Danmaku(
        user_id=user_data.get("user_id", ""),
        username=user_data.get("username", ""),
        content=user_data.get("content", ""),
        timestamp=datetime.now(),
        priority=priority,
        category=category,
        room_id=user_data.get("room_id", "")
    )
    
    # 添加到队列
    await queue.add_danmaku(danmaku)


# 全局弹幕处理器实例
danmaku_queue = PriorityDanmakuQueue()


async def process_danmaku(danmaku: Danmaku) -> Optional[dict]:
    """
    处理单条弹幕（简化版）
    
    参数:
        danmaku: 弹幕对象
    
    返回:
        处理结果
    """
    logger.info(f"处理弹幕: [{danmaku.username}] {danmaku.content}")
    
    # 这里可以添加具体的处理逻辑
    # 例如：调用AI回复、查询数据库等
    
    return {
        "user_id": danmaku.user_id,
        "username": danmaku.username,
        "content": danmaku.content,
        "priority": danmaku.priority.name,
        "category": danmaku.category,
        "processed": True
    }


# 导出全局实例
__all__ = [
    "Priority",
    "Danmaku",
    "DanmakuDeduplicator",
    "PriorityDanmakuQueue",
    "categorize_and_add_danmaku",
    "danmaku_queue",
    "process_danmaku"
]
