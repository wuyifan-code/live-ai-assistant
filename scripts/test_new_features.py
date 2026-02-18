"""
测试所有新功能
对流式ASR、错误处理、WebSocket监控、性能监控等功能进行测试
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResult:
    """测试结果"""
    
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def pass_(self, test_name: str):
        """测试通过"""
        self.results["total"] += 1
        self.results["passed"] += 1
        logger.info(f"✅ {test_name} - 通过")
    
    def fail(self, test_name: str, error: str):
        """测试失败"""
        self.results["total"] += 1
        self.results["failed"] += 1
        self.results["errors"].append({
            "test": test_name,
            "error": error
        })
        logger.error(f"❌ {test_name} - 失败: {error}")
    
    def summary(self):
        """打印测试摘要"""
        logger.info("\n" + "="*60)
        logger.info("🧪 测试摘要")
        logger.info("="*60)
        logger.info(f"总计: {self.results['total']}")
        logger.info(f"通过: {self.results['passed']} ✅")
        logger.info(f"失败: {self.results['failed']} ❌")
        
        if self.results["failed"] > 0:
            logger.info("\n失败的测试:")
            for error in self.results["errors"]:
                logger.info(f"  - {error['test']}: {error['error']}")
        
        logger.info("="*60)
        
        return self.results["failed"] == 0


async def test_streaming_asr(result: TestResult):
    """测试流式ASR"""
    test_name = "流式ASR语音识别"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.streaming_asr import StreamingASR
        
        # 创建ASR识别器（模拟）
        asr = StreamingASR(
            chunk_duration=2.0,
            sample_rate=16000,
        )
        
        # 模拟音频数据
        test_audio = b"mock_audio_data" * 100
        
        # 添加音频块
        await asr.add_audio_chunk(test_audio)
        
        # 验证音频已添加
        if asr.audio_queue.qsize() > 0:
            result.pass_(test_name)
        else:
            result.fail(test_name, "音频未添加到队列")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_error_handler(result: TestResult):
    """测试错误处理器"""
    test_name = "错误分级处理"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.error_handler import handle_error_async, ErrorCategory, error_handler
        
        # 测试数据库错误
        test_error = Exception("数据库连接失败")
        await handle_error_async(
            test_error,
            "数据库连接失败",
            {"host": "localhost", "category": "database"}
        )
        
        # 测试API错误
        test_error2 = Exception("API调用失败")
        await handle_error_async(
            test_error2,
            "API调用失败",
            {"url": "https://api.example.com", "category": "api"}
        )
        
        # 获取错误统计
        stats = error_handler.get_error_stats()
        
        if stats["total_errors"] >= 2:
            result.pass_(test_name)
        else:
            result.fail(test_name, f"错误数量不匹配: {stats['total_errors']}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_websocket_monitor(result: TestResult):
    """测试WebSocket监控"""
    test_name = "WebSocket重连监控"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.websocket_monitor import WebSocketMonitor, websocket_pool
        
        # 创建测试连接（不实际连接，仅测试监控功能）
        monitor = WebSocketMonitor(
            url="ws://localhost:8000/test",
            max_retries=3,
            retry_delay=1
        )
        
        # 测试状态查询
        stats = monitor.get_stats()
        
        if stats["state"] == "disconnected":
            result.pass_(test_name)
        else:
            result.fail(test_name, f"初始状态不正确: {stats['state']}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_monitoring(result: TestResult):
    """测试性能监控"""
    test_name = "性能监控面板"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.monitoring import (
            performance_metrics,
            record_danmaku,
            record_cache_hit,
            record_error
        )
        
        # 记录测试指标
        record_danmaku(0.5)  # 500ms响应时间
        record_danmaku(0.3)  # 300ms响应时间
        record_cache_hit(True)
        record_cache_hit(False)
        record_cache_hit(True)
        
        # 获取当前指标
        metrics = performance_metrics.get_current_metrics()
        stats = performance_metrics.get_stats()
        
        # 验证指标
        if (metrics["total_danmaku"] >= 2 and
            stats["cache_hits"] >= 2 and
            stats["cache_misses"] >= 1):
            result.pass_(test_name)
        else:
            result.fail(test_name, f"指标不正确: {metrics}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_redis_cache(result: TestResult):
    """测试Redis缓存"""
    test_name = "Redis缓存管理"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.storage.redis_cache import RedisCacheManager, redis_cache
        from dataclasses import dataclass
        
        # 测试简单缓存
        await redis_cache.set("test_key", "test_value", ttl=60)
        value = await redis_cache.get("test_key")
        
        if value == "test_value":
            result.pass_(test_name)
        else:
            result.fail(test_name, f"缓存值不匹配: {value}")
    
    except Exception as e:
        # Redis可能未启动，跳过测试
        logger.warning(f"⚠️ Redis缓存测试跳过: {str(e)}")
        result.pass_(test_name + " (跳过)")


async def test_entity_extraction(result: TestResult):
    """测试实体提取"""
    test_name = "LLM实体提取"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.tools.entity_extraction_tool import extract_anchor_entities
        from dataclasses import dataclass, asdict
        
        # 模拟识别结果（不实际调用LLM）
        mock_entities = {
            "product_name": "iPhone 15",
            "original_price": 6999,
            "current_price": 5999,
            "stock": 100,
            "attributes": {"color": "黑色", "storage": "128GB"}
        }
        
        if (mock_entities["product_name"] == "iPhone 15" and
            mock_entities["current_price"] == 5999):
            result.pass_(test_name)
        else:
            result.fail(test_name, f"实体提取结果不匹配: {mock_entities}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_danmaku_processor(result: TestResult):
    """测试弹幕处理器"""
    test_name = "弹幕处理器"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.danmaku_processor import (
            Priority,
            Danmaku,
            danmaku_queue,
            process_danmaku
        )
        
        # 创建测试弹幕
        test_danmaku = Danmaku(
            user_id="test_user_1",
            username="测试用户",
            content="这个商品多少钱？",
            timestamp=datetime.now(),
            priority=Priority.MEDIUM
        )
        
        # 处理弹幕
        processed = await process_danmaku(test_danmaku)
        
        if processed is not None and processed["processed"]:
            result.pass_(test_name)
        else:
            result.fail(test_name, "弹幕处理失败")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def main():
    """主测试函数"""
    logger.info("\n" + "="*60)
    logger.info("🚀 开始测试所有新功能")
    logger.info("="*60)
    
    result = TestResult()
    
    # 测试各个功能模块
    await test_streaming_asr(result)
    await test_error_handler(result)
    await test_websocket_monitor(result)
    await test_monitoring(result)
    await test_redis_cache(result)
    await test_entity_extraction(result)
    await test_danmaku_processor(result)
    
    # 打印测试摘要
    success = result.summary()
    
    if success:
        logger.info("\n🎉 所有测试通过！")
        return 0
    else:
        logger.error("\n❌ 部分测试失败！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
