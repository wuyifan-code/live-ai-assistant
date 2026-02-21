# 抖音直播间API集成指南

## 📋 目录

1. [申请抖音开放平台账号](#1-申请抖音开放平台账号)
2. [配置环境变量](#2-配置环境变量)
3. [使用API工具](#3-使用api工具)
4. [真实直播间集成](#4-真实直播间集成)
5. [常见问题](#5-常见问题)

---

## 1. 申请抖音开放平台账号

### 步骤1: 注册开发者账号

1. 访问 [抖音开放平台](https://developer.open-douyin.com/)
2. 点击右上角"登录/注册"
3. 使用抖音账号扫码登录
4. 完成开发者认证（需要营业执照）

### 步骤2: 创建应用

1. 进入[管理中心](https://developer.open-douyin.com/console)
2. 点击"创建应用"
3. 选择应用类型：
   - **移动应用**：适合移动端直播助手
   - **网站应用**：适合Web端管理后台
   - **小程序**：适合抖音内应用

4. 填写应用信息：
   - 应用名称：如"XX直播助手"
   - 应用简介：AI辅助直播带货助手
   - 应用图标：上传应用logo

### 步骤3: 申请权限

在应用详情页，申请以下权限：

| 权限名称 | 权限码 | 用途 | 备注 |
|---------|--------|------|------|
| 获取直播间信息 | `live.room.info` | 获取直播间状态、在线人数等 | 必需 |
| 获取弹幕列表 | `live.room.danmaku` | 实时获取弹幕消息 | 必需 |
| 发送弹幕消息 | `live.room.send` | AI回复弹幕 | 推荐 |
| 获取商品列表 | `live.room.product` | 同步直播间商品 | 推荐 |
| 直播间统计 | `live.room.stats` | 获取直播间数据统计 | 可选 |

### 步骤4: 获取凭证

在应用详情页，找到：
- **App ID**（应用ID）
- **App Secret**（应用密钥）

⚠️ **重要**：App Secret 非常重要，请妥善保管，不要泄露！

---

## 2. 配置环境变量

### 方式1: 编辑 .env 文件

```bash
# 打开配置文件
vim .env

# 填写抖音API凭证
DOUYIN_APP_ID=你的AppID
DOUYIN_APP_SECRET=你的AppSecret
```

### 方式2: 使用环境变量

```bash
export DOUYIN_APP_ID="你的AppID"
export DOUYIN_APP_SECRET="你的AppSecret"
```

### 验证配置

```bash
python -c "
import os
print(f'App ID: {os.getenv(\"DOUYIN_APP_ID\")}')
print(f'App Secret: {os.getenv(\"DOUYIN_APP_SECRET\")[:10]}...')
"
```

---

## 3. 使用API工具

### 基本使用

```python
from integrations.douyin_api import DouyinLiveAPI

# 创建API实例
api = DouyinLiveAPI()

# 或手动传入凭证
api = DouyinLiveAPI(
    app_id="your_app_id",
    app_secret="your_app_secret"
)
```

### 获取直播间ID

```python
import asyncio

async def get_room_id():
    api = DouyinLiveAPI()
    
    # 从直播间URL提取ID
    room_url = "https://live.douyin.com/123456789"
    room_id = await api.get_room_id_by_url(room_url)
    
    print(f"直播间ID: {room_id}")
    # 输出: 直播间ID: 123456789

asyncio.run(get_room_id())
```

### 获取直播间信息

```python
async def get_info():
    api = DouyinLiveAPI()
    
    room_id = "123456789"
    room_info = await api.get_room_info(room_id)
    
    print(f"标题: {room_info['title']}")
    print(f"主播: {room_info['anchor']['name']}")
    print(f"在线人数: {room_info['viewer_count']}")
    print(f"状态: {room_info['status_text']}")

asyncio.run(get_info())
```

### 获取实时弹幕

```python
async def get_danmaku():
    api = DouyinLiveAPI()
    
    room_id = "123456789"
    
    # 获取最近100条弹幕
    danmaku_list = await api.get_danmaku_list(room_id, count=100)
    
    for danmaku in danmaku_list:
        print(f"[{danmaku['username']}]: {danmaku['content']}")

asyncio.run(get_danmaku())
```

### 发送消息

```python
async def send_message():
    api = DouyinLiveAPI()
    
    room_id = "123456789"
    message = "欢迎来到直播间！"
    
    success = await api.send_message(room_id, message)
    
    if success:
        print("✅ 消息发送成功")
    else:
        print("❌ 消息发送失败")

asyncio.run(send_message())
```

### 获取商品列表

```python
async def get_products():
    api = DouyinLiveAPI()
    
    room_id = "123456789"
    products = await api.get_product_list(room_id)
    
    for product in products:
        print(f"{product['name']} - ¥{product['price']}")
        print(f"  库存: {product['stock']}")

asyncio.run(get_products())
```

---

## 4. 真实直播间集成

### 完整示例

```python
import asyncio
from agents.agent import build_agent
from integrations.douyin_api import DouyinLiveAPI
from live_connector import DanmakuAIBridge

class MyLiveAssistant:
    """自定义直播助手"""
    
    def __init__(self, room_url: str):
        self.room_url = room_url
        self.api = DouyinLiveAPI()
        self.agent = build_agent()
    
    async def start(self):
        """启动助手"""
        # 1. 获取直播间ID
        room_id = await self.api.get_room_id_by_url(self.room_url)
        print(f"直播间ID: {room_id}")
        
        # 2. 获取直播间信息
        room_info = await self.api.get_room_info(room_id)
        print(f"直播间: {room_info['title']}")
        print(f"主播: {room_info['anchor']['name']}")
        
        # 3. 同步商品信息
        products = await self.api.get_product_list(room_id)
        print(f"商品数量: {len(products)}")
        
        # 4. 开始监听弹幕
        print("\n🚀 开始监听弹幕...")
        await self._listen_danmaku(room_id)
    
    async def _listen_danmaku(self, room_id: str):
        """监听弹幕"""
        cursor = "0"
        
        while True:
            # 获取弹幕
            danmaku_list = await self.api.get_danmaku_list(
                room_id,
                count=100,
                cursor=cursor
            )
            
            # 处理每条弹幕
            for danmaku in danmaku_list:
                await self._process_danmaku(room_id, danmaku)
                cursor = danmaku.get("timestamp", cursor)
            
            # 等待2秒
            await asyncio.sleep(2)
    
    async def _process_danmaku(self, room_id: str, danmaku: dict):
        """处理单条弹幕"""
        username = danmaku['username']
        content = danmaku['content']
        
        print(f"\n📥 [{username}]: {content}")
        
        # 调用AI处理
        response = await self._get_ai_response(username, content)
        
        # 发送回复
        if response:
            await self.api.send_message(room_id, response)
            print(f"📤 [AI]: {response}")
    
    async def _get_ai_response(self, username: str, content: str) -> str:
        """获取AI回复"""
        try:
            config = {"configurable": {"thread_id": f"live_{username}"}}
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": f"用户【{username}】说：{content}"}]},
                config=config
            )
            
            return result["messages"][-1].content
            
        except Exception as e:
            print(f"AI处理失败: {str(e)}")
            return None

# 运行
async def main():
    assistant = MyLiveAssistant("https://live.douyin.com/123456789")
    await assistant.start()

asyncio.run(main())
```

### 运行真实集成

```bash
# 方式1: 使用集成脚本
python src/douyin_live_integration.py

# 方式2: 自定义脚本
python your_script.py
```

---

## 5. 常见问题

### Q1: 提示"App ID或App Secret错误"

**原因**：凭证未正确配置

**解决方案**：
1. 检查 `.env` 文件是否正确填写
2. 确认没有多余的空格或换行符
3. 重启应用程序

### Q2: 提示"权限不足"

**原因**：未申请对应的API权限

**解决方案**：
1. 进入抖音开放平台应用详情页
2. 申请所需权限（如 `live.room.danmaku`）
3. 等待审核通过（通常1-3个工作日）

### Q3: 无法获取直播间信息

**可能原因**：
1. 直播间未开播
2. 直播间设置了隐私保护
3. room_id错误

**解决方案**：
```python
# 检查直播间状态
room_info = await api.get_room_info(room_id)
print(f"状态: {room_info['status_text']}")

# 状态说明:
# - 未开播: 需要主播开始直播
# - 直播中: 正常
# - 已结束: 直播已结束
```

### Q4: 获取不到弹幕

**可能原因**：
1. 直播间无人发弹幕
2. 权限未开通
3. 轮询间隔太短

**解决方案**：
```python
# 增加轮询间隔
danmaku_list = await api.get_danmaku_list(room_id, count=100)

# 检查权限
print("请确认已申请 live.room.danmaku 权限")
```

### Q5: 发送消息失败

**可能原因**：
1. 未申请 `live.room.send` 权限
2. 消息内容违规
3. 发送频率限制

**解决方案**：
```python
# 检查发送权限
success = await api.send_message(room_id, "测试消息")

if not success:
    print("请检查:")
    print("1. 是否申请了 live.room.send 权限")
    print("2. 消息内容是否合规")
    print("3. 是否触发频率限制")
```

### Q6: 如何获取直播间URL

**方法1: 从抖音APP分享**
1. 打开抖音APP
2. 进入目标直播间
3. 点击分享按钮
4. 复制链接

**方法2: 从网页版**
1. 访问 https://live.douyin.com
2. 找到目标直播间
3. 复制浏览器地址栏URL

---

## 📊 API限制说明

| 接口 | 频率限制 | 说明 |
|------|---------|------|
| 获取access_token | 100次/天 | Token有效期2小时 |
| 获取直播间信息 | 100次/分钟 | - |
| 获取弹幕列表 | 1000次/分钟 | 建议轮询间隔≥2秒 |
| 发送消息 | 100次/分钟 | 单条消息≤200字符 |
| 获取商品列表 | 100次/分钟 | - |

---

## 🛡️ 安全建议

1. **保护密钥**：不要将App Secret提交到代码仓库
2. **使用环境变量**：所有敏感信息通过环境变量配置
3. **Token缓存**：access_token会自动缓存，避免频繁请求
4. **错误处理**：捕获API异常，避免程序崩溃
5. **频率控制**：遵守API频率限制，避免被封禁

---

## 📞 技术支持

- **抖音开放平台文档**: https://developer.open-douyin.com/docs
- **问题反馈**: 在GitHub Issues提交
- **API状态**: 查看抖音开放平台公告

---

**最后更新**: 2025-01-21
