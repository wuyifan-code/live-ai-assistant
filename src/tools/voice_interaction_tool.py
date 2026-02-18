"""
语音交互工具
TTS语音输出、个性化话术引擎
"""

import logging
import asyncio
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import os

from coze_coding_dev_sdk import TTSClient
from coze_coding_utils.runtime_ctx.context import new_context

logger = logging.getLogger(__name__)


class VoicePersonality(Enum):
    """语音人格类型"""
    PROFESSIONAL = "professional"      # 专业理性的参数专家
    ENTHUSIASTIC = "enthusiastic"      # 热情幽默的福利官
    CARING = "caring"                  # 温柔体贴的客服姐姐
    WITTY = "witty"                    # 机智风趣的导购
    CALM = "calm"                      # 沉稳大气的品牌顾问


class LiveStreamMood(Enum):
    """直播间氛围"""
    EXCITING = "exciting"              # 热闹兴奋（促销、秒杀）
    RELAXED = "relaxed"                # 轻松悠闲（日常聊天）
    INTENSE = "intense"                # 紧张激烈（限时抢购）
    WARM = "warm"                      # 温馨舒适（情感交流）
    SERIOUS = "serious"                # 严肃正式（投诉处理）


@dataclass
class VoiceConfig:
    """语音配置"""
    speaker: str
    speech_rate: int = 0
    loudness_rate: int = 0
    style: str = "normal"


# 人格配置映射
PERSONALITY_CONFIGS = {
    VoicePersonality.PROFESSIONAL: VoiceConfig(
        speaker="zh_male_dayi_saturn_bigtts",  # 大毅，专业男声
        speech_rate=-10,  # 稍慢，稳重
        loudness_rate=0,
        style="professional"
    ),
    VoicePersonality.ENTHUSIASTIC: VoiceConfig(
        speaker="zh_female_jitangnv_saturn_bigtts",  # 激情女声
        speech_rate=20,  # 快速，激情
        loudness_rate=10,
        style="enthusiastic"
    ),
    VoicePersonality.CARING: VoiceConfig(
        speaker="zh_female_meilinvyou_saturn_bigtts",  # 温柔女友
        speech_rate=-5,  # 稍慢，温柔
        loudness_rate=-5,
        style="caring"
    ),
    VoicePersonality.WITTY: VoiceConfig(
        speaker="saturn_zh_female_tiaopigongzhu_tob",  # 俏皮公主
        speech_rate=15,  # 稍快，俏皮
        loudness_rate=5,
        style="witty"
    ),
    VoicePersonality.CALM: VoiceConfig(
        speaker="zh_male_ruyayichen_saturn_bigtts",  # 儒雅男声
        speech_rate=-15,  # 慢，沉稳
        loudness_rate=0,
        style="calm"
    )
}


class PersonalityEngine:
    """个性化话术引擎"""
    
    def __init__(self, default_personality: VoicePersonality = VoicePersonality.ENTHUSIASTIC):
        """
        参数:
            default_personality: 默认人格
        """
        self.default_personality = default_personality
        self.current_personality = default_personality
        self.mood_history = []
    
    def detect_mood_from_context(
        self,
        danmaku_density: float = 0,
        sentiment_score: float = 0.5,
        has_promotion: bool = False,
        has_complaint: bool = False
    ) -> LiveStreamMood:
        """
        从上下文检测直播间氛围
        
        参数:
            danmaku_density: 弹幕密度（条/秒）
            sentiment_score: 情感分数（0-1，1为最积极）
            has_promotion: 是否有促销活动
            has_complaint: 是否有投诉
        
        返回:
            检测到的氛围
        """
        # 有投诉，严肃氛围
        if has_complaint:
            return LiveStreamMood.SERIOUS
        
        # 有促销且弹幕密度高，热闹氛围
        if has_promotion and danmaku_density > 2:
            return LiveStreamMood.EXCITING
        
        # 有促销但密度一般，紧张氛围
        if has_promotion:
            return LiveStreamMood.INTENSE
        
        # 弹幕少且情感积极，轻松氛围
        if danmaku_density < 0.5 and sentiment_score > 0.6:
            return LiveStreamMood.RELAXED
        
        # 情感积极且互动多，温馨氛围
        if sentiment_score > 0.7 and danmaku_density > 1:
            return LiveStreamMood.WARM
        
        # 默认轻松
        return LiveStreamMood.RELAXED
    
    def select_personality(self, mood: LiveStreamMood) -> VoicePersonality:
        """
        根据氛围选择人格
        
        参数:
            mood: 直播间氛围
        
        返回:
            选择的人格
        """
        # 氛围-人格映射
        mood_personality_map = {
            LiveStreamMood.EXCITING: VoicePersonality.ENTHUSIASTIC,
            LiveStreamMood.RELAXED: VoicePersonality.CARING,
            LiveStreamMood.INTENSE: VoicePersonality.WITTY,
            LiveStreamMood.WARM: VoicePersonality.CARING,
            LiveStreamMood.SERIOUS: VoicePersonality.PROFESSIONAL
        }
        
        return mood_personality_map.get(mood, self.default_personality)
    
    def transform_response(
        self,
        response: str,
        personality: VoicePersonality = None
    ) -> str:
        """
        根据人格转换回复话术
        
        参数:
            response: 原始回复
            personality: 人格（可选，默认使用当前人格）
        
        返回:
            转换后的话术
        """
        if personality is None:
            personality = self.current_personality
        
        # 根据人格添加语气词和表情
        style_additions = {
            VoicePersonality.PROFESSIONAL: {
                "prefix": "",
                "suffix": "",
                "connectors": ["首先", "其次", "另外"]
            },
            VoicePersonality.ENTHUSIASTIC: {
                "prefix": "哇，",
                "suffix": "！太棒了！",
                "connectors": ["而且", "再加上", "还有哦"]
            },
            VoicePersonality.CARING: {
                "prefix": "",
                "suffix": "呢~",
                "connectors": ["而且呢", "另外", "还有"]
            },
            VoicePersonality.WITTY: {
                "prefix": "",
                "suffix": "哈~",
                "connectors": ["话说", "对了", "顺便说"]
            },
            VoicePersonality.CALM: {
                "prefix": "",
                "suffix": "。",
                "connectors": ["首先", "其次", "此外"]
            }
        }
        
        additions = style_additions.get(personality, style_additions[self.default_personality])
        
        # 如果是短回复，直接添加前后缀
        if len(response) < 50:
            return f"{additions['prefix']}{response}{additions['suffix']}"
        
        # 长回复，保持原样（由LLM生成时已经考虑人格）
        return response
    
    def get_voice_config(self, personality: VoicePersonality = None) -> VoiceConfig:
        """
        获取人格对应的语音配置
        
        参数:
            personality: 人格
        
        返回:
            语音配置
        """
        if personality is None:
            personality = self.current_personality
        
        return PERSONALITY_CONFIGS.get(personality, PERSONALITY_CONFIGS[self.default_personality])


class TTSVoiceOutput:
    """TTS语音输出"""
    
    def __init__(self):
        self.tts_client = TTSClient(ctx=new_context(method="tts_output"))
        self.personality_engine = PersonalityEngine()
        self.total_outputs = 0
        self.total_duration = 0
    
    async def synthesize_response(
        self,
        text: str,
        personality: VoicePersonality = None,
        output_format: str = "mp3",
        save_to_file: bool = False,
        output_path: str = None
    ) -> Dict[str, Any]:
        """
        将回复合成为语音
        
        参数:
            text: 回复文本
            personality: 人格（可选）
            output_format: 输出格式（mp3/pcm/ogg_opus）
            save_to_file: 是否保存到文件
            output_path: 输出路径（可选）
        
        返回:
            包含音频URL和信息的字典
        """
        try:
            # 获取语音配置
            voice_config = self.personality_engine.get_voice_config(personality)
            
            # 转换话术
            styled_text = self.personality_engine.transform_response(text, personality)
            
            logger.info(f"🔊 合成语音: 人格={personality.value if personality else 'default'}")
            
            # 调用TTS
            audio_url, audio_size = self.tts_client.synthesize(
                uid=f"live_ai_{int(time.time())}",
                text=styled_text,
                speaker=voice_config.speaker,
                audio_format=output_format,
                sample_rate=24000,
                speech_rate=voice_config.speech_rate,
                loudness_rate=voice_config.loudness_rate
            )
            
            self.total_outputs += 1
            
            result = {
                "success": True,
                "audio_url": audio_url,
                "audio_size": audio_size,
                "text": styled_text,
                "personality": personality.value if personality else "default",
                "format": output_format
            }
            
            # 保存到文件
            if save_to_file:
                import requests
                
                audio_data = requests.get(audio_url).content
                
                if output_path is None:
                    output_path = f"/tmp/tts_output_{int(time.time())}.{output_format}"
                
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                
                result["local_path"] = output_path
                logger.info(f"💾 音频已保存: {output_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ TTS合成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def synthesize_batch(
        self,
        texts: List[str],
        personality: VoicePersonality = None
    ) -> List[Dict[str, Any]]:
        """
        批量合成语音
        
        参数:
            texts: 文本列表
            personality: 人格
        
        返回:
            结果列表
        """
        results = []
        
        for i, text in enumerate(texts, 1):
            logger.info(f"🔊 批量合成 {i}/{len(texts)}")
            
            result = await self.synthesize_response(
                text=text,
                personality=personality,
                save_to_file=True,
                output_path=f"/tmp/tts_batch_{i}.mp3"
            )
            
            results.append(result)
            
            # 避免请求过快
            await asyncio.sleep(0.5)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_outputs": self.total_outputs,
            "total_duration": self.total_duration
        }


# 全局实例
tts_output = TTSVoiceOutput()
personality_engine = PersonalityEngine()


def get_voice_output() -> TTSVoiceOutput:
    """获取TTS输出实例"""
    return tts_output


def get_personality_engine() -> PersonalityEngine:
    """获取人格引擎实例"""
    return personality_engine


# 便捷函数
async def speak(text: str, personality: VoicePersonality = None) -> Dict[str, Any]:
    """
    快捷语音合成函数
    
    参数:
        text: 要合成的文本
        personality: 人格
    
    返回:
        合成结果
    """
    return await tts_output.synthesize_response(text, personality)
