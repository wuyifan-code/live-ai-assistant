"""
直播间集成示例 - 抖音/快手/淘宝直播
展示如何将AI助手连接到不同的直播平台
"""

import asyncio
import os
import sys
from datetime import datetime

# 添加项目路径到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from agents.agent import build_agent
from live_connector import LiveConnector, DanmakuAIBridge


# ==================== 抖音直播集成示例 ====================

async def douyin_live_example():
    """
    抖音直播集成示例
    
    前提条件：
    1. 需要申请抖音开放平台开发者账号
    2. 创建应用并获取App ID和App Secret
    3. 申请直播间权限和Webhook地址
    4. 使用抖音SDK或HTTP API获取弹幕数据
    """
    
    print("=" * 60)
    print("📱 抖音直播集成示例")
    print("=" * 60)
    
    # 抖音直播间弹幕接收地址（需要从抖音开放平台获取）
    DOUYIN_WEBSOCKET_URL = "wss://webcast.douyin.com/websocket/im/v1"
    
    # 构建AI Agent
    agent = build_agent()
    
    # 创建直播间连接器
    connector = LiveConnector(
        websocket_url=DOUYIN_WEBSOCKET_URL,
        on_message_callback=on_danmaku_received,
        on_error_callback=on_error
    )
    
    # 创建AI桥接器
    bridge = DanmakuAIBridge(connector, agent)
    
    # 启动连接
    await bridge.start()


async def on_danmaku_received(danmaku_data: dict):
    """收到抖音弹幕的回调函数"""
    print(f"\n📥 [抖音] {danmaku_data['username']}: {danmaku_data['content']}")
    # 处理弹幕逻辑...（见下方完整示例）


async def on_error(error_message: str):
    """错误回调函数"""
    print(f"❌ 错误: {error_message}")


# ==================== 快手直播集成示例 ====================

async def kuaishou_live_example():
    """
    快手直播集成示例
    
    前提条件：
    1. 申请快手开放平台开发者账号
    2. 获取App ID和App Secret
    3. 使用快手直播SDK或API
    """
    
    print("=" * 60)
    print("📹 快手直播集成示例")
    print("=" * 60)
    
    # 快手直播间弹幕接收地址
    KUAISHOU_WEBSOCKET_URL = "wss://live.kuaishou.com/api/v1/websocket"
    
    # 构建AI Agent
    agent = build_agent()
    
    # 创建直播间连接器
    connector = LiveConnector(
        websocket_url=KUAISHOU_WEBSOCKET_URL,
        on_message_callback=on_danmaku_received,
        on_error_callback=on_error
    )
    
    # 创建AI桥接器
    bridge = DanmakuAIBridge(connector, agent)
    
    # 启动连接
    await bridge.start()


# ==================== 淘宝直播集成示例 ====================

async def taobao_live_example():
    """
    淘宝直播集成示例
    
    前提条件：
    1. 申请淘宝开放平台开发者账号
    2. 创建应用并获取App Key和App Secret
    3. 使用淘宝直播开放API
    """
    
    print("=" * 60)
    print("🛒 淘宝直播集成示例")
    print("=" * 60)
    
    # 淘宝直播间弹幕接收地址
    TAOBAO_WEBSOCKET_URL = "wss://live.taobao.com/api/v1/im"
    
    # 构建AI Agent
    agent = build_agent()
    
    # 创建直播间连接器
    connector = LiveConnector(
        websocket_url=TAOBAO_WEBSOCKET_URL,
        on_message_callback=on_danmaku_received,
        on_error_callback=on_error
    )
    
    # 创建AI桥接器
    bridge = DanmakuAIBridge(connector, agent)
    
    # 启动连接
    await bridge.start()


# ==================== 模拟直播场景测试 ====================

class MockLiveConnector(LiveConnector):
    """模拟直播间连接器（用于测试）"""
    
    def __init__(self, mock_danmaku_list: list):
        self.mock_danmaku_list = mock_danmaku_list
        self.current_index = 0
        super().__init__("", None, None)
    
    async def connect(self):
        """模拟连接"""
        print("✅ 模拟直播间连接成功")
        self.is_connected = True
        await self._simulate_danmaku()
    
    async def _simulate_danmaku(self):
        """模拟发送弹幕"""
        while self.current_index < len(self.mock_danmaku_list):
            danmaku = self.mock_danmaku_list[self.current_index]
            self.current_index += 1
            
            # 模拟收到弹幕
            danmaku_data = {
                "user_id": f"user_{self.current_index}",
                "username": danmaku.get("username", f"用户{self.current_index}"),
                "content": danmaku["content"],
                "timestamp": datetime.now().isoformat(),
                "room_id": "mock_room_001"
            }
            
            # 调用回调函数
            if self.on_message:
                await self.on_message(danmaku_data)
            
            # 模拟间隔
            await asyncio.sleep(2)
    
    async def send_message(self, message: str, is_official: bool = False):
        """模拟发送消息"""
        status = "⚠️ [官方更正]" if is_official else "📤 [AI回复]"
        print(f"{status} {message}")


async def test_with_mock_live():
    """使用模拟直播间测试AI助手"""
    
    print("=" * 60)
    print("🧪 模拟直播间测试")
    print("=" * 60)
    
    # 模拟弹幕列表
    mock_danmaku_list = [
        {"username": "小明", "content": "iPhone 15 Pro多少钱？"},
        {"username": "小红", "content": "有现货吗？"},
        {"username": "阿强", "content": "讲咩啊？手机点解咁贵？（粤语）"},
        {"username": "用户D", "content": "我买的耳机有质量问题！"},
        {"username": "用户E", "content": "Apple Watch Series 9多少钱？"}
    ]
    
    # 构建AI Agent
    agent = build_agent()
    
    # 创建模拟连接器
    connector = MockLiveConnector(mock_danmaku_list)
    
    # 创建AI桥接器
    bridge = DanmakuAIBridge(connector, agent)
    
    # 启动模拟直播
    await bridge.start()
    
    print("\n✅ 模拟直播测试完成")


# ==================== 主播语音监听示例 ====================

async def monitor_anchor_speech_example():
    """
    主播语音监听示例
    
    说明：
    1. 需要获取直播间的音频流
    2. 使用ASR（语音转文字）技术将语音转为文本
    3. 将文本传递给AI助手进行核对
    """
    
    print("=" * 60)
    print("🎙️ 主播语音监听示例")
    print("=" * 60)
    
    # 构建AI Agent
    agent = build_agent()
    
    # 模拟主播语音内容（实际应该通过ASR获取）
    anchor_speeches = [
        "iPhone 15 Pro现在只要6999元",
        "MacBook Air M3库存有100台",
        "iPad Air 5还有货"
    ]
    
    for speech in anchor_speeches:
        print(f"\n🎙️ 主播说: {speech}")
        
        # 调用AI助手核对
        config = {"configurable": {"thread_id": "anchor_monitor"}}
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": f"主播说：{speech}。请检测信息是否正确。"}]},
            config=config
        )
        
        ai_response = result["messages"][-1].content
        print(f"🤖 AI分析: {ai_response}")
        
        # 如果检测到错误，发送官方更正
        if "错误" in ai_response or "更正" in ai_response:
            print("⚠️ 需要发送官方更正弹幕！")


# ==================== 完整的主程序 ====================

async def main():
    """主程序入口"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║            直播带货AI助手 - 直播间集成示例                 ║
    ╠════════════════════════════════════════════════════════════╣
    ║  1. 抖音直播集成                                          ║
    ║  2. 快手直播集成                                          ║
    ║  3. 淘宝直播集成                                          ║
    ║  4. 模拟直播测试                                          ║
    ║  5. 主播语音监听                                          ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    choice = input("请选择要运行的功能（输入数字1-5）: ")
    
    if choice == "1":
        await douyin_live_example()
    elif choice == "2":
        await kuaishou_live_example()
    elif choice == "3":
        await taobao_live_example()
    elif choice == "4":
        await test_with_mock_live()
    elif choice == "5":
        await monitor_anchor_speech_example()
    else:
        print("❌ 无效的选择")


if __name__ == "__main__":
    # 运行主程序
    asyncio.run(main())
