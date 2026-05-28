"""Tests for domain/dsl.py — Pydantic model validation."""

import pytest
from pydantic import ValidationError

from domain.dsl import NodeDSL, EdgeDSL, WorkflowDSL, NodeType


class TestNodeDSL:
    def test_valid_node(self):
        node = NodeDSL(id="node-1", type=NodeType.START, config={"input_key": "text"})
        assert node.id == "node-1"
        assert node.type == NodeType.START
        assert node.config == {"input_key": "text"}

    def test_default_config_is_empty_dict(self):
        node = NodeDSL(id="node-1", type=NodeType.LLM)
        assert node.config == {}

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            NodeDSL(id="node-1", type="unknown_type")


class TestEdgeDSL:
    def test_valid_edge(self):
        edge = EdgeDSL(source="node-1", target="node-2")
        assert edge.source == "node-1"
        assert edge.target == "node-2"


class TestWorkflowDSL:
    def test_valid_workflow(self):
        wf = WorkflowDSL(
            id="podcast",
            name="AI 播客生成",
            nodes=[
                NodeDSL(id="start", type=NodeType.START),
                NodeDSL(id="llm", type=NodeType.LLM),
                NodeDSL(id="end", type=NodeType.END),
            ],
            edges=[
                EdgeDSL(source="start", target="llm"),
                EdgeDSL(source="llm", target="end"),
            ],
        )
        assert wf.id == "podcast"
        assert len(wf.nodes) == 3
        assert len(wf.edges) == 2

    def test_workflow_to_json_roundtrip(self):
        """Verify workflow DSL can be serialized and deserialized."""
        wf = WorkflowDSL(
            id="podcast",
            name="AI 播客生成",
            nodes=[
                NodeDSL(id="start", type=NodeType.START),
                NodeDSL(id="llm", type=NodeType.LLM, config={"prompt": "改写文本"}),
            ],
            edges=[EdgeDSL(source="start", target="llm")],
        )
        json_str = wf.model_dump_json()
        restored = WorkflowDSL.model_validate_json(json_str)
        assert restored == wf
