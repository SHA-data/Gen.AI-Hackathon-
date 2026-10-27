"""Tool Registry (Part A2, Part B1, Part B2.5).
Central registry for all tools called by agents in the Chatbot module.
Enforces typed schemas, execution timeout, RBAC permissions, and server-side org scoping.
"""
import asyncio
import inspect
import json
import time
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel

from packages.contracts.envelope import ToolResultEnvelope
from packages.contracts.llm import ToolDefinition
from services.api.app.core.auth import AuthContext, RoleType
from services.api.app.core.audit import audit_logger

class RegisteredTool:
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable,
        args_schema: type[BaseModel],
        risk_level: str = "low",
        allowed_roles: Optional[List[RoleType]] = None,
        timeout_seconds: float = 15.0,
    ):
        self.name = name
        self.description = description
        self.handler = handler
        self.args_schema = args_schema
        self.risk_level = risk_level
        self.allowed_roles = allowed_roles or ["viewer", "member", "admin", "owner"]
        self.timeout_seconds = timeout_seconds

    def to_openai_tool(self) -> ToolDefinition:
        schema = self.args_schema.model_json_schema()
        # Remove internal fields if any
        schema.get("properties", {}).pop("org_id", None)
        schema.get("properties", {}).pop("auth_context", None)
        return ToolDefinition(
            type="function",
            function={
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        )

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, RegisteredTool] = {}

    def register(
        self,
        name: str,
        description: str,
        handler: Callable,
        args_schema: type[BaseModel],
        risk_level: str = "low",
        allowed_roles: Optional[List[RoleType]] = None,
        timeout_seconds: float = 15.0,
    ):
        self._tools[name] = RegisteredTool(
            name=name,
            description=description,
            handler=handler,
            args_schema=args_schema,
            risk_level=risk_level,
            allowed_roles=allowed_roles,
            timeout_seconds=timeout_seconds,
        )

    def get_tool(self, name: str) -> Optional[RegisteredTool]:
        return self._tools.get(name)

    def get_definitions_for_agent(self, allowed_tool_names: List[str]) -> List[ToolDefinition]:
        return [
            tool.to_openai_tool()
            for name, tool in self._tools.items()
            if name in allowed_tool_names or "*" in allowed_tool_names
        ]

    async def execute_tool(
        self,
        name: str,
        raw_arguments: Dict[str, Any],
        auth: AuthContext,
        decision_run_id: Optional[UUID] = None,
    ) -> ToolResultEnvelope[Any]:
        tool = self._tools.get(name)
        if not tool:
            return ToolResultEnvelope(
                status="failed",
                data={},
                sources=[],
                warnings=[f"Tool '{name}' is not registered."],
                run_id=decision_run_id,
            )

        # 1. RBAC validation
        if auth.role not in tool.allowed_roles:
            await audit_logger.log(
                org_id=auth.org_id,
                actor_user_id=auth.user_id,
                action=f"tool_call:{name}",
                entity_type="tool",
                entity_id=uuid4(),
                decision="denied_role",
                metadata={"required_roles": tool.allowed_roles, "user_role": auth.role},
            )
            return ToolResultEnvelope(
                status="failed",
                data={},
                sources=[],
                warnings=[f"Role '{auth.role}' is not authorized to call tool '{name}'."],
                run_id=decision_run_id,
            )

        # 2. Strict Schema Validation & Org Injection
        # Ensure model cannot supply or overwrite org_id!
        clean_args = {k: v for k, v in raw_arguments.items() if k not in ("org_id", "auth_context")}
        try:
            validated_args = tool.args_schema(**clean_args)
        except Exception as e:
            return ToolResultEnvelope(
                status="failed",
                data={},
                sources=[],
                warnings=[f"Argument validation failed for tool '{name}': {str(e)}"],
                run_id=decision_run_id,
            )

        # 3. Timeout-governed Execution
        start_time = time.time()
        try:
            # Check handler signature to inject auth context
            sig = inspect.signature(tool.handler)
            kwargs = validated_args.model_dump()
            if "auth" in sig.parameters or "auth_context" in sig.parameters:
                kwargs["auth"] = auth
            if "org_id" in sig.parameters:
                kwargs["org_id"] = auth.org_id
            if "user_id" in sig.parameters:
                kwargs["user_id"] = auth.user_id

            result = await asyncio.wait_for(tool.handler(**kwargs), timeout=tool.timeout_seconds)
            duration_ms = int((time.time() - start_time) * 1000)

            # 4. Audit Log
            await audit_logger.log(
                org_id=auth.org_id,
                actor_user_id=auth.user_id,
                action=f"tool_call:{name}",
                entity_type="tool",
                entity_id=result.run_id or uuid4(),
                decision="executed",
                metadata={"duration_ms": duration_ms, "status": result.status},
            )

            return result

        except asyncio.TimeoutError:
            return ToolResultEnvelope(
                status="failed",
                data={},
                sources=[],
                warnings=[f"Tool '{name}' execution timed out after {tool.timeout_seconds}s."],
                run_id=decision_run_id,
            )
        except Exception as ex:
            return ToolResultEnvelope(
                status="failed",
                data={},
                sources=[],
                warnings=[f"Tool '{name}' encountered internal execution error: {str(ex)}"],
                run_id=decision_run_id,
            )

tool_registry = ToolRegistry()
