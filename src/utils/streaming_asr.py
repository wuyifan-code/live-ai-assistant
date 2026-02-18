"""
流式ASR语音识别
实时将音频流转换为文本，降低延迟到3-5秒
"""

import asyncio
import logging
import queue
import time
from typing import Optional, Callable, Dict, Any
from collections import deque
from coze_coding_dev_sdk import ASRClient
from coze_coding_utils.runtime_ctx.context import new_context
import base64

logger = logging.getLogger(__name__)


class StreamingASR:
    """流式ASR识别器"""
    
    def __init__(
        self,
        chunk_duration: float = 2.0,
        overlap: float = 0.5,
        sample_rate: int = 16000,
        on_result_callback: Optional[Callable] = None
    ):
        """
        参数:
            chunk_duration: 音频片段时长（秒）
            overlap: 重叠时长（秒），用于提高连续性
            sample_rate: 采样率
            on_result_callback: 结果回调函数
        """
        self.chunk_duration = chunk_duration
        self.overlap = overlap
        self.sample_rate = sample_rate
        self.on_result_callback = on_result_callback
        
        self.asr_client = ASRClient(ctx=new_context(method="streaming_asr"))
        self.audio_queue = asyncio.Queue()
        self.is_running = False
        self.last_result = ""
        self.total_processed = 0
    
    async def add_audio_chunk(self, audio_data: bytes):
        """
        添加音频数据到队列
        
        参数:
            audio_data: PCM格式音频数据（16-bit, mono）
        """
        await self.audio_queue.put(audio_data)
        logger.debug(f"添加音频片段: {len(audio_data)} bytes")
    
    async def start(self):
        """启动流式识别"""
        self.is_running = True
        logger.info("🎙️ 启动流式ASR识别...")
        
        # 启动处理任务
        processing_task = asyncio.create_task(self._process_audio_loop())
        
        return processing_task
    
    async def _process_audio_loop(self):
        """处理音频循环"""
        buffer = deque()
        chunk_size = int(self.chunk_duration * self.sample_rate * 2)  # 16-bit = 2 bytes
        overlap_size = int(self.overlap * self.sample_rate * 2)
        
        logger.info(f"音频片段大小: {chunk_size} bytes, 重叠: {overlap_size} bytes")
        
        while self.is_running:
            try:
                # 获取音频数据
                audio_data = await asyncio.wait_for(
                    self.audio_queue.get(),
                    timeout=1.0
                )
                
                # 添加到缓冲区
                buffer.extend(audio_data)
                
                # 当缓冲区足够大时，进行处理
                while len(buffer) >= chunk_size:
                    # 提取片段
                    chunk = list(buffer)[:chunk_size]
                    del buffer[:chunk_size - overlap_size]  # 保留重叠部分
                    
                    # 转换为字节数组
                    chunk_bytes = bytes(chunk)
                    
                    # 识别语音
                    await self._recognize_chunk(chunk_bytes)
            
            except asyncio.TimeoutError:
                # 没有新音频，继续等待
                continue
            except Exception as e:
                logger.error(f"❌ 处理音频失败: {str(e)}")
                await asyncio.sleep(0.1)
    
    async def _recognize_chunk(self, audio_data: bytes):
        """识别单个音频片段"""
        try:
            # 转换为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 调用ASR
            start_time = time.time()
            text, data = self.asr_client.recognize(
                uid="streaming_asr",
                base64_data=audio_base64
            )
            processing_time = time.time() - start_time
            
            self.total_processed += 1
            
            if text and text != self.last_result:
                logger.info(
                    f"📝 识别结果 (#{self.total_processed}): {text} "
                    f"(处理时间: {processing_time:.2f}s)"
                )
                
                self.last_result = text
                
                # 调用回调函数
                if self.on_result_callback:
                    await self.on_result_callback(text, processing_time)
        
        except Exception as e:
            logger.error(f"❌ ASR识别失败: {str(e)}")
    
    async def stop(self):
        """停止识别"""
        self.is_running = False
        logger.info("⏹️ 流式ASR已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_processed": self.total_processed,
            "queue_size": self.audio_queue.qsize(),
            "last_result": self.last_result,
            "is_running": self.is_running
        }


class SlidingWindowASR(StreamingASR):
    """滑动窗口ASR - 提高连续性和准确性"""
    
    def __init__(
        self,
        chunk_duration: float = 2.0,
        overlap: float = 0.5,
        sample_rate: int = 16000,
        window_size: int = 3,  # 窗口大小（片段数）
        on_result_callback: Optional[Callable] = None
    ):
        super().__init__(chunk_duration, overlap, sample_rate, on_result_callback)
        self.window_size = window_size
        self.results_window = deque(maxlen=window_size)
    
    async def _recognize_chunk(self, audio_data: bytes):
        """识别音频片段并应用滑动窗口"""
        try:
            # 调用父类方法进行识别
            await super()._recognize_chunk(audio_data)
            
            # 添加结果到窗口
            if self.last_result:
                self.results_window.append(self.last_result)
            
            # 如果窗口已满，进行文本融合
            if len(self.results_window) >= self.window_size:
                fused_text = self._fuse_results(list(self.results_window))
                
                logger.info(f"🔗 融合结果: {fused_text}")
                
                # 调用回调函数
                if self.on_result_callback:
                    await self.on_result_callback(fused_text, 0)
        except Exception as e:
            logger.error(f"❌ 流式识别失败: {str(e)}")
            if self.on_error_callback:
                await self.on_error_callback(e)
    
    def _fuse_results(self, results: list) -> str:
        """融合多个识别结果"""
        # 简单的融合策略：取最新结果
        # 可以改进为：去重、合并相似内容等
        return results[-1]


class RealtimeAnchorMonitor:
    """实时主播监控器 - 结合ASR和AI分析"""
    
    def __init__(
        self,
        streaming_asr: StreamingASR,
        verify_callback: Optional[Callable] = None
    ):
        """
        参数:
            streaming_asr: 流式ASR实例
            verify_callback: 验证回调函数
        """
        self.asr = streaming_asr
        self.verify_callback = verify_callback
        self.recent_speeches = deque(maxlen=10)
        self.start_time = time.time()
    
    async def on_speech_result(self, text: str, processing_time: float):
        """
        语音识别结果回调
        
        参数:
            text: 识别的文本
            processing_time: 处理时间
        """
        # 记录语音
        speech_entry = {
            "text": text,
            "timestamp": time.time(),
            "processing_time": processing_time,
            "total_latency": time.time() - self.start_time
        }
        
        self.recent_speeches.append(speech_entry)
        
        logger.info(
            f"🎙️ 主播语音: {text} "
            f"(总延迟: {speech_entry['total_latency']:.2f}s)"
        )
        
        # 调用验证回调
        if self.verify_callback:
            await self.verify_callback(text)
    
    async def start(self):
        """启动监控"""
        logger.info("🔍 启动主播实时监控...")
        
        # 设置ASR回调
        self.asr.on_result_callback = self.on_speech_result
        
        # 启动ASR
        await self.asr.start()
    
    async def stop(self):
        """停止监控"""
        await self.asr.stop()
        logger.info("⏹️ 主播监控已停止")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "asr_stats": self.asr.get_stats(),
            "recent_speeches_count": len(self.recent_speeches),
            "avg_processing_time": sum(
                s['processing_time'] for s in self.recent_speeches
            ) / len(self.recent_speeches) if self.recent_speeches else 0,
            "avg_total_latency": sum(
                s['total_latency'] for s in self.recent_speeches
            ) / len(self.recent_speeches) if self.recent_speeches else 0
        }


async def test_streaming_asr():
    """测试流式ASR"""
    import numpy as np
    
    # 创建流式ASR
    asr = StreamingASR(chunk_duration=2.0, overlap=0.5)
    
    # 创建监控器
    monitor = RealtimeAnchorMonitor(asr)
    
    # 模拟音频流（生成测试音频）
    def simulate_audio_stream():
        """模拟音频流"""
        while True:
            # 生成2秒的测试音频（16kHz, 16-bit, mono）
            duration = 2.0
            sample_rate = 16000
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
            audio_bytes = audio.tobytes()
            
            yield audio_bytes
            time.sleep(2.0)
    
    # 启动监控
    monitor_task = await monitor.start()
    
    # 模拟音频输入
    audio_stream = simulate_audio_stream()
    
    try:
        for i, audio_chunk in enumerate(audio_stream):
            if i >= 3:  # 只测试3个片段
                break
            await monitor.asr.add_audio_chunk(audio_chunk)
            await asyncio.sleep(1)
    
    finally:
        await monitor.stop()
        
        # 打印统计
        stats = monitor.get_stats()
        print("\n📊 监控统计:")
        print(f"  总延迟: {stats['avg_total_latency']:.2f}s")
        print(f"  处理时间: {stats['avg_processing_time']:.2f}s")
        print(f"  识别片段数: {stats['asr_stats']['total_processed']}")


if __name__ == "__main__":
    asyncio.run(test_streaming_asr())
