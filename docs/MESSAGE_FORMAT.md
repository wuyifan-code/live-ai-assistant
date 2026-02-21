# 抖音直播间消息格式规范

## 📋 消息类型定义

### 1. 弹幕消息 (danmaku)

```json
{
  "type": "danmaku",
  "user_id": "123456789",
  "username": "用户昵称",
  "content": "iPhone 15 Pro多少钱？",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "room_id": "room_001"
}
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | ✅ | 消息类型，固定为 "danmaku" |
| user_id | string | ✅ | 用户唯一标识 |
| username | string | ✅ | 用户昵称 |
| content | string | ✅ | 弹幕内容 |
| timestamp | string | ✅ | ISO 8601 格式时间戳 |
| room_id | string | ✅ | 直播间ID |

---

### 2. 礼物消息 (gift)

```json
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
```

**字段说明**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| type | string | ✅ | 消息类型，固定为 "gift" |
| user_id | string | ✅ | 用户唯一标识 |
| username | string | ✅ | 用户昵称 |
| gift_id | string | ✅ | 礼物ID |
| gift_name | string | ✅ | 礼物名称 |
| gift_count | int | ✅ | 礼物数量 |
| gift_value | int | ✅ | 礼物价值（抖币） |
| timestamp | string | ✅ | ISO 8601 格式时间戳 |
| room_id | string | ✅ | 直播间ID |

---

### 3. 点赞消息 (like)

```json
{
  "type": "like",
  "user_id": "123456789",
  "username": "用户昵称",
  "like_count": 1,
  "total_likes": 10000,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "room_id": "room_001"
}
```

---

### 4. 进入直播间 (enter)

```json
{
  "type": "enter",
  "user_id": "123456789",
  "username": "用户昵称",
  "user_level": 10,
  "timestamp": "2024-01-01T12:00:00.000Z",
  "room_id": "room_001"
}
```

---

### 5. 关注主播 (follow)

```json
{
  "type": "follow",
  "user_id": "123456789",
  "username": "用户昵称",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "room_id": "room_001"
}
```

---

### 6. 分享直播间 (share)

```json
{
  "type": "share",
  "user_id": "123456789",
  "username": "用户昵称",
  "share_type": "wechat",
  "timestamp": "2024-01-01T12:00:00.000Z",
  "room_id": "room_001"
}
```

---

### 7. 直播间信息更新 (room_info)

```json
{
  "type": "room_info",
  "room_id": "room_001",
  "title": "iPhone专场直播",
  "viewer_count": 5000,
  "like_count": 10000,
  "status": 1,
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

---

## 💻 Python 数据类定义

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DanmakuMessage:
    """弹幕消息"""
    type: str = "danmaku"
    user_id: str = ""
    username: str = ""
    content: str = ""
    timestamp: str = ""
    room_id: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DanmakuMessage':
        return cls(
            type=data.get("type", "danmaku"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )

@dataclass
class GiftMessage:
    """礼物消息"""
    type: str = "gift"
    user_id: str = ""
    username: str = ""
    gift_id: str = ""
    gift_name: str = ""
    gift_count: int = 1
    gift_value: int = 0
    timestamp: str = ""
    room_id: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GiftMessage':
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
class LikeMessage:
    """点赞消息"""
    type: str = "like"
    user_id: str = ""
    username: str = ""
    like_count: int = 1
    total_likes: int = 0
    timestamp: str = ""
    room_id: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LikeMessage':
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
class EnterMessage:
    """进入直播间消息"""
    type: str = "enter"
    user_id: str = ""
    username: str = ""
    user_level: int = 0
    timestamp: str = ""
    room_id: str = ""
    
    @classmethod
    def from_dict(cls, data: dict) -> 'EnterMessage':
        return cls(
            type=data.get("type", "enter"),
            user_id=data.get("user_id", ""),
            username=data.get("username", "匿名用户"),
            user_level=data.get("user_level", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            room_id=data.get("room_id", "")
        )
```

---

## 🔧 消息处理示例

```python
from typing import Dict, Any, Union
from dataclasses import asdict

def parse_message(data: Dict[str, Any]) -> Union[DanmakuMessage, GiftMessage, LikeMessage, EnterMessage, None]:
    """
    解析消息
    
    参数:
        data: 原始消息字典
    
    返回:
        对应的消息对象
    """
    msg_type = data.get("type")
    
    if msg_type == "danmaku":
        return DanmakuMessage.from_dict(data)
    elif msg_type == "gift":
        return GiftMessage.from_dict(data)
    elif msg_type == "like":
        return LikeMessage.from_dict(data)
    elif msg_type == "enter":
        return EnterMessage.from_dict(data)
    else:
        return None

def message_to_dict(message) -> Dict[str, Any]:
    """将消息对象转换为字典"""
    return asdict(message)
```

---

## 📝 使用示例

### 发送弹幕消息

```python
# 创建弹幕消息
danmaku = DanmakuMessage(
    user_id="123456789",
    username="小明",
    content="iPhone 15 Pro多少钱？",
    timestamp=datetime.now().isoformat(),
    room_id="room_001"
)

# 转换为字典发送
data = message_to_dict(danmaku)
await websocket.send(json.dumps(data))
```

### 接收并处理消息

```python
# 接收消息
raw_data = await websocket.recv()
data = json.loads(raw_data)

# 解析消息
message = parse_message(data)

if isinstance(message, DanmakuMessage):
    print(f"[{message.username}]: {message.content}")
elif isinstance(message, GiftMessage):
    print(f"🎁 {message.username} 送出 {message.gift_name} x{message.gift_count}")
```

---

## ⚠️ 注意事项

1. **时间戳格式**: 使用 ISO 8601 格式 (`YYYY-MM-DDTHH:MM:SS.sssZ`)
2. **必填字段**: `type`、`user_id`、`username`、`timestamp`、`room_id` 是所有消息的必填字段
3. **字符编码**: 使用 UTF-8 编码
4. **JSON格式**: 严格遵循 JSON 规范，不支持注释

---

**最后更新**: 2025-01-21
