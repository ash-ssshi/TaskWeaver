"""
LLM 节点 —— 将用户文本改写成播客风格的逐字稿。

当前使用 mock 模拟大模型行为（带延迟），后续只需替换 execute() 方法
即可接入真实 DeepSeek API，引擎和路由代码完全不用改。

对应 PaiFlow 的 LLM 节点（DeepSeek 集成）。
"""

import asyncio

from nodes.base import BaseNode


class LLMNode(BaseNode):
    """
    文本改写节点（默认 mock）。

    可配置项（通过 DSL 的 config 字段传入）：
        - prompt: 改写提示词，默认 "播客风格改写"
        - delay:  模拟处理耗时（秒），默认 1.5
    """

    async def execute(self, context: dict) -> dict:
        delay = self.config.get("delay", 1.5)
        await asyncio.sleep(delay)

        user_input = context.get("input", "")
        prompt = self.config.get("prompt", "播客风格改写")

        # Mock：模拟 LLM 改写结果
        rewritten = (
            f"【{prompt}】\n"
            f"嘿，各位听众朋友们大家好！欢迎收听今天的节目。\n\n"
            f"今天我们要聊的话题是：{user_input}\n\n"
            f"这期节目就到这里，咱们下期再见！"
        )

        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": rewritten,
            "message": f"LLM 改写完成（耗时 {delay}s）",
        }
