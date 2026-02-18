"""
直播平台API集成
支持抖音、快手、淘宝直播平台
"""

import logging
import asyncio
import time
import hashlib
import hmac
import base64
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlencode
import aiohttp

logger = logging.getLogger(__name__)


class LiveStreamPlatformAPI:
    """
    直播平台API基类
    """
    
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = None
        self.token_expires_at = 0
    
    async def get_access_token(self) -> str:
        """获取访问令牌（子类实现）"""
        raise NotImplementedError
    
    async def get_live_room_info(self, room_id: str) -> Dict[str, Any]:
        """获取直播间信息（子类实现）"""
        raise NotImplementedError
    
    async def get_live_screenshot(self, room_id: str) -> str:
        """获取直播截图（子类实现）"""
        raise NotImplementedError
    
    async def get_danmaku_list(self, room_id: str) -> List[Dict]:
        """获取弹幕列表（子类实现）"""
        raise NotImplementedError


class DouyinLiveAPI(LiveStreamPlatformAPI):
    """
    抖音直播API
    
    文档: https://developer.open-douyin.com/
    """
    
    API_BASE = "https://developer.toutiao.com"
    
    async def get_access_token(self) -> str:
        """
        获取抖音访问令牌
        
        返回:
            access_token
        """
        # 检查缓存的token是否有效
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            url = f"{self.API_BASE}/api/apps/v2/token"
            
            data = {
                "appid": self.app_id,
                "secret": self.app_secret,
                "grant_type": "client_credential"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    
                    if result.get("err_no") == 0:
                        self.access_token = result["data"]["access_token"]
                        self.token_expires_at = time.time() + result["data"]["expires_in"] - 300
                        
                        logger.info("✅ 抖音API访问令牌获取成功")
                        
                        return self.access_token
                    else:
                        raise Exception(f"获取token失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 抖音API访问令牌获取失败: {str(e)}")
            raise
    
    async def get_live_room_info(self, room_id: str) -> Dict[str, Any]:
        """
        获取抖音直播间信息
        
        参数:
            room_id: 直播间ID
        
        返回:
            直播间信息
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/info"
            
            params = {
                "room_id": room_id
            }
            
            headers = {
                "access-token": token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    result = await response.json()
                    
                    if result.get("err_no") == 0:
                        return {
                            "room_id": room_id,
                            "title": result["data"].get("title"),
                            "status": result["data"].get("status"),
                            "viewer_count": result["data"].get("online_count", 0),
                            "anchor_name": result["data"].get("anchor_name"),
                            "cover_url": result["data"].get("cover_url"),
                            "stream_url": result["data"].get("stream_url")
                        }
                    else:
                        raise Exception(f"获取直播间信息失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 获取抖音直播间信息失败: {str(e)}")
            return {}
    
    async def get_live_screenshot(self, room_id: str) -> str:
        """
        获取抖音直播截图
        
        参数:
            room_id: 直播间ID
        
        返回:
            截图URL
        """
        try:
            room_info = await self.get_live_room_info(room_id)
            
            # 使用封面图作为截图
            # 实际项目中应该调用实时截图API
            return room_info.get("cover_url", "")
            
        except Exception as e:
            logger.error(f"❌ 获取直播截图失败: {str(e)}")
            return ""
    
    async def get_danmaku_list(self, room_id: str) -> List[Dict]:
        """
        获取抖音直播间弹幕
        
        参数:
            room_id: 直播间ID
        
        返回:
            弹幕列表
        """
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/api/live/v1/room/danmaku"
            
            params = {
                "room_id": room_id,
                "count": 100
            }
            
            headers = {
                "access-token": token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    result = await response.json()
                    
                    if result.get("err_no") == 0:
                        return [
                            {
                                "user_id": item.get("user_id"),
                                "username": item.get("nickname"),
                                "content": item.get("content"),
                                "timestamp": item.get("timestamp")
                            }
                            for item in result["data"].get("list", [])
                        ]
                    else:
                        raise Exception(f"获取弹幕失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 获取抖音弹幕失败: {str(e)}")
            return []


class KuaishouLiveAPI(LiveStreamPlatformAPI):
    """
    快手直播API
    
    文档: https://open.kuaishou.com/
    """
    
    API_BASE = "https://open.kuaishou.com/openapi"
    
    async def get_access_token(self) -> str:
        """获取快手访问令牌"""
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        try:
            url = f"{self.API_BASE}/oauth2/access_token"
            
            data = {
                "app_id": self.app_id,
                "app_secret": self.app_secret,
                "grant_type": "client_credentials"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    result = await response.json()
                    
                    if result.get("result") == 1:
                        self.access_token = result["data"]["access_token"]
                        self.token_expires_at = time.time() + result["data"]["expires_in"] - 300
                        
                        logger.info("✅ 快手API访问令牌获取成功")
                        
                        return self.access_token
                    else:
                        raise Exception(f"获取token失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 快手API访问令牌获取失败: {str(e)}")
            raise
    
    async def get_live_room_info(self, room_id: str) -> Dict[str, Any]:
        """获取快手直播间信息"""
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/live/info"
            
            params = {
                "liveRoomId": room_id
            }
            
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    result = await response.json()
                    
                    if result.get("result") == 1:
                        data = result["data"]
                        return {
                            "room_id": room_id,
                            "title": data.get("caption"),
                            "status": data.get("livingStatus"),
                            "viewer_count": data.get("watchingCount", 0),
                            "anchor_name": data.get("anchorName"),
                            "cover_url": data.get("coverUrl"),
                            "stream_url": data.get("playUrls")
                        }
                    else:
                        raise Exception(f"获取直播间信息失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 获取快手直播间信息失败: {str(e)}")
            return {}
    
    async def get_live_screenshot(self, room_id: str) -> str:
        """获取快手直播截图"""
        try:
            room_info = await self.get_live_room_info(room_id)
            return room_info.get("cover_url", "")
        except Exception as e:
            logger.error(f"❌ 获取直播截图失败: {str(e)}")
            return ""
    
    async def get_danmaku_list(self, room_id: str) -> List[Dict]:
        """获取快手直播间弹幕"""
        try:
            token = await self.get_access_token()
            
            url = f"{self.API_BASE}/live/danmaku"
            
            params = {
                "liveRoomId": room_id
            }
            
            headers = {
                "Authorization": f"Bearer {token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    result = await response.json()
                    
                    if result.get("result") == 1:
                        return [
                            {
                                "user_id": item.get("userId"),
                                "username": item.get("userName"),
                                "content": item.get("content"),
                                "timestamp": item.get("time")
                            }
                            for item in result["data"].get("list", [])
                        ]
                    else:
                        raise Exception(f"获取弹幕失败: {result}")
                        
        except Exception as e:
            logger.error(f"❌ 获取快手弹幕失败: {str(e)}")
            return []


class LiveStreamAPIFactory:
    """
    直播平台API工厂
    """
    
    @staticmethod
    def create_api(
        platform: str,
        app_id: str,
        app_secret: str
    ) -> LiveStreamPlatformAPI:
        """
        创建直播平台API实例
        
        参数:
            platform: 平台名称 (douyin / kuaishou / taobao)
            app_id: 应用ID
            app_secret: 应用密钥
        
        返回:
            API实例
        """
        platform = platform.lower()
        
        if platform == "douyin":
            return DouyinLiveAPI(app_id, app_secret)
        elif platform == "kuaishou":
            return KuaishouLiveAPI(app_id, app_secret)
        elif platform == "taobao":
            # 淘宝直播API类似实现
            raise NotImplementedError("淘宝直播API待实现")
        else:
            raise ValueError(f"不支持的平台: {platform}")


# 全局API实例（根据配置初始化）
live_api: Optional[LiveStreamPlatformAPI] = None


def init_live_api(platform: str, app_id: str, app_secret: str):
    """
    初始化直播API
    
    参数:
        platform: 平台名称
        app_id: 应用ID
        app_secret: 应用密钥
    """
    global live_api
    
    live_api = LiveStreamAPIFactory.create_api(platform, app_id, app_secret)
    
    logger.info(f"✅ 直播平台API初始化成功: {platform}")


def get_live_api() -> Optional[LiveStreamPlatformAPI]:
    """获取直播API实例"""
    return live_api
