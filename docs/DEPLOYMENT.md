# 直播带货AI助手 - 生产环境部署文档

## 📋 目录

1. [架构概览](#架构概览)
2. [环境要求](#环境要求)
3. [快速开始](#快速开始)
4. [详细配置](#详细配置)
5. [部署方案](#部署方案)
6. [监控告警](#监控告警)
7. [运维指南](#运维指南)
8. [故障排查](#故障排查)

---

## 🏗️ 架构概览

### 系统架构

```
┌─────────────────┐
│   直播平台API   │
│ (抖音/快手/淘宝) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  WebSocket服务  │
│  (实时弹幕接收) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│          AI Agent 核心引擎          │
│  ┌──────────┐  ┌──────────┐        │
│  │ 多模态   │  │ 知识库   │        │
│  │ 视觉识别 │  │ RAG      │        │
│  └──────────┘  └──────────┘        │
│  ┌──────────┐  ┌──────────┐        │
│  │ 人机协作 │  │ TTS语音  │        │
│  │          │  │          │        │
│  └──────────┘  └──────────┘        │
└────────┬────────────────────────────┘
         │
         ├─► Redis (缓存/会话)
         ├─► PostgreSQL + pgvector (向量数据库)
         ├─► 对象存储 (图片/音频)
         └─► 监控告警系统
```

### 技术栈

- **核心框架**: LangChain 1.0.3 + LangGraph 1.0.2
- **大模型**: 豆包 doubao-seed-1-8-251228
- **数据库**: 
  - PostgreSQL (Supabase) - 向量存储
  - Redis 5.0.1 - 缓存和会话管理
- **实时通信**: WebSocket (websockets 15.0.1)
- **监控**: Prometheus + Grafana
- **告警**: 飞书机器人 + 企业微信机器人

---

## 💻 环境要求

### 最低配置

| 组件 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 存储 | 20GB | 50GB+ |
| 网络 | 5Mbps | 20Mbps+ |

### 软件要求

- Python 3.12+
- Redis 5.0+
- PostgreSQL 14+ (with pgvector extension)
- Docker 20.10+ (可选)
- Docker Compose 2.0+ (可选)

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd live-streaming-ai-assistant
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置
vim .env
```

**必须配置的环境变量**:

```env
# 大模型配置
COZE_WORKLOAD_IDENTITY_API_KEY=your_api_key_here
COZE_INTEGRATION_MODEL_BASE_URL=https://ark.cn-beijing.volces.com/api/v3

# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password

# PostgreSQL配置 (Supabase)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=your_supabase_key
DATABASE_URL=postgresql://user:pass@host:5432/db

# 对象存储配置 (火山引擎TOS)
TOS_ACCESS_KEY=your_access_key
TOS_SECRET_KEY=your_secret_key
TOS_ENDPOINT=https://tos-cn-beijing.volces.com
TOS_BUCKET=your-bucket-name

# 直播平台API配置
DOUYIN_APP_ID=your_douyin_app_id
DOUYIN_APP_SECRET=your_douyin_app_secret

# 告警配置
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# 监控配置
ENABLE_MONITORING=true
MONITORING_PORT=9090
```

### 4. 初始化数据库

```bash
# 运行数据库迁移
python scripts/init_database.py

# 导入示例知识库
python -m src.utils.knowledge_importer import_sample
```

### 5. 启动服务

```bash
# 开发环境
python scripts/run_dev.py

# 生产环境
python scripts/run_prod.py
```

---

## ⚙️ 详细配置

### 1. Redis配置

```python
# config/production_config.py
REDIS_CONFIG = {
    "url": "redis://localhost:6379/0",
    "max_connections": 50,
    "socket_timeout": 5,
    "socket_connect_timeout": 5,
    "retry_on_timeout": True,
    "health_check_interval": 30
}
```

**Redis连接池管理**:

系统使用 `src/storage/redis_pool.py` 管理Redis连接，自动重连和健康检查。

### 2. 向量数据库配置

Supabase配置步骤:

1. **创建Supabase项目**
   - 访问 https://supabase.com
   - 创建新项目
   - 记录 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`

2. **启用pgvector扩展**
   ```sql
   -- 在Supabase SQL编辑器执行
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **创建数据表**
   ```sql
   -- 文档表
   CREATE TABLE IF NOT EXISTS knowledge_documents (
       id SERIAL PRIMARY KEY,
       doc_id VARCHAR(255) UNIQUE NOT NULL,
       product_id VARCHAR(255),
       product_name VARCHAR(500),
       content TEXT NOT NULL,
       chunk_type VARCHAR(50),
       chunk_index INTEGER,
       metadata JSONB,
       created_at TIMESTAMP DEFAULT NOW(),
       updated_at TIMESTAMP DEFAULT NOW()
   );
   
   -- 向量表
   CREATE TABLE IF NOT EXISTS knowledge_embeddings (
       id SERIAL PRIMARY KEY,
       doc_id VARCHAR(255) REFERENCES knowledge_documents(doc_id) ON DELETE CASCADE,
       embedding VECTOR(1024),
       created_at TIMESTAMP DEFAULT NOW()
   );
   
   -- 创建向量索引
   CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
   ON knowledge_embeddings 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

4. **创建搜索函数**
   ```sql
   CREATE OR REPLACE FUNCTION search_similar_documents(
       query_vector VECTOR,
       match_threshold FLOAT,
       match_count INT,
       filter_product_id VARCHAR DEFAULT NULL
   )
   RETURNS TABLE (
       doc_id VARCHAR,
       content TEXT,
       metadata JSONB,
       similarity FLOAT
   )
   AS $$
   BEGIN
       RETURN QUERY
       SELECT 
           d.doc_id,
           d.content,
           d.metadata,
           1 - (e.embedding <=> query_vector) as similarity
       FROM knowledge_documents d
       JOIN knowledge_embeddings e ON d.doc_id = e.doc_id
       WHERE 
           (filter_product_id IS NULL OR d.product_id = filter_product_id)
           AND 1 - (e.embedding <=> query_vector) > match_threshold
       ORDER BY e.embedding <=> query_vector
       LIMIT match_count;
   END;
   $$ LANGUAGE plpgsql;
   ```

### 3. 直播平台API配置

#### 抖音直播

1. **申请开发者账号**
   - 访问 https://developer.open-douyin.com
   - 创建应用并申请直播权限
   - 获取 `APP_ID` 和 `APP_SECRET`

2. **配置权限**
   - `live.room.info` - 获取直播间信息
   - `live.room.danmaku` - 获取弹幕
   - `live.room.screenshot` - 获取截图

#### 快手直播

1. **申请开发者账号**
   - 访问 https://open.kuaishou.com
   - 创建应用并申请直播权限
   - 获取 `APP_ID` 和 `APP_SECRET`

### 4. 告警系统配置

#### 飞书机器人

1. **创建机器人**
   - 在飞书群组中添加自定义机器人
   - 获取Webhook URL
   - 配置安全设置（IP白名单）

2. **配置环境变量**
   ```env
   FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
   ```

#### 企业微信机器人

1. **创建机器人**
   - 在企业微信群中添加机器人
   - 获取Webhook Key

2. **配置环境变量**
   ```env
   WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
   ```

---

## 🐳 部署方案

### 方案1: Docker部署 (推荐)

#### 1. 构建镜像

```bash
docker build -t live-assistant:latest .
```

#### 2. 使用Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    image: live-assistant:latest
    container_name: live-assistant
    restart: always
    ports:
      - "8000:8000"
      - "9090:9090"
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/live_assistant
    env_file:
      - .env
    depends_on:
      - redis
      - postgres
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - live-assistant-network
  
  redis:
    image: redis:5.0-alpine
    container_name: live-assistant-redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    networks:
      - live-assistant-network
  
  postgres:
    image: pgvector/pgvector:pg14
    container_name: live-assistant-postgres
    restart: always
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: live_assistant
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - live-assistant-network

volumes:
  redis-data:
  postgres-data:

networks:
  live-assistant-network:
    driver: bridge
```

#### 3. 启动服务

```bash
docker-compose up -d
```

### 方案2: Kubernetes部署

#### 1. 创建ConfigMap

```yaml
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: live-assistant-config
data:
  REDIS_URL: "redis://redis-service:6379/0"
  ENABLE_MONITORING: "true"
  MONITORING_PORT: "9090"
```

#### 2. 创建Secret

```yaml
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: live-assistant-secrets
type: Opaque
stringData:
  COZE_WORKLOAD_IDENTITY_API_KEY: "your_api_key"
  SUPABASE_URL: "https://xxx.supabase.co"
  SUPABASE_ANON_KEY: "your_key"
```

#### 3. 创建Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: live-assistant
spec:
  replicas: 3
  selector:
    matchLabels:
      app: live-assistant
  template:
    metadata:
      labels:
        app: live-assistant
    spec:
      containers:
      - name: app
        image: live-assistant:latest
        ports:
        - containerPort: 8000
        - containerPort: 9090
        envFrom:
        - configMapRef:
            name: live-assistant-config
        - secretRef:
            name: live-assistant-secrets
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

#### 4. 创建Service

```yaml
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: live-assistant-service
spec:
  selector:
    app: live-assistant
  ports:
  - name: http
    port: 80
    targetPort: 8000
  - name: metrics
    port: 9090
    targetPort: 9090
  type: LoadBalancer
```

#### 5. 部署

```bash
kubectl apply -f k8s/
```

---

## 📊 监控告警

### 1. Prometheus监控

#### 配置指标收集

```python
# 系统已集成以下指标:
- live_assistant_requests_total (请求总数)
- live_assistant_response_time (响应时间)
- live_assistant_errors_total (错误数)
- live_assistant_active_websockets (活跃WebSocket连接)
- live_assistant_danmaku_processed (处理的弹幕数)
- live_assistant_human_takeovers (人工接管数)
```

#### Prometheus配置

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'live-assistant'
    static_configs:
      - targets: ['live-assistant-service:9090']
```

### 2. Grafana仪表板

#### 导入仪表板

系统已预置监控面板，访问 `http://localhost:8000/monitoring` 即可查看：

- **实时统计**: 请求QPS、响应时间、错误率
- **WebSocket连接**: 活跃连接数、消息吞吐量
- **AI性能**: 模型调用次数、平均延迟、Token消耗
- **人机协作**: 人工接管次数、待处理队列长度
- **知识库**: 查询次数、命中率、Top查询

### 3. 告警规则

#### 告警触发条件

| 告警类型 | 触发条件 | 级别 | 通知渠道 |
|---------|---------|------|---------|
| 人工接管 | 触发人工接管 | CRITICAL | 飞书+企微 |
| 系统异常 | 错误率 > 5% | ERROR | 飞书+企微 |
| 置信度低 | 置信度 < 0.6 | WARNING | 飞书 |
| API限流 | QPS超限 | WARNING | 飞书 |
| 服务宕机 | 健康检查失败 | CRITICAL | 飞书+企微 |

---

## 🔧 运维指南

### 日常运维

#### 1. 查看日志

```bash
# 实时日志
tail -f /app/work/logs/bypass/app.log

# 错误日志
grep "ERROR" /app/work/logs/bypass/app.log | tail -n 50
```

#### 2. 查看监控

访问监控面板: `http://localhost:8000/monitoring`

#### 3. 知识库管理

```bash
# 导入知识库
python -m src.utils.knowledge_importer import_json /path/to/data.json

# 查看知识库统计
curl http://localhost:8000/api/knowledge/stats
```

#### 4. A/B测试管理

```bash
# 查看实验列表
curl http://localhost:8000/api/ab/experiments

# 查看实验结果
curl http://localhost:8000/api/ab/experiments/{experiment_id}/results

# 暂停实验
curl -X POST http://localhost:8000/api/ab/experiments/{experiment_id}/pause

# 结束实验
curl -X POST http://localhost:8000/api/ab/experiments/{experiment_id}/complete
```

### 扩容指南

#### 水平扩展

1. **增加应用实例**
   ```bash
   # Kubernetes
   kubectl scale deployment live-assistant --replicas=5
   
   # Docker Compose
   docker-compose up -d --scale app=5
   ```

2. **配置负载均衡**
   - 使用Nginx或云负载均衡器
   - 配置WebSocket sticky session

#### 垂直扩展

1. **升级服务器配置**
   - CPU: 4核 → 8核
   - 内存: 8GB → 16GB

2. **调整应用参数**
   ```env
   WORKERS=8
   MAX_CONNECTIONS=1000
   ```

---

## 🐛 故障排查

### 常见问题

#### 1. WebSocket连接失败

**症状**: 无法建立WebSocket连接

**排查步骤**:
```bash
# 1. 检查服务是否启动
curl http://localhost:8000/health

# 2. 检查端口是否监听
netstat -tlnp | grep 8000

# 3. 检查防火墙
sudo ufw status

# 4. 查看日志
tail -f /app/work/logs/bypass/app.log | grep WebSocket
```

**解决方案**:
- 确保服务正常运行
- 检查防火墙规则
- 确认WebSocket路径正确 (`ws://host:8000/ws`)

#### 2. 知识库查询无结果

**症状**: 用户提问无法匹配到知识库内容

**排查步骤**:
```bash
# 1. 检查向量数据库连接
curl http://localhost:8000/api/knowledge/stats

# 2. 检查数据是否导入
python -c "from storage.vector_db_persistent import get_vector_db; import asyncio; db = asyncio.run(get_vector_db()); print(asyncio.run(db.get_stats()))"

# 3. 检查相似度阈值
# 在配置中查看 VECTOR_SEARCH_THRESHOLD (默认0.7)
```

**解决方案**:
- 重新导入知识库数据
- 降低相似度阈值
- 优化embedding模型

#### 3. 人工接管频繁触发

**症状**: 大量请求触发人工接管

**排查步骤**:
```bash
# 1. 查看接管原因分布
curl http://localhost:8000/api/human-collab/stats

# 2. 查看日志中的接管记录
grep "人工接管" /app/work/logs/bypass/app.log | tail -n 20

# 3. 检查模型置信度
grep "confidence" /app/work/logs/bypass/app.log | tail -n 20
```

**解决方案**:
- 优化Prompt提高模型置信度
- 调整接管阈值
- 丰富知识库内容

#### 4. 内存泄漏

**症状**: 内存占用持续增长

**排查步骤**:
```bash
# 1. 监控内存使用
docker stats live-assistant

# 2. 检查对象计数
python -c "import gc; gc.collect(); print(len(gc.get_objects()))"

# 3. 查看内存泄漏
# 使用memory_profiler
```

**解决方案**:
- 检查是否有未释放的连接
- 定期清理缓存
- 重启服务

#### 5. Redis连接超时

**症状**: Redis操作超时

**排查步骤**:
```bash
# 1. 检查Redis状态
redis-cli ping

# 2. 检查连接数
redis-cli info clients

# 3. 检查内存使用
redis-cli info memory
```

**解决方案**:
- 增加Redis最大连接数
- 优化Redis配置
- 升级Redis内存

---

## 📚 附录

### API文档

访问: `http://localhost:8000/docs`

### 性能基准

| 指标 | 值 |
|-----|---|
| 单实例QPS | 100-200 |
| 平均响应时间 | 1-2秒 |
| WebSocket并发 | 1000+ |
| 知识库查询延迟 | <100ms |

### 成本估算

**月度成本** (按1000并发计算):

| 项目 | 规格 | 费用(元/月) |
|-----|------|-----------|
| 云服务器 | 4核8GB × 3 | 1500 |
| Redis | 8GB | 300 |
| PostgreSQL | Supabase Pro | 600 |
| 对象存储 | 500GB | 100 |
| 大模型API | 100万Token | 500 |
| **总计** | - | **3000** |

### 安全建议

1. **API密钥管理**
   - 使用环境变量存储密钥
   - 定期轮换密钥
   - 限制密钥权限

2. **网络安全**
   - 启用HTTPS
   - 配置防火墙规则
   - 使用VPC隔离

3. **数据安全**
   - 数据库加密
   - 日志脱敏
   - 定期备份

---

## 📞 技术支持

- **文档**: `docs/` 目录
- **问题反馈**: GitHub Issues
- **监控面板**: http://localhost:8000/monitoring
- **API文档**: http://localhost:8000/docs

---

**最后更新**: 2025-01-21
