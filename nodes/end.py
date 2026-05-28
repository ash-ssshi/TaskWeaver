"""
结束节点 —— 汇总所有节点的执行结果，输出最终结果。

对应 PaiFlow 的 EndNode。
"""

from nodes.base import BaseNode


class EndNode(BaseNode):
    """工作流的出口。把前面所有节点的结果汇总到一起。"""

    async def execute(self, context: dict) -> dict:
        return {
            "node_id": self.node_id,
            "status": "completed",
            "output": context.get("node_results", []),
            "message": "工作流执行完毕",
        }
