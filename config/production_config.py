"""
生产环境配置
Redis、向量数据库、系统参数
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 100
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30


@dataclass
class VectorDBConfig:
    """向量数据库配置"""
    provider: str = "supabase"  # supabase / pinecone / weaviate
    embedding_dimensions: int = 1024
    index_name: str = "product_knowledge"
    namespace: str = "default"
    
    # Supabase配置
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    
    # Pinecone配置
    pinecone_api_key: Optional[str] = None
    pinecone_environment: Optional[str] = None
    
    # Weaviate配置
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None


@dataclass
class LiveStreamConfig:
    """直播平台配置"""
    platform: str = "douyin"  # douyin / kuaishou / taobao
    
    # 抖音配置
    douyin_app_id: Optional[str] = None
    douyin_app_secret: Optional[str] = None
    
    # 快手配置
    kuaishou_app_id: Optional[str] = None
    kuaishou_app_secret: Optional[str] = None
    
    # 淘宝配置
    taobao_app_key: Optional[str] = None
    taobao_app_secret: Optional[str] = None


@dataclass
class AlertConfig:
    """告警配置"""
    enable_feishu: bool = False
    feishu_webhook: Optional[str] = None
    
    enable_wechat: bool = False
    wechat_webhook: Optional[str] = None
    
    enable_email: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    alert_email: Optional[str] = None


@dataclass
class ProductionConfig:
    """生产环境完整配置"""
    redis: RedisConfig = None
    vector_db: VectorDBConfig = None
    live_stream: LiveStreamConfig = None
    alert: AlertConfig = None
    
    # 系统配置
    debug: bool = False
    log_level: str = "INFO"
    max_workers: int = 4
    request_timeout: int = 30
    
    def __post_init__(self):
        if self.redis is None:
            self.redis = RedisConfig()
        if self.vector_db is None:
            self.vector_db = VectorDBConfig()
        if self.live_stream is None:
            self.live_stream = LiveStreamConfig()
        if self.alert is None:
            self.alert = AlertConfig()


def load_config_from_env() -> ProductionConfig:
    """
    从环境变量加载配置
    
    环境变量格式：
    - REDIS_HOST
    - REDIS_PORT
    - SUPABASE_URL
    - DOUYIN_APP_ID
    - FEISHU_WEBHOOK
    """
    # Redis配置
    redis_config = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD"),
        db=int(os.getenv("REDIS_DB", "0")),
        max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "100")),
    )
    
    # 向量数据库配置
    vector_db_config = VectorDBConfig(
        provider=os.getenv("VECTOR_DB_PROVIDER", "supabase"),
        embedding_dimensions=int(os.getenv("EMBEDDING_DIMENSIONS", "1024")),
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_ANON_KEY"),
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
        pinecone_environment=os.getenv("PINECONE_ENVIRONMENT"),
    )
    
    # 直播平台配置
    live_stream_config = LiveStreamConfig(
        platform=os.getenv("LIVE_PLATFORM", "douyin"),
        douyin_app_id=os.getenv("DOUYIN_APP_ID"),
        douyin_app_secret=os.getenv("DOUYIN_APP_SECRET"),
        kuaishou_app_id=os.getenv("KUAISHOU_APP_ID"),
        kuaishou_app_secret=os.getenv("KUAISHOU_APP_SECRET"),
    )
    
    # 告警配置
    alert_config = AlertConfig(
        enable_feishu=os.getenv("ENABLE_FEISHU_ALERT", "false").lower() == "true",
        feishu_webhook=os.getenv("FEISHU_WEBHOOK"),
        enable_wechat=os.getenv("ENABLE_WECHAT_ALERT", "false").lower() == "true",
        wechat_webhook=os.getenv("WECHAT_WEBHOOK"),
    )
    
    return ProductionConfig(
        redis=redis_config,
        vector_db=vector_db_config,
        live_stream=live_stream_config,
        alert=alert_config,
        debug=os.getenv("DEBUG", "false").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        max_workers=int(os.getenv("MAX_WORKERS", "4")),
    )


# 全局配置实例
production_config = load_config_from_env()


def get_config() -> ProductionConfig:
    """获取全局配置"""
    return production_config


def validate_config(config: ProductionConfig) -> Dict[str, Any]:
    """
    验证配置
    
    返回:
        验证结果
    """
    issues = []
    warnings = []
    
    # 检查Redis配置
    if not config.redis.host:
        issues.append("Redis host 未配置")
    
    # 检查向量数据库配置
    if config.vector_db.provider == "supabase":
        if not config.vector_db.supabase_url:
            warnings.append("Supabase URL 未配置，将使用内存存储")
    
    # 检查直播平台配置
    if config.live_stream.platform == "douyin":
        if not config.live_stream.douyin_app_id:
            warnings.append("抖音 App ID 未配置，实时画面获取功能将不可用")
    
    # 检查告警配置
    if config.alert.enable_feishu and not config.alert.feishu_webhook:
        issues.append("飞书告警已启用但 Webhook 未配置")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings
    }


def print_config_summary():
    """打印配置摘要"""
    config = get_config()
    
    print("\n" + "="*60)
    print("📋 生产环境配置摘要")
    print("="*60)
    
    print(f"\n🔴 Redis配置:")
    print(f"  主机: {config.redis.host}:{config.redis.port}")
    print(f"  数据库: {config.redis.db}")
    print(f"  最大连接数: {config.redis.max_connections}")
    
    print(f"\n🔷 向量数据库配置:")
    print(f"  提供商: {config.vector_db.provider}")
    print(f"  向量维度: {config.vector_db.embedding_dimensions}")
    
    print(f"\n📺 直播平台配置:")
    print(f"  平台: {config.live_stream.platform}")
    
    print(f"\n🔔 告警配置:")
    print(f"  飞书告警: {'已启用' if config.alert.enable_feishu else '未启用'}")
    print(f"  企微告警: {'已启用' if config.alert.enable_wechat else '未启用'}")
    
    print(f"\n⚙️ 系统配置:")
    print(f"  Debug模式: {config.debug}")
    print(f"  日志级别: {config.log_level}")
    print(f"  最大工作进程: {config.max_workers}")
    
    # 验证配置
    validation = validate_config(config)
    
    if validation["issues"]:
        print(f"\n❌ 配置问题:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    if validation["warnings"]:
        print(f"\n⚠️ 配置警告:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    print_config_summary()
