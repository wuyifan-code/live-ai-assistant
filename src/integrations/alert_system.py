"""
告警通知系统
集成飞书和企业微信机器人
"""

import logging
import asyncio
import time
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import os

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """告警渠道"""
    FEISHU = "feishu"
    WECOM = "wecom"
    BOTH = "both"


class AlertManager:
    """
    告警管理器
    
    支持飞书和企业微信机器人通知
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        参数:
            config: 配置字典
        """
        self.config = config or {
            "feishu_webhook": os.getenv("FEISHU_WEBHOOK_URL"),
            "wecom_webhook": os.getenv("WECOM_WEBHOOK_URL"),
            "alert_cooldown": 300,  # 相同告警冷却时间(秒)
        }
        
        # 告警历史（用于去重）
        self.alert_history: Dict[str, float] = {}
        
        # 告警计数（统计）
        self.alert_counts = {
            AlertLevel.INFO: 0,
            AlertLevel.WARNING: 0,
            AlertLevel.ERROR: 0,
            AlertLevel.CRITICAL: 0
        }
    
    def _get_feishu_webhook(self) -> str:
        """获取飞书webhook URL"""
        try:
            from coze_workload_identity import Client
            client = Client()
            credential = client.get_integration_credential("integration-feishu-message")
            return json.loads(credential)["webhook_url"]
        except:
            return self.config.get("feishu_webhook", "")
    
    def _send_feishu_text(self, message: str, level: AlertLevel) -> bool:
        """
        发送飞书文本消息
        
        参数:
            message: 消息内容
            level: 告警级别
        
        返回:
            是否成功
        """
        try:
            webhook_url = self._get_feishu_webhook()
            
            if not webhook_url:
                logger.warning("⚠️ 飞书webhook未配置")
                return False
            
            # 根据级别添加emoji
            emoji_map = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }
            
            emoji = emoji_map.get(level, "ℹ️")
            
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"{emoji} 【直播助手告警】\n\n{message}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("✅ 飞书告警发送成功")
                return True
            else:
                logger.error(f"❌ 飞书告警发送失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 飞书告警发送异常: {str(e)}")
            return False
    
    def _send_feishu_card(self, title: str, content: str, level: AlertLevel) -> bool:
        """
        发送飞书卡片消息
        
        参数:
            title: 标题
            content: 内容
            level: 告警级别
        
        返回:
            是否成功
        """
        try:
            webhook_url = self._get_feishu_webhook()
            
            if not webhook_url:
                return False
            
            # 根据级别设置颜色
            color_map = {
                AlertLevel.INFO: "blue",
                AlertLevel.WARNING: "yellow",
                AlertLevel.ERROR: "red",
                AlertLevel.CRITICAL: "red"
            }
            
            color = color_map.get(level, "blue")
            
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": color
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": content
                            }
                        },
                        {
                            "tag": "div",
                            "text": {
                                "tag": "plain_text",
                                "content": f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        }
                    ]
                }
            }
            
            response = requests.post(webhook_url, json=payload)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ 飞书卡片发送异常: {str(e)}")
            return False
    
    def _send_wecom_text(self, message: str, level: AlertLevel) -> bool:
        """
        发送企业微信文本消息
        
        参数:
            message: 消息内容
            level: 告警级别
        
        返回:
            是否成功
        """
        try:
            webhook_url = self.config.get("wecom_webhook")
            
            if not webhook_url:
                logger.warning("⚠️ 企业微信webhook未配置")
                return False
            
            # 根据级别添加emoji
            emoji_map = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }
            
            emoji = emoji_map.get(level, "ℹ️")
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"{emoji} 【直播助手告警】\n\n{message}\n\n时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            response = requests.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                logger.info("✅ 企业微信告警发送成功")
                return True
            else:
                logger.error(f"❌ 企业微信告警发送失败: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 企业微信告警发送异常: {str(e)}")
            return False
    
    def _send_wecom_markdown(self, title: str, content: str, level: AlertLevel) -> bool:
        """
        发送企业微信Markdown消息
        
        参数:
            title: 标题
            content: 内容
            level: 告警级别
        
        返回:
            是否成功
        """
        try:
            webhook_url = self.config.get("wecom_webhook")
            
            if not webhook_url:
                return False
            
            # 添加颜色标记
            color_map = {
                AlertLevel.INFO: "🔵",
                AlertLevel.WARNING: "🟡",
                AlertLevel.ERROR: "🔴",
                AlertLevel.CRITICAL: "🔴"
            }
            
            color = color_map.get(level, "🔵")
            
            markdown_content = f"# {color} {title}\n\n{content}\n\n> 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": markdown_content
                }
            }
            
            response = requests.post(webhook_url, json=payload)
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"❌ 企业微信Markdown发送异常: {str(e)}")
            return False
    
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.WARNING,
        channel: AlertChannel = AlertChannel.BOTH,
        deduplicate: bool = True
    ) -> Dict[str, bool]:
        """
        发送告警
        
        参数:
            message: 消息内容
            level: 告警级别
            channel: 告警渠道
            deduplicate: 是否去重
        
        返回:
            {"feishu": bool, "wecom": bool}
        """
        # 去重检查
        if deduplicate:
            message_key = f"{level.value}:{message}"
            now = time.time()
            
            if message_key in self.alert_history:
                last_sent = self.alert_history[message_key]
                if now - last_sent < self.config["alert_cooldown"]:
                    logger.info(f"⏭️ 告警已去重: {message[:30]}...")
                    return {"feishu": False, "wecom": False, "reason": "duplicate"}
            
            self.alert_history[message_key] = now
        
        # 更新计数
        self.alert_counts[level] += 1
        
        # 发送消息
        results = {}
        
        if channel in [AlertChannel.FEISHU, AlertChannel.BOTH]:
            results["feishu"] = self._send_feishu_text(message, level)
        
        if channel in [AlertChannel.WECOM, AlertChannel.BOTH]:
            results["wecom"] = self._send_wecom_text(message, level)
        
        return results
    
    def send_alert_card(
        self,
        title: str,
        content: str,
        level: AlertLevel = AlertLevel.WARNING,
        channel: AlertChannel = AlertChannel.BOTH
    ) -> Dict[str, bool]:
        """
        发送卡片告警
        
        参数:
            title: 标题
            content: 内容
            level: 告警级别
            channel: 告警渠道
        
        返回:
            {"feishu": bool, "wecom": bool}
        """
        results = {}
        
        if channel in [AlertChannel.FEISHU, AlertChannel.BOTH]:
            results["feishu"] = self._send_feishu_card(title, content, level)
        
        if channel in [AlertChannel.WECOM, AlertChannel.BOTH]:
            results["wecom"] = self._send_wecom_markdown(title, content, level)
        
        return results
    
    def send_live_assistant_alert(
        self,
        alert_type: str,
        details: Dict[str, Any],
        level: AlertLevel = AlertLevel.WARNING
    ):
        """
        发送直播助手专用告警
        
        参数:
            alert_type: 告警类型
            details: 详情
            level: 告警级别
        """
        # 构建告警内容
        if alert_type == "human_takeover":
            title = "🚨 人工接管告警"
            content = f"""**主播**: {details.get('anchor_name', '未知')}
**直播间**: {details.get('room_id', '未知')}
**触发原因**: {details.get('reason', '未知')}
**待处理消息**: {details.get('pending_message', '无')}

请及时登录后台处理！"""
        
        elif alert_type == "system_error":
            title = "❌ 系统异常告警"
            content = f"""**错误类型**: {details.get('error_type', '未知')}
**错误信息**: {details.get('error_msg', '无')}
**影响范围**: {details.get('impact', '未知')}

请立即检查系统状态！"""
        
        elif alert_type == "confidence_low":
            title = "⚠️ 置信度低告警"
            content = f"""**问题类型**: {details.get('query_type', '未知')}
**用户问题**: {details.get('user_query', '无')}
**当前置信度**: {details.get('confidence', 0):.2%}

建议审核话术库！"""
        
        elif alert_type == "api_rate_limit":
            title = "⚠️ API限流告警"
            content = f"""**API**: {details.get('api_name', '未知')}
**当前QPS**: {details.get('current_qps', 0)}
**限制QPS**: {details.get('limit_qps', 0)}

请注意调整请求频率！"""
        
        else:
            title = "ℹ️ 系统通知"
            content = str(details)
        
        # 发送卡片告警
        self.send_alert_card(title, content, level)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        return {
            "alert_counts": {
                level.value: count 
                for level, count in self.alert_counts.items()
            },
            "alert_history_size": len(self.alert_history)
        }


# 全局实例
alert_manager: Optional[AlertManager] = None


def init_alert_manager(config: Dict[str, Any] = None):
    """
    初始化告警管理器
    
    参数:
        config: 配置字典
    """
    global alert_manager
    alert_manager = AlertManager(config)
    logger.info("✅ 告警管理器初始化成功")


def get_alert_manager() -> Optional[AlertManager]:
    """获取告警管理器实例"""
    return alert_manager
