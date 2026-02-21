"""
抖音直播间消息格式定义
标准化的消息数据结构
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Union, Optional
import json


@dataclass
class BaseMessage:
    """消息基类"""
    type: str
    user_id: str = ""
    username: str = ""
    timestamp: str = ""
    room_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class DanmakuMessage(BaseMessage):
    """
    弹幕消息
    
    示例:
    {
        "type": "danmaku",
        "user_id": "123456789",
        "username": "用户昵称",
        "content": "iPhone 15 Pro多少钱？",
        "timestamp": "2024-01-01T12:00:00.000Z",
        "room_id": "room_001"
    }
    """
    type: str = "danmaku"
    content: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DanmakuMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "danmaku"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class GiftMessage(BaseMessage):
    """
    礼物消息
    
    示例:
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
    type: str = "gift"
    gift_id: str = ""
    gift_name: str = ""
    gift_count: int = 1
    gift_value: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GiftMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "gift"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            gift_id=data.get("gift_id", ""),
            gift_name=data.get("gift_name", ""),
            gift_count=data.get("gift_count", 1),
            gift_value=data.get("gift_value", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class LikeMessage(BaseMessage):
    """
    点赞消息
    """
    type: str = "like"
    like_count: int = 1
    total_likes: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LikeMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "like"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            like_count=data.get("like_count", 1),
            total_likes=data.get("total_likes", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class EnterMessage(BaseMessage):
    """
    进入直播间消息
    """
    type: str = "enter"
    user_level: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnterMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "enter"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            user_level=data.get("user_level", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class FollowMessage(BaseMessage):
    """
    关注主播消息
    """
    type: str = "follow"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FollowMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "follow"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class ShareMessage(BaseMessage):
    """
    分享直播间消息
    """
    type: str = "share"
    share_type: str = ""  # wechat, weibo, qq等
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ShareMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "share"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            share_type=data.get("share_type", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )


@dataclass
class RoomInfoMessage:
    """
    直播间信息更新消息
    """
    type: str = "room_info"
    room_id: str = ""
    title: str = ""
    viewer_count: int = 0
    like_count: int = 0
    status: int = 1  # 0-未开播, 1-直播中, 2-已结束
    timestamp: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoomInfoMessage':
        """从字典创建"""
        return cls(
            type=data.get("type", "room_info"),
            room_id=data.get("room_id", ""),
            title=data.get("title", ""),
            viewer_count=data.get("viewer_count", 0),
            like_count=data.get("like_count", 0),
            status=data.get("status", 1),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


# 消息类型联合
Message = Union[
    DanmakuMessage,
    GiftMessage,
    LikeMessage,
    EnterMessage,
    FollowMessage,
    ShareMessage,
    RoomInfoMessage
]


def parse_message(data: Dict[str, Any]) -> Optional[Message]:
    """
    解析消息
    
    参数:
        data: 原始消息字典
    
    返回:
        对应的消息对象，解析失败返回None
    
    示例:
        >>> data = {
        ...     "type": "danmaku",
        ...     "user_id": "123456789",
        ...     "username": "用户昵称",
        ...     "content": "iPhone 15 Pro多少钱？",
        ...     "timestamp": "2024-01-01T12:00:00.000Z",
        ...     "room_id": "room_001"
        ... }
        >>> message = parse_message(data)
        >>> isinstance(message, DanmakuMessage)
        True
        >>> message.content
        'iPhone 15 Pro多少钱？'
    """
    msg_type = data.get("type")
    
    parsers = {
        "danmaku": DanmakuMessage.from_dict,
        "gift": GiftMessage.from_dict,
        "like": LikeMessage.from_dict,
        "enter": EnterMessage.from_dict,
        "follow": FollowMessage.from_dict,
        "share": ShareMessage.from_dict,
        "room_info": RoomInfoMessage.from_dict
    }
    
    parser = parsers.get(msg_type)
    
    if parser:
        return parser(data)
    
    return None


def create_danmaku(
    user_id: str,
    username: str,
    content: str,
    room_id: str
) -> DanmakuMessage:
    """
    创建弹幕消息
    
    参数:
        user_id: 用户ID
        username: 用户名
        content: 弹幕内容
        room_id: 直播间ID
    
    返回:
        弹幕消息对象
    
    示例:
        >>> msg = create_danmaku("123", "小明", "你好", "room_001")
        >>> msg.content
        '你好'
    """
    return DanmakuMessage(
        user_id=user_id,
        username=username,
        content=content,
        timestamp=datetime.now().isoformat(),
        room_id=room_id
    )


def create_gift(
    user_id: str,
    username: str,
    gift_name: str,
    gift_count: int,
    gift_value: int,
    room_id: str
) -> GiftMessage:
    """
    创建礼物消息
    """
    return GiftMessage(
        user_id=user_id,
        username=username,
        gift_name=gift_name,
        gift_count=gift_count,
        gift_value=gift_value,
        timestamp=datetime.now().isoformat(),
        room_id=room_id
    )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 示例：解析弹幕消息
    danmaku_data = {
        "type": "danmaku",
        "user_id": "123456789",
        "username": "用户昵称",
        "content": "iPhone 15 Pro多少钱？",
        "timestamp": "2024-01-01T12:00:00.000Z",
        "room_id": "room_001"
    }
    
    message = parse_message(danmaku_data)
    
    if isinstance(message, DanmakuMessage):
        print(f"✅ 弹幕消息解析成功")
        print(f"  用户: {message.username}")
        print(f"  内容: {message.content}")
        print(f"  时间: {message.timestamp}")
    
    # 示例：创建消息
    new_danmaku = create_danmaku(
        user_id="987654321",
        username="小红",
        content="MacBook有货吗？",
        room_id="room_001"
    )
    
    print(f"\n📤 新弹幕: {new_danmaku.to_json()}")
