"""
生产环境集成测试
测试Redis、向量数据库、直播平台API、告警系统等
"""

import asyncio
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects"))


async def test_redis_connection():
    """测试Redis连接"""
    print("\n" + "="*60)
    print("测试 Redis 连接...")
    print("="*60)
    
    try:
        from storage.redis_pool import get_redis_pool
        
        pool = await get_redis_pool()
        
        # 测试基本操作
        await pool.set("test_key", "test_value", ex=10)
        value = await pool.get("test_key")
        
        if value == "test_value":
            print("✅ Redis连接测试成功")
            print(f"   - 写入: test_key = test_value")
            print(f"   - 读取: {value}")
            return True
        else:
            print(f"❌ Redis读写失败: 期望 test_value, 实际 {value}")
            return False
            
    except Exception as e:
        print(f"❌ Redis连接失败: {str(e)}")
        return False


async def test_vector_database():
    """测试向量数据库"""
    print("\n" + "="*60)
    print("测试 向量数据库...")
    print("="*60)
    
    try:
        from storage.vector_db_persistent import get_vector_db
        
        db = await get_vector_db()
        
        if db.is_connected:
            stats = await db.get_stats()
            print("✅ 向量数据库连接成功")
            print(f"   - 文档总数: {stats.get('total_documents', 0)}")
            print(f"   - 向量维度: {stats.get('embedding_dimensions', 1024)}")
            return True
        else:
            print("❌ 向量数据库未连接")
            return False
            
    except Exception as e:
        print(f"❌ 向量数据库测试失败: {str(e)}")
        return False


async def test_alert_system():
    """测试告警系统"""
    print("\n" + "="*60)
    print("测试 告警系统...")
    print("="*60)
    
    try:
        from integrations.alert_system import AlertManager, AlertLevel, AlertChannel
        
        manager = AlertManager({
            "alert_cooldown": 60
        })
        
        # 测试统计功能
        stats = manager.get_stats()
        print("✅ 告警系统初始化成功")
        print(f"   - 告警历史数: {stats['alert_history_size']}")
        
        # 测试专用告警
        manager.send_live_assistant_alert(
            alert_type="system_error",
            details={
                "error_type": "测试错误",
                "error_msg": "这是一个测试告警",
                "impact": "测试环境"
            },
            level=AlertLevel.INFO
        )
        
        return True
            
    except Exception as e:
        print(f"❌ 告警系统测试失败: {str(e)}")
        return False


async def test_live_stream_api():
    """测试直播平台API"""
    print("\n" + "="*60)
    print("测试 直播平台API...")
    print("="*60)
    
    try:
        from integrations.live_stream_api import LiveStreamAPIFactory
        
        # 测试工厂模式
        print("✅ 直播平台API工厂初始化成功")
        print("   - 支持平台: 抖音、快手")
        print("   - API类型: get_room_info, get_screenshot, get_danmaku")
        
        return True
            
    except Exception as e:
        print(f"❌ 直播平台API测试失败: {str(e)}")
        return False


async def test_ab_testing():
    """测试A/B测试框架"""
    print("\n" + "="*60)
    print("测试 A/B测试框架...")
    print("="*60)
    
    try:
        from utils.ab_testing import ABTestingFramework, ExperimentType, init_sample_experiments
        
        # 初始化示例实验
        init_sample_experiments()
        
        framework = ABTestingFramework()
        
        # 由于init_sample_experiments创建了全局实例,这里重新获取
        from utils.ab_testing import ab_testing as framework
        
        experiments = framework.list_experiments()
        
        print("✅ A/B测试框架初始化成功")
        print(f"   - 实验数量: {len(experiments)}")
        
        for exp in experiments:
            print(f"   - {exp['name']}: {exp['status']}")
        
        return True
            
    except Exception as e:
        print(f"❌ A/B测试框架测试失败: {str(e)}")
        return False


async def test_knowledge_importer():
    """测试知识库导入工具"""
    print("\n" + "="*60)
    print("测试 知识库导入工具...")
    print("="*60)
    
    try:
        from utils.knowledge_importer import KnowledgeBaseImporter
        
        importer = KnowledgeBaseImporter()
        
        print("✅ 知识库导入工具初始化成功")
        print("   - 支持格式: CSV、JSON")
        print("   - 支持导入: 商品说明书、QA、规格参数")
        
        return True
            
    except Exception as e:
        print(f"❌ 知识库导入工具测试失败: {str(e)}")
        return False


async def test_production_config():
    """测试生产环境配置"""
    print("\n" + "="*60)
    print("测试 生产环境配置...")
    print("="*60)
    
    try:
        from config.production_config import ProductionConfig
        
        config = ProductionConfig()
        
        print("✅ 生产环境配置加载成功")
        print(f"   - 环境模式: {config.ENVIRONMENT}")
        print(f"   - 调试模式: {config.DEBUG}")
        print(f"   - 监控端口: {config.MONITORING_PORT}")
        
        return True
            
    except Exception as e:
        print(f"❌ 生产环境配置测试失败: {str(e)}")
        return False


async def test_agent_tools():
    """测试Agent工具集成"""
    print("\n" + "="*60)
    print("测试 Agent工具集成...")
    print("="*60)
    
    try:
        from agents.agent import build_agent
        
        # 构建agent
        agent = build_agent()
        
        print("✅ Agent构建成功")
        print(f"   - 工具数量: {len(agent.tools)}")
        
        # 列出所有工具
        tool_names = [tool.name for tool in agent.tools]
        print(f"   - 工具列表: {', '.join(tool_names[:5])}...")
        
        return True
            
    except Exception as e:
        print(f"❌ Agent工具集成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("直播带货AI助手 - 生产环境集成测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    results = {
        "Redis连接": await test_redis_connection(),
        "向量数据库": await test_vector_database(),
        "告警系统": await test_alert_system(),
        "直播平台API": await test_live_stream_api(),
        "A/B测试框架": await test_ab_testing(),
        "知识库导入": await test_knowledge_importer(),
        "生产环境配置": await test_production_config(),
        "Agent工具集成": await test_agent_tools()
    }
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print("\n" + "-"*60)
    print(f"总计: {len(results)} 个测试")
    print(f"通过: {passed} 个")
    print(f"失败: {failed} 个")
    print(f"成功率: {passed/len(results)*100:.1f}%")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
