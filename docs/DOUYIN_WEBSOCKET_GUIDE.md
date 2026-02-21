# 抖音WebSocket实时监听集成

## 📋 概述

抖音直播间WebSocket连接方式，实现**毫秒级**实时弹幕监听，比轮询API更快更高效。

---

## 🚀 快速开始

### 1. 配置抖音API凭证

```bash
# 编辑 .env 文件
vim .env

# 填写凭证
DOUYIN_APP_ID=你的AppID
DOUYIN_APP_SECRET=你的AppSecret
```

### 2. 运行WebSocket监听

```bash
python src/douyin_live_websocket.py
```

按提示输入直播间URL：
```
请输入抖音直播间URL: https://live.douyin.com/123456789
```

---

## 📡 WebSocket连接方式

### 连接地址

```python
WEBSOCKET_URL = f"wss://webcast.douyin.com/websocket/im/v1?room_id={room_id}&signature={signature}"
```

### 参数说明

| 参数 | 类型 | 说明 |
|------|------|------|
| room_id | string | 直播间ID |
| app_id | string | 应用ID |
| signature | string | 签名（可选） |
| timestamp | int | 时间戳 |
| compress | string | 压缩方式（gzip） |

---

## 🔄 消息类型

### 支持的消息类型

| 类型 | 编号 | 说明 | 字段 |
|------|------|------|------|
| 弹幕 | 1 | 用户发送的弹幕消息 | user_id, username, content |
| 礼物 | 2 | 用户送出礼物 | user_id, username, gift_name, gift_count |
| 点赞 | 3 | 用户点赞 | user_id, username, like_count |
| 进入 | 4 | 用户进入直播间 | user_id, username |
| 关注 | 5 | 用户关注主播 | user_id, username |
| 分享 | 6 | 用户分享直播间 | user_id, username |
| 直播间信息 | 7 | 直播间状态更新 | room_info |

---

## 💻 使用示例

### 基本使用

```python
from integrations.douyin_websocket import DouyinWebSocketConnector
import asyncio

async def on_danmaku(danmaku: dict):
    """弹幕回调"""
    print(f"[{danmaku['username']}]: {danmaku['content']}")

async def on_gift(gift: dict):
    """礼物回调"""
    print(f"🎁 {gift['username']} 送出 {gift['gift_name']}")

# 创建连接器
connector = DouyinWebSocketConnector(
    room_id="123456789",
    on_danmaku=on_danmaku,
    on_gift=on_gift
)

# 连接
await connector.connect()

# 断开
await connector.disconnect()
```

### 完整直播助手

```python
from integrations.douyin_websocket import DouyinWebSocketConnector
from agents.agent import build_agent

class MyLiveAssistant:
    def __init__(self, room_id: str):
        self.room_id = room_id
        self.agent = build_agent()
        self.connector = None
    
    async def start(self):
        # 创建WebSocket连接器
        self.connector = DouyinWebSocketConnector(
            room_id=self.room_id,
            on_danmaku=self._on_danmaku,
            on_gift=self._on_gift
        )
        
        # 连接
        await self.connector.connect()
    
    async def _on_danmaku(self, danmaku: dict):
        # AI生成回复
        response = await self._get_ai_response(danmaku['content'])
        
        # 发送回复
        if response:
            await self.connector.send_message(response)
    
    async def _get_ai_response(self, content: str) -> str:
        # 调用AI Agent
        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": content}]}
        )
        return result["messages"][-1].content
    
    async def _on_gift(self, gift: dict):
        thank_msg = f"感谢 {gift['username']} 送出的 {gift['gift_name']}！"
        await self.connector.send_message(thank_msg)

# 运行
assistant = MyLiveAssistant("123456789")
await assistant.start()
```

---

## ⚙️ 高级配置

### 心跳设置

```python
connector = DouyinWebSocketConnector(
    room_id="123456789",
    on_danmaku=on_danmaku
)

# 修改心跳间隔（默认10秒）
connector.heartbeat_interval = 5
```

### 消息过滤

```python
async def on_danmaku(danmaku: dict):
    content = danmaku['content']
    
    # 过滤敏感词
    sensitive_words = ["违禁词1", "违禁词2"]
    if any(word in content for word in sensitive_words):
        return  # 忽略
    
    # 处理正常弹幕
    print(f"[{danmaku['username']}]: {content}")
```

### 统计信息

```python
# 获取统计
stats = connector.get_stats()

print(f"总消息数: {stats['total_messages']}")
print(f"弹幕数: {stats['danmaku_count']}")
print(f"礼物数: {stats['gift_count']}")
print(f"点赞数: {stats['like_count']}")
print(f"进入数: {stats['enter_count']}")
```

---

## 🔧 错误处理

### 连接断开自动重连

```python
async def run_with_reconnect(room_id: str, max_retries: int = 5):
    """带自动重连的运行"""
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            connector = DouyinWebSocketConnector(
                room_id=room_id,
                on_danmaku=on_danmaku,
                on_error=on_error
            )
            
            await connector.connect()
            
            # 连接成功，重置重试计数
            retry_count = 0
            
        except Exception as e:
            retry_count += 1
            print(f"连接失败 ({retry_count}/{max_retries}): {str(e)}")
            
            if retry_count < max_retries:
                await asyncio.sleep(5)  # 等待5秒后重试
            else:
                print("达到最大重试次数，退出")
                raise

async def on_error(error: str):
    print(f"WebSocket错误: {error}")
```

---

## 📊 性能对比

| 方式 | 延迟 | 资源消耗 | 推荐场景 |
|------|------|---------|---------|
| WebSocket | < 100ms | 低 | **实时监听（推荐）** |
| API轮询 | 2-3秒 | 中 | 数据分析、统计 |
| 混合模式 | 混合 | 中 | 复杂业务场景 |

---

## ⚠️ 注意事项

1. **连接数量限制**
   - 单个应用同时连接的直播间数量有限制
   - 建议：单个应用连接不超过100个直播间

2. **消息频率**
   - 高热度直播间消息量很大
   - 建议实现消息过滤和队列机制

3. **心跳机制**
   - 必须定期发送心跳包，否则会被断开
   - 默认心跳间隔10秒

4. **签名验证**
   - 某些场景需要签名验证
   - 请参考抖音开放平台文档

5. **消息压缩**
   - 服务器可能返回gzip压缩的消息
   - 代码已自动处理解压

---

## 🛠️ 故障排查

### 问题1: 无法连接WebSocket

**检查项**：
```python
# 1. 检查房间ID是否正确
print(f"Room ID: {room_id}")

# 2. 检查直播间是否开播
from integrations.douyin_api import DouyinLiveAPI
api = DouyinLiveAPI()
room_info = await api.get_room_info(room_id)
print(f"状态: {room_info['status_text']}")

# 3. 检查网络连接
import socket
socket.create_connection(("webcast.douyin.com", 443), timeout=5)
print("网络连接正常")
```

### 问题2: 连接后立即断开

**可能原因**：
- 签名验证失败
- 直播间已结束
- 频率限制

**解决方案**：
```python
# 添加错误处理
async def on_error(error: str):
    print(f"错误详情: {error}")
    
    if "signature" in error.lower():
        print("签名验证失败，请检查AppID和AppSecret")
    elif "room" in error.lower():
        print("直播间状态异常，请检查直播间是否开播")
```

### 问题3: 消息延迟

**优化方案**：
```python
# 使用异步处理
async def on_danmaku(danmaku: dict):
    # 快速处理，不要阻塞
    asyncio.create_task(process_danmaku(danmaku))

async def process_danmaku(danmaku: dict):
    # 复杂处理逻辑
    ...
```

---

## 📚 相关文档

- **API集成指南**: `docs/DOUYIN_API_GUIDE.md`
- **环境配置**: `docs/INFRASTRUCTURE_SETUP.md`
- **快速开始**: `docs/QUICK_START.md`

---

**最后更新**: 2025-01-21
