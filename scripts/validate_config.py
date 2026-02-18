"""
环境配置验证脚本
检查所有必要的配置项是否正确设置
"""

import os
import sys
import asyncio
import logging
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    # 也添加src目录
    sys.path.insert(0, os.path.join(project_root, 'src'))

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class ConfigLevel(Enum):
    """配置级别"""
    REQUIRED = "required"      # 必需
    RECOMMENDED = "recommended"  # 推荐
    OPTIONAL = "optional"       # 可选


@dataclass
class ConfigItem:
    """配置项"""
    key: str
    level: ConfigLevel
    description: str
    example: str = ""


# 配置项清单
CONFIG_CHECKLIST: List[ConfigItem] = [
    # 必需配置
    ConfigItem(
        key="COZE_WORKLOAD_IDENTITY_API_KEY",
        level=ConfigLevel.REQUIRED,
        description="大模型API密钥（通常自动注入）",
        example="your-api-key"
    ),
    ConfigItem(
        key="DATABASE_URL",
        level=ConfigLevel.REQUIRED,
        description="PostgreSQL数据库连接字符串",
        example="postgresql://user:pass@localhost:5432/db"
    ),
    ConfigItem(
        key="REDIS_HOST",
        level=ConfigLevel.REQUIRED,
        description="Redis服务器地址",
        example="localhost"
    ),
    ConfigItem(
        key="DOUYIN_APP_ID",
        level=ConfigLevel.REQUIRED,
        description="抖音开放平台应用ID",
        example="your-app-id"
    ),
    ConfigItem(
        key="DOUYIN_APP_SECRET",
        level=ConfigLevel.REQUIRED,
        description="抖音开放平台应用密钥",
        example="your-app-secret"
    ),
    
    # 推荐配置
    ConfigItem(
        key="SUPABASE_URL",
        level=ConfigLevel.RECOMMENDED,
        description="Supabase项目URL",
        example="https://xxx.supabase.co"
    ),
    ConfigItem(
        key="SUPABASE_ANON_KEY",
        level=ConfigLevel.RECOMMENDED,
        description="Supabase匿名密钥",
        example="your-anon-key"
    ),
    ConfigItem(
        key="ENABLE_FEISHU_ALERT",
        level=ConfigLevel.RECOMMENDED,
        description="启用飞书告警",
        example="true"
    ),
    ConfigItem(
        key="FEISHU_WEBHOOK",
        level=ConfigLevel.RECOMMENDED,
        description="飞书机器人Webhook",
        example="https://open.feishu.cn/..."
    ),
    ConfigItem(
        key="ENABLE_VISUAL_RECOGNITION",
        level=ConfigLevel.RECOMMENDED,
        description="启用视觉识别",
        example="true"
    ),
    ConfigItem(
        key="ENABLE_TTS_OUTPUT",
        level=ConfigLevel.RECOMMENDED,
        description="启用TTS语音输出",
        example="true"
    ),
    
    # 可选配置
    ConfigItem(
        key="KUAISHOU_APP_ID",
        level=ConfigLevel.OPTIONAL,
        description="快手开放平台应用ID",
        example="your-app-id"
    ),
    ConfigItem(
        key="ENABLE_PROMETHEUS",
        level=ConfigLevel.OPTIONAL,
        description="启用Prometheus监控",
        example="true"
    ),
]


class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.results: Dict[str, Tuple[bool, str]] = {}
    
    def check_env_file(self) -> bool:
        """检查.env文件是否存在"""
        env_path = os.path.join(project_root, ".env")
        
        if os.path.exists(env_path):
            logger.info("✅ .env 文件存在")
            return True
        else:
            logger.warning("⚠️  .env 文件不存在，请从 .env.example 创建")
            return False
    
    def check_config_item(self, item: ConfigItem) -> Tuple[bool, str]:
        """检查单个配置项"""
        value = os.getenv(item.key)
        
        if value is None or value == "" or value.startswith("your-"):
            if item.level == ConfigLevel.REQUIRED:
                return False, "❌ 缺少必需配置"
            elif item.level == ConfigLevel.RECOMMENDED:
                return False, "⚠️  推荐配置（未设置）"
            else:
                return True, "ℹ️  可选配置（未设置）"
        else:
            return True, f"✅ 已设置: {value[:20]}..." if len(value) > 20 else f"✅ 已设置: {value}"
    
    def validate_all_configs(self) -> Dict:
        """验证所有配置"""
        logger.info("\n" + "="*60)
        logger.info("📋 配置项检查")
        logger.info("="*60)
        
        results = {
            "required": {"passed": 0, "failed": 0},
            "recommended": {"passed": 0, "failed": 0},
            "optional": {"passed": 0, "failed": 0}
        }
        
        # 按级别分组检查
        for level in [ConfigLevel.REQUIRED, ConfigLevel.RECOMMENDED, ConfigLevel.OPTIONAL]:
            level_name = level.value
            logger.info(f"\n【{level_name.upper()}】")
            
            items = [item for item in CONFIG_CHECKLIST if item.level == level]
            
            for item in items:
                passed, message = self.check_config_item(item)
                
                # 记录结果
                status_key = "passed" if passed else "failed"
                results[level_name][status_key] += 1
                
                # 显示结果
                logger.info(f"  {item.key}: {message}")
                if not passed and level == ConfigLevel.REQUIRED:
                    logger.info(f"    描述: {item.description}")
                    logger.info(f"    示例: {item.example}")
        
        return results
    
    async def check_redis_connection(self) -> bool:
        """检查Redis连接"""
        logger.info("\n" + "="*60)
        logger.info("🔴 Redis连接检查")
        logger.info("="*60)
        
        try:
            from storage.redis_pool import get_redis_pool
            
            pool = await get_redis_pool()
            
            # 测试读写
            test_key = "config_test_key"
            test_value = "test_value"
            
            await pool.set(test_key, test_value, ex=10)
            result = await pool.get(test_key)
            
            if result == test_value:
                logger.info("✅ Redis连接正常，读写测试成功")
                return True
            else:
                logger.error("❌ Redis读写测试失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ Redis连接失败: {str(e)}")
            logger.info("请检查Redis服务是否启动，以及配置是否正确")
            return False
    
    async def check_database_connection(self) -> bool:
        """检查数据库连接"""
        logger.info("\n" + "="*60)
        logger.info("🗄️  数据库连接检查")
        logger.info("="*60)
        
        try:
            from storage.database.supabase_client import get_supabase_client
            
            client = get_supabase_client()
            
            # 测试查询
            response = client.table('products').select('count', count='exact').execute()
            
            count = response.count if hasattr(response, 'count') else 0
            logger.info(f"✅ 数据库连接正常，商品表记录数: {count}")
            
            return True
                
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {str(e)}")
            logger.info("请检查数据库服务是否启动，以及连接字符串是否正确")
            return False
    
    async def check_llm_connection(self) -> bool:
        """检查大模型连接"""
        logger.info("\n" + "="*60)
        logger.info("🤖 大模型连接检查")
        logger.info("="*60)
        
        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
        
        if not api_key or api_key.startswith("your-"):
            logger.warning("⚠️  未配置API密钥，可能依赖环境自动注入")
            logger.info("如果在生产环境运行，API密钥会自动注入")
            return True
        
        try:
            from langchain_openai import ChatOpenAI
            
            llm = ChatOpenAI(
                model="doubao-seed-1-8-251228",
                api_key=api_key,
                base_url=base_url or "https://ark.cn-beijing.volces.com/api/v3",
                timeout=10
            )
            
            # 测试简单调用
            response = await llm.ainvoke("测试")
            
            logger.info("✅ 大模型连接正常")
            return True
                
        except Exception as e:
            logger.warning(f"⚠️  大模型连接测试失败: {str(e)}")
            logger.info("这不影响系统启动，但可能影响AI功能")
            return True  # 不阻塞启动
    
    def print_summary(self, results: Dict):
        """打印汇总报告"""
        logger.info("\n" + "="*60)
        logger.info("📊 配置验证汇总")
        logger.info("="*60)
        
        # 统计
        required_failed = results["required"]["failed"]
        recommended_failed = results["recommended"]["failed"]
        
        if required_failed == 0:
            logger.info("✅ 所有必需配置项已正确设置")
        else:
            logger.error(f"❌ {required_failed} 个必需配置项未设置")
        
        if recommended_failed > 0:
            logger.warning(f"⚠️  {recommended_failed} 个推荐配置项未设置")
        
        # 建议
        logger.info("\n📝 后续步骤:")
        
        if required_failed > 0:
            logger.info("  1. 编辑 .env 文件，填写缺失的必需配置项")
            logger.info("  2. 重新运行此验证脚本")
        else:
            logger.info("  1. 运行 python scripts/init_database.py 初始化数据库")
            logger.info("  2. 运行 python scripts/run_prod.py 启动服务")
        
        logger.info("\n📚 详细文档:")
        logger.info("  - 环境配置: docs/INFRASTRUCTURE_SETUP.md")
        logger.info("  - 部署指南: docs/DEPLOYMENT.md")
    
    async def run_all_checks(self):
        """运行所有检查"""
        logger.info("\n🔍 开始环境配置验证...\n")
        
        # 检查.env文件
        self.check_env_file()
        
        # 验证配置项
        config_results = self.validate_all_configs()
        
        # 检查服务连接
        redis_ok = await self.check_redis_connection()
        db_ok = await self.check_database_connection()
        llm_ok = await self.check_llm_connection()
        
        # 打印汇总
        self.print_summary(config_results)
        
        # 返回是否可以启动
        required_ok = config_results["required"]["failed"] == 0
        return required_ok and redis_ok and db_ok


async def main():
    """主函数"""
    validator = ConfigValidator()
    can_start = await validator.run_all_checks()
    
    if can_start:
        logger.info("\n✅ 环境配置验证通过，可以启动服务！")
        return 0
    else:
        logger.error("\n❌ 环境配置验证失败，请根据提示修复问题")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
