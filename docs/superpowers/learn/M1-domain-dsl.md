# M1: 工作流 DSL 数据模型

## 功能概述

`domain/dsl.py` 定义了工作流的"语言"——用 Python 类来描述一个工作流长什么样。

## 核心知识点

### 1. DSL（领域特定语言）是什么？

DSL 就是针对特定问题设计的"小语言"。在这里，我们不用 YAML 或 JSON 直接操作，
而是用 Pydantic 类定义结构，让代码有类型检查 + 自动校验。

### 2. 三个核心类

| 类 | 作用 | 对应 PaiFlow |
|---|---|---|
| `NodeDSL` | 描述一个节点：ID、类型、配置 | `domain/entities/flow.py` 中的 `Node` |
| `EdgeDSL` | 描述一条连线：从哪个节点到哪个节点 | `domain/entities/flow.py` 中的 `Edge` |
| `WorkflowDSL` | 完整工作流 = 节点列表 + 连线列表 | `domain/entities/flow.py` 中的 `WorkflowData` |

### 3. 工作流本质上是一个 DAG（有向无环图）

```
[Start] → [LLM] → [TTS] → [End]
```

- **节点（Node）** = 图中的顶点，每个节点做一件事
- **边（Edge）** = 图中的有向边，定义执行顺序

### 4. Pydantic v2 关键特性

- `BaseModel`：自动提供 `__init__`、校验、序列化
- `Field(...)`：必填字段，省略号表示 required
- `model_dump_json()` / `model_validate_json()`：一行序列化/反序列化

## 代码逐行讲解

```python
class NodeType(str, Enum):
    START = "start"
    LLM = "llm"
    TTS = "tts"
    END = "end"
```
用 Enum 限制节点类型，防止手误写错。`str, Enum` 双重继承让它在 JSON 中表现为字符串。

```python
class NodeDSL(BaseModel):
    id: str = Field(..., description="Unique node ID")
    type: NodeType = Field(..., description="Node type")
    config: dict[str, Any] = Field(default_factory=dict)
```
- `id`：每个节点的唯一标识，必填
- `type`：NodeType 枚举，非法值直接报 ValidationError
- `config`：灵活的配置字典，不同节点存不同参数（prompt/voice/speed 等），默认空 dict

```python
class EdgeDSL(BaseModel):
    source: str
    target: str
```
一条有向边，source → target。只有两个字段就够了。

```python
class WorkflowDSL(BaseModel):
    id: str
    name: str
    nodes: list[NodeDSL]
    edges: list[EdgeDSL]
```
顶级容器。`nodes` 和 `edges` 共同描述完整的工作流图。

## 学习检查

1. 为什么用 Pydantic 而不是普通 dict？（类型安全 + 自动校验）
2. DAG 的"无环"是什么意思？（不能有循环引用，后面 executor 会处理）
3. `config` 字段为什么设计成 dict？（不同节点需要不同参数，dict 最灵活）
