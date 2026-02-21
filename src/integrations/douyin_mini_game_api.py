"""
抖音直播小玩法 API 集成
适配个人开发者场景
"""
import os
import time
import json
import hashlib
import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DouyinMiniGameAPI:
    """
    抖音直播小玩法 API 客户端
    适配个人开发者场景
    """
    
    def __init__(self):
        self.app_id = os.getenv("DOUYIN_APP_ID", "")
        self.app_secret = os.getenv("DOUYIN_APP_SECRET", "")
        self.mini_game_id = os.getenv("DOUYIN_MINI_GAME_ID", "")
        
        self.base_url = "https://mini-game.douyin.com"
        self.access_token = None
        self.token_expires_at = 0
        
        logger.info("🎮 抖音直播小玩法API初始化完成")
    
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """
        生成签名（直播小玩法使用签名机制）
        
        参数:
            params: 请求参数字典
        
        返回:
            签名字符串
        """
        # 1. 参数按字典序排序
        sorted_params = sorted(params.items())
        
        # 2. 拼接参数
        param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        
        # 3. 添加密钥
        sign_str = f"{param_str}&key={self.app_secret}"
        
        # 4. MD5加密
        sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()
        
        return sign
    
    async def get_access_token(self) -> str:
        """
        获取访问令牌（直播小玩法方式）
        
        返回:
            access_token
        """
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        url = f"{self.base_url}/api/apps/v2/token"
        
        params = {
            "appid": self.app_id,
            "secret": self.app_secret,
            "grant_type": "client_credential"
        }
        
        # 生成签名
        params["sign"] = self._generate_sign(params)
        
        try:
            response = requests.post(url, json=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                self.access_token = result["access_token"]
                self.token_expires_at = time.time() + result.get("expires_in", 7200) - 300
                
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
        
        url = f"{self.base_url}/api/live/v2/room/info"
        
        params = {
            "access_token": token,
            "room_id": room_id
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
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
    
    async def get_danmaku_list(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取弹幕列表
        
        参数:
            room_id: 直播间ID
            limit: 获取数量
        
        返回:
            弹幕列表
        """
        token = await self.get_access_token()
        
        url = f"{self.base_url}/api/live/v2/danmaku/list"
        
        params = {
            "access_token": token,
            "room_id": room_id,
            "limit": limit
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                danmaku_list = result.get("data", {}).get("list", [])
                
                logger.info(f"✅ 获取到 {len(danmaku_list)} 条弹幕")
                
                formatted_list = []
                for danmaku in danmaku_list:
                    formatted_list.append({
                        "user_id": danmaku.get("user_id", ""),
                        "username": danmaku.get("nickname", ""),
                        "content": danmaku.get("content", ""),
                        "timestamp": danmaku.get("timestamp", int(time.time() * 1000))
                    })
                
                return formatted_list
            else:
                logger.error(f"❌ 获取弹幕列表失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取弹幕列表异常: {str(e)}")
            return []
    
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
        
        url = f"{self.base_url}/api/live/v2/danmaku/send"
        
        data = {
            "access_token": token,
            "room_id": room_id,
            "content": content,
            "mini_game_id": self.mini_game_id
        }
        
        data["sign"] = self._generate_sign(data)
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"📤 消息发送成功: {content}")
                return True
            else:
                logger.error(f"❌ 消息发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送消息异常: {str(e)}")
            return False
    
    async def get_gift_list(self, room_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取礼物列表
        
        参数:
            room_id: 直播间ID
            limit: 获取数量
        
        返回:
            礼物列表
        """
        token = await self.get_access_token()
        
        url = f"{self.base_url}/api/live/v2/gift/list"
        
        params = {
            "access_token": token,
            "room_id": room_id,
            "limit": limit
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                gift_list = result.get("data", {}).get("list", [])
                
                logger.info(f"✅ 获取到 {len(gift_list)} 条礼物记录")
                
                formatted_list = []
                for gift in gift_list:
                    formatted_list.append({
                        "user_id": gift.get("user_id", ""),
                        "username": gift.get("nickname", ""),
                        "gift_name": gift.get("gift_name", ""),
                        "gift_count": gift.get("count", 1),
                        "gift_value": gift.get("value", 0),
                        "timestamp": gift.get("timestamp", int(time.time() * 1000))
                    })
                
                return formatted_list
            else:
                logger.error(f"❌ 获取礼物列表失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取礼物列表异常: {str(e)}")
            return []
    
    async def get_product_list(self, room_id: str) -> List[Dict[str, Any]]:
        """
        获取直播间商品列表
        
        参数:
            room_id: 直播间ID
        
        返回:
            商品列表
        """
        token = await self.get_access_token()
        
        url = f"{self.base_url}/api/live/v2/product/list"
        
        params = {
            "access_token": token,
            "room_id": room_id
        }
        
        params["sign"] = self._generate_sign(params)
        
        try:
            response = requests.get(url, params=params, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
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
    
    async def send_product_card(self, room_id: str, product_id: str, 
                                text: str = "") -> bool:
        """
        发送商品卡片
        
        参数:
            room_id: 直播间ID
            product_id: 商品ID
            text: 附文
        
        返回:
            是否发送成功
        """
        token = await self.get_access_token()
        
        url = f"{self.base_url}/api/live/v2/product/card"
        
        data = {
            "access_token": token,
            "room_id": room_id,
            "product_id": product_id,
            "text": text,
            "mini_game_id": self.mini_game_id
        }
        
        data["sign"] = self._generate_sign(data)
        
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("errcode") == 0:
                logger.info(f"🛒 商品卡片发送成功: {product_id}")
                return True
            else:
                logger.error(f"❌ 商品卡片发送失败: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 发送商品卡片异常: {str(e)}")
            return False


# 模拟数据版本（用于开发测试）
class MockDouyinMiniGameAPI(DouyinMiniGameAPI):
    """
    模拟直播小玩法API（用于开发测试）
    """
    
    async def get_access_token(self) -> str:
        """模拟获取token"""
        return "mock_token_12345"
    
    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """模拟获取直播间信息"""
        logger.info(f"🎮 [模拟] 获取直播间信息: {room_id}")
        return {
            "room_id": room_id,
            "title": "测试直播间 - 直播带货AI助手",
            "anchor_name": "测试主播",
            "online_count": 1234,
            "status": "live"
        }
    
    async def get_danmaku_list(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """模拟获取弹幕"""
        logger.info(f"🎮 [模拟] 获取弹幕列表")
        import random
        from datetime import datetime, timedelta
        
        users = ["小明", "小红", "张三", "李四", "王五"]
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
            "能便宜点吗？"
        ]
        
        danmaku_list = []
        for i in range(min(limit, 10)):
            danmaku_list.append({
                "user_id": f"user_{i}",
                "username": random.choice(users),
                "content": random.choice(messages),
                "timestamp": int((datetime.now() - timedelta(minutes=i)).timestamp() * 1000)
            })
        
        return danmaku_list
    
    async def send_message(self, room_id: str, content: str) -> bool:
        """模拟发送消息"""
        logger.info(f"📤 [模拟] 发送消息: {content}")
        return True
    
    async def get_gift_list(self, room_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """模拟获取礼物"""
        logger.info(f"🎁 [模拟] 获取礼物列表")
        import random
        
        users = ["粉丝A", "粉丝B", "粉丝C", "粉丝D", "粉丝E"]
        gifts = ["爱心", "火箭", "抖音一号", "嘉年华", "小心心", "热气球"]
        
        gift_list = []
        for i in range(min(limit, 5)):
            gift_name = random.choice(gifts)
            count = random.randint(1, 10)
            
            gift_list.append({
                "user_id": f"gift_user_{i}",
                "username": random.choice(users),
                "gift_name": gift_name,
                "gift_count": count,
                "gift_value": count * (10 if gift_name in ["爱心", "小心心"] else 100),
                "timestamp": int(time.time() * 1000)
            })
        
        return gift_list
    
    async def get_product_list(self, room_id: str) -> List[Dict[str, Any]]:
        """模拟获取商品列表"""
        logger.info(f"🛒 [模拟] 获取商品列表")
        
        return [
            {
                "product_id": "prod_001",
                "title": "iPhone 15 Pro 256GB",
                "price": 7999,
                "image_url": "",
                "link": "",
                "stock": 50
            },
            {
                "product_id": "prod_002",
                "title": "无线蓝牙耳机",
                "price": 299,
                "image_url": "",
                "link": "",
                "stock": 200
            },
            {
                "product_id": "prod_003",
                "title": "智能手表",
                "price": 1299,
                "image_url": "",
                "link": "",
                "stock": 30
            }
        ]
