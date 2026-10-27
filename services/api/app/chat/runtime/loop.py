"""Typed Agent Tool Loop (Part B1, Part B2.1, Part B2.3).
Executes LLM tool-calling turns deterministically, emitting SSE events.
"""
import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID, uuid4

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.llm import LLMProvider, Message, ToolCall
from services.api.app.chat.adapters.llm.provider import get_llm_provider
from services.api.app.chat.agents.base import AgentDefinition
from services.api.app.chat.agents.moonshot import moonshot_agent
from services.api.app.chat.agents.neuralcfo import neuralcfo_agent
from services.api.app.chat.runtime.context import ExecutionContext, TurnCitation
from services.api.app.chat.runtime.streamer import (
    sse_action_proposal,
    sse_chart,
    sse_citation,
    sse_done,
    sse_error,
    sse_stage,
    sse_token,
    sse_tool_result,
    sse_tool_start,
)
from services.api.app.chat.tools.registry import tool_registry
from services.api.app.chat.verifier.engine import verifier_engine
from services.api.app.core.auth import AuthContext

class AgentRuntimeLoop:
    def __init__(self, llm_provider: Optional[LLMProvider] = None, max_iterations: int = 5):
        self.llm = llm_provider or get_llm_provider()
        self.max_iterations = max_iterations

    async def execute_turn(
        self,
        conversation_id: UUID,
        user_message: str,
        auth: AuthContext,
        agent_key: str = "neuralcfo",
        history_messages: Optional[List[Message]] = None,
    ) -> AsyncGenerator[str, None]:
        # 1. Initialize execution context
        decision_run_id = uuid4()
        asst_message_id = uuid4()
        ctx = ExecutionContext(
            conversation_id=conversation_id,
            decision_run_id=decision_run_id,
            auth=auth,
        )

        agent: AgentDefinition = moonshot_agent if agent_key == "moonshot" else neuralcfo_agent
        tools = tool_registry.get_definitions_for_agent(agent.allowed_tools)

        # Working message turn sequence
        turn_messages: List[Message] = [Message(role="system", content=agent.system_prompt)]
        if history_messages:
            turn_messages.extend(history_messages)
        turn_messages.append(Message(role="user", content=user_message))

        turn_tool_results: List[Any] = []
        final_answer = ""
        verification_status = "verified"

        try:
            for iteration in range(self.max_iterations):
                llm_response = await self.llm.chat_with_tools(
                    messages=turn_messages,
                    tools=tools,
                    temperature=0.0,
                )

                # Case A: Model issued tool calls
                if llm_response.tool_calls:
                    # Append assistant message with tool calls
                    turn_messages.append(
                        Message(
                            role="assistant",
                            content=llm_response.content,
                            tool_calls=llm_response.tool_calls,
                        )
                    )

                    for tc in llm_response.tool_calls:
                        func_name = tc.function.name
                        raw_args = json.loads(tc.function.arguments or "{}")

                        # Emit tool_start
                        yield sse_tool_start(func_name, raw_args, tc.id)

                        # If tool is moonshot.run, emit starting stages
                        if func_name == "moonshot.run":
                            yield sse_stage(1, "Intake & Safety", "started")
                            yield sse_stage(2, "Decomposition & Constraints", "started")

                        # Execute registered tool
                        result_env = await tool_registry.execute_tool(
                            name=func_name,
                            raw_arguments=raw_args,
                            auth=auth,
                            decision_run_id=decision_run_id,
                        )
                        ctx.tool_results.append(result_env)
                        turn_tool_results.append(result_env.data)

                        # Check if kind is needs_input
                        kind = "needs_input" if isinstance(result_env.data, dict) and result_env.data.get("kind") == "needs_input" else "normal"

                        # Emit tool_result
                        yield sse_tool_result(
                            tool_name=func_name,
                            tool_call_id=tc.id,
                            status=result_env.status,
                            kind=kind,
                            warnings=result_env.warnings,
                            data=result_env.data if kind == "needs_input" else None,
                        )

                        # Emit citation events if tool returned source UUIDs
                        for src_uuid in result_env.sources:
                            cit_id = uuid4()
                            target_type = "source_row" if "metric" in func_name else "forecast_point"
                            yield sse_citation(
                                citation_id=cit_id,
                                target_type=target_type,
                                target_id=src_uuid,
                                label=f"Source [{str(src_uuid)[:8]}]",
                            )

                        # Emit chart event if tool returned scenario cases
                        cases_data = None
                        if hasattr(result_env.data, "cases"):
                            cases_data = {k: v.model_dump() for k, v in result_env.data.cases.items()}
                        elif isinstance(result_env.data, dict) and "cases" in result_env.data:
                            cases_data = result_env.data["cases"]

                        if cases_data:
                            yield sse_chart(
                                chart_type="line",
                                title=raw_args.get("name", "Scenario Forecast"),
                                cases=cases_data,
                            )

                        # Emit action proposal if dashboard action
                        if func_name == "dashboard.propose_action" and isinstance(result_env.data, dict) and "action_id" in result_env.data:
                            yield sse_action_proposal(
                                action_id=UUID(result_env.data["action_id"]),
                                action_type=result_env.data["action_type"],
                                risk_level=result_env.data["risk_level"],
                                preview=result_env.data["preview"],
                                requires_approval=result_env.data["requires_approval"],
                            )

                        # Feed tool result back to LLM for next turn reasoning
                        turn_messages.append(
                            Message(
                                role="tool",
                                tool_call_id=tc.id,
                                name=func_name,
                                content=json.dumps(result_env.model_dump(), default=str),
                            )
                        )
                    continue

                # Case B: Model produced final answer
                final_answer = llm_response.content or ""
                break

            # 2. Run Verifier post-turn
            v_summary = verifier_engine.verify_turn(
                answer_text=final_answer,
                current_turn_tool_results=turn_tool_results,
                caller_org_id=auth.org_id,
                is_report_turn=(agent_key == "moonshot"),
            )
            verification_status = v_summary.overall_status

            # If V9 failure, attempt single regeneration
            if v_summary.should_regenerate:
                retry_prompt = (
                    f"Your answer failed deterministic verification: {v_summary.caveat_message}. "
                    "Regenerate your answer strictly referencing only verified tool result numbers and ensure disclaimers are present."
                )
                turn_messages.append(Message(role="user", content=retry_prompt))
                retry_resp = await self.llm.chat_with_tools(turn_messages, temperature=0.0)
                if retry_resp.content:
                    final_answer = retry_resp.content
                    v_summary_retry = verifier_engine.verify_turn(
                        answer_text=final_answer,
                        current_turn_tool_results=turn_tool_results,
                        caller_org_id=auth.org_id,
                        is_report_turn=(agent_key == "moonshot"),
                    )
                    verification_status = v_summary_retry.overall_status

            # 3. Stream token deltas
            words = final_answer.split(" ")
            for i, word in enumerate(words):
                delta = word + (" " if i < len(words) - 1 else "")
                yield sse_token(delta)
                await asyncio.sleep(0.005)

            # 4. Stream final done event
            yield sse_done(
                message_id=asst_message_id,
                decision_run_id=decision_run_id,
                status=verification_status,
                claims_count=len(turn_tool_results),
            )

        except Exception as e:
            yield sse_error("TURN_EXECUTION_ERROR", str(e))
