#!/usr/bin/env python3
"""
抖音直播智能互动插件测试脚本
"""
import asyncio
import logging
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_mock_intelligent_api():
    """测试模拟直播智能互动插件API"""
    logger.info("=" * 60)
    logger.info("🤖 开始测试直播智能互动插件API（模拟模式）")
    logger.info("=" * 60)
    
    try:
        from integrations.douyin_intelligent_api import MockDouyinLiveIntelligentAPI
        
        # 初始化模拟API
        api = MockDouyinLiveIntelligentAPI()
        
        # 1. 测试获取token
        logger.info("\n1️⃣ 测试获取access_token...")
        token = await api.get_access_token()
        logger.info(f"   ✅ Token: {token[:30]}...")
        
        # 2. 测试获取直播间信息
        logger.info("\n2️⃣ 测试获取直播间信息...")
        room_info = await api.get_room_info("7609299821102730003")
        logger.info(f"   ✅ 直播间: {room_info['title']}")
        logger.info(f"   ✅ 主播: {room_info['anchor_name']}")
        logger.info(f"   ✅ 在线: {room_info['online_count']}人")
        
        # 3. 测试获取弹幕
        logger.info("\n3️⃣ 测试获取弹幕数据...")
        danmaku_list = await api.get_interaction_data("7609299821102730003", "danmaku", limit=5)
        logger.info(f"   ✅ 获取到 {len(danmaku_list)} 条弹幕")
        for i, danmaku in enumerate(danmaku_list[:3], 1):
            logger.info(f"      {i}. {danmaku['username']}: {danmaku['content']}")
        
        # 4. 测试获取礼物
        logger.info("\n4️⃣ 测试获取礼物数据...")
        gift_list = await api.get_interaction_data("7609299821102730003", "gift", limit=3)
        logger.info(f"   ✅ 获取到 {len(gift_list)} 条礼物记录")
        for i, gift in enumerate(gift_list, 1):
            logger.info(f"      {i}. {gift['username']} 送出 {gift['gift_name']} x{gift['gift_count']}")
        
        # 5. 测试获取点赞
        logger.info("\n5️⃣ 测试获取点赞数据...")
        like_list = await api.get_interaction_data("7609299821102730003", "like", limit=3)
        logger.info(f"   ✅ 获取到 {len(like_list)} 条点赞记录")
        
        # 6. 测试发送消息
        logger.info("\n6️⃣ 测试发送消息...")
        success = await api.send_message("7609299821102730003", "欢迎来到直播间！我是智能助手～")
        logger.info(f"   ✅ 消息发送: {'成功' if success else '失败'}")
        
        # 7. 测试获取商品
        logger.info("\n7️⃣ 测试获取商品列表...")
        product_list = await api.get_product_list("7609299821102730003")
        logger.info(f"   ✅ 获取到 {len(product_list)} 个商品")
        for i, product in enumerate(product_list, 1):
            logger.info(f"      {i}. {product['title']} - ¥{product['price']} (库存:{product['stock']})")
        
        # 8. 测试获取统计数据
        logger.info("\n8️⃣ 测试获取统计数据...")
        stats = await api.get_statistics("7609299821102730003")
        logger.info(f"   ✅ 在线人数: {stats.get('online_count', 0)}")
        logger.info(f"   ✅ 弹幕数: {stats.get('danmaku_count', 0)}")
        logger.info(f"   ✅ 礼物数: {stats.get('gift_count', 0)}")
        logger.info(f"   ✅ 点赞数: {stats.get('like_count', 0)}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 所有测试通过！直播智能互动插件API工作正常！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def test_real_intelligent_api(app_id: str, app_secret: str, room_id: str):
    """测试真实直播智能互动插件API"""
    logger.info("=" * 60)
    logger.info("🔌 开始测试直播智能互动插件API（真实模式）")
    logger.info("=" * 60)
    
    try:
        from integrations.douyin_intelligent_api import DouyinLiveIntelligentAPI
        
        # 初始化真实API
        api = DouyinLiveIntelligentAPI()
        api.app_id = app_id
        api.app_secret = app_secret
        
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
        logger.info("\n3️⃣ 测试获取弹幕数据...")
        danmaku_list = await api.get_interaction_data(room_id, "danmaku", limit=10)
        logger.info(f"   ✅ 获取到 {len(danmaku_list)} 条弹幕")
        
        # 4. 测试发送消息
        logger.info("\n4️⃣ 测试发送消息...")
        success = await api.send_message(room_id, "【测试】智能助手已上线！")
        logger.info(f"   ✅ 消息发送: {'成功' if success else '失败'}")
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 真实API测试完成！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🤖 抖音直播智能互动插件测试")
    print("=" * 60)
    print("您的配置：")
    print(f"  App ID: tt66fc1041f89cf9e210")
    print(f"  App Secret: 0e8d346f6baa1e0a68b7fda1835155ddf292db90")
    print(f"  直播间ID: 7609299821102730003")
    print()
    print("1. 🧪 测试模拟模式（推荐 - 无需网络）
    print("2. 🔌 测试真实模式（需要权限）
    print("3. ❌ 退出")
    print("=" * 60)
    
    choice = input("\n请选择 [1-3]: ").strip()
    
    if choice == "1":
        asyncio.run(test_mock_intelligent_api())
        
    elif choice == "2":
        app_id = "tt66fc1041f89cf9e210"
        app_secret = "0e8d346f6baa1e0a68b7fda1835155ddf292db90"
        room_id = "7609299821102730003"
        asyncio.run(test_real_intelligent_api(app_id, app_secret, room_id))
        
    elif choice == "3":
        print("👋 再见！")
        
    else:
        print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    main()
