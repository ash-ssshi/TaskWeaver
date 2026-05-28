"""节点实现的单元测试。"""

import pytest

from domain.dsl import NodeDSL, NodeType
from nodes import NODE_REGISTRY
from nodes.base import BaseNode


class TestNodeRegistry:
    def test_all_node_types_registered(self):
        """验证所有 NodeType 都已注册"""
        for node_type in NodeType:
            assert node_type in NODE_REGISTRY, f"缺少注册: {node_type}"

    def test_registry_values_are_base_node_subclasses(self):
        """验证注册表中每个值都是 BaseNode 的子类"""
        for node_class in NODE_REGISTRY.values():
            assert issubclass(node_class, BaseNode)


class TestStartNode:
    @pytest.mark.asyncio
    async def test_extracts_input(self):
        """测试开始节点正确提取用户输入"""
        dsl = NodeDSL(id="start", type=NodeType.START)
        node = NODE_REGISTRY[NodeType.START](dsl)
        result = await node.execute({"input": "你好世界"})
        assert result["status"] == "completed"
        assert result["output"] == "你好世界"


class TestLLMNode:
    @pytest.mark.asyncio
    async def test_rewrites_text(self):
        """测试 LLM 节点正确改写文本"""
        dsl = NodeDSL(id="llm-1", type=NodeType.LLM, config={"delay": 0.01})
        node = NODE_REGISTRY[NodeType.LLM](dsl)
        result = await node.execute({"input": "AI 技术"})
        assert result["status"] == "completed"
        assert "AI 技术" in result["output"]
        assert "听众朋友们" in result["output"]


class TestTTSNode:
    @pytest.mark.asyncio
    async def test_generates_audio_url(self):
        """测试 TTS 节点返回音频 URL"""
        dsl = NodeDSL(id="tts-1", type=NodeType.TTS, config={"delay": 0.01})
        node = NODE_REGISTRY[NodeType.TTS](dsl)
        result = await node.execute({"input": "some text"})
        assert result["status"] == "completed"
        assert result["output"].startswith("https://")


class TestEndNode:
    @pytest.mark.asyncio
    async def test_collects_results(self):
        """测试结束节点正确汇总结果"""
        dsl = NodeDSL(id="end", type=NodeType.END)
        node = NODE_REGISTRY[NodeType.END](dsl)
        result = await node.execute({"node_results": [{"a": 1}]})
        assert result["status"] == "completed"
        assert result["output"] == [{"a": 1}]
