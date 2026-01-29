import json
import inspect
import hashlib
import os
from typing import List, Dict, Any, Optional, Callable
from .infer_layer import Inferrer, ChatConfig

class DialogueManager:
    """
    Dialogue management layer, responsible for handling conversation flow, tool calls, and context maintenance.
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
            except:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except:
            pass

    def _get_func_hash(self, func: Callable) -> str:
        source = inspect.getsource(func)
        return hashlib.md5(source.encode("utf-8")).hexdigest()

    async def _generate_tool_schema(self, func: Callable, model: str) -> Dict[str, Any]:
        """
        Use LLM to convert a Python function to OpenAI tool format.
        """
        source = inspect.getsource(func)
        prompt = f"""
Please convert the following Python function into a JSON Schema tool definition format that complies with the OpenAI SDK standard.
Requirements:
1. Must include 'type': 'function' top-level structure.
2. Extract function name, description (from docstring), parameter names, types, and descriptions.
3. Strictly output JSON format without any Markdown tags.

Function source code:
```python
{source}
```
"""
        response = await self.inferrer.run(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content.strip()
        # Remove potential markdown code block tags
        if content.startswith("```json"):
            content = content[7:-3]
        elif content.startswith("```"):
            content = content[3:-3]
        
        return json.loads(content)

    async def register_tools(self, funcs: List[Callable], model: Optional[str] = None):
        """
        Automatically register tools: convert Python functions to OpenAI tool format and maintain cache.
        """
        self.tools_schema = []
        updated = False

        for func in funcs:
            func_name = func.__name__
            func_hash = self._get_func_hash(func)
            
            # Check cache
            if func_name in self._cache and self._cache[func_name]["hash"] == func_hash:
                schema = self._cache[func_name]["schema"]
            else:
                # Regenerate
                print(f"--- Generating tool schema for function {func_name} ---")
                if not model:
                    raise ValueError(f"Generating schema for tool {func_name} requires a model parameter")
                
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
        Handle a single chat request, supporting automatic tool calls.
        """
        current_messages = list(messages)
        turns = 0
        
        # If tools are registered via register_tools and not provided in kwargs, inject them automatically
        if self.tools_schema and "tools" not in kwargs and (not config or not config.tools):
            kwargs["tools"] = self.tools_schema

        while turns < max_turns:
            # Execute inference
            response = await self.inferrer.run(config=config, messages=current_messages, **kwargs)
            message = response.choices[0].message
            
            # Add model response to history
            current_messages.append(message.model_dump(exclude_none=True))

            # Check for tool calls
            if not message.tool_calls:
                return response

            # Handle tool calls
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                # Get and execute tool
                if function_name in self.tools_map:
                    tool_func = self.tools_map[function_name]
                    try:
                        # Execute tool function
                        if hasattr(tool_func, "__code__") and "async" in str(type(tool_func)):
                             tool_result = await tool_func(**function_args)
                        else:
                             tool_result = tool_func(**function_args)
                    except Exception as e:
                        tool_result = f"Error executing tool {function_name}: {str(e)}"
                else:
                    tool_result = f"Tool {function_name} not found."

                # Add tool execution result to history
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": str(tool_result)
                })
            
            turns += 1

        return response
