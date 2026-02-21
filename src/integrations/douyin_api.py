"""
抖音开放平台API工具
完整的直播间管理功能
"""

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class DouyinLiveAPI:
    """
    抖音直播API客户端
    
    文档: https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/live
    """
    
    API_BASE = "https://developer.toutiao.com"
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        """
        参数:
            app_id: 应用ID（从环境变量或参数获取）
            app_secret: 应用密钥
        """
        self.app_id = app_id or os.getenv("DOUYIN_APP_ID")
        self.app_secret = app_secret or os.getenv("DOUYIN_APP_SECRET")
        
        self.access_token = None
        self.token_expires_at = 0
        
        if not self.app_id or not self.app_secret:
            logger.warning("⚠️ 抖音API凭证未配置，请设置 DOUYIN_APP_ID 和 DOUYIN_APP_SECRET")
    
    async def get_access_token(self) -> str:
        """
        获取access_token
        
        返回:
            access_token字符串
        """
        # 检查缓存的token
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            logger.info("🔑 获取抖音API access_token...")
            
            url = f"{self.API_BASE}/api/apps/v2/token"
            
            data = {
                "appid": self.app_id,
                "secret": self.app_secret,
                "grant_type": "client_credential"
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                self.access_token = result["data"]["access_token"]
                # 提前5分钟过期
                self.token_expires_at = time.time() + result["data"]["expires_in"] - 300
                
                logger.info("✅ access_token获取成功")
                return self.access_token
            else:
                raise Exception(f"获取token失败: {result.get('err_msg', '未知错误')}")
                
        except Exception as e:
            logger.error(f"❌ 获取access_token失败: {str(e)}")
            raise
    
    async def get_room_id_by_url(self, room_url: str) -> str:
        """
        根据直播间URL获取直播间ID
        
        参数:
            room_url: 直播间URL（如: https://live.douyin.com/123456789）
        
        返回:
            直播间ID
        """
        try:
            token = await self.get_access_token()
            
            # 从URL中提取room_id
            # 格式: https://live.douyin.com/{room_id}
            if "live.douyin.com" in room_url:
                room_id = room_url.split("/")[-1].split("?")[0]
                logger.info(f"📍 从URL提取直播间ID: {room_id}")
                return room_id
            
            # 如果无法从URL提取，调用API查询
            url = f"{self.API_BASE}/api/live/v1/room/info"
            
            headers = {"access-token": token}
            params = {"room_url": room_url}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                room_id = result["data"]["room_id"]
                logger.info(f"📍 API查询直播间ID: {room_id}")
                return room_id
            else:
                raise Exception(f"获取直播间ID失败: {result}")
                
        except Exception as e:
            logger.error(f"❌ 获取直播间ID失败: {str(e)}")
            raise
    
    async def get_room_info(self, room_id: str) -> Dict[str, Any]:
        """
        获取直播间详细信息
        
        参数:
            room_id: 直播间ID
        
        返回:
            直播间信息字典
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/info"
            
            headers = {"access-token": token}
            params = {"room_id": room_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                data = result["data"]
                
                return {
                    "room_id": room_id,
                    "title": data.get("title", ""),
                    "status": data.get("status", 0),  # 0-未开播, 1-直播中, 2-已结束
                    "status_text": self._get_status_text(data.get("status", 0)),
                    "viewer_count": data.get("online_count", 0),
                    "like_count": data.get("like_count", 0),
                    "anchor": {
                        "id": data.get("anchor_id", ""),
                        "name": data.get("anchor_name", ""),
                        "avatar": data.get("anchor_avatar", "")
                    },
                    "cover_url": data.get("cover_url", ""),
                    "stream_url": data.get("stream_url", ""),
                    "start_time": data.get("create_time", ""),
                    "tags": data.get("tags", [])
                }
            else:
                raise Exception(f"获取直播间信息失败: {result}")
                
        except Exception as e:
            logger.error(f"❌ 获取直播间信息失败: {str(e)}")
            return {}
    
    async def get_danmaku_list(
        self,
        room_id: str,
        count: int = 100,
        cursor: str = "0"
    ) -> List[Dict[str, Any]]:
        """
        获取直播间弹幕列表
        
        参数:
            room_id: 直播间ID
            count: 获取数量（默认100）
            cursor: 游标（用于分页）
        
        返回:
            弹幕列表
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/danmaku"
            
            headers = {"access-token": token}
            params = {
                "room_id": room_id,
                "count": count,
                "cursor": cursor
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                danmaku_list = []
                
                for item in result["data"].get("list", []):
                    danmaku_list.append({
                        "user_id": item.get("user_id", ""),
                        "username": item.get("nickname", "匿名用户"),
                        "content": item.get("content", ""),
                        "timestamp": item.get("timestamp", ""),
                        "type": "danmaku"
                    })
                
                return danmaku_list
            else:
                logger.warning(f"获取弹幕失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取弹幕列表失败: {str(e)}")
            return []
    
    async def get_product_list(self, room_id: str) -> List[Dict[str, Any]]:
        """
        获取直播间商品列表
        
        参数:
            room_id: 直播间ID
        
        返回:
            商品列表
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/product"
            
            headers = {"access-token": token}
            params = {"room_id": room_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                products = []
                
                for item in result["data"].get("list", []):
                    products.append({
                        "product_id": item.get("product_id", ""),
                        "name": item.get("name", ""),
                        "price": float(item.get("price", 0)) / 100,  # 转换为元
                        "original_price": float(item.get("original_price", 0)) / 100,
                        "stock": item.get("stock", 0),
                        "image_url": item.get("image_url", ""),
                        "status": item.get("status", 0)  # 0-未上架, 1-上架中
                    })
                
                return products
            else:
                logger.warning(f"获取商品列表失败: {result}")
                return []
                
        except Exception as e:
            logger.error(f"❌ 获取商品列表失败: {str(e)}")
            return []
    
    async def send_message(
        self,
        room_id: str,
        message: str,
        message_type: str = "text"
    ) -> bool:
        """
        发送消息到抖音直播间
        
        API端点: POST /live/chat/send
        
        参数:
            room_id: 直播间ID
            message: 消息内容
            message_type: 消息类型（text/image）
        
        返回:
            是否发送成功
        
        示例:
            >>> success = await api.send_message("room_001", "欢迎来到直播间！")
            >>> print(success)
            True
        """
        try:
            token = await self.get_access_token()
            
            # API端点
            url = f"{self.API_BASE}/live/chat/send"
            
            headers = {"access-token": token}
            
            data = {
                "room_id": room_id,
                "content": message,
                "msg_type": message_type
            }
            
            logger.info(f"📤 发送消息到直播间 {room_id}: {message[:30]}...")
            
            response = requests.post(
                url,
                headers=headers,
                json=data,
                timeout=10
            )
            
            result = response.json()
            
            # 检查响应
            if result.get("err_no") == 0:
                logger.info(f"✅ 消息发送成功")
                return True
            else:
                err_msg = result.get("err_msg", "未知错误")
                err_no = result.get("err_no", -1)
                
                # 常见错误码处理
                error_messages = {
                    10001: "参数错误",
                    10002: "token无效或过期",
                    10003: "权限不足",
                    10004: "直播间不存在",
                    10005: "直播间未开播",
                    10006: "消息内容违规",
                    10007: "发送频率超限",
                    10008: "消息过长（最大200字符）"
                }
                
                error_desc = error_messages.get(err_no, err_msg)
                logger.warning(f"消息发送失败 [{err_no}]: {error_desc}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ 发送消息超时")
            return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 网络请求失败: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ 发送消息失败: {str(e)}")
            return False
    
    async def get_room_stats(self, room_id: str) -> Dict[str, Any]:
        """
        获取直播间统计数据
        
        参数:
            room_id: 直播间ID
        
        返回:
            统计数据
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/stats"
            
            headers = {"access-token": token}
            params = {"room_id": room_id}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            result = response.json()
            
            if result.get("err_no") == 0:
                data = result["data"]
                
                return {
                    "total_viewers": data.get("total_viewers", 0),
                    "peak_viewers": data.get("peak_viewers", 0),
                    "total_likes": data.get("total_likes", 0),
                    "total_gift_value": data.get("total_gift_value", 0),
                    "total_sales": data.get("total_sales", 0),
                    "duration": data.get("duration", 0)
                }
            else:
                return {}
                
        except Exception as e:
            logger.error(f"❌ 获取统计数据失败: {str(e)}")
            return {}
    
    def _get_status_text(self, status: int) -> str:
        """获取状态文本"""
        status_map = {
            0: "未开播",
            1: "直播中",
            2: "已结束"
        }
        return status_map.get(status, "未知")


# 全局实例
douyin_api: Optional[DouyinLiveAPI] = None


def get_douyin_api() -> DouyinLiveAPI:
    """获取抖音API实例"""
    global douyin_api
    
    if douyin_api is None:
        douyin_api = DouyinLiveAPI()
    
    return douyin_api


# ==================== 使用示例 ====================

async def example_usage():
    """使用示例"""
    api = DouyinLiveAPI()
    
    # 1. 根据URL获取直播间ID
    room_url = "https://live.douyin.com/123456789"
    room_id = await api.get_room_id_by_url(room_url)
    print(f"直播间ID: {room_id}")
    
    # 2. 获取直播间信息
    room_info = await api.get_room_info(room_id)
    print(f"直播间信息: {json.dumps(room_info, ensure_ascii=False, indent=2)}")
    
    # 3. 获取弹幕列表
    danmaku_list = await api.get_danmaku_list(room_id, count=50)
    for danmaku in danmaku_list:
        print(f"[{danmaku['username']}]: {danmaku['content']}")
    
    # 4. 发送消息
    await api.send_message(room_id, "欢迎来到直播间！")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
