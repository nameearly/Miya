"""
TTSWrapper - TTS包装器（来自NagaAgent）

解决asyncio事件循环冲突问题
在独立线程中运行事件循环，实现线程安全的TTS调用
"""

import asyncio
import threading
import logging
import tempfile

logger = logging.getLogger(__name__)

try:
    import edge_tts
except ImportError:
    edge_tts = None
    logger.warning("edge-tts 未安装")

class TTSWrapper:
    """TTS包装器，处理asyncio和线程安全问题"""
    
    def __init__(self):
        self._loop = None
        self._thread = None
        self._start_loop()
    
    def _start_loop(self):
        """在独立线程中启动事件循环"""
        def run_loop():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
        
        # 等待事件循环启动
        while self._loop is None:
            import time
            time.sleep(0.01)
    
    def generate_speech_safe(self, text, voice="zh-CN-XiaoxiaoNeural", response_format="mp3", speed=1.0):
        """线程安全的TTS生成"""
        if not edge_tts:
            logger.error("edge-tts 未安装")
            return None
        
        try:
            # 在独立的事件循环中运行异步任务
            future = asyncio.run_coroutine_threadsafe(
                self._generate_audio_async(text, voice, response_format, speed),
                self._loop
            )
            # 等待结果（最多30秒）
            result = future.result(timeout=30)
            return result
        except Exception as e:
            logger.error(f"[TTSWrapper] 生成语音失败: {e}")
            return self._fallback_generate(text, voice, response_format, speed)
    
    async def _generate_audio_async(self, text, voice, response_format, speed):
        """异步生成音频"""
        communicate = edge_tts.Communicate(text, voice, rate=f"+{int((speed-1)*100)}%")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(suffix=f".{response_format}", delete=False) as f:
            temp_path = f.name
            await communicate.save(temp_path)
        
        # 读取音频数据
        with open(temp_path, "rb") as f:
            audio_data = f.read()
        
        # 删除临时文件
        try:
            import os
            os.remove(temp_path)
        except:
            pass
        
        return audio_data
    
    def _fallback_generate(self, text, voice, response_format, speed):
        """回退方案：直接使用edge_tts同步方法"""
        if not edge_tts:
            return None
        
        try:
            import subprocess
            rate = f"+{int((speed-1)*100)}%"
            # 使用命令行方式
            cmd = f'edge-tts -t "{text}" -v {voice} -r {rate} -o temp_audio.{response_format}'
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            
            if result.returncode == 0:
                with open(f'temp_audio.{response_format}', "rb") as f:
                    data = f.read()
                import os
                os.remove(f'temp_audio.{response_format}')
                return data
        except Exception as e:
            logger.error(f"[TTSWrapper] 回退方案失败: {e}")
        
        return None
