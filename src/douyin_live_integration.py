"""
抖音直播间真实集成示例
使用抖音开放平台API连接直播间
"""

import asyncio
import logging
from datetime import datetime
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from agents.agent import build_agent
from live_connector import LiveConnector, DanmakuAIBridge
from integrations.douyin_api import DouyinLiveAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DouyinLiveConnector(LiveConnector):
    """
    抖音直播间连接器
    
    使用抖音开放平台API实现：
    1. 获取直播间信息
    2. 实时弹幕拉取
    3. AI回复发送
    """
    
    def __init__(
        self,
        room_id: str,
        on_message_callback=None,
        on_error_callback=None,
        poll_interval: float = 2.0
    ):
        """
        参数:
            room_id: 直播间ID
            on_message_callback: 弹幕回调
            on_error_callback: 错误回调
            poll_interval: 弹幕轮询间隔（秒）
        """
        super().__init__("", on_message_callback, on_error_callback)
        
        self.room_id = room_id
        self.poll_interval = poll_interval
        self.douyin_api = DouyinLiveAPI()
        
        self.is_running = False
        self.last_cursor = "0"
        self.processed_messages = set()  # 去重
    
    async def connect(self):
        """连接到抖音直播间"""
        try:
            logger.info(f"🔌 连接抖音直播间: {self.room_id}")
            
            # 获取直播间信息
            room_info = await self.douyin_api.get_room_info(self.room_id)
            
            if not room_info:
                raise Exception("无法获取直播间信息")
            
            if room_info["status"] != 1:
                raise Exception(f"直播间状态异常: {room_info['status_text']}")
            
            self.is_connected = True
            self.is_running = True
            
            logger.info("✅ 连接成功")
            logger.info(f"📌 直播间: {room_info['title']}")
            logger.info(f"👤 主播: {room_info['anchor']['name']}")
            logger.info(f"👀 在线人数: {room_info['viewer_count']}")
            
            # 启动弹幕轮询
            asyncio.create_task(self._poll_danmaku())
            
        except Exception as e:
            logger.error(f"❌ 连接失败: {str(e)}")
            if self.on_error:
                await self.on_error(str(e))
    
    async def _poll_danmaku(self):
        """轮询获取弹幕"""
        logger.info("🔄 开始监听弹幕...")
        
        while self.is_running:
            try:
                # 获取弹幕列表
                danmaku_list = await self.douyin_api.get_danmaku_list(
                    self.room_id,
                    count=100,
                    cursor=self.last_cursor
                )
                
                # 处理新弹幕
                for danmaku in danmaku_list:
                    # 去重
                    msg_id = f"{danmaku['user_id']}_{danmaku['timestamp']}_{danmaku['content']}"
                    
                    if msg_id not in self.processed_messages:
                        self.processed_messages.add(msg_id)
                        
                        # 调用回调
                        if self.on_message:
                            await self.on_message(danmaku)
                
                # 更新游标
                if danmaku_list:
                    self.last_cursor = danmaku_list[-1].get("timestamp", self.last_cursor)
                
                # 清理旧消息（避免内存泄漏）
                if len(self.processed_messages) > 10000:
                    self.processed_messages = set(list(self.processed_messages)[-5000:])
                
                # 等待下一次轮询
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"轮询弹幕失败: {str(e)}")
                await asyncio.sleep(5)  # 出错后等待更长时间
    
    async def send_message(self, message: str, is_official: bool = False):
        """
        发送消息到直播间
        
        参数:
            message: 消息内容
            is_official: 是否为官方消息（会添加特殊标记）
        """
        if is_official:
            message = f"【官方更正】{message}"
        
        success = await self.douyin_api.send_message(
            self.room_id,
            message,
            message_type="text"
        )
        
        if success:
            prefix = "📢 [官方]" if is_official else "📤 [AI]"
            logger.info(f"{prefix} {message}")
        
        return success
    
    async def disconnect(self):
        """断开连接"""
        self.is_running = False
        self.is_connected = False
        logger.info("👋 已断开抖音直播间连接")


class DouyinAIBridge(DanmakuAIBridge):
    """
    抖音直播AI桥接器
    
    扩展功能：
    1. 商品信息同步
    2. 直播间统计
    3. 主播语音监听
    """
    
    def __init__(self, connector: DouyinLiveConnector, agent, room_id: str):
        super().__init__(connector, agent)
        self.room_id = room_id
        self.douyin_api = DouyinLiveAPI()
        
        # 商品信息缓存
        self.products_cache = []
    
    async def sync_products(self):
        """同步直播间商品信息"""
        logger.info("📦 同步直播间商品...")
        
        products = await self.douyin_api.get_product_list(self.room_id)
        
        self.products_cache = products
        
        logger.info(f"✅ 同步完成，共 {len(products)} 个商品")
        
        for product in products:
            status = "✅" if product["status"] == 1 else "⏸️"
            logger.info(f"  {status} {product['name']} - ¥{product['price']}")
    
    async def get_room_stats(self):
        """获取直播间统计"""
        stats = await self.douyin_api.get_room_stats(self.room_id)
        
        logger.info("📊 直播间统计:")
        logger.info(f"  总观看: {stats.get('total_viewers', 0)}")
        logger.info(f"  峰值在线: {stats.get('peak_viewers', 0)}")
        logger.info(f"  总点赞: {stats.get('total_likes', 0)}")
        logger.info(f"  销售额: ¥{stats.get('total_sales', 0)}")
        
        return stats


async def main():
    """主程序"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║         抖音直播间AI助手 - 真实集成                        ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # 配置
    ROOM_URL = input("请输入抖音直播间URL: ").strip()
    
    if not ROOM_URL:
        print("❌ 请提供直播间URL")
        return
    
    try:
        # 初始化API
        douyin_api = DouyinLiveAPI()
        
        # 获取直播间ID
        print("\n🔍 获取直播间ID...")
        room_id = await douyin_api.get_room_id_by_url(ROOM_URL)
        print(f"✅ 直播间ID: {room_id}")
        
        # 构建AI Agent
        print("\n🤖 初始化AI助手...")
        agent = build_agent()
        print("✅ AI助手就绪")
        
        # 创建连接器
        connector = DouyinLiveConnector(room_id)
        
        # 创建桥接器
        bridge = DouyinAIBridge(connector, agent, room_id)
        
        # 同步商品信息
        await bridge.sync_products()
        
        # 连接直播间
        print("\n🚀 启动AI助手...")
        await bridge.start()
        
    except KeyboardInterrupt:
        print("\n\n👋 正在停止...")
    except Exception as e:
        print(f"\n❌ 运行错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
