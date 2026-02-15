# 直播平台集成方案

## 概述

将AI助手连接到直播间需要与不同的直播平台进行集成。本文档提供主流直播平台（抖音、快手、淘宝直播）的详细集成方案。

## 📋 目录

1. [技术架构](#技术架构)
2. [抖音直播集成](#抖音直播集成)
3. [快手直播集成](#快手直播集成)
4. [淘宝直播集成](#淘宝直播集成)
5. [通用WebSocket方案](#通用websocket方案)
6. [主播语音监听](#主播语音监听)
7. [部署方案](#部署方案)

---

## 技术架构

### 系统架构图

```
┌─────────────┐     WebSocket/HTTP     ┌──────────────┐
│  直播平台    │ ──────────────────────▶  AI助手系统   │
│ (抖音/快手) │                       └──────────────┘
└─────────────┘                                │
        │                                       │
        │ 弹幕数据                               │
        │                                       │
        ▼                                       ▼
┌─────────────┐     弹幕分析      ┌──────────────┐
│  弹幕接收器  │ ────────────────▶  AI Agent    │
└─────────────┘               └──────────────┘
        ▲                                 │
        │                                 │
        │ AI回复                          │
        │                                 │
        │                         ┌───────┴───────┐
        │                         │  工具调用      │
        │                         └───────────────┘
        │                                 │
        │                         ┌───────┴───────┐
        └─────────────────────────│  商品数据库    │
                                  └───────────────┘
```

### 核心组件

1. **直播间连接器** (`LiveConnector`) - 负责与直播平台建立WebSocket连接
2. **弹幕AI桥接器** (`DanmakuAIBridge`) - 连接直播间和AI助手
3. **AI Agent** - 处理弹幕并生成回复
4. **商品数据库** - 提供商品信息查询

---

## 抖音直播集成

### 1. 申请开发者账号

1. 访问 [抖音开放平台](https://developer.open-douyin.com/)
2. 注册开发者账号
3. 创建应用，获取 `App ID` 和 `App Secret`

### 2. 申请权限

需要申请以下权限：

- **直播间弹幕接收权限** - 用于获取实时弹幕
- **直播间消息发送权限** - 用于发送AI回复
- **直播间音频流权限** - 用于监听主播语音（可选）

### 3. 获取直播间信息

使用抖音开放API获取直播间ID：

```python
import requests

DOUYIN_API_BASE = "https://open.douyin.com"
APP_ID = "your_app_id"
APP_SECRET = "your_app_secret"

def get_live_room_id(room_url: str):
    """根据直播间URL获取直播间ID"""
    # 1. 获取access_token
    token_response = requests.post(
        f"{DOUYIN_API_BASE}/oauth/access_token",
        params={
            "client_key": APP_ID,
            "client_secret": APP_SECRET,
            "grant_type": "client_credential"
        }
    )
    access_token = token_response.json()["data"]["access_token"]
    
    # 2. 获取直播间ID
    live_response = requests.get(
        f"{DOUYIN_API_BASE}/live/room/info",
        headers={"access-token": access_token},
        params={"room_url": room_url}
    )
    
    room_id = live_response.json()["data"]["room_id"]
    return room_id
```

### 4. 连接直播间WebSocket

抖音直播间弹幕WebSocket地址：

```python
DOUYIN_WEBSOCKET_URL = f"wss://webcast.douyin.com/websocket/im/v1?room_id={room_id}&signature={signature}"
```

需要生成签名（具体参考抖音开放文档）。

### 5. 接收弹幕数据

抖音弹幕消息格式：

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

### 6. 发送消息到直播间

使用抖音开放API发送消息：

```python
def send_douyin_message(room_id: str, message: str):
    """发送消息到抖音直播间"""
    response = requests.post(
        f"{DOUYIN_API_BASE}/live/chat/send",
        headers={"access-token": access_token},
        json={
            "room_id": room_id,
            "content": message,
            "msg_type": "text"
        }
    )
    return response.json()
```

---

## 快手直播集成

### 1. 申请开发者账号

1. 访问 [快手开放平台](https://open.kuaishou.com/)
2. 注册开发者账号
3. 创建应用，获取 `App ID` 和 `App Secret`

### 2. 申请权限

需要申请以下权限：

- **直播间弹幕接收权限**
- **直播间消息发送权限**
- **直播间音频流权限**

### 3. 获取直播间信息

```python
KUAISHOU_API_BASE = "https://open.kuaishou.com"

def get_kuaishou_live_room_id(live_url: str):
    """获取快手直播间ID"""
    token_response = requests.post(
        f"{KUAISHOU_API_BASE}/oauth2/access_token",
        params={
            "app_id": APP_ID,
            "app_secret": APP_SECRET,
            "grant_type": "client_credentials"
        }
    )
    access_token = token_response.json()["access_token"]
    
    # 解析直播间URL获取room_id
    # https://live.kuaishou.com/u/{user_id} -> user_id
    return room_id
```

### 4. 连接直播间WebSocket

```python
KUAISHOU_WEBSOCKET_URL = f"wss://live.kuaishou.com/api/v1/websocket?room_id={room_id}"
```

### 5. 接收和发送消息

与抖音类似，使用WebSocket接收弹幕，使用HTTP API发送消息。

---

## 淘宝直播集成

### 1. 申请开发者账号

1. 访问 [淘宝开放平台](https://open.taobao.com/)
2. 注册开发者账号
3. 创建应用，获取 `App Key` 和 `App Secret`

### 2. 申请权限

- **直播间弹幕接收权限**
- **直播间消息发送权限**
- **淘宝直播开放API权限**

### 3. 获取直播间信息

```python
TAOBAO_API_BASE = "https://eco.taobao.com/router/rest"

def get_taobao_live_room_id(live_id: str):
    """获取淘宝直播间信息"""
    params = {
        "method": "taobao.live.room.get",
        "app_key": APP_KEY,
        "session": access_token,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "v": "2.0",
        "format": "json",
        "live_id": live_id
    }
    
    response = requests.get(TAOBAO_API_BASE, params=params)
    return response.json()
```

### 4. 连接直播间

淘宝直播使用WebSocket进行实时通信：

```python
TAOBAO_WEBSOCKET_URL = f"wss://live.taobao.com/api/v1/im?room_id={room_id}"
```

---

## 通用WebSocket方案

如果平台不提供官方API，可以使用以下方案：

### 方案1: 浏览器自动化

使用Selenium或Playwright模拟浏览器访问直播间，抓取弹幕数据：

```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class BrowserDanmakuCrawler:
    """浏览器弹幕爬虫"""
    
    def __init__(self, live_url: str):
        self.driver = webdriver.Chrome()
        self.live_url = live_url
    
    def start(self):
        """开始爬取弹幕"""
        self.driver.get(self.live_url)
        
        # 等待直播间加载
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "danmaku-container"))
        )
        
        # 持续监听弹幕
        while True:
            danmaku_elements = self.driver.find_elements(By.CLASS_NAME, "danmaku-item")
            
            for element in danmaku_elements:
                username = element.find_element(By.CLASS_NAME, "username").text
                content = element.find_element(By.CLASS_NAME, "content").text
                
                print(f"{username}: {content}")
            
            time.sleep(1)
```

### 方案2: 网络请求拦截

使用mitmproxy或Charles抓包工具分析直播间WebSocket通信：

```python
from mitmproxy import http

def request(flow: http.HTTPFlow):
    """拦截HTTP请求"""
    if flow.request.pretty_url.startswith("wss://"):
        print(f"检测到WebSocket连接: {flow.request.pretty_url}")
```

### 方案3: 直播平台SDK

部分平台提供官方SDK：

```python
# 抖音SDK示例
from douyin.open import DouyinClient

client = DouyinClient(app_id=APP_ID, app_secret=APP_SECRET)
client.connect_live_room(room_id=room_id)
```

---

## 主播语音监听

### 1. 获取直播间音频流

使用FFmpeg获取直播间的音频流：

```bash
# 获取直播间的音频流
ffmpeg -i "直播流地址" -vn -acodec pcm_s16le -ar 16000 -ac 1 output.wav
```

### 2. 使用ASR转换语音为文本

调用ASR服务将语音转为文本：

```python
from coze_coding_dev_sdk import ASRClient
from coze_coding_utils.runtime_ctx.context import new_context

async def transcribe_audio(audio_file: str):
    """将音频转为文本"""
    ctx = new_context(method="transcribe_audio")
    client = ASRClient(ctx=ctx)
    
    with open(audio_file, "rb") as f:
        audio_data = f.read()
        import base64
        audio_base64 = base64.b64encode(audio_data).decode("utf-8")
    
    text, data = client.recognize(
        uid="anchor_monitor",
        base64_data=audio_base64
    )
    
    return text
```

### 3. 实时监听流程

```python
import asyncio
import subprocess
from datetime import datetime

async def monitor_anchor_audio(live_url: str):
    """实时监听主播语音"""
    
    # 使用FFmpeg持续下载音频
    process = subprocess.Popen([
        "ffmpeg",
        "-i", live_url,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-f", "wav",
        "-t", "10",  # 每10秒一个片段
        f"/tmp/audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    ])
    
    while True:
        # 等待音频文件生成
        await asyncio.sleep(10)
        
        # 转换最新音频文件
        audio_file = get_latest_audio_file()
        if audio_file:
            text = await transcribe_audio(audio_file)
            
            # 将文本传递给AI助手进行核对
            if text:
                print(f"🎙️ 主播说: {text}")
                await verify_anchor_speech(text)
```

---

## 部署方案

### 方案1: 云服务器部署

推荐使用云服务器部署，如阿里云、腾讯云：

```yaml
# docker-compose.yml
version: '3'

services:
  live-ai-assistant:
    image: live-ai-assistant:latest
    container_name: live-ai-assistant
    ports:
      - "8000:8000"
    environment:
      - COZE_WORKSPACE_PATH=/workspace/projects
      - DOUYIN_APP_ID=${DOUYIN_APP_ID}
      - DOUYIN_APP_SECRET=${DOUYIN_APP_SECRET}
    volumes:
      - ./config:/workspace/projects/config
      - ./assets:/workspace/projects/assets
      - ./logs:/app/logs
    restart: always
```

### 方案2: Serverless部署

使用云函数（如阿里云函数计算、腾讯云SCF）：

```python
# 函数入口
def handler(event, context):
    """处理直播间弹幕"""
    danmaku_data = json.loads(event["body"])
    
    # 调用AI Agent
    agent = build_agent()
    result = agent.invoke({"messages": [{"role": "user", "content": danmaku_data}]})
    
    # 发送回复
    send_reply(result["response"])
    
    return {"statusCode": 200, "body": "OK"}
```

### 方案3: 本地开发测试

使用模拟数据进行本地测试：

```python
# 运行模拟测试
python src/live_integration_example.py

# 选择选项4运行模拟直播测试
```

---

## 注意事项

### 1. 权限申请

- 不同平台的权限申请流程不同，需要仔细阅读官方文档
- 部分高级权限可能需要企业认证或付费

### 2. 频率限制

- 平台对弹幕发送频率有限制（如每秒最多3条）
- 需要实现消息队列和限流机制

### 3. 稳定性保障

- WebSocket连接可能断开，需要实现自动重连机制
- 需要监控服务状态，及时发现和处理异常

### 4. 数据安全

- 不要泄露API密钥和敏感信息
- 使用环境变量存储配置信息

### 5. 合规要求

- 遵守直播平台的用户协议和API使用规范
- AI回复内容需要符合平台内容审核规则

---

## 下一步

1. 根据目标平台申请开发者账号
2. 测试模拟直播场景（运行 `python src/live_integration_example.py`）
3. 集成实际的直播间API
4. 部署到生产环境
5. 监控和优化性能

如有问题，请参考对应平台的官方文档或联系技术支持。
