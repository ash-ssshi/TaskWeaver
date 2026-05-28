"""
节点注册表：NodeType → 节点类

执行引擎通过查这张表来创建节点实例，而不是写一大堆 if/else。
对应 PaiFlow 的 NodeFactory（engine/node.py）。
"""

from domain.dsl import NodeType
from nodes.base import BaseNode
from nodes.start import StartNode
from nodes.llm import LLMNode
from nodes.tts import TTSNode
from nodes.end import EndNode

NODE_REGISTRY: dict[NodeType, type[BaseNode]] = {
    NodeType.START: StartNode,
    NodeType.LLM: LLMNode,
    NodeType.TTS: TTSNode,
    NodeType.END: EndNode,
}
