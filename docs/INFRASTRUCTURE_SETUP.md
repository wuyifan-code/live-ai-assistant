# 🚀 环境配置和服务部署指南

本文档详细说明如何配置和部署直播带货AI助手所需的基础设施。

---

## 📋 目录

1. [环境变量配置](#1-环境变量配置)
2. [Redis服务配置](#2-redis服务配置)
3. [PostgreSQL数据库配置](#3-postgresql数据库配置)
4. [ASR语音识别服务配置](#4-asr语音识别服务配置)
5. [直播平台API配置](#5-直播平台api配置)
6. [服务启动验证](#6-服务启动验证)

---

## 1. 环境变量配置

### 1.1 创建环境变量文件

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 1.2 必填配置项

以下配置项**必须**填写，否则系统无法正常运行：

#### 🔑 大模型API密钥
```env
# Coze平台会自动注入，无需手动配置
# 如果在本地开发环境，需要设置：
COZE_WORKLOAD_IDENTITY_API_KEY=your-api-key-here
COZE_INTEGRATION_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
```

#### 🗄️ PostgreSQL数据库连接
```env
# 本地PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/live_ai_db

# 或使用Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
```

#### 🔴 Redis缓存服务
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

#### 📺 直播平台凭证
```env
# 抖音开放平台
DOUYIN_APP_ID=your-app-id
DOUYIN_APP_SECRET=your-app-secret
```

### 1.3 推荐配置项

以下配置项建议配置，以获得完整功能：

```env
# 告警通知
ENABLE_FEISHU_ALERT=true
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# 功能开关
ENABLE_VISUAL_RECOGNITION=true
ENABLE_TTS_OUTPUT=true
ENABLE_RAG_KNOWLEDGE=true
ENABLE_HUMAN_COLLABORATION=true
```

---

## 2. Redis服务配置

Redis是系统运行的**必需**组件，用于：
- 会话管理和状态存储
- 商品信息缓存
- 弹幕去重
- 多级优先级队列

### 2.1 安装Redis

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### CentOS/RHEL
```bash
sudo yum install redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### Docker方式
```bash
# 启动Redis容器
docker run -d \
  --name live-ai-redis \
  -p 6379:6379 \
  redis:5.0-alpine \
  redis-server --appendonly yes

# 或使用docker-compose
docker-compose up -d redis
```

### 2.2 配置Redis

编辑 `/etc/redis/redis.conf`:

```conf
# 绑定地址（生产环境建议修改）
bind 127.0.0.1

# 端口
port 6379

# 密码（生产环境强烈建议设置）
requirepass your-redis-password

# 最大内存
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化
appendonly yes
appendfsync everysec

# 最大连接数
maxclients 10000
```

重启Redis服务：
```bash
sudo systemctl restart redis-server
```

### 2.3 验证Redis连接

```bash
# 测试连接
redis-cli ping

# 如果设置了密码
redis-cli -a your-password ping

# 测试读写
redis-cli set test_key "Hello Redis"
redis-cli get test_key
```

### 2.4 配置环境变量

在 `.env` 文件中配置：
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
REDIS_MAX_CONNECTIONS=100
```

---

## 3. PostgreSQL数据库配置

### 3.1 安装PostgreSQL

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### macOS
```bash
brew install postgresql@14
brew services start postgresql@14
```

### 3.2 创建数据库

```bash
# 切换到postgres用户
sudo -u postgres psql

# 创建数据库
CREATE DATABASE live_ai_db;

# 创建用户
CREATE USER live_ai_user WITH PASSWORD 'your-password';

# 授权
GRANT ALL PRIVILEGES ON DATABASE live_ai_db TO live_ai_user;

# 启用pgvector扩展（用于向量搜索）
\c live_ai_db
CREATE EXTENSION IF NOT EXISTS vector;

# 退出
\q
```

### 3.3 使用Supabase（推荐）

Supabase提供了托管的PostgreSQL + pgvector服务：

1. 访问 https://supabase.com
2. 创建新项目
3. 获取连接信息：
   - `SUPABASE_URL`: 项目URL
   - `SUPABASE_ANON_KEY`: 匿名密钥
4. 在SQL编辑器中运行 `CREATE EXTENSION IF NOT EXISTS vector;`

### 3.4 初始化数据库表

```bash
# 运行初始化脚本
python scripts/init_database.py
```

这将创建以下表：
- `products` - 商品信息表
- `user_sessions` - 用户会话表
- `live_sessions` - 直播记录表
- `danmaku_records` - 弹幕记录表
- `sales_records` - 销售记录表
- `human_takeovers` - 人工接管记录表
- `knowledge_documents` - 知识库文档表
- `knowledge_embeddings` - 向量嵌入表

---

## 4. ASR语音识别服务配置

ASR（自动语音识别）用于实时监听直播间语音。

### 4.1 启用ASR功能

在 `.env` 中配置：
```env
ENABLE_REALTIME_LISTENING=true
```

### 4.2 ASR客户端配置

系统使用 `coze-coding-dev-sdk` 提供的ASR服务：

```python
from coze_coding_dev_sdk import ASRClient

# 初始化ASR客户端
asr_client = ASRClient()

# 实时转录
async for result in asr_client.transcribe_stream(audio_stream):
    print(result.text)
```

### 4.3 音频输入配置

支持两种音频输入方式：

#### 方式1: 实时音频流
```python
# 从直播平台获取音频流
audio_stream = get_live_audio_stream(room_id)
await asr_client.transcribe_stream(audio_stream)
```

#### 方式2: 音频文件
```python
# 上传音频文件进行转录
result = await asr_client.transcribe_file("audio.wav")
```

### 4.4 验证ASR服务

```python
# 测试脚本
from coze_coding_dev_sdk import ASRClient
import asyncio

async def test_asr():
    client = ASRClient()
    
    # 模拟音频流（实际使用时替换为真实音频）
    test_audio = b"..."  # 音频数据
    
    async for result in client.transcribe_stream(test_audio):
        print(f"识别结果: {result.text}")

asyncio.run(test_asr())
```

---

## 5. 直播平台API配置

### 5.1 抖音开放平台

#### 申请步骤

1. **注册开发者账号**
   - 访问 https://developer.open-douyin.com
   - 完成开发者认证

2. **创建应用**
   - 创建移动应用/网站应用
   - 申请直播权限

3. **获取凭证**
   - 复制 `App ID` 和 `App Secret`

#### 配置权限

需要申请以下权限：
- `live.room.info` - 获取直播间信息
- `live.room.danmaku` - 获取弹幕列表
- `live.room.screenshot` - 获取直播截图

#### 配置环境变量

```env
LIVE_PLATFORM=douyin
DOUYIN_APP_ID=your-app-id
DOUYIN_APP_SECRET=your-app-secret
```

### 5.2 快手开放平台

#### 申请步骤

1. 访问 https://open.kuaishou.com
2. 创建应用并申请直播权限
3. 获取 `App ID` 和 `App Secret`

#### 配置环境变量

```env
LIVE_PLATFORM=kuaishou
KUAISHOU_APP_ID=your-app-id
KUAISHOU_APP_SECRET=your-app-secret
```

### 5.3 验证平台API

```python
from integrations.live_stream_api import LiveStreamAPIFactory

# 创建API客户端
api = LiveStreamAPIFactory.create_api(
    platform="douyin",
    app_id="your-app-id",
    app_secret="your-app-secret"
)

# 测试获取直播间信息
room_info = await api.get_live_room_info("room_id")
print(room_info)
```

---

## 6. 服务启动验证

### 6.1 完整启动流程

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
vim .env  # 填写必要配置

# 3. 启动Redis
sudo systemctl start redis-server
# 或 Docker
docker run -d --name redis -p 6379:6379 redis:5.0-alpine

# 4. 初始化数据库
python scripts/init_database.py

# 5. 导入知识库（可选）
python -m src.utils.knowledge_importer import_sample

# 6. 启动服务
python scripts/run_prod.py
```

### 6.2 验证服务状态

#### 检查Redis连接
```python
from storage.redis_pool import get_redis_pool
import asyncio

async def test_redis():
    pool = await get_redis_pool()
    await pool.set("test", "ok")
    value = await pool.get("test")
    print(f"Redis测试: {value}")

asyncio.run(test_redis())
```

#### 检查数据库连接
```python
from storage.database.supabase_client import get_supabase_client

client = get_supabase_client()
result = client.table('products').select('count').execute()
print(f"商品数量: {result.count}")
```

#### 检查Agent运行
```python
from agents.agent import build_agent

agent = build_agent()
print(f"工具数量: {len(agent.tools)}")
```

### 6.3 访问监控面板

启动服务后，访问以下地址：

- **主服务**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **监控面板**: http://localhost:8000/monitoring
- **Prometheus**: http://localhost:9090

---

## 🔧 故障排查

### Redis连接失败

```bash
# 检查Redis是否运行
redis-cli ping

# 检查Redis配置
redis-cli config get bind
redis-cli config get requirepass

# 查看Redis日志
tail -f /var/log/redis/redis-server.log
```

### 数据库连接失败

```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试连接
psql -U postgres -d live_ai_db

# 检查连接字符串
echo $DATABASE_URL
```

### API调用失败

```bash
# 检查环境变量
echo $DOUYIN_APP_ID
echo $DOUYIN_APP_SECRET

# 查看应用日志
tail -f /app/work/logs/bypass/app.log
```

---

## 📝 配置检查清单

在启动服务前，请确认以下配置已完成：

- [ ] `.env` 文件已创建并填写
- [ ] Redis服务已启动并可连接
- [ ] PostgreSQL数据库已创建
- [ ] 数据库表已初始化
- [ ] 直播平台API凭证已配置
- [ ] 大模型API密钥已配置（或自动注入）
- [ ] 告警通知渠道已配置（可选）
- [ ] 对象存储已配置（可选）

全部确认后，即可启动服务！
