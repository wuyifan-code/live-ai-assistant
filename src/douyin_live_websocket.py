"""
抖音直播间真实集成（WebSocket方式）
使用抖音官方WebSocket接口实时监听弹幕
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from agents.agent import build_agent
from integrations.douyin_websocket import DouyinWebSocketConnector
from integrations.douyin_api import DouyinLiveAPI

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DouyinLiveAssistant:
    """
    抖音直播AI助手（完整版）
    
    功能：
    1. 实时弹幕监听（WebSocket）
    2. AI智能回复
    3. 主播语音核对
    4. 商品信息同步
    5. 直播间统计
    """
    
    def __init__(self, room_url: str):
        """
        参数:
            room_url: 直播间URL（如: https://live.douyin.com/123456789）
        """
        self.room_url = room_url
        self.room_id = None
        
        # API客户端
        self.api = DouyinLiveAPI()
        
        # AI Agent
        self.agent = build_agent()
        
        # WebSocket连接器
        self.ws_connector = None
        
        # 直播间信息
        self.room_info = None
        self.products = []
        
        # AI回复队列（避免刷屏）
        self.reply_queue = asyncio.Queue()
        self.last_reply_time = 0
        self.reply_cooldown = 3  # AI回复冷却时间（秒）
        
        # 统计
        self.stats = {
            "total_danmaku": 0,
            "ai_responses": 0,
            "official_corrections": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """初始化"""
        logger.info("="*60)
        logger.info("🚀 初始化抖音直播AI助手")
        logger.info("="*60)
        
        # 1. 获取直播间ID
        logger.info("\n📍 步骤1: 获取直播间ID")
        self.room_id = await self.api.get_room_id_by_url(self.room_url)
        logger.info(f"✅ 直播间ID: {self.room_id}")
        
        # 2. 获取直播间信息
        logger.info("\n📋 步骤2: 获取直播间信息")
        self.room_info = await self.api.get_room_info(self.room_id)
        
        if not self.room_info:
            raise Exception("无法获取直播间信息")
        
        logger.info(f"📌 标题: {self.room_info['title']}")
        logger.info(f"👤 主播: {self.room_info['anchor']['name']}")
        logger.info(f"👀 在线: {self.room_info['viewer_count']}")
        logger.info(f"📊 状态: {self.room_info['status_text']}")
        
        if self.room_info['status'] != 1:
            raise Exception(f"直播间未开播: {self.room_info['status_text']}")
        
        # 3. 同步商品信息
        logger.info("\n📦 步骤3: 同步商品信息")
        self.products = await self.api.get_product_list(self.room_id)
        logger.info(f"✅ 商品数量: {len(self.products)}")
        
        for product in self.products[:5]:  # 显示前5个
            status = "✅" if product['status'] == 1 else "⏸️"
            logger.info(f"  {status} {product['name']} - ¥{product['price']}")
        
        if len(self.products) > 5:
            logger.info(f"  ... 还有 {len(self.products) - 5} 个商品")
        
        # 4. 初始化AI Agent
        logger.info("\n🤖 步骤4: 初始化AI助手")
        logger.info("✅ AI助手就绪")
        
        logger.info("\n" + "="*60)
        logger.info("✅ 初始化完成，开始监听直播")
        logger.info("="*60)
    
    async def start(self):
        """启动监听"""
        try:
            # 初始化
            await self.initialize()
            
            # 创建WebSocket连接器
            self.ws_connector = DouyinWebSocketConnector(
                room_id=self.room_id,
                on_danmaku=self._on_danmaku,
                on_gift=self._on_gift,
                on_like=self._on_like,
                on_enter=self._on_enter,
                on_error=self._on_error
            )
            
            # 启动AI回复任务
            asyncio.create_task(self._ai_reply_loop())
            
            # 连接WebSocket
            await self.ws_connector.connect()
            
        except Exception as e:
            logger.error(f"❌ 启动失败: {str(e)}")
            raise
    
    async def _on_danmaku(self, danmaku: dict):
        """处理弹幕"""
        self.stats["total_danmaku"] += 1
        
        username = danmaku['username']
        content = danmaku['content']
        
        # 显示弹幕
        logger.info(f"💬 [{username}]: {content}")
        
        # 判断是否需要AI回复
        if self._should_reply(content):
            # 加入回复队列
            await self.reply_queue.put({
                "username": username,
                "content": content,
                "timestamp": datetime.now()
            })
    
    async def _on_gift(self, gift: dict):
        """处理礼物"""
        username = gift['username']
        gift_name = gift['gift_name']
        gift_count = gift['gift_count']
        
        logger.info(f"🎁 [{username}] 送出 {gift_name} x{gift_count}")
        
        # 可以添加感谢逻辑
        if gift['gift_value'] >= 100:  # 高价值礼物
            thank_msg = f"感谢 {username} 送出的 {gift_name}！❤️"
            await self.api.send_message(self.room_id, thank_msg)
    
    async def _on_like(self, like: dict):
        """处理点赞"""
        # 点赞消息量很大，可以选择性处理
        pass
    
    async def _on_enter(self, enter: dict):
        """处理进入直播间"""
        username = enter['username']
        logger.debug(f"👋 {username} 进入直播间")
    
    async def _on_error(self, error: str):
        """处理错误"""
        self.stats["errors"] += 1
        logger.error(f"❌ WebSocket错误: {error}")
    
    def _should_reply(self, content: str) -> bool:
        """
        判断是否需要AI回复
        
        规则：
        1. 包含问号
        2. 包含商品关键词
        3. 包含价格、库存等关键词
        4. 长度适中
        """
        # 问句
        if "?" in content or "？" in content:
            return True
        
        # 商品关键词
        product_keywords = ["多少钱", "价格", "有货", "库存", "什么时候", 
                           "怎么买", "链接", "优惠", "活动"]
        if any(kw in content for kw in product_keywords):
            return True
        
        # 其他情况，随机回复（避免刷屏）
        # return random.random() < 0.3
        return False
    
    async def _ai_reply_loop(self):
        """AI回复循环"""
        while True:
            try:
                # 从队列获取消息
                item = await self.reply_queue.get()
                
                # 检查冷却时间
                now = time.time()
                if now - self.last_reply_time < self.reply_cooldown:
                    await asyncio.sleep(self.reply_cooldown)
                
                # 调用AI生成回复
                response = await self._generate_ai_response(
                    item['username'],
                    item['content']
                )
                
                # 发送回复
                if response:
                    # 检查是否需要官方更正
                    is_correction = "更正" in response or "错误" in response
                    
                    success = await self.api.send_message(
                        self.room_id,
                        response
                    )
                    
                    if success:
                        self.stats["ai_responses"] += 1
                        
                        if is_correction:
                            self.stats["official_corrections"] += 1
                            logger.info(f"📢 [官方更正]: {response}")
                        else:
                            logger.info(f"🤖 [AI回复]: {response}")
                    
                    self.last_reply_time = time.time()
                
            except Exception as e:
                logger.error(f"AI回复失败: {str(e)}")
                await asyncio.sleep(1)
    
    async def _generate_ai_response(self, username: str, content: str) -> str:
        """生成AI回复"""
        try:
            # 构建输入
            user_input = f"用户【{username}】在直播间问：{content}"
            
            # 调用Agent
            config = {"configurable": {"thread_id": f"live_{username}"}}
            
            result = await self.agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config=config
            )
            
            # 提取回复
            if result and "messages" in result:
                return result["messages"][-1].content
            
            return None
            
        except Exception as e:
            logger.error(f"AI生成失败: {str(e)}")
            return None
    
    async def stop(self):
        """停止"""
        logger.info("\n🛑 停止AI助手...")
        
        if self.ws_connector:
            await self.ws_connector.disconnect()
        
        # 打印统计
        logger.info("\n📊 运行统计:")
        logger.info(f"  总弹幕: {self.stats['total_danmaku']}")
        logger.info(f"  AI回复: {self.stats['ai_responses']}")
        logger.info(f"  官方更正: {self.stats['official_corrections']}")
        logger.info(f"  错误次数: {self.stats['errors']}")


async def main():
    """主程序"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║       抖音直播AI助手 - WebSocket实时监听                   ║
    ╠════════════════════════════════════════════════════════════╣
    ║  功能:                                                    ║
    ║  - 实时弹幕监听（WebSocket）                             ║
    ║  - AI智能回复                                            ║
    ║  - 礼物感谢                                              ║
    ║  - 主播错误检测                                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # 获取直播间URL
    room_url = input("请输入抖音直播间URL: ").strip()
    
    if not room_url:
        print("❌ 请提供直播间URL")
        return
    
    # 示例URL: https://live.douyin.com/123456789
    if "live.douyin.com" not in room_url:
        print("❌ 请输入正确的抖音直播间URL")
        print("示例: https://live.douyin.com/123456789")
        return
    
    # 创建助手
    assistant = DouyinLiveAssistant(room_url)
    
    try:
        # 启动
        await assistant.start()
        
    except KeyboardInterrupt:
        print("\n\n👋 用户中断")
    except Exception as e:
        print(f"\n❌ 运行错误: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 停止
        await assistant.stop()


if __name__ == "__main__":
    asyncio.run(main())
