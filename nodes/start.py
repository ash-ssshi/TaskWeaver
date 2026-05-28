"""
开始节点 —— 工作流的入口，提取用户输入放入 context。

对应 PaiFlow 的 StartNode。
"""

import asyncio

from nodes.base import BaseNode


class StartNode(BaseNode):
    """每个工作流的第一站。从 context 里读出用户输入。"""

    async def execute(self, context: dict) -> dict:
        await asyncio.sleep(0.1)  # 模拟最短处理时间
        user_input = context.get("input", "")
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": user_input,
            "message": f"收到用户输入：{user_input[:50]}...",
        }
