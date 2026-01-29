from openai import AsyncOpenAI
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ChatConfig:
    """
    Stores inference parameters in an OpenAI-compatible way.
    """
    model: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    tools: Optional[List[Dict[str, Any]]] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    stop: Optional[Any] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[Dict[str, int]] = None
    user: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert into a kwargs dict for OpenAI SDK calls.
        """
        params = {
            "model": self.model,
            "messages": self.messages,
        }
        
        # Add optional non-empty parameters
        optional_fields = [
            "tools", "temperature", "top_p", "n", "stream", "stop", 
            "max_tokens", "presence_penalty", "frequency_penalty", 
            "logit_bias", "user"
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                params[field_name] = value
                
        # Merge extra OpenAI-compatible parameters
        if self.extra_params:
            params.update(self.extra_params)
            
        return params

class Inferrer:

    def __init__(self, server_base_url: str, server_apikey: str = None) -> None:
        self.apikey = server_apikey or os.getenv("INFER_API_KEY")
        
        if not self.apikey:
            raise ValueError("未提供 API Key，且未在环境变量中找到 INFER_API_KEY")

        self.base_url = server_base_url
        self.client = AsyncOpenAI(api_key=self.apikey, base_url=self.base_url)


    async def run(self, config: Optional[ChatConfig] = None, **kwargs) -> Any:
        """
        Execute a chat completion request.
        Accepts either a ChatConfig object or loose kwargs.
        If both are provided, kwargs override config fields.
        """
        # Prepare base params
        if config:
            full_params = config.to_dict()
        else:
            # If config is not provided, start from an empty ChatConfig
            full_params = ChatConfig().to_dict()
        
        # Override with provided kwargs
        if kwargs:
            full_params.update(kwargs)

        # Validate required parameters
        if not full_params.get("model"):
            raise ValueError("推理请求必须包含 'model' 参数")
        if not full_params.get("messages"):
            raise ValueError("推理请求必须包含 'messages' 参数")

        # Call OpenAI SDK
        response = await self.client.chat.completions.create(**full_params)
        return response
