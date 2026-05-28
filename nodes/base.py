"""
所有工作流节点的抽象基类。

每个节点都遵循同一个接口：接收 context 字典 → 干自己的活 → 返回结果字典。
这就是策略模式——执行引擎不关心每个节点内部怎么实现。

对应 PaiFlow 的 BaseNode（engine/nodes/base_node.py）。
"""

from abc import ABC, abstractmethod


class BaseNode(ABC):
    """
    抽象节点 —— 所有工作流节点必须实现 execute() 方法。

    使用方式（由执行引擎调用）：
        node_class = NODE_REGISTRY[node_dsl.type]
        node = node_class(node_dsl)
        result = await node.execute(context)
    """

    def __init__(self, node_dsl):
        self.node_id = node_dsl.id
        self.config = node_dsl.config

    @abstractmethod
    async def execute(self, context: dict) -> dict:
        """
        执行该节点的逻辑。

        参数:
            context: 在节点间传递的共享状态字典。
                     至少包含 {"input": "用户文本", ...}
        返回:
            包含至少 {"node_id": str, "status": str, "output": ...} 的字典
        """
        ...
