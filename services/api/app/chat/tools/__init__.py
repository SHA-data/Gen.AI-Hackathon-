"""Initialize tool registry with all canonical tools from Part A6."""
from services.api.app.chat.tools.registry import tool_registry
from services.api.app.chat.tools.finance import (
    GetMetricArgs,
    RunScenarioArgs,
    ListSourceRowsArgs,
    ExplainChangeArgs,
    handle_get_metric,
    handle_run_scenario,
    handle_list_source_rows,
    handle_explain_change,
)
from services.api.app.chat.tools.moonshot import MoonshotRunArgs, handle_moonshot_run
from services.api.app.chat.tools.rag import RagSearchArgs, handle_rag_search
from services.api.app.chat.tools.memory import (
    MemoryReadArgs,
    MemoryWriteArgs,
    handle_memory_read,
    handle_memory_write,
)
from services.api.app.chat.tools.action import ProposeActionArgs, handle_propose_action
from services.api.app.chat.tools.search import WebSearchArgs, handle_web_search

# 1. Finance Tools
tool_registry.register(
    name="finance.get_metric",
    description="Retrieve financial metrics (cash, burn, revenue, payroll, spend) with source row references.",
    handler=handle_get_metric,
    args_schema=GetMetricArgs,
    risk_level="low",
    allowed_roles=["viewer", "member", "admin", "owner"],
    timeout_seconds=10.0,
)

tool_registry.register(
    name="finance.run_scenario",
    description="Run the deterministic forecast scenario engine (Part A5) for hiring, delay, or revenue changes.",
    handler=handle_run_scenario,
    args_schema=RunScenarioArgs,
    risk_level="low",
    allowed_roles=["member", "admin", "owner"],
    timeout_seconds=15.0,
)

tool_registry.register(
    name="finance.list_source_rows",
    description="List the exact source transactions behind a figure.",
    handler=handle_list_source_rows,
    args_schema=ListSourceRowsArgs,
    risk_level="low",
    allowed_roles=["viewer", "member", "admin", "owner"],
    timeout_seconds=10.0,
)

tool_registry.register(
    name="finance.explain_change",
    description="Explain why a financial metric changed between two periods.",
    handler=handle_explain_change,
    args_schema=ExplainChangeArgs,
    risk_level="low",
    allowed_roles=["viewer", "member", "admin", "owner"],
    timeout_seconds=10.0,
)

# 2. Moonshot Tool
tool_registry.register(
    name="moonshot.run",
    description="Execute the 6-card Moonshot strategic workflow or collect missing constraints.",
    handler=handle_moonshot_run,
    args_schema=MoonshotRunArgs,
    risk_level="low",
    allowed_roles=["member", "admin", "owner"],
    timeout_seconds=30.0,
)

# 3. RAG Search Tool
tool_registry.register(
    name="rag.search",
    description="Hybrid semantic and keyword search across uploaded organization documents and policies.",
    handler=handle_rag_search,
    args_schema=RagSearchArgs,
    risk_level="low",
    allowed_roles=["viewer", "member", "admin", "owner"],
    timeout_seconds=5.0,
)

# 4. Memory Tools
tool_registry.register(
    name="memory.read",
    description="Read confirmed user and organization memories.",
    handler=handle_memory_read,
    args_schema=MemoryReadArgs,
    risk_level="low",
    allowed_roles=["viewer", "member", "admin", "owner"],
    timeout_seconds=5.0,
)

tool_registry.register(
    name="memory.write",
    description="Propose a fact or business assumption to be remembered (requires user confirmation).",
    handler=handle_memory_write,
    args_schema=MemoryWriteArgs,
    risk_level="medium",
    allowed_roles=["member", "admin", "owner"],
    timeout_seconds=5.0,
)

# 5. Dashboard Action Tool
tool_registry.register(
    name="dashboard.propose_action",
    description="Propose a validated dashboard modification (chart, KPI, date range, report).",
    handler=handle_propose_action,
    args_schema=ProposeActionArgs,
    risk_level="low",
    allowed_roles=["member", "admin", "owner"],
    timeout_seconds=5.0,
)

# 6. Web Search Tool
tool_registry.register(
    name="web.search",
    description="Search the web for current market context (context only; untrusted).",
    handler=handle_web_search,
    args_schema=WebSearchArgs,
    risk_level="low",
    allowed_roles=["member", "admin", "owner"],
    timeout_seconds=10.0,
)
