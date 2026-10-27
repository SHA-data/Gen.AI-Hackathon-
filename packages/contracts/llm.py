"""LLM Provider protocol and Fake implementation (Part B0.3, B2.1)."""
import json
import re
from typing import Any, AsyncGenerator, Dict, List, Literal, Optional, Protocol, Union
from uuid import uuid4
from pydantic import BaseModel, Field

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

    async def generate_structured(
        self,
        messages: List[Message],
        schema: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5,
    ) -> List[tuple[int, float]]:
        ...

class FakeLLMProvider:
    """Deterministic, runnable fake for testing without network or API keys."""

    def __init__(self, default_model: str = "fake-nemotron-3"):
        self.default_model = default_model

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

        # 2. Metric detection: "spend", "revenue", "cash", "burn"
        if any(w in content_lower for w in ["spend", "spent", "revenue", "cash", "burn"]):
            metric = "spend" if "spend" in content_lower else "cash"
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

    async def generate_structured(
        self,
        messages: List[Message],
        schema: Dict[str, Any],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {"intent": "finance_query", "confidence": 0.95}

    async def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: int = 5,
    ) -> List[tuple[int, float]]:
        return [(i, 1.0 - (i * 0.1)) for i in range(min(top_n, len(documents)))]
