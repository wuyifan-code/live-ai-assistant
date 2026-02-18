# 直播带货AI助手 - 快速开始指南

## 🚀 快速启动（3步完成）

### 方式1: 使用快速启动脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/wuyifan-code/live-ai-assistant.git
cd live-ai-assistant

# 2. 运行快速启动脚本
./scripts/quick_start.sh
```

脚本会自动完成：
- ✅ 检查Python环境
- ✅ 创建.env配置文件
- ✅ 检查Redis和PostgreSQL服务
- ✅ 安装Python依赖
- ✅ 初始化数据库
- ✅ 导入示例知识库
- ✅ 启动服务

### 方式2: 手动配置

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
vim .env  # 填写必要配置

# 3. 初始化数据库
python scripts/init_database.py

# 4. 启动服务
python scripts/run_prod.py
```

---

## 📋 环境要求

### 必需服务

| 服务 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 运行环境 |
| Redis | 5.0+ | 缓存和会话管理 |
| PostgreSQL | 14+ | 数据存储（或使用Supabase） |

### 必需配置

在 `.env` 文件中必须配置以下项：

```env
# 数据库
DATABASE_URL=postgresql://user:pass@localhost:5432/live_ai_db

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# 直播平台API
DOUYIN_APP_ID=your-app-id
DOUYIN_APP_SECRET=your-app-secret
```

---

## 🔧 配置指南

### 1. Redis安装

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
```

#### macOS
```bash
brew install redis
brew services start redis
```

#### Docker
```bash
docker run -d --name redis -p 6379:6379 redis:5.0-alpine
```

### 2. PostgreSQL安装

#### Ubuntu/Debian
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# 创建数据库
sudo -u postgres psql
CREATE DATABASE live_ai_db;
\q
```

#### 或使用Supabase（推荐）
1. 访问 https://supabase.com
2. 创建项目
3. 获取 `SUPABASE_URL` 和 `SUPABASE_ANON_KEY`

### 3. 直播平台配置

#### 抖音开放平台
1. 访问 https://developer.open-douyin.com
2. 创建应用并申请直播权限
3. 获取 `APP_ID` 和 `APP_SECRET`

---

## 🧪 验证配置

运行配置验证脚本：

```bash
python scripts/validate_config.py
```

输出示例：
```
✅ .env 文件存在
✅ 所有必需配置项已正确设置
✅ Redis连接正常，读写测试成功
✅ 数据库连接正常，商品表记录数: 8
✅ 大模型连接正常

✅ 环境配置验证通过，可以启动服务！
```

---

## 🌐 访问服务

启动成功后，访问以下地址：

| 服务 | 地址 | 说明 |
|------|------|------|
| 主服务 | http://localhost:8000 | WebSocket和HTTP接口 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| 监控面板 | http://localhost:8000/monitoring | 实时统计图表 |
| Prometheus | http://localhost:9090 | 指标监控 |

---

## 📚 详细文档

- **环境配置**: [docs/INFRASTRUCTURE_SETUP.md](docs/INFRASTRUCTURE_SETUP.md)
- **部署指南**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **功能说明**: [docs/FEATURES.md](docs/FEATURES.md)

---

## 🐛 常见问题

### Q: Redis连接失败
```bash
# 检查Redis状态
redis-cli ping

# 启动Redis
sudo systemctl start redis-server
```

### Q: 数据库初始化失败
```bash
# 检查数据库连接
psql -U postgres -d live_ai_db

# 确认环境变量
echo $DATABASE_URL
```

### Q: 大模型调用失败
- 检查 `COZE_WORKLOAD_IDENTITY_API_KEY` 环境变量
- 生产环境会自动注入，无需手动配置

---

## 💡 快速测试

启动服务后，运行测试：

```bash
# 测试核心功能
python scripts/test_production_integration.py
```

---

## 🎯 下一步

- [ ] 添加商品知识库数据
- [ ] 配置告警通知渠道
- [ ] 启用A/B测试
- [ ] 部署到生产环境

有问题？查看 [故障排查指南](docs/DEPLOYMENT.md#故障排查)
