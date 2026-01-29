from openai import AsyncOpenAI
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class ChatConfig:
    """
    Configuration for chat completion, compatible with OpenAI protocol.
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
        Convert to parameter dictionary for OpenAI SDK calls.
        """
        params = {
            "model": self.model,
            "messages": self.messages,
        }
        
        # Add non-empty optional parameters
        optional_fields = [
            "tools", "temperature", "top_p", "n", "stream", "stop", 
            "max_tokens", "presence_penalty", "frequency_penalty", 
            "logit_bias", "user"
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                params[field_name] = value
                
        # Merge custom parameters
        if self.extra_params:
            params.update(self.extra_params)
            
        return params

class Inferrer:

    def __init__(self, server_base_url: str, server_apikey: str = None) -> None:
        self.apikey = server_apikey or os.getenv("INFER_API_KEY")
        
        if not self.apikey:
            raise ValueError("API Key not provided and INFER_API_KEY not found in environment variables")

        self.base_url = server_base_url
        self.client = AsyncOpenAI(api_key=self.apikey, base_url=self.base_url)


    async def run(self, config: Optional[ChatConfig] = None, **kwargs) -> Any:
        """
        Execute inference request.
        Accepts either a ChatConfig object or individual parameters (kwargs).
        If both are provided, kwargs will override settings in config.
        """
        # Prepare base parameters
        if config:
            full_params = config.to_dict()
        else:
            # Use default config and update with kwargs if config is not provided
            full_params = ChatConfig().to_dict()
        
        # Override parameters with kwargs
        if kwargs:
            full_params.update(kwargs)

        # Check mandatory parameters
        if not full_params.get("model"):
            raise ValueError("Inference request must contain 'model' parameter")
        if not full_params.get("messages"):
            raise ValueError("Inference request must contain 'messages' parameter")

        # Call OpenAI SDK
        response = await self.client.chat.completions.create(**full_params)
        return response