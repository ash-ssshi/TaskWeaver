"""工作流执行引擎的单元测试。"""

import json
import tempfile
from pathlib import Path

import pytest

from domain.dsl import NodeDSL, EdgeDSL, WorkflowDSL, NodeType
from engine.executor import WorkflowExecutor


@pytest.fixture
def temp_workflows_dir():
    """创建临时目录存放测试用的工作流 JSON 文件"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def executor(temp_workflows_dir):
    """创建指向临时目录的执行器实例"""
    return WorkflowExecutor(workflows_dir=temp_workflows_dir)


class TestTopologicalSort:
    def test_linear_chain(self, executor):
        """A → B → C 排序结果应为 [A, B, C]"""
        nodes = [
            NodeDSL(id="a", type=NodeType.START),
            NodeDSL(id="b", type=NodeType.LLM),
            NodeDSL(id="c", type=NodeType.END),
        ]
        edges = [
            EdgeDSL(source="a", target="b"),
            EdgeDSL(source="b", target="c"),
        ]
        order = executor._topological_sort(nodes, edges)
        assert order == ["a", "b", "c"]

    def test_diamond_shape(self, executor):
        """菱形结构：A → B, A → C, B → D, C → D"""
        nodes = [
            NodeDSL(id="a", type=NodeType.START),
            NodeDSL(id="b", type=NodeType.LLM),
            NodeDSL(id="c", type=NodeType.TTS),
            NodeDSL(id="d", type=NodeType.END),
        ]
        edges = [
            EdgeDSL(source="a", target="b"),
            EdgeDSL(source="a", target="c"),
            EdgeDSL(source="b", target="d"),
            EdgeDSL(source="c", target="d"),
        ]
        order = executor._topological_sort(nodes, edges)
        assert order[0] == "a"   # 入口必须是 a
        assert order[-1] == "d"  # 出口必须是 d
        assert set(order[1:3]) == {"b", "c"}  # b 和 c 顺序可以互换

    def test_cycle_detection(self, executor):
        """A → B → C → A 形成环，应抛出 ValueError"""
        nodes = [
            NodeDSL(id="a", type=NodeType.START),
            NodeDSL(id="b", type=NodeType.LLM),
            NodeDSL(id="c", type=NodeType.TTS),
        ]
        edges = [
            EdgeDSL(source="a", target="b"),
            EdgeDSL(source="b", target="c"),
            EdgeDSL(source="c", target="a"),  # 环！
        ]
        with pytest.raises(ValueError, match="循环依赖"):
            executor._topological_sort(nodes, edges)


class TestWorkflowExecution:
    @pytest.mark.asyncio
    async def test_full_workflow_execution(self, executor, temp_workflows_dir):
        """端到端：创建临时工作流 JSON → 执行 → 验证事件序列"""
        wf = WorkflowDSL(
            id="test",
            name="测试工作流",
            nodes=[
                NodeDSL(id="start", type=NodeType.START),
                NodeDSL(id="llm", type=NodeType.LLM, config={"delay": 0.01}),
                NodeDSL(id="tts", type=NodeType.TTS, config={"delay": 0.01}),
                NodeDSL(id="end", type=NodeType.END),
            ],
            edges=[
                EdgeDSL(source="start", target="llm"),
                EdgeDSL(source="llm", target="tts"),
                EdgeDSL(source="tts", target="end"),
            ],
        )
        filepath = Path(temp_workflows_dir) / "test.json"
        filepath.write_text(wf.model_dump_json(), encoding="utf-8")

        events = []
        async for event in executor.run("test", "今天的主题是 AI"):
            events.append(event)

        # 验证事件类型序列
        event_types = [e["event"] for e in events]
        assert event_types == [
            "workflow_started",
            "node_started", "node_completed",  # start
            "node_started", "node_completed",  # llm
            "node_started", "node_completed",  # tts
            "node_started", "node_completed",  # end
            "workflow_completed",
        ]

    @pytest.mark.asyncio
    async def test_missing_workflow(self, executor):
        """请求不存在的工作流应抛出 FileNotFoundError"""
        with pytest.raises(FileNotFoundError):
            async for _ in executor.run("nonexistent", "input"):
                pass
