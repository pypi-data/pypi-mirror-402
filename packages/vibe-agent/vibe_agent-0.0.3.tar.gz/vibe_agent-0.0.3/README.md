## VibeAgent / VibeAgent（中文）

VibeAgent 是一个轻量的 AI Agent SDK，核心目标是用尽量少的抽象把「对话 → 推理 → 工具调用 → 工具结果回传 → 继续推理」这条链路跑通，并保持与 OpenAI 协议的兼容性（`chat.completions` / tools）。

### 安装

```bash
pip install vibe-agent
```

### 快速开始

#### 1) 初始化推理层（Inferrer）

你需要显式传入 `server_base_url` 与 API Key（或通过环境变量提供）。

- API Key 优先级：`server_apikey` 参数 > 环境变量 `INFER_API_KEY`
- 如果两者都缺失，会抛出异常

```python
import asyncio
from vibe_agent.infer_layer import Inferrer

async def main():
    inferrer = Inferrer(
        server_base_url="https://openrouter.ai/api/v1",
        server_apikey="YOUR_API_KEY"
    )

    resp = await inferrer.run(
        model="google/gemini-3-flash-preview",
        messages=[{"role": "user", "content": "你好"}],
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

#### 2) 使用 ChatConfig 管理推理参数

`ChatConfig` 用于集中存储推理参数（messages、tools、temperature 等），并允许通过 `extra_params` 透传符合 OpenAI 协议的自定义参数。

```python
from vibe_agent.infer_layer import ChatConfig

config = ChatConfig(
    model="google/gemini-3-flash-preview",
    messages=[{"role": "user", "content": "总结一下这段话"}],
    temperature=0.2,
    extra_params={"top_k": 40},
)
```

#### 3) 使用对话管理层（DialogueManager）自动执行工具

`DialogueManager` 会在模型返回 `tool_calls` 时，自动调用本地工具函数，并把工具结果按 OpenAI 协议（role=tool）回传给模型，直至模型不再请求工具或达到 `max_turns`。

```python
import asyncio
from vibe_agent.infer_layer import Inferrer
from vibe_agent.dialogue_layer import DialogueManager

def get_weather(city: str):
    return f"{city} weather is sunny."

async def main():
    inferrer = Inferrer(
        server_base_url="https://openrouter.ai/api/v1",
        server_apikey="YOUR_API_KEY"
    )
    dm = DialogueManager(inferrer=inferrer, tools_map={"get_weather": get_weather})

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information for a city.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "City name"}
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    resp = await dm.chat(
        messages=[{"role": "user", "content": "北京天气怎么样？"}],
        model="google/gemini-3-flash-preview",
        tools=tools
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

#### 4) 自动把 Python 函数转换为 tools schema（并带本地缓存）

如果你不想手写 tools schema，可以用 `register_tools()`：

- 输入：若干 Python `callable`
- 输出：自动生成并注入符合 OpenAI SDK 的 `tools` 列表
- 缓存：如果函数源码未变化，会复用本地缓存（默认 `.vibe_tool_cache.json`）避免重复消耗推理成本

```python
import asyncio
from vibe_agent.infer_layer import Inferrer
from vibe_agent.dialogue_layer import DialogueManager

def calculate_sum(a: int, b: int):
    \"\"\"Calculate sum of two integers.\"\"\"
    return a + b

async def main():
    inferrer = Inferrer(
        server_base_url="https://openrouter.ai/api/v1",
        server_apikey="YOUR_API_KEY"
    )
    dm = DialogueManager(inferrer=inferrer)

    await dm.register_tools([calculate_sum], model="google/gemini-3-flash-preview")

    resp = await dm.chat(
        messages=[{"role": "user", "content": "帮我算 123 + 456"}],
        model="google/gemini-3-flash-preview",
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

### 环境变量

- `INFER_API_KEY`: 当 `server_apikey` 未传入时使用

### 安全提示

- 不要把 API Key 写进代码或提交到 Git
- `.trae/rules/pypi.md` 用于本地保存 PyPI Token，必须保持不入库

---

## VibeAgent (English)

VibeAgent is a lightweight AI Agent SDK that keeps the core loop minimal:
conversation → inference → tool calls → tool execution → tool result back to the model.
It stays compatible with the OpenAI-style `chat.completions` interface and tools schema.

### Installation

```bash
pip install vibe-agent
```

### Quick Start

#### 1) Initialize Inferrer

You must pass `server_base_url` explicitly, and provide an API key via argument or environment.

- API key priority: `server_apikey` argument > `INFER_API_KEY` env var
- If both are missing, an exception is raised

```python
import asyncio
from vibe_agent.infer_layer import Inferrer

async def main():
    inferrer = Inferrer(
        server_base_url="https://openrouter.ai/api/v1",
        server_apikey="YOUR_API_KEY"
    )

    resp = await inferrer.run(
        model="google/gemini-3-flash-preview",
        messages=[{"role": "user", "content": "Hello"}],
    )
    print(resp.choices[0].message.content)

asyncio.run(main())
```

#### 2) Manage parameters with ChatConfig

`ChatConfig` stores inference parameters (messages/tools/temperature/etc.) and supports passing extra OpenAI-compatible fields via `extra_params`.

#### 3) Use DialogueManager for tool execution

`DialogueManager` detects `tool_calls` in model responses, executes local tool callables, and appends OpenAI-style tool messages back to the conversation until no more tool calls are requested (or `max_turns` is reached).

#### 4) Auto-generate tools schema from Python callables (with local caching)

Use `register_tools()` to let the model generate OpenAI tools schema from Python functions. Results are cached by function source hash in `.vibe_tool_cache.json` (default).

