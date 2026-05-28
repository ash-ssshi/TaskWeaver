# M2: 节点实现 — 策略模式

## 功能概述

`nodes/` 目录包含 5 种节点实现，每种节点做一件事。通过统一的接口（`execute(context) -> result`），执行引擎不需要知道每个节点内部怎么工作。

## 核心知识点

### 1. 策略模式（Strategy Pattern）

- **Context（执行引擎）**：持有当前状态，按顺序调用节点
- **Strategy（BaseNode）**：抽象接口 `execute(context)`
- **ConcreteStrategy（StartNode/LLMNode/TTSNode/EndNode）**：具体实现

好处：新增节点类型只需加一个文件 + 注册到 NODE_REGISTRY，引擎代码不用改。

### 2. 节点注册表

```python
NODE_REGISTRY: dict[NodeType, type[BaseNode]] = {
    NodeType.START: StartNode,
    NodeType.LLM: LLMNode,
    NodeType.TTS: TTSNode,
    NodeType.END: EndNode,
}
```

这是**依赖注入**的简单形式：执行引擎通过查表来创建节点实例，而不是硬编码 `if type == "llm": LLMNode()`。

### 3. Context 传递模式

所有节点共享一个 `context` 字典，像一个"背包"在节点间传递：

```
StartNode: context["input"] = "用户原文"     # 写入
   ↓
LLMNode:   text = context["input"]            # 读取
           context["rewritten"] = "改写后"    # 写入
   ↓
TTSNode:   text = context["rewritten"]         # 读取
           context["audio_url"] = "http://..." # 写入
```

### 4. Mock vs 真实 API

当前 LLM 和 TTS 用 mock，替换为真实 API 只需改 execute() 方法：

```python
# Mock 版本（当前）
async def execute(self, context):
    await asyncio.sleep(1.5)
    return {"output": "mock 改写结果..."}

# 真实 DeepSeek 版本（以后替换）
async def execute(self, context):
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.config['api_key']}"},
            json={"model": "deepseek-chat", "messages": [...]},
        )
    return {"output": resp.json()["choices"][0]["message"]["content"]}
```

**只改节点文件，引擎、路由、SSE 全部不动。**

## 五种节点对比

| 节点 | 职责 | 输入 | 输出 | 延迟 |
|------|------|------|------|------|
| StartNode | 提取用户输入 | context["input"] | 原文 | 0.1s |
| LLMNode | 文本改写 | context["input"] | 播客逐字稿 | 1.5s(mock) |
| TTSNode | 语音合成 | 上一节点输出 | 音频URL | 2.0s(mock) |
| EndNode | 汇总结果 | context["node_results"] | 汇总列表 | 0s |

## 学习检查

1. 如果要新增一个"翻译节点"，需要改哪些文件？（新增 `nodes/translate.py` + 在 `NodeType` 枚举加一项 + 在 `NODE_REGISTRY` 注册）
2. 为什么 context 用 dict 而不是强类型对象？（dict 灵活，节点可以随意读写自己关心的字段）
3. 为什么 execute 是 async？（真实场景有网络 IO，async 不阻塞其他请求）
