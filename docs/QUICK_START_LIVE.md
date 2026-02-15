# 直播AI助手 - 快速开始指南

## 🚀 如何连接直播间

连接直播AI助手到直播间需要以下步骤：

### 方案选择

根据你的需求选择合适的集成方案：

| 方案 | 适用场景 | 难度 | 推荐度 |
|------|---------|------|--------|
| **方案1: 官方API集成** | 已有开发者账号，需要稳定集成 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **方案2: 浏览器自动化** | 临时测试，无开发者账号 | ⭐⭐ | ⭐⭐⭐ |
| **方案3: WebSocket代理** | 通用方案，支持多平台 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

---

## 📱 方案1: 官方API集成（推荐）

### 第一步：申请开发者账号

**抖音直播**
1. 访问 https://developer.open-douyin.com/
2. 注册开发者账号
3. 创建应用，获取 `App ID` 和 `App Secret`
4. 申请权限：直播间弹幕接收、直播间消息发送

**快手直播**
1. 访问 https://open.kuaishou.com/
2. 注册开发者账号
3. 创建应用，获取 `App ID` 和 `App Secret`
4. 申请权限：直播间弹幕接收、直播间消息发送

**淘宝直播**
1. 访问 https://open.taobao.com/
2. 注册开发者账号
3. 创建应用，获取 `App Key` 和 `App Secret`
4. 申请权限：直播间弹幕接收、直播间消息发送

### 第二步：配置环境变量

```bash
# 抖音直播配置
export DOUYIN_APP_ID="your_douyin_app_id"
export DOUYIN_APP_SECRET="your_douyin_app_secret"

# 快手直播配置
export KUAISHOU_APP_ID="your_kuaishou_app_id"
export KUAISHOU_APP_SECRET="your_kuaishou_app_secret"
```

### 第三步：运行集成程序

```bash
# 进入项目目录
cd /workspace/projects

# 运行直播间集成示例
python src/live_integration_example.py

# 根据提示选择对应的平台（1=抖音, 2=快手, 3=淘宝）
```

---

## 🧪 方案2: 快速测试（模拟直播）

如果你只是想快速测试AI助手功能，可以先使用模拟直播：

```bash
# 进入项目目录
cd /workspace/projects

# 运行直播间集成示例
python src/live_integration_example.py

# 选择选项4：模拟直播测试
```

这将运行一个模拟的直播场景，AI助手会处理预设的弹幕，包括：
- 价格询问
- 库存查询
- 粤语弹幕
- 投诉处理

---

## 🔧 方案3: 通用WebSocket方案

如果平台不提供官方API，可以使用通用WebSocket连接：

### 安装依赖

```bash
pip install websockets
```

### 使用示例

```python
import asyncio
from websockets import connect

async def connect_live_room(websocket_url: str):
    """连接到直播间"""
    async with connect(websocket_url) as websocket:
        # 接收弹幕
        async for message in websocket:
            print(f"收到弹幕: {message}")
            
            # 调用AI助手处理
            ai_response = process_danmaku(message)
            
            # 发送回复
            await websocket.send(ai_response)
```

参考文档：
- `docs/live_integration_guide.md` - 详细的WebSocket连接器实现
- `docs/live_platform_integration.md` - 各平台详细集成方案

---

## 📂 项目文件说明

```
项目根目录/
├── src/
│   ├── agents/
│   │   └── agent.py                    # AI Agent核心逻辑
│   ├── tools/                          # 工具集合
│   │   ├── product_query_tool.py       # 商品查询工具
│   │   ├── price_stock_verify_tool.py  # 价格/库存核对工具
│   │   └── danmaku_analysis_tool.py    # 弹幕分析工具
│   └── live_integration_example.py     # 直播间集成示例 ⭐
├── docs/
│   ├── live_integration_guide.md       # WebSocket连接器文档
│   ├── live_platform_integration.md    # 各平台详细集成方案 ⭐
│   └── QUICK_START_LIVE.md             # 本文档
├── config/
│   └── agent_llm_config.json           # AI配置
└── assets/
    └── products.json                   # 商品数据
```

---

## 🔍 快速测试流程

### 1. 测试弹幕回复功能

```bash
# 运行模拟直播测试
python src/live_integration_example.py
# 选择 4

# 观察AI助手如何处理不同类型的弹幕：
# - 价格询问
# - 库存查询
# - 粤语识别
# - 投诉处理
```

### 2. 测试主播错误检测

```bash
python src/live_integration_example.py
# 选择 5

# 测试AI助手如何检测主播的错误：
# - 主播说错价格 → AI立即更正
# - 主播说错库存 → AI立即更正
# - 商品售罄 → AI紧急提醒
```

### 3. 集成实际直播间

```bash
# 1. 配置环境变量
export DOUYIN_APP_ID="your_app_id"
export DOUYIN_APP_SECRET="your_app_secret"

# 2. 运行集成程序
python src/live_integration_example.py
# 选择 1（抖音）

# 3. AI助手将自动：
#    - 连接到直播间
#    - 接收弹幕
#    - 生成回复
#    - 发送到直播间
```

---

## ⚙️ 高级配置

### 自定义商品数据

编辑 `assets/products.json` 添加你的商品信息：

```json
[
  {
    "id": 1,
    "name": "商品名称",
    "price": 999.00,
    "stock": 100,
    "description": "商品描述",
    "category": "分类",
    "sku": "SKU编号",
    "is_active": true
  }
]
```

### 自定义AI回复风格

编辑 `config/agent_llm_config.json` 的 `sp` 字段：

```json
{
  "sp": "你是一个专业的直播AI助手...\n\n# 回复风格\n- 语气：亲切热情\n- 长度：不超过100字\n- 口头禅：~、🥳、🎉"
}
```

---

## 📞 常见问题

### Q1: 如何获取直播间的WebSocket地址？

**A:** 不同平台的方式不同：
- 抖音：使用开放平台API获取房间ID，然后连接到 `wss://webcast.douyin.com/websocket/im/v1?room_id={room_id}`
- 快手：参考快手开放文档
- 淘宝：使用淘宝直播API

### Q2: 弹幕发送频率有限制吗？

**A:** 是的，大多数平台都有频率限制：
- 抖音：每秒最多3条
- 快手：每分钟最多100条
- 建议：使用消息队列和限流机制

### Q3: 如何实现主播语音监听？

**A:** 需要两个步骤：
1. 使用FFmpeg获取直播间音频流
2. 使用ASR（语音转文字）服务转换语音

参考 `docs/live_platform_integration.md` 的"主播语音监听"章节。

### Q4: 如何处理断线重连？

**A:** WebSocket连接器已内置自动重连机制：

```python
async def connect_with_retry(self, max_retries=5):
    """带重试的连接"""
    for i in range(max_retries):
        try:
            await self.connect()
            break
        except Exception as e:
            if i < max_retries - 1:
                print(f"连接失败，3秒后重试...")
                await asyncio.sleep(3)
            else:
                raise e
```

### Q5: 支持多语言/方言吗？

**A:** 完全支持！AI助手会自动检测弹幕语言并用相同语言回复：
- 粤语弹幕 → 粤语回复 ✅
- 英语弹幕 → 英语回复 ✅
- 日语弹幕 → 日语回复 ✅

---

## 📚 更多文档

- **[完整集成方案](docs/live_platform_integration.md)** - 各平台详细集成指南
- **[WebSocket连接器](docs/live_integration_guide.md)** - 连接器实现细节
- **[系统提示词](config/agent_llm_config.json)** - AI助手配置说明

---

## 🎉 开始使用

1. 先运行模拟测试，熟悉功能：
   ```bash
   python src/live_integration_example.py
   # 选择 4
   ```

2. 申请目标平台的开发者账号

3. 配置环境变量并集成真实直播间

4. 部署到生产环境

祝你集成顺利！如有问题，请参考详细文档或联系技术支持。
