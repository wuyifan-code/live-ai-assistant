"""
抖音直播智能互动插件 API 集成
适配直播智能体助手应用
"""
import os
import time
import json
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DouyinLiveIntelligentAPI:
    """
    抖音直播智能互动插件 API 客户端
    适配直播智能体助手应用
    """
    
    def __init__(self):
        self.app_id = os.getenv("DOUYIN_APP_ID", "tt66fc1041f89cf9e210")
        self.app_secret = os.getenv("DOUYIN_APP_SECRET", "0e8d346f6baa1e0a68b7fda1835155ddf292db90")
        
        self.base_url = "https://developer.open-douyin.com"
        self.access_token = None
        self.token_expires_at = 0
        
        logger.info("🤖 抖音直播智能互动插件API初始化完成")
        logger.info(f"   App ID: {self.app_id}")
    
    async def get_access_token(self) -> str:
        """
        获取访问令牌
        
        返回:
            access_token
        """
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # 直播智能插件的token获取方式
        url = f"{self.base_url}/oauth/access_token/"
        
        params = {
            "client_key": self.app_id,
            "client_secret": self.app_secret,
            "grant_type": "client_credential"
        }
        
        try:
            response = requests.post(url, json=params, timeout=10)
            result = response.json()
            
            if result.get("data", {}).get("access_token"):
                self.access_token = result["data"]["access_token"]
                expires_in = result["data"].get("expires_in", 7200)
                self.token_expires_at = time.time() + expires_in - 300
                
                logger.info(f"✅ 获取access_token成功")
                return self.access_token
            else:
                logger.error(f"❌ 获取access_token失败: {result}")
                raise Exception(f"获取token失败: {result}")
                
        except Exception as e:
            logger.error(f"❌ 获取access_token异常: {str(e)}")
            raise
    
    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """
        获取直播间信息
        
        参数:
            room_id: 直播间ID
        
        返回:
            直播间信息字典
        """
        token = await self.get_access_token()
        
        # 直播智能插件的数据获取接口
        url = f"{self.base_url}/interactplugin/room/info"
        
        params = {
            "access_token": token,
            "room_id": room_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                room_info = result.get("data", {})
                
                logger.info(f"✅ 获取直播间信息成功: {room_info.get('title', '未命名')}")
                
                return {
                    "room_id": room_id,
                    "title": room_info.get("title", ""),
                    "anchor_name": room_info.get("anchor_name", ""),
                    "online_count": room_info.get("online_count", 0),
                    "status": room_info.get("status", "unknown")
                }
            else:
                logger.error(f"❌ 获取直播间信息失败: {result}")
                raise Exception(f"获取直播间信息失败: {result}")
                
        except Exception as e:
            logger.error(f"❌ 获取直播间信息异常: {str(e)}")
            raise
    
    async def get_interaction_data(self, room_id: str, data_type: str = "danmaku", 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取互动数据（弹幕、礼物、点赞等）
        
        参数:
            room_id: 直播间ID
            data_type: 数据类型 (danmaku/gift/like/enter)
            limit: 获取数量
        
        返回:
            数据列表
        """
        token = await self.get_access_token()
        
        # 直播智能插件的互动数据接口
        url = f"{self.base_url}/interactplugin/interaction/list"
        
        params = {
            "access_token": token,
            "room_id": room_id,
            "type": data_type,
            "limit": limit
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                data_list = result.get("data", {}).get("list", [])
                
                logger.info(f"✅ 获取到 {len(data_list)} 条{data_type}数据")
                
                return self._format_interaction_data(data_list, data_type)
            else:
                logger.error(f"❌ 获取{data_type}数据失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取{data_type}数据异常: {str(e)}")
            return []
    
    def _format_interaction_data(self, raw_data: List[Dict], data_type: str) -> List[Dict]:
        """
        格式化互动数据
        
        参数:
            raw_data: 原始数据
            data_type: 数据类型
        
        返回:
            格式化后的数据
        """
        formatted_list = []
        
        for item in raw_data:
            if data_type == "danmaku":
                formatted_list.append({
                    "message_id": item.get("msg_id", ""),
                    "user_id": item.get("user_id", ""),
                    "username": item.get("nickname", ""),
                    "content": item.get("content", ""),
                    "timestamp": item.get("timestamp", int(time.time() * 1000))
                })
            elif data_type == "gift":
                formatted_list.append({
                    "message_id": item.get("msg_id", ""),
                    "user_id": item.get("user_id", ""),
                    "username": item.get("nickname", ""),
                    "gift_name": item.get("gift_name", ""),
                    "gift_count": item.get("count", 1),
                    "gift_value": item.get("value", 0),
                    "timestamp": item.get("timestamp", int(time.time() * 1000))
                })
            elif data_type == "like":
                formatted_list.append({
                    "message_id": item.get("msg_id", ""),
                    "user_id": item.get("user_id", ""),
                    "username": item.get("nickname", ""),
                    "count": item.get("count", 1),
                    "timestamp": item.get("timestamp", int(time.time() * 1000))
                })
            elif data_type == "enter":
                formatted_list.append({
                    "message_id": item.get("msg_id", ""),
                    "user_id": item.get("user_id", ""),
                    "username": item.get("nickname", ""),
                    "timestamp": item.get("timestamp", int(time.time() * 1000))
                })
        
        return formatted_list
    
    async def send_message(self, room_id: str, content: str) -> bool:
        """
        发送弹幕消息到直播间
        
        参数:
            room_id: 直播间ID
            content: 消息内容
        
        返回:
            是否发送成功
        """
        if len(content) > 200:
            logger.warning(f"⚠️ 消息过长，截断到200字符")
            content = content[:200]
        
        token = await self.get_access_token()
        
        # 直播智能插件的消息发送接口
        url = f"{self.base_url}/interactplugin/message/send"
        
        data = {
            "access_token": token,
            "room_id": room_id,
            "content": content,
            "msg_type": "text"  # text/image
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                logger.info(f"📤 消息发送成功: {content}")
                return True
            else:
                logger.error(f"❌ 消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送消息异常: {str(e)}")
            return False
    
    async def get_product_list(self, room_id: str) -> List[Dict[str, Any]]:
        """
        获取直播间商品列表
        
        参数:
            room_id: 直播间ID
        
        返回:
            商品列表
        """
        token = await self.get_access_token()
        
        # 直播智能插件的商品接口
        url = f"{self.base_url}/interactplugin/product/list"
        
        params = {
            "access_token": token,
            "room_id": room_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                product_list = result.get("data", {}).get("list", [])
                
                logger.info(f"✅ 获取到 {len(product_list)} 个商品")
                
                formatted_list = []
                for product in product_list:
                    formatted_list.append({
                        "product_id": product.get("product_id", ""),
                        "title": product.get("title", ""),
                        "price": product.get("price", 0),
                        "image_url": product.get("image_url", ""),
                        "link": product.get("link", ""),
                        "stock": product.get("stock", 0)
                    })
                
                return formatted_list
            else:
                logger.error(f"❌ 获取商品列表失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取商品列表异常: {str(e)}")
            return []
    
    async def get_statistics(self, room_id: str) -> Dict[str, Any]:
        """
        获取直播间统计数据
        
        参数:
            room_id: 直播间ID
        
        返回:
            统计数据
        """
        token = await self.get_access_token()
        
        url = f"{self.base_url}/interactplugin/stats"
        
        params = {
            "access_token": token,
            "room_id": room_id
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("code") == 0:
                stats = result.get("data", {})
                
                logger.info(f"✅ 获取统计数据成功")
                
                return {
                    "online_count": stats.get("online_count", 0),
                    "danmaku_count": stats.get("danmaku_count", 0),
                    "gift_count": stats.get("gift_count", 0),
                    "like_count": stats.get("like_count", 0),
                    "product_view_count": stats.get("product_view_count", 0),
                    "order_count": stats.get("order_count", 0)
                }
            else:
                logger.error(f"❌ 获取统计数据失败: {result}")
                return {}
                
        except Exception as e:
            logger.error(f"❌ 获取统计数据异常: {str(e)}")
            return {}


# 模拟数据版本
class MockDouyinLiveIntelligentAPI(DouyinLiveIntelligentAPI):
    """
    模拟直播智能互动插件API（用于开发测试）
    """
    
    async def get_access_token(self) -> str:
        """模拟获取token"""
        return "mock_token_intelligent_12345"
    
    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """模拟获取直播间信息"""
        logger.info(f"🤖 [模拟] 获取直播间信息: {room_id}")
        return {
            "room_id": room_id,
            "title": "直播智能体助手 - 测试直播间",
            "anchor_name": "AI主播",
            "online_count": 5678,
            "status": "live"
        }
    
    async def get_interaction_data(self, room_id: str, data_type: str = "danmaku", 
                                   limit: int = 50) -> List[Dict[str, Any]]:
        """模拟获取互动数据"""
        logger.info(f"🤖 [模拟] 获取{data_type}数据")
        import random
        from datetime import datetime, timedelta
        
        if data_type == "danmaku":
            users = ["小明", "小红", "张三", "李四", "王五", "赵六", "钱七", "孙八"]
            messages = [
                "这个多少钱？",
                "有优惠吗？",
                "质量怎么样？",
                "什么时候发货？",
                "有其他颜色吗？",
                "我买了，快点发货！",
                "主播推荐的这个真的好用",
                "链接在哪里？",
                "库存还有多少？",
                "能便宜点吗？",
                "支持7天无理由吗？",
                "正品保证吗？"
            ]
            
            data_list = []
            for i in range(min(limit, 8)):
                data_list.append({
                    "msg_id": f"msg_{i}",
                    "user_id": f"user_{i}",
                    "nickname": random.choice(users),
                    "content": random.choice(messages),
                    "timestamp": int((datetime.now() - timedelta(minutes=i)).timestamp() * 1000)
                })
            
            return self._format_interaction_data(data_list, data_type)
        
        elif data_type == "gift":
            users = ["粉丝A", "粉丝B", "粉丝C", "粉丝D", "粉丝E"]
            gifts = ["爱心", "火箭", "抖音一号", "嘉年华", "小心心", "热气球", "鲜花"]
            
            data_list = []
            for i in range(min(limit, 5)):
                gift_name = random.choice(gifts)
                count = random.randint(1, 10)
                
                data_list.append({
                    "msg_id": f"gift_{i}",
                    "user_id": f"gift_user_{i}",
                    "nickname": random.choice(users),
                    "gift_name": gift_name,
                    "count": count,
                    "value": count * (10 if gift_name in ["爱心", "小心心", "鲜花"] else 100),
                    "timestamp": int(time.time() * 1000)
                })
            
            return self._format_interaction_data(data_list, data_type)
        
        elif data_type == "like":
            data_list = []
            for i in range(min(limit, 5)):
                data_list.append({
                    "msg_id": f"like_{i}",
                    "user_id": f"like_user_{i}",
                    "nickname": f"用户{i}",
                    "count": random.randint(1, 10),
                    "timestamp": int(time.time() * 1000)
                })
            
            return self._format_interaction_data(data_list, data_type)
        
        return []
    
    async def send_message(self, room_id: str, content: str) -> bool:
        """模拟发送消息"""
        logger.info(f"📤 [模拟] 发送消息: {content}")
        return True
    
    async def get_product_list(self, room_id: str) -> List[Dict[str, Any]]:
        """模拟获取商品列表"""
        logger.info(f"🤖 [模拟] 获取商品列表")
        
        return [
            {
                "product_id": "prod_001",
                "title": "iPhone 15 Pro 256GB 钛金属原色",
                "price": 7999,
                "image_url": "",
                "link": "",
                "stock": 50
            },
            {
                "product_id": "prod_002",
                "title": "AirPods Pro 2代 主动降噪蓝牙耳机",
                "price": 1899,
                "image_url": "",
                "link": "",
                "stock": 200
            },
            {
                "product_id": "prod_003",
                "title": "Apple Watch Series 9 智能手表",
                "price": 2999,
                "image_url": "",
                "link": "",
                "stock": 80
            },
            {
                "product_id": "prod_004",
                "title": "MagSafe 无线充电器",
                "price": 329,
                "image_url": "",
                "link": "",
                "stock": 500
            }
        ]
    
    async def get_statistics(self, room_id: str) -> Dict[str, Any]:
        """模拟获取统计数据"""
        logger.info(f"🤖 [模拟] 获取统计数据")
        
        return {
            "online_count": 5678,
            "danmaku_count": 1234,
            "gift_count": 456,
            "like_count": 8901,
            "product_view_count": 3456,
            "order_count": 234
        }
