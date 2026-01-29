import json
import inspect
import hashlib
import os
from typing import List, Dict, Any, Optional, Callable
from .infer_layer import Inferrer, ChatConfig

class DialogueManager:
    """
    A dialogue management layer that handles conversation flow, tool calls, and state.
    """
    def __init__(self, inferrer: Inferrer, tools_map: Optional[Dict[str, Callable]] = None, cache_path: str = ".vibe_tool_cache.json"):
        self.inferrer = inferrer
        self.tools_map = tools_map or {}
        self.tools_schema = []
        self.cache_path = cache_path
        self._cache = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _get_func_hash(self, func: Callable) -> str:
        source = inspect.getsource(func)
        return hashlib.md5(source.encode("utf-8")).hexdigest()

    async def _generate_tool_schema(self, func: Callable, model: str) -> Dict[str, Any]:
        """
        Use the LLM to convert a Python callable into an OpenAI tools schema item.
        """
        source = inspect.getsource(func)
        prompt = f"""
Convert the following Python function into an OpenAI SDK compatible tool definition JSON schema.
Requirements:
1. The top-level structure must include: {{\"type\": \"function\"}}.
2. Extract function name, description (from docstring), and parameters (name, type, description).
3. Output strict JSON only. Do not include any Markdown formatting.

Function source:
```python
{source}
```
"""
        response = await self.inferrer.run(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Strip possible Markdown code fences
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        return json.loads(content)

    async def register_tools(self, funcs: List[Callable], model: Optional[str] = None):
        """
        Register tools automatically by generating OpenAI tool schemas from Python callables.
        Uses a local cache keyed by function source hash to avoid repeated costs.
        """
        self.tools_schema = []
        updated = False

        for func in funcs:
            func_name = func.__name__
            func_hash = self._get_func_hash(func)
            
            # Cache hit
            if func_name in self._cache and self._cache[func_name]["hash"] == func_hash:
                schema = self._cache[func_name]["schema"]
            else:
                # Cache miss, regenerate schema
                print(f"--- Generating tool schema for function: {func_name} ---")
                if not model:
                    raise ValueError(f"生成工具 {func_name} 的 Schema 需要指定 model 参数")
                
                schema = await self._generate_tool_schema(func, model)
                self._cache[func_name] = {
                    "hash": func_hash,
                    "schema": schema
                }
                updated = True
            
            self.tools_schema.append(schema)
            self.tools_map[func_name] = func

        if updated:
            self._save_cache()

    async def chat(
        self, 
        messages: List[Dict[str, str]], 
        config: Optional[ChatConfig] = None,
        max_turns: int = 5,
        **kwargs
    ) -> Any:
        """
        Process a chat request with automatic tool call execution.
        """
        current_messages = list(messages)
        turns = 0
        
        # If tools were registered and not explicitly provided, inject them automatically
        if self.tools_schema and "tools" not in kwargs and (not config or not config.tools):
            kwargs["tools"] = self.tools_schema

        while turns < max_turns:
            # Run inference
            response = await self.inferrer.run(config=config, messages=current_messages, **kwargs)
            message = response.choices[0].message
            
            # Append the assistant message to history
            current_messages.append(message.model_dump(exclude_none=True))

            # Stop if no tool calls are requested
            if not message.tool_calls:
                return response

            # Execute tool calls
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Resolve and execute the tool
                if function_name in self.tools_map:
                    tool_func = self.tools_map[function_name]
                    try:
                        # Execute the tool callable (sync or async)
                        if inspect.iscoroutinefunction(tool_func):
                            tool_result = await tool_func(**function_args)
                        else:
                            tool_result = tool_func(**function_args)
                    except Exception as e:
                        tool_result = f"Error executing tool {function_name}: {str(e)}"
                else:
                    tool_result = f"Tool {function_name} not found."

                # Append tool result message
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(tool_result)
                })
            
            turns += 1

        return response
