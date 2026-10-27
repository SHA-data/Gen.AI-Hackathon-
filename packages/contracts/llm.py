"""LLM Provider protocol and Fake implementation (Part B0.3, B2.1 & Moonshot Mode)."""
from __future__ import annotations

import json
import os
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Protocol, Type, TypeVar, Union
from uuid import uuid4
from pydantic import BaseModel, Field

T = TypeVar("T", bound=BaseModel)

class FunctionCall(BaseModel):
    name: str
    arguments: str  # JSON string

class ToolCall(BaseModel):
    id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:12]}")
    type: Literal["function"] = "function"
    function: FunctionCall

class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Literal["stop", "tool_calls", "length", "error"] = "stop"
    usage: LLMUsage = Field(default_factory=LLMUsage)

class LLMStreamChunk(BaseModel):
    delta_content: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None
    finish_reason: Optional[str] = None

class ToolDefinition(BaseModel):
    type: Literal["function"] = "function"
    function: Dict[str, Any]

class LLMProvider(Protocol):
    """Protocol for all LLM backends (OpenAI, NVIDIA NIM, Local, Fakes)."""

    async def chat_with_tools(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        ...

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        ...

    def generate_structured(
        self,
        *args,
        **kwargs,
    ) -> Any:
        ...

    def rerank(
        self,
        *args,
        **kwargs,
    ) -> Any:
        ...

    def get_model_name(self) -> str:
        ...


class AwaitableList(list):
    """List that can also be awaited in async contexts."""
    def __await__(self):
        async def _id():
            return list(self)
        return _id().__await__()


class GeminiLLMProvider:
    """Gemini API Provider using REST API for zero heavy dependencies."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model
        self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def get_model_name(self) -> str:
        return f"google/{self.model}"

    def generate_structured(self, prompt: Any = None, schema: Any = None, system_prompt: Optional[str] = None, *args, **kwargs) -> Any:
        import requests
        prompt_str = prompt if isinstance(prompt, str) else str(prompt or kwargs.get("prompt", ""))
        target_schema = schema or kwargs.get("schema")
        json_schema = target_schema.model_json_schema() if hasattr(target_schema, "model_json_schema") else {}
        headers = {"Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "contents": [{"parts": [{"text": prompt_str}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.2,
            },
        }
        if json_schema:
            payload["generationConfig"]["response_schema"] = json_schema
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

        resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return target_schema.model_validate_json(raw_text) if hasattr(target_schema, "model_validate_json") else json.loads(raw_text)

    def rerank(self, query: str = "", candidates: Any = None, top_k: int = 5, documents: Any = None, top_n: Optional[int] = None, *args, **kwargs) -> Any:
        import requests
        items = candidates if candidates is not None else (documents or kwargs.get("candidates") or kwargs.get("documents"))
        limit = top_n if top_n is not None else top_k
        if not items:
            return AwaitableList([])
        titles = "\n".join(f"{i}: {c.get('title', c)}" for i, c in enumerate(items))
        prompt = f"Goal: {query}\n\nCandidate Strategies:\n{titles}\n\nReturn the integer indices of the top {limit} most relevant strategies as a JSON array of integers, e.g. [0, 3, 1]."
        try:
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.0},
            }
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
            resp.raise_for_status()
            indices = json.loads(resp.json()["candidates"][0]["content"]["parts"][0]["text"])
            return AwaitableList([items[i] for i in indices if 0 <= i < len(items)][:limit])
        except Exception:
            return AwaitableList(items[:limit])


class FakeLLMProvider:
    """Deterministic, runnable fake for testing without network or API keys."""

    def __init__(self, default_model: str = "fake-nemotron-3", canned_responses: Optional[Dict[str, Any]] = None):
        self.default_model = default_model
        self.canned_responses = canned_responses or {}

    def get_model_name(self) -> str:
        return self.default_model

    async def chat_with_tools(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        last_msg = messages[-1] if messages else Message(role="user", content="")
        content_lower = (last_msg.content or "").lower()

        # If previous message is a tool response, synthesize the final verified answer
        if last_msg.role == "tool":
            tool_data = json.loads(last_msg.content or "{}")
            if "cases" in tool_data.get("data", {}):
                cases = tool_data["data"]["cases"]
                exp = cases.get("expected", {})
                min_c = exp.get("min_cash", "$45,000.00")
                runway = exp.get("runway_weeks", "18")
                return LLMResponse(
                    content=(
                        f"Based on the simulation, your projected minimum cash point is {min_c} "
                        f"with an estimated runway of {runway} weeks. Under worst-case collections, "
                        f"a cash reserve breach is triggered."
                    ),
                    tool_calls=None,
                    finish_reason="stop",
                )
            if "amount" in tool_data.get("data", {}):
                amt = tool_data["data"]["amount"]
                metric = tool_data["data"]["metric_name"]
                return LLMResponse(
                    content=f"Your {metric} for the requested period was ${amt}.",
                    tool_calls=None,
                    finish_reason="stop",
                )
            return LLMResponse(
                content=f"Operation completed with status: {tool_data.get('status', 'ok')}.",
                tool_calls=None,
                finish_reason="stop",
            )

        # 1. Routing & scenario detection: "hire", "late", "developer"
        if any(w in content_lower for w in ["hire", "late", "developer", "delay"]):
            tool_call = ToolCall(
                function=FunctionCall(
                    name="finance.run_scenario",
                    arguments=json.dumps({
                        "name": "Hire 2 Devs + 30d Client Delay",
                        "horizon_weeks": 26,
                        "changes": [
                            {"lever": "hire", "op": "add", "value": 2, "params": {"monthly_cost": 6000}},
                            {"lever": "payment_delay", "op": "set", "value": 30, "params": {"client": "Client Alpha"}},
                        ],
                    }),
                )
            )
            return LLMResponse(tool_calls=[tool_call], finish_reason="tool_calls")

        # 2. Metric lookup: "spend", "balance", "burn"
        if any(w in content_lower for w in ["spend", "balance", "cost", "burn", "software"]):
            metric = "spend" if "spend" in content_lower or "software" in content_lower else "burn"
            tool_call = ToolCall(
                function=FunctionCall(
                    name="finance.get_metric",
                    arguments=json.dumps({"metric_name": metric}),
                )
            )
            return LLMResponse(tool_calls=[tool_call], finish_reason="tool_calls")

        # 3. Moonshot detection: "bold move", "moonshot", "strategy"
        if any(w in content_lower for w in ["bold", "moonshot", "strategy", "fix this"]):
            tool_call = ToolCall(
                function=FunctionCall(
                    name="moonshot.run",
                    arguments=json.dumps({"goal": last_msg.content or "Protect cash runway"}),
                )
            )
            return LLMResponse(tool_calls=[tool_call], finish_reason="tool_calls")

        # 4. Memory detection: "remember", "note that"
        if "remember" in content_lower or "note that" in content_lower:
            tool_call = ToolCall(
                function=FunctionCall(
                    name="memory.write",
                    arguments=json.dumps({
                        "category": "payroll_terms",
                        "key": "payroll_date",
                        "value": "Payroll is scheduled on the 28th of every month.",
                    }),
                )
            )
            return LLMResponse(tool_calls=[tool_call], finish_reason="tool_calls")

        # 5. Dashboard action: "add chart", "add kpi"
        if "chart" in content_lower or "dashboard" in content_lower:
            tool_call = ToolCall(
                function=FunctionCall(
                    name="dashboard.propose_action",
                    arguments=json.dumps({
                        "action_type": "add_chart",
                        "payload": {"chart_type": "line", "title": "Runway Forecast", "metric": "cash"},
                        "risk_level": "low",
                    }),
                )
            )
            return LLMResponse(tool_calls=[tool_call], finish_reason="tool_calls")

        # Fallback normal conversational response
        return LLMResponse(
            content=f"I have received your inquiry: '{last_msg.content}'. How can NeuralCFO assist your decision?",
            tool_calls=None,
            finish_reason="stop",
        )

    async def stream_chat(
        self,
        messages: List[Message],
        tools: Optional[List[ToolDefinition]] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[LLMStreamChunk, None]:
        resp = await self.chat_with_tools(messages, tools, model, temperature, max_tokens)
        if resp.tool_calls:
            yield LLMStreamChunk(tool_calls=resp.tool_calls, finish_reason="tool_calls")
        elif resp.content:
            words = resp.content.split(" ")
            for i, word in enumerate(words):
                delta = word + (" " if i < len(words) - 1 else "")
                yield LLMStreamChunk(delta_content=delta)
            yield LLMStreamChunk(finish_reason="stop")

    def generate_structured(
        self,
        prompt: Any = None,
        schema: Any = None,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        messages: Any = None,
        *args,
        **kwargs,
    ) -> Any:
        target_schema = schema or kwargs.get("schema")
        raw_prompt = prompt if prompt is not None else messages or kwargs.get("prompt") or kwargs.get("messages")
        
        prompt_text = ""
        if isinstance(raw_prompt, str):
            prompt_text = raw_prompt
        elif isinstance(raw_prompt, list):
            prompt_text = " ".join(str(getattr(m, "content", m)) for m in raw_prompt)
        else:
            prompt_text = str(raw_prompt or "")

        prompt_lower = prompt_text.lower()
        schema_name = getattr(target_schema, "__name__", "").lower()

        if target_schema and hasattr(target_schema, "model_validate"):
            if "assumption" in schema_name or "decompose" in prompt_lower:
                canned = {
                    "assumptions": [
                        {
                            "text": "Enterprise clients will accept 100% upfront deposits on retainer contracts",
                            "importance": 90.0,
                            "is_critical": True,
                            "category": "demand",
                        },
                        {
                            "text": "Self-serve onboarding flow will convert free users without dedicated sales staff",
                            "importance": 85.0,
                            "is_critical": True,
                            "category": "demand",
                        },
                        {
                            "text": "Core delivery team of 4 can deliver 3 concurrent retainers without burnout",
                            "importance": 70.0,
                            "is_critical": False,
                            "category": "execution",
                        },
                    ]
                }
                return target_schema.model_validate(canned)
            if "stresstest" in schema_name or "pre-mortem" in prompt_lower or "skeptic" in prompt_lower:
                canned = {
                    "pre_mortem_scenarios": [
                        {
                            "failure_mode": "Key clients reject upfront retainer terms and delay signing",
                            "probability": "medium",
                            "impact": "high",
                            "mitigation": "Offer 50% split deposit with 5% discount for 100% prepay",
                        },
                        {
                            "failure_mode": "Self-serve freemium usage explodes server costs before monetization",
                            "probability": "low",
                            "impact": "medium",
                            "mitigation": "Set strict free tier quotas and automated upgrade prompts",
                        },
                    ],
                    "experiments": [
                        {
                            "title": "30-Day Retainer Pilot",
                            "metric": "Deposit acceptance rate",
                            "target": ">= 60% of new proposals accept upfront retainer",
                            "duration_days": 30,
                        }
                    ],
                }
                return target_schema.model_validate(canned)
            try:
                return target_schema()
            except Exception:
                return target_schema.model_construct()

        return {"intent": "finance_query", "confidence": 0.95}

    def rerank(
        self,
        query: str = "",
        candidates: Any = None,
        top_k: int = 5,
        documents: Any = None,
        top_n: Optional[int] = None,
        *args,
        **kwargs,
    ) -> Any:
        items = candidates if candidates is not None else (documents or kwargs.get("candidates") or kwargs.get("documents"))
        limit = top_n if top_n is not None else top_k
        if not items:
            return AwaitableList([])
        first = items[0]
        if isinstance(first, str):
            return AwaitableList([(i, 1.0 - (i * 0.1)) for i in range(min(limit, len(items)))])
        return AwaitableList(sorted(
            items,
            key=lambda c: (c.get("evidence_tier") != "A", c.get("time_to_signal_days", 999)),
        )[:limit])


def get_llm_provider() -> LLMProvider:
    """Factory creating the appropriate provider based on environment variables."""
    sample_mode = os.getenv("SAMPLE_MODE", "false").lower() == "true"
    gemini_key = os.getenv("GEMINI_API_KEY")

    if not sample_mode and gemini_key:
        return GeminiLLMProvider(api_key=gemini_key)

    return FakeLLMProvider()
