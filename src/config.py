"""
配置管理模块
统一管理项目配置
"""
import os
from typing import Optional


class Config:
    """配置管理类"""
    
    def __init__(self):
        # 抖音直播小玩法配置
        self.app_id: str = os.getenv("DOUYIN_APP_ID", "")
        self.app_secret: str = os.getenv("DOUYIN_APP_SECRET", "")
        self.mini_game_id: str = os.getenv("DOUYIN_MINI_GAME_ID", "")
        self.test_room_id: str = os.getenv("DOUYIN_TEST_ROOM_ID", "")
        
        # 日志配置
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    def is_complete(self) -> bool:
        """
        检查配置是否完整
        
        返回:
            True 如果配置完整
        """
        return all([
            self.app_id,
            self.app_secret,
            self.mini_game_id,
            self.test_room_id
        ])
    
    def get_missing_configs(self) -> list:
        """
        获取缺失的配置项
        
        返回:
            缺失的配置项列表
        """
        missing = []
        
        if not self.app_id:
            missing.append("DOUYIN_APP_ID")
        if not self.app_secret:
            missing.append("DOUYIN_APP_SECRET")
        if not self.mini_game_id:
            missing.append("DOUYIN_MINI_GAME_ID")
        if not self.test_room_id:
            missing.append("DOUYIN_TEST_ROOM_ID")
        
        return missing
    
    def summary(self) -> str:
        """返回配置摘要（不包含敏感信息）"""
        return f"""
📋 配置摘要:
- App ID: {self.app_id[:10]}...{self.app_id[-5:] if self.app_id else '(未设置)'}
- App Secret: {'******' if self.app_secret else '(未设置)'}
- 小游戏ID: {self.mini_game_id or '(未设置)'}
- 测试直播间ID: {self.test_room_id or '(未设置)'}
- 配置完整: {'✅' if self.is_complete() else '❌'}
"""


# 全局配置实例
config = Config()


def load_env_file(env_file: str = ".env"):
    """
    从.env文件加载配置
    
    参数:
        env_file: .env文件路径
    """
    if not os.path.exists(env_file):
        return
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if value and not os.getenv(key):
                        os.environ[key] = value
        
        print(f"✅ 已从 {env_file} 加载配置")
        
    except Exception as e:
        print(f"⚠️ 加载配置文件失败: {e}")
