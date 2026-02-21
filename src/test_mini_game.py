#!/usr/bin/env python3
"""
抖音直播小玩法集成测试脚本
支持模拟模式和真实模式
"""
import asyncio
import logging
import sys
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mock_api():
    """测试模拟API（无需真实凭证）"""
    logger.info("=" * 60)
    logger.info("🧪 开始测试模拟API")
    logger.info("=" * 60)
    
    try:
        from integrations.douyin_mini_game_api import MockDouyinMiniGameAPI
        
        # 初始化模拟API
        api = MockDouyinMiniGameAPI()
        
        # 1. 测试获取token
        logger.info("\n1️⃣ 测试获取access_token...")
        token = await api.get_access_token()
        logger.info(f"   ✅ Token: {token[:20]}...")
        
        # 2. 测试获取直播间信息
        logger.info("\n2️⃣ 测试获取直播间信息...")
        room_info = await api.get_room_info("test_room_123")
        logger.info(f"   ✅ 直播间: {room_info['title']}")
        logger.info(f"   ✅ 主播: {room_info['anchor_name']}")
        logger.info(f"   ✅ 在线: {room_info['online_count']}人")
        
        # 3. 测试获取弹幕
        logger.info("\n3️⃣ 测试获取弹幕列表...")
        danmaku_list = await api.get_danmaku_list("test_room_123", limit=5)
        logger.info(f"   ✅ 获取到 {len(danmaku_list)} 条弹幕")
        for i, danmaku in enumerate(danmaku_list[:3], 1):
            logger.info(f"      {i}. {danmaku['username']}: {danmaku['content']}")
        
        # 4. 测试发送消息
        logger.info("\n4️⃣ 测试发送消息...")
        success = await api.send_message("test_room_123", "欢迎来到直播间！我是AI助手～")
        logger.info(f"   ✅ 消息发送: {'成功' if success else '失败'}")
        
        # 5. 测试获取礼物
        logger.info("\n5️⃣ 测试获取礼物列表...")
        gift_list = await api.get_gift_list("test_room_123", limit=3)
        logger.info(f"   ✅ 获取到 {len(gift_list)} 条礼物记录")
        for i, gift in enumerate(gift_list, 1):
            logger.info(f"      {i}. {gift['username']} 送出 {gift['gift_name']} x{gift['gift_count']}")
        
        # 6. 测试获取商品
        logger.info("\n6️⃣ 测试获取商品列表...")
        product_list = await api.get_product_list("test_room_123")
        logger.info(f"   ✅ 获取到 {len(product_list)} 个商品")
        for i, product in enumerate(product_list, 1):
            logger.info(f"      {i}. {product['title']} - ¥{product['price']} (库存:{product['stock']})")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 模拟API测试全部通过！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_real_api(app_id: str, app_secret: str, mini_game_id: str, room_id: str):
    """测试真实API（需要配置凭证）"""
    logger.info("=" * 60)
    logger.info("🔌 开始测试真实API")
    logger.info("=" * 60)
    
    try:
        from integrations.douyin_mini_game_api import DouyinMiniGameAPI
        
        # 初始化真实API
        api = DouyinMiniGameAPI()
        api.app_id = app_id
        api.app_secret = app_secret
        api.mini_game_id = mini_game_id
        
        # 1. 测试获取token
        logger.info("\n1️⃣ 测试获取access_token...")
        token = await api.get_access_token()
        logger.info(f"   ✅ Token获取成功")
        
        # 2. 测试获取直播间信息
        logger.info("\n2️⃣ 测试获取直播间信息...")
        room_info = await api.get_room_info(room_id)
        logger.info(f"   ✅ 直播间: {room_info['title']}")
        logger.info(f"   ✅ 主播: {room_info['anchor_name']}")
        
        # 3. 测试获取弹幕
        logger.info("\n3️⃣ 测试获取弹幕列表...")
        danmaku_list = await api.get_danmaku_list(room_id, limit=10)
        logger.info(f"   ✅ 获取到 {len(danmaku_list)} 条弹幕")
        
        # 4. 测试发送消息
        logger.info("\n4️⃣ 测试发送消息...")
        success = await api.send_message(room_id, "【测试】AI助手已上线！")
        logger.info(f"   ✅ 消息发送: {'成功' if success else '失败'}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 真实API测试全部通过！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def print_menu():
    """打印菜单"""
    print("\n" + "=" * 60)
    print("🎮 抖音直播小玩法集成测试")
    print("=" * 60)
    print("1. 🧪 测试模拟API（推荐 - 无需凭证）")
    print("2. 🔌 测试真实API（需要抖音凭证）")
    print("3. 📖 查看使用指南")
    print("4. ❌ 退出")
    print("=" * 60)


def main():
    """主函数"""
    import os
    
    while True:
        print_menu()
        
        choice = input("\n请选择 [1-4]: ").strip()
        
        if choice == "1":
            # 测试模拟API
            asyncio.run(test_mock_api())
            
        elif choice == "2":
            # 测试真实API
            app_id = input("请输入 App ID: ").strip()
            app_secret = input("请输入 App Secret: ").strip()
            mini_game_id = input("请输入 小游戏ID: ").strip()
            room_id = input("请输入 直播间ID: ").strip()
            
            if not all([app_id, app_secret, mini_game_id, room_id]):
                logger.error("❌ 所有字段都必须填写！")
                continue
            
            asyncio.run(test_real_api(app_id, app_secret, mini_game_id, room_id))
            
        elif choice == "3":
            # 查看指南
            guide_path = os.path.join(os.path.dirname(__file__), "..", "docs", "MINI_GAME_GUIDE.md")
            if os.path.exists(guide_path):
                with open(guide_path, 'r', encoding='utf-8') as f:
                    print(f.read())
            else:
                print("指南文件不存在，请查看 docs/MINI_GAME_GUIDE.md")
            
        elif choice == "4":
            print("👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()
