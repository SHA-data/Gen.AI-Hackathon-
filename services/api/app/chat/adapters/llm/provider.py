"""LLM Provider factory and adapters."""
import json
import os
from typing import Any, AsyncGenerator, Dict, List, Optional
import httpx

from packages.contracts.llm import (
    FakeLLMProvider,
    LLMProvider,
    LLMResponse,
    LLMStreamChunk,
    Message,
    ToolCall,
    ToolDefinition,
    FunctionCall,
)
from services.api.app.core.config import settings

class OpenAILikeLLMProvider:
    """Real LLM provider supporting OpenAI, NVIDIA NIM, and compatible endpoints."""
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("NVIDIA_API_KEY") or "fake-key"
        self.base_url = (base_url or os.getenv("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.default_model = model or settings.MODEL_NAME

    async def chat_with_tools(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.default_model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = [t.model_dump(exclude_none=True) for t in tools]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        content = choice.get("content")
        raw_tools = choice.get("tool_calls")
        tool_calls = None
        if raw_tools:
            tool_calls = [
                ToolCall(
                    id=rt["id"],
                    function=FunctionCall(
                        name=rt["function"]["name"],
                        arguments=rt["function"]["arguments"],
                    ),
                )
                for rt in raw_tools
            ]

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=data["choices"][0].get("finish_reason", "stop"),
        )

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model or self.default_model,
            "messages": [m.model_dump(exclude_none=True) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            payload["tools"] = [t.model_dump(exclude_none=True) for t in tools]

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions", headers=headers, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    line_data = line[6:].strip()
                    if line_data == "[DONE]":
                        break
                    chunk_json = json.loads(line_data)
                    delta = chunk_json["choices"][0]["delta"]
                    delta_content = delta.get("content")
                    finish = chunk_json["choices"][0].get("finish_reason")
                    yield LLMStreamChunk(delta_content=delta_content, finish_reason=finish)

    async def generate_structured(
        self,
        messages: List[Message],
        schema: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        sys_msg = Message(
            role="system",
            content=f"You must return ONLY a valid JSON object strictly conforming to this JSON Schema:\n{json.dumps(schema)}",
        )
        resp = await self.chat_with_tools([sys_msg] + messages, model=model, temperature=0.0)
        return json.loads(resp.content or "{}")

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5,
    ) -> List[tuple[int, float]]:
        # Default simple keyword-overlap heuristic if external reranker is unavailable
        scored = []
        q_words = set(query.lower().split())
        for idx, doc in enumerate(documents):
            d_words = set(doc.lower().split())
            score = len(q_words & d_words) / (len(q_words) or 1)
            scored.append((idx, float(score)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

def get_llm_provider() -> LLMProvider:
    """Factory returning configured LLMProvider. Uses Fake by default unless API key configured."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("NVIDIA_API_KEY")
    if api_key and settings.ENV != "test":
        return OpenAILikeLLMProvider(api_key=api_key)
    return FakeLLMProvider()
