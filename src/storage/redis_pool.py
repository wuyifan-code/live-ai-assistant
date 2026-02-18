"""
Redis连接池管理器
生产环境优化的Redis连接管理
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json
import os

logger = logging.getLogger(__name__)


class RedisConnectionPool:
    """
    Redis连接池管理器
    
    特点：
    - 自动连接池管理
    - 健康检查
    - 自动重连
    - 连接复用
    - 性能监控
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        参数:
            config: Redis配置字典
        """
        self.config = config or {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", 6379)),
            "password": os.getenv("REDIS_PASSWORD"),
            "db": int(os.getenv("REDIS_DB", 0)),
            "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", 100)),
            "socket_timeout": 5,
            "socket_connect_timeout": 5,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
        self.pool = None
        self.redis_client = None
        self.is_connected = False
        self.last_health_check = None
        self.connection_errors = 0
        
        # 性能统计
        self.stats = {
            "total_commands": 0,
            "total_errors": 0,
            "avg_latency": 0.0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    async def connect(self) -> bool:
        """
        建立Redis连接
        
        返回:
            是否成功
        """
        try:
            import redis.asyncio as aioredis
            
            # 创建连接池
            self.pool = aioredis.ConnectionPool(
                host=self.config["host"],
                port=self.config["port"],
                password=self.config["password"],
                db=self.config["db"],
                max_connections=self.config["max_connections"],
                socket_timeout=self.config["socket_timeout"],
                socket_connect_timeout=self.config["socket_connect_timeout"],
                retry_on_timeout=self.config["retry_on_timeout"],
                decode_responses=True
            )
            
            # 创建客户端
            self.redis_client = aioredis.Redis(connection_pool=self.pool)
            
            # 测试连接
            await self.redis_client.ping()
            
            self.is_connected = True
            self.last_health_check = datetime.now()
            
            logger.info(
                f"✅ Redis连接成功: "
                f"{self.config['host']}:{self.config['port']}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {str(e)}")
            self.is_connected = False
            self.connection_errors += 1
            return False
    
    async def disconnect(self):
        """断开Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
        
        if self.pool:
            await self.pool.disconnect()
        
        self.is_connected = False
        logger.info("🔌 Redis连接已断开")
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        返回:
            是否健康
        """
        if not self.redis_client:
            return False
        
        try:
            start_time = time.time()
            await self.redis_client.ping()
            latency = (time.time() - start_time) * 1000
            
            self.last_health_check = datetime.now()
            self.stats["avg_latency"] = (
                self.stats["avg_latency"] * 0.9 + latency * 0.1
            )
            
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Redis健康检查失败: {str(e)}")
            self.is_connected = False
            return False
    
    async def reconnect(self) -> bool:
        """重新连接"""
        logger.info("🔄 尝试重新连接Redis...")
        
        await self.disconnect()
        await asyncio.sleep(1)
        
        return await self.connect()
    
    async def execute_command(self, command: str, *args, **kwargs) -> Any:
        """
        执行Redis命令
        
        参数:
            command: 命令名称
            *args: 命令参数
            **kwargs: 额外参数
        
        返回:
            命令结果
        """
        if not self.is_connected:
            if not await self.reconnect():
                raise Exception("Redis连接不可用")
        
        try:
            start_time = time.time()
            
            result = await getattr(self.redis_client, command)(*args, **kwargs)
            
            latency = (time.time() - start_time) * 1000
            self.stats["total_commands"] += 1
            self.stats["avg_latency"] = (
                self.stats["avg_latency"] * 0.95 + latency * 0.05
            )
            
            return result
            
        except Exception as e:
            self.stats["total_errors"] += 1
            logger.error(f"❌ Redis命令执行失败: {command} - {str(e)}")
            
            # 尝试重连
            if "ConnectionError" in str(type(e).__name__):
                await self.reconnect()
            
            raise
    
    # ============ 缓存操作 ============
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        result = await self.execute_command("get", key)
        
        if result is not None:
            self.stats["cache_hits"] += 1
            try:
                return json.loads(result)
            except:
                return result
        else:
            self.stats["cache_misses"] += 1
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = None
    ) -> bool:
        """设置缓存"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        if ttl:
            return await self.execute_command("setex", key, ttl, value)
        else:
            return await self.execute_command("set", key, value)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        result = await self.execute_command("delete", key)
        return result > 0
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        result = await self.execute_command("exists", key)
        return result > 0
    
    async def expire(self, key: str, seconds: int) -> bool:
        """设置过期时间"""
        return await self.execute_command("expire", key, seconds)
    
    async def ttl(self, key: str) -> int:
        """获取剩余过期时间"""
        return await self.execute_command("ttl", key)
    
    # ============ 哈希操作 ============
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段"""
        result = await self.execute_command("hget", name, key)
        
        if result:
            try:
                return json.loads(result)
            except:
                return result
        return None
    
    async def hset(
        self,
        name: str,
        key: str,
        value: Any
    ) -> bool:
        """设置哈希字段"""
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        
        return await self.execute_command("hset", name, key, value)
    
    async def hgetall(self, name: str) -> Dict[str, Any]:
        """获取所有哈希字段"""
        result = await self.execute_command("hgetall", name)
        
        if result:
            return {
                k: json.loads(v) if v else v
                for k, v in result.items()
            }
        return {}
    
    # ============ 列表操作 ============
    
    async def lpush(self, key: str, *values) -> int:
        """从左侧插入列表"""
        return await self.execute_command("lpush", key, *values)
    
    async def rpush(self, key: str, *values) -> int:
        """从右侧插入列表"""
        return await self.execute_command("rpush", key, *values)
    
    async def lpop(self, key: str) -> Optional[Any]:
        """从左侧弹出"""
        result = await self.execute_command("lpop", key)
        
        if result:
            try:
                return json.loads(result)
            except:
                return result
        return None
    
    async def lrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1
    ) -> List[Any]:
        """获取列表范围"""
        result = await self.execute_command("lrange", key, start, end)
        
        if result:
            return [
                json.loads(item) if item else item
                for item in result
            ]
        return []
    
    # ============ 有序集合操作 ============
    
    async def zadd(
        self,
        key: str,
        mapping: Dict[str, float]
    ) -> int:
        """添加有序集合成员"""
        return await self.execute_command("zadd", key, mapping)
    
    async def zrange(
        self,
        key: str,
        start: int = 0,
        end: int = -1,
        withscores: bool = False
    ) -> List[Any]:
        """获取有序集合范围"""
        return await self.execute_command(
            "zrange", key, start, end, withscores=withscores
        )
    
    # ============ 统计信息 ============
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "is_connected": self.is_connected,
            "connection_errors": self.connection_errors,
            "last_health_check": (
                self.last_health_check.isoformat()
                if self.last_health_check else None
            ),
            "cache_hit_rate": (
                self.stats["cache_hits"] /
                (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0
                else 0
            )
        }


# 全局Redis连接池实例
redis_pool = RedisConnectionPool()


async def get_redis() -> RedisConnectionPool:
    """获取Redis连接池实例"""
    if not redis_pool.is_connected:
        await redis_pool.connect()
    return redis_pool


async def init_redis():
    """初始化Redis连接"""
    await redis_pool.connect()
    
    # 启动健康检查任务
    asyncio.create_task(_health_check_loop())


async def _health_check_loop():
    """健康检查循环"""
    while True:
        try:
            await asyncio.sleep(30)
            await redis_pool.health_check()
        except Exception as e:
            logger.error(f"❌ Redis健康检查异常: {str(e)}")
