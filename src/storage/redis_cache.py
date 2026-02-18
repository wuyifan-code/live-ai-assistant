"""
Redis缓存管理
用于缓存商品信息，减少数据库查询压力
"""

import os
import json
import logging
from typing import Optional, Any
from datetime import timedelta

logger = logging.getLogger(__name__)


class RedisCache:
    """Redis缓存管理器"""
    
    def __init__(self):
        self.redis_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化Redis客户端"""
        try:
            import redis
            
            # 从环境变量获取Redis配置
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            redis_db = int(os.getenv("REDIS_DB", 0))
            
            # 创建Redis连接
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                password=redis_password,
                db=redis_db,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # 测试连接
            self.redis_client.ping()
            logger.info("✅ Redis连接成功")
            
        except ImportError:
            logger.warning("⚠️ Redis客户端未安装，缓存功能将不可用")
            self.redis_client = None
        except Exception as e:
            logger.warning(f"⚠️ Redis连接失败: {str(e)}，缓存功能将不可用")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """检查Redis是否可用"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value is not None:
                # 尝试解析JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"获取缓存失败 [{key}]: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        设置缓存值
        
        参数:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认5分钟
        """
        if not self.is_available():
            return False
        
        try:
            # 如果是字典或列表，转换为JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"设置缓存失败 [{key}]: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除缓存失败 [{key}]: {str(e)}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """删除匹配模式的缓存"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"批量删除缓存失败 [{pattern}]: {str(e)}")
            return 0
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"检查缓存存在失败 [{key}]: {str(e)}")
            return False
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        if not self.is_available():
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("✅ 所有缓存已清空")
            return True
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False


# 商品缓存键前缀
PRODUCT_CACHE_PREFIX = "product:"
PRODUCT_PRICE_CACHE_PREFIX = "product_price:"
PRODUCT_STOCK_CACHE_PREFIX = "product_stock:"


# 全局缓存实例
_cache_instance: Optional[RedisCache] = None


def get_cache() -> RedisCache:
    """获取缓存实例（单例模式）"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


def cache_product(product_id: int, product_data: dict, ttl: int = 600):
    """
    缓存商品完整信息
    
    参数:
        product_id: 商品ID
        product_data: 商品数据
        ttl: 过期时间（秒），默认10分钟
    """
    cache = get_cache()
    key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
    cache.set(key, product_data, ttl)


def get_cached_product(product_id: int) -> Optional[dict]:
    """获取缓存的商品信息"""
    cache = get_cache()
    key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
    return cache.get(key)


def cache_product_price(product_id: int, price: float, ttl: int = 300):
    """
    缓存商品价格
    
    参数:
        product_id: 商品ID
        price: 价格
        ttl: 过期时间（秒），默认5分钟
    """
    cache = get_cache()
    key = f"{PRODUCT_PRICE_CACHE_PREFIX}{product_id}"
    cache.set(key, price, ttl)


def get_cached_product_price(product_id: int) -> Optional[float]:
    """获取缓存的商品价格"""
    cache = get_cache()
    key = f"{PRODUCT_PRICE_CACHE_PREFIX}{product_id}"
    return cache.get(key)


def cache_product_stock(product_id: int, stock: int, ttl: int = 120):
    """
    缓存商品库存
    
    参数:
        product_id: 商品ID
        stock: 库存数量
        ttl: 过期时间（秒），默认2分钟（库存变化较频繁）
    """
    cache = get_cache()
    key = f"{PRODUCT_STOCK_CACHE_PREFIX}{product_id}"
    cache.set(key, stock, ttl)


def get_cached_product_stock(product_id: int) -> Optional[int]:
    """获取缓存的商品库存"""
    cache = get_cache()
    key = f"{PRODUCT_STOCK_CACHE_PREFIX}{product_id}"
    return cache.get(key)


def invalidate_product_cache(product_id: int):
    """使商品缓存失效"""
    cache = get_cache()
    cache.delete(f"{PRODUCT_CACHE_PREFIX}{product_id}")
    cache.delete(f"{PRODUCT_PRICE_CACHE_PREFIX}{product_id}")
    cache.delete(f"{PRODUCT_STOCK_CACHE_PREFIX}{product_id}")


def invalidate_all_product_cache():
    """使所有商品缓存失效"""
    cache = get_cache()
    cache.delete_pattern(f"{PRODUCT_CACHE_PREFIX}*")
    cache.delete_pattern(f"{PRODUCT_PRICE_CACHE_PREFIX}*")
    cache.delete_pattern(f"{PRODUCT_STOCK_CACHE_PREFIX}*")
