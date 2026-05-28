"""
TTS 节点 —— 将文本转为语音音频。

当前使用 mock 返回一个假的音频 URL，后续替换 execute() 即可接入真实讯飞 TTS API。

对应 PaiFlow 的 TTS 节点（讯飞超拟人合成集成）。
"""

import asyncio

from nodes.base import BaseNode


class TTSNode(BaseNode):
    """
    语音合成节点（默认 mock）。

    可配置项（通过 DSL 的 config 字段传入）：
        - voice: 发音人名称，默认 "xiaoming"
        - speed: 语速倍率，默认 1.0
        - delay: 模拟处理耗时（秒），默认 2.0
    """

    async def execute(self, context: dict) -> dict:
        delay = self.config.get("delay", 2.0)
        await asyncio.sleep(delay)

        voice = self.config.get("voice", "xiaoming")
        speed = self.config.get("speed", 1.0)

        # Mock：模拟音频生成
        fake_url = f"https://audio.example.com/podcast/{self.node_id}-output.wav"

        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": fake_url,
            "message": (
                f"语音合成完成：发音人={voice}, 语速={speed}x, "
                f"音频地址={fake_url}（耗时 {delay}s）"
            ),
        }
