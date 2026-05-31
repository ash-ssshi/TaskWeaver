# M3: 工作流执行引擎

## 功能概述

`engine/executor.py` 是整个引擎的大脑。它加载工作流 DSL → 按拓扑顺序排列节点 → 逐个执行 → 通过 async generator 流式返回每个节点的执行结果。

对应 PaiFlow 的 `core/workflow/engine/dsl_engine.py`（WorkflowEngineCtx + 执行循环）。

## 核心知识点

### 1. DAG（有向无环图）与拓扑排序

工作流本质是一个 DAG。节点是顶点，边是有向边。拓扑排序保证每个节点在其所有前驱节点执行完后才执行。

**Kahn 算法（BFS 版拓扑排序）步骤：**
1. 计算每个节点的入度（有几条边指向它）
2. 入度为 0 的节点入队（没有依赖，可以直接执行）
3. 每次出队一个节点，把它指向的邻居入度减 1
4. 如果邻居入度变为 0，入队
5. 最后如果排序结果数量 ≠ 总节点数，说明存在环

```
例子：A → B → C

入度: A=0, B=1, C=1
第1轮: 队列=[A]，出队 A，B 入度减为 0，入队 B
第2轮: 出队 B，C 入度减为 0，入队 C
第3轮: 出队 C，队列空 → 结果 [A, B, C]
```

### 2. Async Generator（async yield）

```python
async def run(self, flow_id, input_text):
    yield {"event": "workflow_started", ...}   # 立即发送
    for node_id in node_order:
        result = await node.execute(context)    # 等这个节点完成
        yield {"event": "node_completed", ...}  # 立即发送
    yield {"event": "workflow_completed", ...}  # 最后发送
```

`async yield` 让调用方可以逐个处理事件（后续会通过 SSE 推送给浏览器），而不需要等所有节点执行完。

### 3. Context 背包模式

```python
context = {"input": "用户原文", "node_results": []}

# 每个节点执行时：
#   读取 context 中自己需要的字段
#   写入自己的结果供后续节点使用
context["node_results"].append(result)
```

所有节点共享一个 context 字典，像"背包"一样在节点间传递数据。

### 4. 三个关键方法

| 方法 | 职责 | 输入 | 输出 |
|------|------|------|------|
| `load_workflow()` | 从 JSON 文件加载 DSL | flow_id | WorkflowDSL 对象 |
| `_topological_sort()` | 确定执行顺序 | nodes + edges | 有序的 node_id 列表 |
| `run()` | 逐节点执行并流式产出事件 | flow_id + input | async generator |

### 5. 错误处理

```python
try:
    result = await node_instance.execute(context)
except Exception as e:
    yield {"event": "node_failed", "data": {"node_id": node_id, "error": str(e)}}
    raise  # 中断整个工作流
```

节点执行失败时先发送 `node_failed` 事件通知调用方，然后抛出异常中断执行。

## 与 PaiFlow 的对比

| 特性 | PaiFlow | TaskWeaver |
|------|---------|------------|
| 执行引擎 | WorkflowEngineCtx (Pydantic 模型) | WorkflowExecutor (纯 Python 类) |
| 拓扑排序 | Chains + SimplePath 算法 | Kahn BFS 算法 |
| 状态管理 | Redis 缓存 + VariablePool | 内存 dict |
| 并发模型 | 多线程分布式 | 单进程 async |
| 事件回调 | ChatCallBacks 回调类 | async generator (yield) |

## 学习检查

1. 为什么要拓扑排序而不用 nodes 数组的原始顺序？（用户可能不按执行顺序定义节点，拓扑排序保证正确性）
2. 如果工作流有环会怎样？（Kahn 算法检测到环，抛出 ValueError）
3. async generator 和普通 return list 的区别？（generator 流式输出，不用等全部完成才能拿到第一条结果）
