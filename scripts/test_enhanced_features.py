"""
测试所有新增强功能
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


async def test_visual_awareness(result: TestResult):
    """测试视觉识别"""
    test_name = "多模态视觉增强"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.tools.visual_awareness_tool import (
            extract_text_from_screen,
            detect_product_in_scene,
            analyze_scene_context
        )
        
        # 测试工具是否正确导入
        if all([
            extract_text_from_screen,
            detect_product_in_scene,
            analyze_scene_context
        ]):
            result.pass_(test_name)
        else:
            result.fail(test_name, "工具导入失败")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_human_collaboration(result: TestResult):
    """测试人机协作"""
    test_name = "人机协作逻辑"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.human_collaboration import (
            takeover_trigger,
            audit_queue,
            TakeoverReason,
            UrgencyLevel
        )
        
        # 测试接管触发
        request = takeover_trigger.check_takeover_needed(
            user_id="test_user",
            username="测试用户",
            content="我要投诉你们！这是假货！",
            confidence=0.3
        )
        
        if request and request.reason == TakeoverReason.SEVERE_COMPLAINT:
            result.pass_(test_name)
        else:
            result.fail(test_name, "接管触发失败")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_voice_interaction(result: TestResult):
    """测试语音交互"""
    test_name = "TTS语音输出"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.tools.voice_interaction_tool import (
            tts_output,
            personality_engine,
            VoicePersonality,
            LiveStreamMood
        )
        
        # 测试人格选择
        personality = personality_engine.select_personality(LiveStreamMood.EXCITING)
        
        if personality == VoicePersonality.ENTHUSIASTIC:
            result.pass_(test_name)
        else:
            result.fail(test_name, f"人格选择错误: {personality}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_enhanced_monitoring(result: TestResult):
    """测试增强版监控"""
    test_name = "增强版监控面板"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.utils.enhanced_monitoring import (
            enhanced_performance_metrics,
            EnhancedMonitoringAPI
        )
        
        # 测试指标记录
        enhanced_performance_metrics.record_danmaku(0.5)
        enhanced_performance_metrics.record_cache_hit(True)
        enhanced_performance_metrics.record_tts_output()
        
        metrics = enhanced_performance_metrics.get_current_metrics()
        
        if metrics["total_danmaku"] >= 1 and metrics["tts_outputs"] >= 1:
            result.pass_(test_name)
        else:
            result.fail(test_name, f"指标不正确: {metrics}")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def test_knowledge_base(result: TestResult):
    """测试知识库"""
    test_name = "知识库增强（RAG）"
    logger.info(f"\n🧪 测试: {test_name}")
    
    try:
        from src.tools.knowledge_base_tool import (
            VectorDatabase,
            RAGRetriever,
            ProductKnowledgeBase
        )
        
        # 测试向量数据库
        vector_db = VectorDatabase(embedding_dimensions=512)
        
        # 测试知识库实例
        if vector_db and ProductKnowledgeBase:
            result.pass_(test_name)
        else:
            result.fail(test_name, "知识库初始化失败")
    
    except Exception as e:
        result.fail(test_name, str(e))


async def main():
    """主测试函数"""
    logger.info("\n" + "="*60)
    logger.info("🚀 开始测试所有增强功能")
    logger.info("="*60)
    
    result = TestResult()
    
    # 测试各个功能模块
    await test_visual_awareness(result)
    await test_human_collaboration(result)
    await test_voice_interaction(result)
    await test_enhanced_monitoring(result)
    await test_knowledge_base(result)
    
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
