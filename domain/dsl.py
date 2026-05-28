"""
TaskWeaver DSL (Domain Specific Language) data models.

Defines the structure of a workflow: what nodes exist, how they connect,
and what each node should do. Uses Pydantic v2 for validation.

Corresponds to PaiFlow's:
  - core/workflow/domain/entities/flow.py (Node, Edge, Data, WorkflowData)
  - core/workflow/engine/entities/workflow_dsl.py (WorkflowDSL)
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    """Supported node types in a workflow."""
    START = "start"
    LLM = "llm"
    TTS = "tts"
    END = "end"


class NodeDSL(BaseModel):
    """
    A single node in the workflow graph.

    Corresponds to PaiFlow's `Node` in domain/entities/flow.py
    and `SparkFlowEngineNode` in engine/entities/node_entities.py.

    :param id: Unique node identifier (e.g. "node-1", "node-llm")
    :param type: What kind of node this is (start/llm/tts/end)
    :param config: Node-specific settings (prompt, voice, etc.)
    """
    id: str = Field(..., description="Unique node ID")
    type: NodeType = Field(..., description="Node type")
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Node-specific configuration"
    )


class EdgeDSL(BaseModel):
    """
    A directed edge connecting two nodes: source → target.

    Corresponds to PaiFlow's `Edge` in domain/entities/flow.py.

    :param source: ID of the source node
    :param target: ID of the target node
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")


class WorkflowDSL(BaseModel):
    """
    A complete workflow definition — nodes + edges.

    Corresponds to PaiFlow's `WorkflowData` in domain/entities/flow.py.

    :param id: Unique workflow identifier (e.g. "podcast")
    :param name: Human-readable name
    :param nodes: All nodes in this workflow
    :param edges: All connections between nodes
    """
    id: str = Field(..., description="Workflow ID")
    name: str = Field(..., description="Workflow name")
    nodes: list[NodeDSL] = Field(..., description="Workflow nodes")
    edges: list[EdgeDSL] = Field(..., description="Node connections")
