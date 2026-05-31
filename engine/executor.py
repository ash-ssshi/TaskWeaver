"""
工作流执行引擎。

加载工作流 DSL（从 JSON 文件），根据 edges 做拓扑排序确定执行顺序，
然后逐个执行节点，通过 context 字典在节点间传递数据。

对应 PaiFlow 的：
  - core/workflow/engine/dsl_engine.py（WorkflowEngineCtx + 执行循环）
  - core/workflow/service/chat_service.py（编排层）
"""

import asyncio
import json
from collections import deque
from pathlib import Path

from domain.dsl import WorkflowDSL, NodeDSL, NodeType
from nodes import NODE_REGISTRY


class WorkflowExecutor:
    """
    根据 DSL 定义执行一个工作流。

    使用方式：
        executor = WorkflowExecutor(workflows_dir="workflows")
        async for event in executor.run("podcast", "用户输入的文本"):
            print(event)  # {"event": "node_completed", "data": {...}}
    """

    def __init__(self, workflows_dir: str = "workflows"):
        self.workflows_dir = Path(workflows_dir)

    def load_workflow(self, flow_id: str) -> WorkflowDSL:
        """从 JSON 文件加载工作流 DSL。"""
        filepath = self.workflows_dir / f"{flow_id}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"工作流不存在: {filepath}")
        with open(filepath, "r", encoding="utf-8") as f:
            return WorkflowDSL.model_validate_json(f.read())

    def _build_adjacency(self, nodes: list[NodeDSL], edges: list) -> tuple[dict, dict]:
        """
        从节点和边构建邻接表和入度表。

        返回：
            adjacency: {node_id: [邻居节点 id 列表]}
            in_degree: {node_id: 入边的数量}
        """
        adjacency: dict[str, list[str]] = {n.id: [] for n in nodes}
        in_degree: dict[str, int] = {n.id: 0 for n in nodes}

        for edge in edges:
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] += 1

        return adjacency, in_degree

    def _topological_sort(self, nodes: list[NodeDSL], edges: list) -> list[str]:
        """
        Kahn 算法 —— 对 DAG 做拓扑排序。

        返回按执行顺序排列的 node_id 列表。如果检测到环，抛出 ValueError。

        Kahn 算法步骤：
        1. 计算每个节点的入度（有几条边指向它）
        2. 入度为 0 的节点入队（没有依赖，可以直接执行）
        3. 每次出队一个节点，把它指向的邻居入度减 1
        4. 邻居入度变 0 后入队
        5. 排序结果数量 ≠ 总节点数 → 存在环
        """
        adjacency, in_degree = self._build_adjacency(nodes, edges)

        # 所有入度为 0 的节点先入队
        queue: deque[str] = deque(
            node_id for node_id, deg in in_degree.items() if deg == 0
        )
        sorted_ids: list[str] = []

        while queue:
            current = queue.popleft()
            sorted_ids.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_ids) != len(nodes):
            raise ValueError(
                f"工作流存在循环依赖！已排序: {len(sorted_ids)}, 总节点: {len(nodes)}"
            )

        return sorted_ids

    async def run(self, flow_id: str, input_text: str):
        """
        执行工作流，每完成一个节点就 yield 一个事件（供 SSE 流式输出）。

        参数：
            flow_id: 工作流 ID（对应 workflows/ 下的 JSON 文件名）
            input_text: 用户输入的文本
        产出：
            事件字典，格式 {"event": "事件名", "data": {...}}
        """
        # 1. 加载工作流定义
        workflow = self.load_workflow(flow_id)

        # 2. 拓扑排序确定执行顺序
        node_order = self._topological_sort(workflow.nodes, workflow.edges)

        # 快速查找表：node_id → NodeDSL
        node_map: dict[str, NodeDSL] = {n.id: n for n in workflow.nodes}

        # 3. 初始化 context（在节点间传递的"背包"）
        context: dict = {"input": input_text, "node_results": []}

        # 4. 按顺序执行节点
        yield {
            "event": "workflow_started",
            "data": {
                "flow_id": flow_id,
                "flow_name": workflow.name,
                "execution_order": node_order,
            },
        }

        for node_id in node_order:
            node_dsl = node_map[node_id]
            node_class = NODE_REGISTRY[node_dsl.type]
            node_instance = node_class(node_dsl)

            # 发送"节点开始执行"事件
            yield {
                "event": "node_started",
                "data": {"node_id": node_id, "node_type": node_dsl.type.value},
            }

            # 执行节点
            try:
                result = await node_instance.execute(context)
            except Exception as e:
                yield {
                    "event": "node_failed",
                    "data": {"node_id": node_id, "error": str(e)},
                }
                raise

            context["node_results"].append(result)

            # 发送"节点执行完成"事件
            yield {
                "event": "node_completed",
                "data": result,
            }

        # 5. 全部执行完毕
        yield {
            "event": "workflow_completed",
            "data": {
                "total_nodes": len(node_order),
                "final_output": context["node_results"][-1] if context["node_results"] else None,
            },
        }
