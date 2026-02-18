"""
错误分级处理系统
自动分类错误、发送告警、尝试自动恢复
"""

import logging
import asyncio
import traceback
from enum import Enum
from typing import Optional, Callable, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, field
import os
import requests

logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    """错误级别"""
    FATAL = 1    # 致命错误：需要立即人工介入
    ERROR = 2    # 严重错误：影响核心功能，需要处理
    WARN = 3     # 警告：不影响核心功能，但需要关注
    INFO = 4     # 信息：正常运行日志


class ErrorCategory(Enum):
    """错误类别"""
    DATABASE = "database"           # 数据库相关
    CACHE = "cache"                # 缓存相关
    API = "api"                    # 外部API相关
    WEBSOCKET = "websocket"        # WebSocket相关
    ASR = "asr"                    # 语音识别相关
    LLM = "llm"                    # 大模型相关
    NETWORK = "network"            # 网络相关
    SYSTEM = "system"              # 系统相关


@dataclass
class ErrorRecord:
    """错误记录"""
    level: ErrorLevel
    category: ErrorCategory
    message: str
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    retry_count: int = 0


class ErrorClassifier:
    """错误分类器"""
    
    ERROR_PATTERNS = {
        ErrorCategory.DATABASE: [
            "database", "sql", "postgres", "supabase", "connection",
            "psycopg2", "deadlock", "timeout"
        ],
        ErrorCategory.CACHE: [
            "redis", "cache", "memcached", "expired"
        ],
        ErrorCategory.API: [
            "api", "http", "request", "rate limit", "429", "503"
        ],
        ErrorCategory.WEBSOCKET: [
            "websocket", "connection", "closed", "disconnected"
        ],
        ErrorCategory.ASR: [
            "asr", "speech", "audio", "recognition", "whisper"
        ],
        ErrorCategory.LLM: [
            "llm", "model", "openai", "token", "timeout"
        ],
        ErrorCategory.NETWORK: [
            "network", "dns", "socket", "connection refused"
        ],
        ErrorCategory.SYSTEM: [
            "memory", "disk", "cpu", "permission", "file not found"
        ]
    }
    
    @classmethod
    def classify_error(cls, error: Exception, message: str) -> ErrorCategory:
        """分类错误"""
        error_info = str(error).lower() + " " + message.lower()
        
        for category, patterns in cls.ERROR_PATTERNS.items():
            if any(pattern in error_info for pattern in patterns):
                return category
        
        return ErrorCategory.SYSTEM
    
    @classmethod
    def determine_level(cls, error: Exception, category: ErrorCategory) -> ErrorLevel:
        """确定错误级别"""
        # 根据异常类型和类别确定级别
        error_type = type(error).__name__
        
        # 致命错误
        if error_type in ["MemoryError", "OSError", "SystemExit"]:
            return ErrorLevel.FATAL
        
        if category == ErrorCategory.DATABASE and "connection" in str(error).lower():
            return ErrorLevel.FATAL
        
        # 严重错误
        if category in [ErrorCategory.DATABASE, ErrorCategory.CACHE]:
            return ErrorLevel.ERROR
        
        if category == ErrorCategory.WEBSOCKET and "disconnected" in str(error).lower():
            return ErrorLevel.ERROR
        
        # 警告
        if category in [ErrorCategory.API, ErrorCategory.ASR]:
            return ErrorLevel.WARN
        
        return ErrorLevel.INFO


class AlertChannel(Enum):
    """告警渠道"""
    WEBHOOK = "webhook"
    EMAIL = "email"
    SMS = "sms"
    LOG = "log"


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.webhook_url = os.getenv("MONITOR_WEBHOOK_URL", "")
        self.email = os.getenv("MONITOR_EMAIL", "")
        self.phone = os.getenv("MONITOR_PHONE", "")
    
    async def send_alert(
        self,
        error: ErrorRecord,
        channels: List[AlertChannel] = None
    ):
        """
        发送告警
        
        参数:
            error: 错误记录
            channels: 告警渠道列表
        """
        if channels is None:
            # 根据错误级别选择默认渠道
            if error.level == ErrorLevel.FATAL:
                channels = [AlertChannel.WEBHOOK, AlertChannel.EMAIL, AlertChannel.SMS]
            elif error.level == ErrorLevel.ERROR:
                channels = [AlertChannel.WEBHOOK, AlertChannel.EMAIL]
            else:
                channels = [AlertChannel.LOG]
        
        for channel in channels:
            try:
                if channel == AlertChannel.WEBHOOK:
                    await self._send_webhook_alert(error)
                elif channel == AlertChannel.EMAIL:
                    await self._send_email_alert(error)
                elif channel == AlertChannel.SMS:
                    await self._send_sms_alert(error)
                elif channel == AlertChannel.LOG:
                    self._send_log_alert(error)
            except Exception as e:
                logger.error(f"发送告警失败 [{channel}]: {str(e)}")
    
    async def _send_webhook_alert(self, error: ErrorRecord):
        """发送Webhook告警"""
        if not self.webhook_url:
            return
        
        payload = {
            "level": error.level.name,
            "category": error.category.value,
            "message": error.message,
            "timestamp": error.timestamp.isoformat(),
            "context": error.context
        }
        
        response = requests.post(self.webhook_url, json=payload, timeout=10)
        response.raise_for_status()
        
        logger.info(f"✅ Webhook告警已发送: {error.message[:50]}")
    
    async def _send_email_alert(self, error: ErrorRecord):
        """发送邮件告警"""
        # TODO: 实现邮件发送逻辑
        logger.info(f"📧 邮件告警: {error.message[:50]}")
    
    async def _send_sms_alert(self, error: ErrorRecord):
        """发送短信告警"""
        # TODO: 实现短信发送逻辑
        logger.info(f"📱 短信告警: {error.message[:50]}")
    
    def _send_log_alert(self, error: ErrorRecord):
        """记录日志告警"""
        log_method = {
            ErrorLevel.FATAL: logger.critical,
            ErrorLevel.ERROR: logger.error,
            ErrorLevel.WARN: logger.warning,
            ErrorLevel.INFO: logger.info
        }.get(error.level, logger.info)
        
        log_method(
            f"[{error.level.name}] {error.category.value}: {error.message}\n"
            f"Context: {error.context}"
        )


class AutoRecovery:
    """自动恢复机制"""
    
    RECOVERY_STRATEGIES = {
        ErrorCategory.DATABASE: "retry_with_backoff",
        ErrorCategory.CACHE: "clear_and_retry",
        ErrorCategory.WEBSOCKET: "reconnect",
        ErrorCategory.API: "retry_with_exponential_backoff",
        ErrorCategory.NETWORK: "retry_with_exponential_backoff",
    }
    
    def __init__(self):
        self.retry_handlers: Dict[ErrorCategory, Callable] = {}
    
    def register_handler(self, category: ErrorCategory, handler: Callable):
        """注册恢复处理器"""
        self.retry_handlers[category] = handler
    
    async def attempt_recovery(
        self,
        error: ErrorRecord,
        max_retries: int = 3
    ) -> bool:
        """
        尝试自动恢复
        
        参数:
            error: 错误记录
            max_retries: 最大重试次数
        
        返回:
            True if recovery succeeded, False otherwise
        """
        if error.retry_count >= max_retries:
            logger.warning(f"⚠️ 已达到最大重试次数: {max_retries}")
            return False
        
        strategy = self.RECOVERY_STRATEGIES.get(error.category)
        
        if not strategy:
            logger.info(f"❌ 无自动恢复策略: {error.category}")
            return False
        
        # 执行恢复策略
        try:
            if strategy == "retry_with_backoff":
                await self._retry_with_backoff(error)
            elif strategy == "clear_and_retry":
                await self._clear_and_retry(error)
            elif strategy == "reconnect":
                await self._reconnect(error)
            elif strategy == "retry_with_exponential_backoff":
                await self._retry_with_exponential_backoff(error)
            
            error.retry_count += 1
            logger.info(f"✅ 恢复成功: {error.message}")
            return True
        
        except Exception as e:
            logger.error(f"❌ 恢复失败: {str(e)}")
            return False
    
    async def _retry_with_backoff(self, error: ErrorRecord):
        """带退避的重试"""
        delay = min(2 ** error.retry_count, 30)  # 最大30秒
        logger.info(f"⏳ {delay}秒后重试...")
        await asyncio.sleep(delay)
    
    async def _clear_and_retry(self, error: ErrorRecord):
        """清除缓存并重试"""
        # TODO: 实现缓存清除逻辑
        await asyncio.sleep(1)
    
    async def _reconnect(self, error: ErrorRecord):
        """重新连接"""
        # TODO: 实现重连逻辑
        await asyncio.sleep(2)
    
    async def _retry_with_exponential_backoff(self, error: ErrorRecord):
        """指数退避重试"""
        delay = (2 ** error.retry_count) * 1.5
        delay = min(delay, 60)  # 最大60秒
        logger.info(f"⏳ {delay:.1f}秒后重试（指数退避）...")
        await asyncio.sleep(delay)


class ErrorHandler:
    """错误处理器 - 统一的错误处理入口"""
    
    def __init__(self):
        self.classifier = ErrorClassifier()
        self.alert_manager = AlertManager()
        self.auto_recovery = AutoRecovery()
        self.error_history: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
    
    async def handle_error(
        self,
        error: Exception,
        message: str,
        context: Dict[str, Any] = None,
        enable_recovery: bool = True,
        enable_alert: bool = True
    ) -> ErrorRecord:
        """
        处理错误
        
        参数:
            error: 异常对象
            message: 错误消息
            context: 上下文信息
            enable_recovery: 是否启用自动恢复
            enable_alert: 是否发送告警
        
        返回:
            错误记录
        """
        # 分类错误
        category = self.classifier.classify_error(error, message)
        level = self.classifier.determine_level(error, category)
        
        # 创建错误记录
        error_record = ErrorRecord(
            level=level,
            category=category,
            message=message,
            exception=error,
            stack_trace=traceback.format_exc(),
            context=context or {}
        )
        
        # 记录错误历史
        self.error_history.append(error_record)
        
        # 统计错误次数
        error_key = f"{category.value}:{level.name}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        
        # 发送告警
        if enable_alert:
            await self.alert_manager.send_alert(error_record)
        
        # 尝试自动恢复
        if enable_recovery:
            recovery_success = await self.auto_recovery.attempt_recovery(error_record)
            if recovery_success:
                error_record.resolved = True
        
        return error_record
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        recent_errors = [
            e for e in self.error_history
            if (datetime.now() - e.timestamp).total_seconds() < 3600  # 最近1小时
        ]
        
        return {
            "total_errors": len(self.error_history),
            "recent_errors": len(recent_errors),
            "error_counts": self.error_counts,
            "unresolved_errors": len([e for e in recent_errors if not e.resolved])
        }


# 全局错误处理器实例
error_handler = ErrorHandler()


async def handle_error_async(
    error: Exception,
    message: str,
    context: Dict[str, Any] = None
) -> ErrorRecord:
    """异步处理错误的便捷函数"""
    return await error_handler.handle_error(error, message, context)
